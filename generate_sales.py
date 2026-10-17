import argparse
import json
from pathlib import Path
from receipts import generate
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("count must be positive")
    Path("data").mkdir(exist_ok=True)
    Path("data/sales.json").write_text(json.dumps(generate(args.count, args.seed), indent=2))
    print(f"Created {args.count} synthetic receipts in data/sales.json")
