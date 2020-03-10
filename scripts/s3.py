import os
import boto3

class S3Client:
    """
    A simple interface for uploading small files to an S3 bucket
    """

    def __init__(self):
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_s3_endpoint_url = os.getenv("AWS_S3_ENDPOINT_URL")

        self.s3_client = boto3.client('s3',
                                      aws_access_key_id=aws_access_key_id,
                                      aws_secret_access_key=aws_secret_access_key,
                                      endpoint_url=aws_s3_endpoint_url)

    def upload_file(self, source, bucket, destination):
        self.s3_client.upload_file(source, bucket, destination)

