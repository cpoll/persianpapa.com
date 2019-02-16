'''
Script to update website-redirect-location for files in s3
'''

import os
import yaml
import argparse

import boto3


def change_website_redirect_location(s3_resource, bucket, key, redirect_location):
    s3_object = s3_resource.Object(bucket, key)
    s3_object.copy_from(
        CopySource={
            'Bucket': bucket,
            'Key': key
        },
        WebsiteRedirectLocation=redirect_location
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', type=str, help='bucket name, e.g. persianpapa.com')
    parser.add_argument('--definition-file', type=str, help='path to list of redirects')
    parser.add_argument('--destination-base', type=str,
                        help='base path, string replaces {BASE_PATH} in the definition file')
    args = parser.parse_args()

    redirect_definitions = yaml.load(open(args.definition_file), Loader=yaml.Loader)['redirects']

    s3_resource = boto3.resource('s3')

    for redirect in redirect_definitions:
        change_website_redirect_location(
            s3_resource,
            args.bucket,
            redirect['key'],
            redirect['destination'].format(BASE_PATH=args.destination_base)
        )
