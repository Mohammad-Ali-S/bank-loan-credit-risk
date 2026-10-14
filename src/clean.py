"""Clean the raw loan CSV and engineer dashboard/ML-ready columns."""
import os
import pandas as pd

RAW_PATH = os.path.join("data", "raw", "financial_loan.csv")
CLEAN_PATH = os.path.join("data", "processed", "loans_clean.csv")

RISK_BUCKETS = {
    "A": "Low", "B": "Low", "C": "Medium", "D": "Medium",
    "E": "High", "F": "Very High", "G": "Very High",
}

def load_raw(path=RAW_PATH):
    df = pd.read_csv(path, parse_dates=["issue_date"])
    return df

def clean(df):
    df = df.drop_duplicates(subset="loan_id").copy()

    numeric_cols = ["loan_amount", "funded_amount", "int_rate", "installment",
                     "annual_income", "dti", "total_payment"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["loan_amount", "funded_amount", "int_rate", "loan_status"])

    df["annual_income"] = df["annual_income"].fillna(df["annual_income"].median())
    df["dti"] = df["dti"].fillna(df["dti"].median())
    df["emp_length"] = df["emp_length"].fillna("Unknown")

    df["loan_status_group"] = df["loan_status"].map({
        "Fully Paid": "Good Loan",
        "Current": "Current",
        "Charged Off": "Bad Loan",
    })
    df["is_default"] = df["loan_status"].map({
        "Fully Paid": 0, "Charged Off": 1, "Current": pd.NA
    })
    df["risk_tier"] = df["grade"].map(RISK_BUCKETS).fillna("Medium")
    df["issue_month"] = df["issue_date"].dt.month
    df["issue_year"] = df["issue_date"].dt.year
    return df

def main():
    os.makedirs(os.path.dirname(CLEAN_PATH), exist_ok=True)
    df = clean(load_raw())
    df.to_csv(CLEAN_PATH, index=False)
    print(f"Rows: {len(df)}")
    print(f"Nulls per column:\n{df.isna().sum()[df.isna().sum() > 0]}")
    print(f"loan_status_group counts:\n{df['loan_status_group'].value_counts()}")
    print(f"Wrote cleaned data to {CLEAN_PATH}")

if __name__ == "__main__":
    main()
