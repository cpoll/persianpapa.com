from datetime import datetime

import boto3


def upload_template_to_s3(s3_client, stack_name, bucket_name, timestamp, template):
    '''
    Upload tropo template to S3 and return the bucket url
    '''

    object_name = f'{stack_name}/{timestamp}.json'

    template_json = template.to_json()

    s3_client.put_object(
        Body=template_json.encode('utf-8'),
        Bucket=bucket_name,
        Key=object_name
    )

    return f'https://s3.amazonaws.com/{bucket_name}/{object_name}'


def create_or_update_stack(stack_name, template, stack_policy, aws_region_name,
                           cf_template_bucket, notification_arn=None):
    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')

    # Create the stack
    stack_params = {
        'StackName': stack_name,
        'TimeoutInMinutes': 30,
        'Capabilities': ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
        # 'ResourceTypes':['AWS::IAM::Role'],
        # 'RoleARN':'string',
        'OnFailure': 'DO_NOTHING',
        'StackPolicyBody': stack_policy,
        'Tags': [
            # {
            #     'Key': 'Name',
            #     'Value': 'string'
            # },
        ],
        'ClientRequestToken': f'{stack_name}-{timestamp}',
        'EnableTerminationProtection': False
    }
    if notification_arn:
        stack_params['NotificationARNs'] = [notification_arn]

    # Create boto3 clients
    cloudformation_client = boto3.client(
        'cloudformation',
        region_name=aws_region_name
    )
    s3_client = boto3.client(
        's3',
        region_name=aws_region_name
    )

    # Check if stack exists
    try:
        cloudformation_client.describe_stacks(StackName=stack_name)
        stack_exists = True
    except cloudformation_client.exceptions.ClientError as e:
        if 'does not exist' in e.response['Error']['Message']:
            stack_exists = False
        else:
            raise

    if stack_exists and input(f"\nUpdate stack {stack_name} (N/y)? ").lower() == 'y':
        print("Applying stack policy to existing stack")
        response = cloudformation_client.set_stack_policy(
            StackName=stack_name,
            StackPolicyBody=stack_policy
        )
        print(response)

        print("Updating stack")
        stack_params.pop('TimeoutInMinutes', None)
        stack_params.pop('OnFailure', None)
        stack_params.pop('EnableTerminationProtection', None)
        stack_params.pop('StackPolicyBody', None)
        stack_params['TemplateURL'] = upload_template_to_s3(s3_client, stack_name, cf_template_bucket,
                                                            timestamp, template)
        response = cloudformation_client.update_stack(**stack_params)
        print(response)

    elif not stack_exists and input(f"\nCreate stack {stack_name} (N/y)? ").lower() == 'y':
        print("Creating stack")
        stack_params['TemplateURL'] = upload_template_to_s3(s3_client, stack_name, cf_template_bucket,
                                                            timestamp, template)
        response = cloudformation_client.create_stack(**stack_params)
        print(response)
