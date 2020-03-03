import os
import boto3

def s3_upload_file(source, bucket, destination):
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_s3_endpoint=os.getenv("AWS_S3_ENDPOINT")

    endpoint_url=f"http://{aws_s3_endpoint}"

    s3 = boto3.client('s3',
                      aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key,
                      endpoint_url=endpoint_url)

    s3.upload_file(source, bucket, destination)
