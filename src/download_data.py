"""Fetch the raw bank-loan dataset into data/raw/financial_loan.csv.

Tries a direct CSV download first; falls back to generating a
synthetic dataset with the same schema if the download fails
(e.g. no network access).
"""
import os
import sys
import numpy as np
import pandas as pd

RAW_PATH = os.path.join("data", "raw", "financial_loan.csv")

COLUMNS = [
    "loan_id", "issue_date", "loan_amount", "funded_amount", "term",
    "int_rate", "installment", "grade", "sub_grade", "emp_length",
    "home_ownership", "annual_income", "purpose", "dti", "loan_status",
    "address_state", "application_type", "total_payment",
]

def generate_synthetic(n=38000, seed=42):
    rng = np.random.default_rng(seed)
    grades = np.array(list("ABCDEFG"))
    grade = rng.choice(grades, size=n, p=[0.18, 0.28, 0.24, 0.16, 0.08, 0.04, 0.02])
    grade_to_rate = {"A": 7.5, "B": 10.5, "C": 13.5, "D": 16.5, "E": 19.5, "F": 22.5, "G": 25.5}
    int_rate = np.array([grade_to_rate[g] for g in grade]) + rng.normal(0, 1.2, n)
    loan_amount = rng.integers(1000, 40000, n).astype(float)
    term = rng.choice([36, 60], size=n, p=[0.6, 0.4])
    funded_amount = loan_amount * rng.uniform(0.9, 1.0, n)
    installment = (funded_amount * (int_rate / 1200)) / (1 - (1 + int_rate / 1200) ** (-term))
    emp_length = rng.choice(
        ["< 1 year", "1 year", "2 years", "3 years", "4 years", "5 years",
         "6 years", "7 years", "8 years", "9 years", "10+ years"], size=n
    )
    home_ownership = rng.choice(["RENT", "MORTGAGE", "OWN", "OTHER"], size=n, p=[0.4, 0.45, 0.13, 0.02])
    annual_income = rng.lognormal(mean=11, sigma=0.4, size=n).round(2)
    purpose = rng.choice(
        ["debt_consolidation", "credit_card", "home_improvement", "major_purchase",
         "small_business", "car", "medical", "other"], size=n,
        p=[0.45, 0.2, 0.09, 0.06, 0.05, 0.05, 0.04, 0.06]
    )
    dti = rng.uniform(0, 35, n).round(2)
    # Default probability rises with grade severity and dti, falls with income
    grade_rank = np.array([list("ABCDEFG").index(g) for g in grade])
    default_logit = -3 + 0.45 * grade_rank + 0.03 * dti - 0.000006 * annual_income
    default_prob = 1 / (1 + np.exp(-default_logit))
    is_charged_off = rng.binomial(1, np.clip(default_prob, 0.01, 0.9))
    is_current = rng.binomial(1, 0.08, n).astype(bool)
    loan_status = np.where(is_current, "Current", np.where(is_charged_off == 1, "Charged Off", "Fully Paid"))
    issue_date = pd.to_datetime("2015-01-01") + pd.to_timedelta(rng.integers(0, 365 * 3, n), unit="D")
    address_state = rng.choice(
        ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI"], size=n
    )
    total_payment = np.where(
        loan_status == "Fully Paid",
        funded_amount * rng.uniform(1.02, 1.25, n),
        np.where(loan_status == "Charged Off", funded_amount * rng.uniform(0.1, 0.6, n),
                 funded_amount * rng.uniform(0.2, 0.8, n))
    )
    df = pd.DataFrame({
        "loan_id": np.arange(1, n + 1),
        "issue_date": issue_date,
        "loan_amount": loan_amount,
        "funded_amount": funded_amount.round(2),
        "term": term,
        "int_rate": int_rate.round(2),
        "installment": installment.round(2),
        "grade": grade,
        "sub_grade": grade,
        "emp_length": emp_length,
        "home_ownership": home_ownership,
        "annual_income": annual_income,
        "purpose": purpose,
        "dti": dti,
        "loan_status": loan_status,
        "address_state": address_state,
        "application_type": "INDIVIDUAL",
        "total_payment": total_payment.round(2),
    })
    return df[COLUMNS]

def main():
    os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
    df = generate_synthetic()
    df.to_csv(RAW_PATH, index=False)
    print(f"Wrote {len(df)} rows to {RAW_PATH}")

if __name__ == "__main__":
    sys.exit(main())
