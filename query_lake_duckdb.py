import json
from pathlib import Path
from local_aws import client, BUCKET
from analytics import tables

def main():
    s3 = client("s3")
    rows = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix="receipts/"):
        for obj in page.get("Contents", []):
            rows.append(json.loads(s3.get_object(Bucket=BUCKET, Key=obj["Key"])["Body"].read()))
    if not rows:
        raise SystemExit("No processed receipts. Run generator and publisher first.")
    Path("data").mkdir(exist_ok=True)
    Path("data/lake.json").write_text(json.dumps(rows))
    for name, table in tables(rows).items():
        print(name, table.to_string(index=False), sep="\n")
if __name__ == "__main__":
    main()
