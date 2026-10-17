import random
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

PRODUCTS = {"Milk": "1.50", "Bread": "1.20", "Eggs": "2.50", "Apples": "0.60", "Bananas": "0.35", "Rice": "3.25", "Pasta": "1.10", "Cheese": "2.80"}
STORES = ["LONDON-001", "LONDON-002", "MANCHESTER-001"]

def money(value):
    if not isinstance(value, str):
        raise ValueError("Money must be a decimal string")
    try:
        d = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid money") from exc
    if not d.is_finite() or d < 0 or d.as_tuple().exponent < -2:
        raise ValueError("Money must be finite, nonnegative, with at most two decimals")
    return d

def validate(r):
    if not isinstance(r, dict):
        raise ValueError("Receipt must be an object")
    for field in ("receipt_id", "store_id"):
        if not isinstance(r.get(field), str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", r[field]):
            raise ValueError("Invalid " + field)
    dt = datetime.fromisoformat(r["purchased_at"])
    if dt.tzinfo is None:
        raise ValueError("Timestamp requires timezone")
    if r.get("currency") != "GBP" or not isinstance(r.get("items"), list) or not r["items"]:
        raise ValueError("GBP and nonempty items required")
    total = Decimal("0.00")
    for item in r["items"]:
        if not isinstance(item.get("product"), str) or not item["product"].strip():
            raise ValueError("Product required")
        q = item.get("quantity")
        if type(q) is not int or q <= 0:
            raise ValueError("Positive integer quantity required")
        line = money(item["unit_price_gbp"]) * q
        if line != money(item["line_total_gbp"]):
            raise ValueError("Line total mismatch")
        total += line
    if total != money(r["total_gbp"]):
        raise ValueError("Receipt total mismatch")
    return dt.astimezone(timezone.utc)

def object_key(r):
    dt = validate(r)
    return f"receipts/year={dt:%Y}/month={dt:%m}/day={dt:%d}/store_id={r['store_id']}/{r['receipt_id']}.json"

def generate(count=500, seed=42):
    rng = random.Random(seed)
    result = []
    base = datetime(2026, 10, 1, 8, tzinfo=timezone.utc)
    for n in range(count):
        items = []
        for product in rng.sample(list(PRODUCTS), rng.randint(1, 5)):
            q = rng.randint(1, 4)
            items.append(dict(product=product, quantity=q, unit_price_gbp=PRODUCTS[product], line_total_gbp=str(Decimal(PRODUCTS[product])*q)))
        result.append(dict(receipt_id=f"R-{seed}-{n:06}", store_id=rng.choice(STORES), purchased_at=(base+timedelta(days=rng.randrange(14), minutes=rng.randrange(720))).isoformat(), currency="GBP", items=items, total_gbp=str(sum((Decimal(i['line_total_gbp']) for i in items), Decimal('0.00')))))
    return result
