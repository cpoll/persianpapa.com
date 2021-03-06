import os

import yaml
from troposphere import Base64, Join, Ref, Template, GetAtt, Output, Export, Tags, Split, Select, ImportValue
from troposphere import (
    ec2, elasticloadbalancingv2, autoscaling, iam, ecs, s3, cloudwatch, sns, kms, certificatemanager, route53, cloudfront)

from util import create_or_update_stack


# Load stack config
stack_config_file = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'stack_config.yml')
CONFIG = yaml.load(open(stack_config_file), Loader=yaml.Loader)['config']

###
# Initialize template
###
t = Template()
t.set_version('2010-09-09')

###
# Shared Tags
###
shared_tags_args = {
    'Stack': CONFIG['STACK_NAME'],
}


###
# As of July 2018:
# When you use the AWS::CertificateManager::Certificate resource in an AWS CloudFormation stack, the stack will remain
# in the CREATE_IN_PROGRESS state and any further stack operations will be delayed until you act upon the instructions
# in the certificate validation email. (DNS validation is not supported).
# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-certificatemanager-certificate.html
#
# Furthermore, DNS validation is not supported (only email validation)
#
# Workaround:
# - Run CloudFormation with this commented out the first time
# - Set up DNS (NS pointing to hosted zone) and webmaster@domain
#

CloudFrontCertificate = t.add_resource(certificatemanager.Certificate(
    'CloudFrontCertificate',
    DomainName=CONFIG['DOMAIN_NAME'],
    SubjectAlternativeNames=CONFIG.get('SUBJECT_ALTERNATIVE_NAMES') or [],
    Tags=Tags(**shared_tags_args),
))

###
# CloudFront OriginAccessIdentity
###
# OriginAccessIdentity = t.add_resource(cloudfront.CloudFrontOriginAccessIdentity(
#     'OriginAccessIdentity',
#     CloudFrontOriginAccessIdentityConfig=cloudfront.CloudFrontOriginAccessIdentityConfig(
#         Comment=f'{CONFIG["STACK_NAME"]}'
#     )
# ))

###
# S3 Bucket
###
StaticHostingPublicBucketName = f'{CONFIG["DOMAIN_NAME"]}'
StaticHostingPublicBucket = t.add_resource(s3.Bucket(
    'StaticHostingPublicBucket',
    BucketName=StaticHostingPublicBucketName,
    DeletionPolicy='Retain',
    # LoggingConfiguration=s3.LoggingConfiguration(
    #     LogFilePrefix='s3-server-access-logs/'
    # ),
    AccessControl="PublicRead",
    VersioningConfiguration=s3.VersioningConfiguration(
        Status='Enabled'
    ),

    # Enable website configuration to handle various redirect behaviours (e.g. /a -> /a/index.html)
    WebsiteConfiguration=s3.WebsiteConfiguration(
        ErrorDocument='error.html',
        IndexDocument='index.html'
    ),
    Tags=Tags(**shared_tags_args),
))
t.add_resource(s3.BucketPolicy(
    'StaticHostingPublicBucketPolicy',
    Bucket=Ref(StaticHostingPublicBucket),
    PolicyDocument={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicRead",
                "Action": ["s3:GetObject"],
                "Effect":"Allow",
                "Resource": [
                    Join("", ["arn:aws:s3:::", Ref(StaticHostingPublicBucket), "/*"]),
                    Join("", ["arn:aws:s3:::", Ref(StaticHostingPublicBucket)]),
                ],
                "Principal": "*",
            }
        ]
    }
))

###
# Cloudfront Distribution
###
CloudfrontDistribution = t.add_resource(cloudfront.Distribution(
    "CloudfrontDistribution",
    DistributionConfig=cloudfront.DistributionConfig(
        Aliases=[CONFIG['DOMAIN_NAME']],
        Origins=[
            cloudfront.Origin(
                Id="Origin 1",

                # turn `http://mybucket.s3-website-us-east-1.amazonaws.com/`y
                # into `mybucket.s3-website-us-east-1.amazonaws.com`
                DomainName=Select(2, Split("/", GetAtt(StaticHostingPublicBucket, 'WebsiteURL'))),

                # S3 website hosting only serves on 80
                CustomOriginConfig=cloudfront.CustomOriginConfig(
                    HTTPPort=80,
                    OriginProtocolPolicy='http-only',
                )
            )
        ],
        ViewerCertificate=cloudfront.ViewerCertificate(
            AcmCertificateArn=Ref(CloudFrontCertificate),
            SslSupportMethod='sni-only',
        ),
        DefaultCacheBehavior=cloudfront.DefaultCacheBehavior(
            TargetOriginId="Origin 1",
            ForwardedValues=cloudfront.ForwardedValues(
                QueryString=False
            ),
            ViewerProtocolPolicy="redirect-to-https",
            AllowedMethods=["GET", "HEAD"],
            DefaultTTL=86400  # one day
        ),
        DefaultRootObject='index.html',
        Enabled=True,
        HttpVersion='http2',
        # Logging=cloudfront.Logging(
        #     Bucket=GetAtt(CloudfrontLogBucket, 'DomainName'),
        #     IncludeCookies=False
        # ),
        PriceClass='PriceClass_100',
    ),
    Tags=Tags(**shared_tags_args)
))


###
# Route 53
###
HostedZone = t.add_resource(route53.HostedZone(
    'HostedZone',
    Name=CONFIG['DOMAIN_NAME'],
    HostedZoneConfig=route53.HostedZoneConfiguration(
        Comment=f'{CONFIG["STACK_NAME"]} stack HostedZone'
    ),
))

t.add_resource(route53.RecordSetGroup(
    'HostedZoneRecordSetGroup',
    HostedZoneId=Ref(HostedZone),
    RecordSets=[
        route53.RecordSet(
            'HostedZoneAliasToCloudFront',
            Name=f'{CONFIG["DOMAIN_NAME"]}.',
            Type='A',
            AliasTarget=route53.AliasTarget(
                HostedZoneId='Z2FDTNDATAQYW2',  # CloudFront HostedZoneId magic string
                DNSName=GetAtt(CloudfrontDistribution, 'DomainName'),
            )
        ),
        route53.RecordSet(
            'HostedZoneAliasToCloudFrontIpv6',
            Name=f'{CONFIG["DOMAIN_NAME"]}.',
            Type='AAAA',
            AliasTarget=route53.AliasTarget(
                HostedZoneId='Z2FDTNDATAQYW2',  # CloudFront HostedZoneId magic string
                DNSName=GetAtt(CloudfrontDistribution, 'DomainName'),
            )
        )
    ]
))


if __name__ == '__main__':

    stack_policy = '''{ "Statement" : [
        {
            "Effect" : "Allow",
            "Principal" : "*",
            "Action" : "Update:*",
            "Resource" : "*"
        }
    ]}'''

    create_or_update_stack(
        stack_name=CONFIG['STACK_NAME'],
        template=t,
        stack_policy=stack_policy,
        aws_region_name=CONFIG['AWS_REGION_NAME'],
        notification_arn=CONFIG.get('CLOUDFORMATION_NOTIFICATION_ARN'),
        cf_template_bucket=CONFIG['CF_TEMPLATE_BUCKET'])
