# Retail Lens — Supermarket Sales Analytics

A runnable portfolio prototype: deterministic POS receipts, decimal validation, an optional LocalStack SQS → Lambda → S3 pipeline, and a Streamlit/DuckDB analytics dashboard.

## Start with the dashboard

Python 3.11+ recommended. From this folder:

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints. Demo mode generates 500 synthetic receipts across three UK stores and 14 days. Filter dates/stores, compare sales and products, inspect hourly checkout volume, and download receipts. Demo mode needs no AWS account or Docker.

## Run the local cloud pipeline

Requires Docker with permission to launch containers. Lambda needs the Docker socket mount. LocalStack distribution/authentication requirements can change: configure LOCALSTACK_AUTH_TOKEN if your installation requires one. Compose uses `latest` for initial setup; pin a tested image version before relying on reproducible builds. This configuration is local development only.

```bash
docker compose up -d
# Wait for LocalStack to report ready in docker compose logs.
python setup_local_aws.py
python generate_sales.py
python send_to_sqs_local.py
python query_lake_duckdb.py
streamlit run app.py
```

Select **Processed lake export** in the dashboard. This mode reads `data/lake.json`, exported from the actual S3 emulator; it does not query S3 continuously. Rerun the export to refresh it. CLI analytics fetch S3 objects through boto3 and query them with DuckDB locally; no httpfs extension or Athena deployment is included.

## Data contract and reliability

Each receipt has a safe receipt ID and store ID, timezone-aware purchase timestamp, GBP currency, nonempty line items, positive integer quantities, and decimal-string money. Validation checks every line and the basket total. S3 paths partition on the UTC purchase date and store:

`receipts/year=2026/month=10/day=01/store_id=LONDON-001/R-42-000000.json`

Repeated delivery of an identical receipt overwrites the same object rather than creating another row. Receipt IDs must identify immutable purchases; conflicting revisions using the same ID are not detected. This is replay safety for identical events, not exactly-once processing. Production would need conflict detection, schema/version controls, monitoring, access policies and infrastructure management.

The Lambda returns only failed SQS message IDs. Provisioning explicitly enables `ReportBatchItemFailures`. A 90-second visibility timeout exceeds six times the 15-second Lambda timeout; the redrive policy sends repeatedly failed messages to a DLQ after three receives. Automated unit tests cover mixed batches and write failures; an end-to-end DLQ test is not included.

## Verify

```bash
python -m unittest test_receipts -v
python -c "from receipts import generate; from analytics import tables; print(tables(generate())['summary'])"
```

No real AWS resources are provisioned by these scripts; local clients require a loopback emulator endpoint and use dummy credentials.

## Publish a portfolio demo

Push these source files to a GitHub repository, then configure a compatible Streamlit hosting service with `app.py` as its entry point and this requirements file. The hosted dashboard runs in synthetic demo mode. Hosting, account setup and publication are not performed by this package. Do not upload credentials or commit `.env` files.


## Author

**Kedharnath Thanikonda**  
GitHub: [@KEDHAR2004](https://github.com/KEDHAR2004)

## Acknowledgements

Thanks to [@yharshithareddy](https://github.com/yharshithareddy) for their support with this project.

## Reference documentation

- https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html
- https://docs.localstack.cloud/aws/services/lambda/
- https://docs.localstack.cloud/aws/services/sqs/
