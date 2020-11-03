import boto3
from boto3.session import Session
import botocore
import os
import sys


def image_sort(elem):
    """Basic sort element"""
    return elem.get('CreationDate')


def main():
    ami_name_pattern = os.environ["INPUT_AMI_NAME_PATTERN"]
    pr_number = os.environ["INPUT_PR_NUMBER"]
    aws_region = os.environ["INPUT_AWS_REGION"]
    aws_owner_account = os.environ["INPUT_AWS_OWNER_ACCOUNT"]
    aws_access_key = os.environ["INPUT_AWS_ACCESS_KEY"]
    aws_secret_key = os.environ["INPUT_AWS_SECRET_KEY"]

    if 'INPUT_AWS_ADDITIONAL_ACCOUNTS' in os.environ:
        aws_additional_accounts = os.environ["INPUT_AWS_ADDITIONAL_ACCOUNTS"]
    else:
        aws_additional_accounts = False

    if 'INPUT_AWS_ROLE_ARN' in os.environ:
        aws_role_arn = os.environ["INPUT_AWS_ROLE_ARN"]
    else:
        aws_role_arn = False

    # configure a client using a role if provided
    if aws_role_arn:
        try:
            client = boto3.client(
                'sts',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region)

            response = client.assume_role(
                RoleArn=aws_role_arn,
                RoleSessionName='github-promote-ami'
            )
        except botocore.exceptions.ClientError as e:
            sys.exit(e)

        session = Session(
            aws_access_key_id=response['Credentials']['AccessKeyId'],
            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
            aws_session_token=response['Credentials']['SessionToken']
        )

        client = session.client(
            'ec2',
            region_name=aws_region
        )

    else:
        client = boto3.client(
            'ec2',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )

    # retrieve the AMI id of the target AMI based on name and PR_number
    try:
        response = client.describe_images(
            Filters=[
                {
                    'Name': 'name',
                    'Values': [
                        ami_name_pattern
                    ]
                },
                {
                    'Name': 'tag:PR_number',
                    'Values': [
                        pr_number
                    ]
                }
            ],
            Owners=[aws_owner_account]
        )
    except botocore.exceptions.ClientError as e:
        sys.exit(e)

    images = response.get('Images')
    images.sort(key=image_sort, reverse=True)

    # promote the most recent ami that is found
    if len(images):
        ami_id = images[0]['ImageId']
        ami_name = images[0]['Name']
        ebs_volumes = images[0]['BlockDeviceMappings']

        print(f"Found AMI ID {ami_id}")

        num_images = len(images)

        # if more than one image exists, delete older images from previous PRs
        if num_images > 1:
            print('Delete old images')
            for n in range(1, num_images):
                print(f"Deleting {images[n]['ImageId']}")

                try:
                    client.deregister_image(
                        ImageId=images[n]['ImageId']
                    )
                except botocore.exceptions.ClientError as e:
                    sys.exit(e)

                # also need to delete snapshots associated with this ami
                for volume in images[n]['BlockDeviceMappings']:
                    if 'Ebs' in volume:
                        print(f"Deleting snapshot {volume['Ebs']['SnapshotId']}")
                        try:
                            client.delete_snapshot(
                                SnapshotId=volume['Ebs']['SnapshotId']
                            )
                        except botocore.exceptions.ClientError as e:
                            sys.exit(e)

        # update the AMI tag to production
        response = client.create_tags(
            Resources=[
                ami_id
            ],
            Tags=[
                {
                    'Key': 'Release',
                    'Value': 'Production'
                }
            ]
        )

        # modify the snapshots to allow access from accounts if necessary
        if aws_additional_accounts:
            for volume in ebs_volumes:
                if 'Ebs' in volume:
                    try:
                        response = client.modify_snapshot_attribute(
                            Attribute='createVolumePermission',
                            SnapshotId=volume['Ebs']['SnapshotId'],
                            OperationType='add',
                            UserIds=[aws_additional_accounts]
                        )
                    except botocore.exceptions.ClientError as e:
                        sys.exit(e)

        # set GitHub Action output variables
        print(f"::set-output name=ami_id::{ami_id}")
        print(f"::set-output name=ami_name::{ami_name}")

    # no ami found
    else:
        sys.exit('No AMI found matching input pattern.')


if __name__ == "__main__":
    main()
