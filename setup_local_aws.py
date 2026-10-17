import io
import json
import zipfile
from pathlib import Path
from local_aws import client, BUCKET, QUEUE, DLQ

def main():
    s3, sqs, iam, lam = [client(s) for s in ("s3", "sqs", "iam", "lambda")]
    s3.create_bucket(Bucket=BUCKET)
    dlq = sqs.create_queue(QueueName=DLQ)["QueueUrl"]
    arn = sqs.get_queue_attributes(QueueUrl=dlq, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
    url = sqs.create_queue(QueueName=QUEUE, Attributes={"VisibilityTimeout": "90", "RedrivePolicy": json.dumps({"deadLetterTargetArn": arn, "maxReceiveCount": "3"})})["QueueUrl"]
    queue_arn = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
    role_name = "retail-lambda-role"
    try:
        role = iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps({"Version":"2012-10-17", "Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}))["Role"]
    except iam.exceptions.EntityAlreadyExistsException:
        role = iam.get_role(RoleName=role_name)["Role"]
    iam.put_role_policy(RoleName=role_name, PolicyName="retail-local", PolicyDocument=json.dumps({"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:PutObject"],"Resource":f"arn:aws:s3:::{BUCKET}/*"},{"Effect":"Allow","Action":["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"],"Resource":queue_arn},{"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Resource":"*"}]}))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for f in ("lambda_function.py", "receipts.py"):
            z.write(Path(__file__).parent/f, f)
    name = "retail-receipt-validator"
    try:
        lam.get_function(FunctionName=name)
    except lam.exceptions.ResourceNotFoundException:
        lam.create_function(FunctionName=name, Runtime="python3.12", Role=role["Arn"], Handler="lambda_function.handler", Code={"ZipFile":buf.getvalue()}, Timeout=15, Environment={"Variables":{"BUCKET_NAME":BUCKET}})
    else:
        lam.update_function_code(FunctionName=name, ZipFile=buf.getvalue())
    lam.get_waiter("function_active_v2").wait(FunctionName=name)
    if not lam.list_event_source_mappings(FunctionName=name, EventSourceArn=queue_arn)["EventSourceMappings"]:
        lam.create_event_source_mapping(FunctionName=name, EventSourceArn=queue_arn, BatchSize=10, FunctionResponseTypes=["ReportBatchItemFailures"])
    print("Local pipeline ready:", url)
if __name__ == "__main__":
    main()
