import json
import duckdb

def tables(rows):
    # Parameterized JSON input; decimal casts preserve financial aggregation precision.
    with duckdb.connect() as con:
        con.execute("CREATE TABLE receipts AS SELECT unnest(?::JSON::STRUCT(receipt_id VARCHAR, store_id VARCHAR, purchased_at VARCHAR, currency VARCHAR, items STRUCT(product VARCHAR, quantity INTEGER, unit_price_gbp VARCHAR, line_total_gbp VARCHAR)[], total_gbp VARCHAR)[]) AS payload", [json.dumps(rows)])
        # Expand the struct returned above into a regular relation.
        con.execute("CREATE VIEW sales AS SELECT payload.* FROM receipts")
        return {
            "summary": con.execute("SELECT count(*) receipts, coalesce(sum(total_gbp::DECIMAL(18,2)),0) revenue, coalesce(avg(total_gbp::DECIMAL(18,2)),0) basket FROM sales").df(),
            "stores": con.execute("SELECT store_id, count(*) receipts, sum(total_gbp::DECIMAL(18,2)) revenue FROM sales GROUP BY 1 ORDER BY 3 DESC").df(),
            "products": con.execute("SELECT item.product product, sum(item.quantity) units, sum(item.line_total_gbp::DECIMAL(18,2)) revenue FROM sales, UNNEST(items) t(item) GROUP BY 1 ORDER BY 2 DESC").df(),
            "hours": con.execute("SELECT hour(purchased_at::TIMESTAMPTZ) hour_utc, count(*) receipts FROM sales GROUP BY 1 ORDER BY 1").df(),
        }
