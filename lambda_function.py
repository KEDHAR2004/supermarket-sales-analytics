import json
import logging
import os
from receipts import object_key
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
_s3 = None

def get_s3():
    global _s3
    if _s3 is None:
        import boto3
        host = os.environ.get("LOCALSTACK_HOSTNAME")
        endpoint = f"http://{host}:4566" if host else os.environ.get("AWS_ENDPOINT_URL")
        _s3 = boto3.client("s3", endpoint_url=endpoint)
    return _s3

def handler(event, context):
    failures = []
    for record in event["Records"]:
        try:
            receipt = json.loads(record["body"])
            key = object_key(receipt)
            get_s3().put_object(Bucket=os.environ["BUCKET_NAME"], Key=key, Body=json.dumps(receipt).encode(), ContentType="application/json")
            logger.info(json.dumps({"status": "stored", "message_id": record["messageId"], "key": key}))
        except Exception as exc:
            logger.warning(json.dumps({"status": "failed", "message_id": record["messageId"], "error_type": type(exc).__name__}))
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
