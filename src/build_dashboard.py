"""Build the self-contained interactive dashboard (dashboard/index.html)."""
import json
import os

import pandas as pd

SCORED_PATH = os.path.join("data", "processed", "loans_scored.csv")
IMPORTANCE_CSV = os.path.join("data", "processed", "feature_importance.csv")
METRICS_PATH = os.path.join("data", "processed", "model_metrics.json")
TEMPLATE_PATH = os.path.join("src", "dashboard_template.html")
OUT_PATH = os.path.join("dashboard", "index.html")

CATEGORICALS = {
    "status": "loan_status_group", "term": "term", "grade": "grade", "tier": "risk_tier",
    "band": "predicted_risk_band", "state": "address_state", "purpose": "purpose",
    "emp": "emp_length", "home": "home_ownership",
}


def encode(series):
    s = series.astype(str)
    names = sorted(s.unique())
    lookup = {n: i for i, n in enumerate(names)}
    return {"names": names, "codes": [lookup[v] for v in s]}


def main():
    df = pd.read_csv(SCORED_PATH, parse_dates=["issue_date"])
    data = {
        "n": len(df),
        "cols": {
            "year": df["issue_year"].tolist(),
            "month": df["issue_month"].tolist(),
            "funded": df["funded_amount"].round(2).tolist(),
            "recv": df["total_payment"].round(2).tolist(),
            "int_rate": df["int_rate"].round(2).tolist(),
            "dti": df["dti"].round(2).tolist(),
            "pred": df["predicted_risk_score"].round(4).tolist(),
        },
        "cats": {k: encode(df[col]) for k, col in CATEGORICALS.items()},
        "importance": pd.read_csv(IMPORTANCE_CSV).round(4).to_dict("records"),
        "metrics": json.load(open(METRICS_PATH)),
    }
    html = open(TEMPLATE_PATH, encoding="utf-8").read().replace(
        "__DATA__", json.dumps(data, separators=(",", ":")))
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT_PATH} ({os.path.getsize(OUT_PATH) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
