import json
import time
from pathlib import Path
from local_aws import client, BUCKET, QUEUE
from receipts import object_key

def main():
    receipts = json.loads(Path("data/sales.json").read_text())
    expected = {object_key(r) for r in receipts}
    sqs, s3 = client("sqs"), client("s3")
    url = sqs.get_queue_url(QueueName=QUEUE)["QueueUrl"]
    for start in range(0, len(receipts), 10):
        result = sqs.send_message_batch(QueueUrl=url, Entries=[{"Id":str(i), "MessageBody":json.dumps(r)} for i,r in enumerate(receipts[start:start+10])])
        if result.get("Failed"):
            raise RuntimeError(result["Failed"])
    deadline = time.monotonic()+180
    while time.monotonic()<deadline:
        found = {o["Key"] for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix="receipts/") for o in page.get("Contents",[])}
        if expected <= found:
            print(f"Verified all {len(expected)} expected receipt objects in S3")
            return
        time.sleep(2)
    raise TimeoutError("Some expected receipts did not reach S3; inspect Lambda logs and DLQ")
if __name__ == "__main__":
    main()
