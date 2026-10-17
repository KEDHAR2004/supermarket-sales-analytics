import json
from datetime import datetime
from pathlib import Path
import streamlit as st
from receipts import generate, validate
from analytics import tables
st.set_page_config(page_title="Retail Lens | Sales Analytics", page_icon="🛒", layout="wide")
st.title("Retail Lens")
st.caption("SUPERMARKET SALES ANALYTICS · Python / DuckDB / SQS / Lambda / S3")
lake_file = Path(__file__).parent / "data/lake.json"
sources = ["Synthetic demo"]
if lake_file.exists():
    sources.append("Processed lake export")
mode = st.sidebar.radio("Data source", sources)
if mode == "Synthetic demo":
    rows = generate()
    st.info("Demo: 500 synthetic receipts. These have not passed through SQS or Lambda.")
else:
    path = Path(__file__).parent/"data/lake.json"
    if not path.exists():
        st.warning("Run query_lake_duckdb.py to export your processed LocalStack S3 receipts first.")
        st.stop()
    rows = json.loads(path.read_text())
    st.success("Source: exported LocalStack S3 objects. Run the export again to refresh.")
for r in rows:
    validate(r)
stores = st.sidebar.multiselect("Stores", sorted({r['store_id'] for r in rows}), default=sorted({r['store_id'] for r in rows}))
dates = sorted({datetime.fromisoformat(r['purchased_at']).date() for r in rows})
period = st.sidebar.date_input("Purchase dates", (dates[0], dates[-1]), min_value=dates[0], max_value=dates[-1])
if len(period) != 2:
    st.stop()
filtered = [r for r in rows if r['store_id'] in stores and period[0] <= datetime.fromisoformat(r['purchased_at']).date() <= period[1]]
if not filtered:
    st.warning("No receipts match these filters.")
    st.stop()
t = tables(filtered)
s = t['summary'].iloc[0]
a,b,c = st.columns(3)
a.metric("Receipts", f"{int(s['receipts']):,}")
b.metric("Gross sales", f"£{s['revenue']:,.2f}")
c.metric("Average basket", f"£{s['basket']:,.2f}")
l,r = st.columns(2)
with l:
    st.subheader("Store performance")
    st.bar_chart(t['stores'].set_index('store_id')['revenue'])
    st.dataframe(t['stores'], hide_index=True)
with r:
    st.subheader("Top products")
    st.bar_chart(t['products'].set_index('product')['units'])
    st.dataframe(t['products'], hide_index=True)
st.subheader("Checkout volume by hour · UTC")
st.line_chart(t['hours'].set_index('hour_utc')['receipts'])
st.download_button("Download filtered receipts", json.dumps(filtered, indent=2), "receipts.json", "application/json")
with st.expander("How this project works"):
    st.markdown("POS simulator → SQS → Lambda validation → partitioned S3 objects → local export → DuckDB → dashboard. Failed records are retried individually; the queue redrives repeatedly failing messages to a DLQ.")
st.caption("Portfolio prototype · Synthetic data · Not a production deployment")
st.divider()
st.markdown(
    "**Authors:** "
    "[Kedharnath Thanikonda](https://github.com/KEDHAR2004) · "
    "[Harshitha Reddy](https://github.com/yharshithareddy)"
)
st.markdown(
    "[View project source on GitHub]"
    "(https://github.com/KEDHAR2004/supermarket-sales-analytics)"
)
