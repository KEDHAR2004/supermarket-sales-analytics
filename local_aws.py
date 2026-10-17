import os
import boto3
BUCKET = "retail-receipts"
QUEUE = "retail-receipts"
DLQ = "retail-receipts-dlq"
def client(service):
    endpoint = os.environ.get("LOCAL_AWS_ENDPOINT", "http://localhost:4566")
    # This project provisions only local emulation; never default to a real AWS account.
    from urllib.parse import urlparse
    if urlparse(endpoint).hostname not in ("localhost", "127.0.0.1", "localhost.localstack.cloud"):
        raise ValueError("LocalStack loopback endpoint required")
    return boto3.client(service, endpoint_url=endpoint, region_name="us-east-1", aws_access_key_id="test", aws_secret_access_key="test")
