# Bank Loan / Credit Risk & Default Prediction — Design

## Goal
Portfolio project assessing whether a borrower will repay a loan or default, based on historical profile data. Deliverable is an end-to-end pipeline (SQL + Python + ML + BI dashboard), fully free/open tooling.

## Problem Statement
Given historical loan application data (borrower profile, loan terms, payment status), analyze the loan portfolio and predict the likelihood a loan will default (be "Charged Off") vs. be paid back ("Fully Paid").

## Dataset
- Public bank-loan dataset in the style of the well-known "Bank Loan Dashboard" Kaggle dataset (`financial_loan.csv`), ~38k rows.
- Columns include: loan_id, issue_date, loan_amount, funded_amount (or similar), term, int_rate, installment, grade/sub_grade, emp_length, home_ownership, annual_income, purpose, dti, loan_status (Fully Paid / Charged Off / Current), address_state, application_type, etc.
- No API key required; downloaded as a CSV (or synthesized with the same schema/stats if the exact Kaggle file can't be fetched directly) and stored under `data/raw/`.

## Tech Stack (all free)
- **Python** (pandas, scikit-learn, matplotlib/seaborn for EDA) — cleaning, feature engineering, ML model.
- **SQLite** — local file database (`data/loans.db`), no server install needed.
- **Power BI Desktop** (free) — final multi-page interactive dashboard.

## Pipeline

### 1. Data Cleaning (Python)
- Load raw CSV, fix dtypes (dates, numerics), handle nulls/duplicates.
- Derive columns:
  - `loan_status_group`: Good Loan (Fully Paid, Current) vs Bad Loan (Charged Off).
  - `risk_tier`: bucketed from `grade`/`int_rate`/`dti` (e.g. Low/Medium/High/Very High).
  - `issue_month`, `issue_year` for trend charts.
- Save cleaned dataset to `data/processed/loans_clean.csv`.

### 2. SQL Layer (SQLite)
- Load cleaned CSV into `data/loans.db` as table `loans`.
- Write SQL views/queries for dashboard KPIs:
  - Total loan applications, total funded amount, total amount received.
  - Good loan % vs Bad loan % (count and amount).
  - Breakdowns: by state, purpose, term, grade, home ownership, employment length.
  - Monthly/MTD trend of applications and funded amount.
- Scripts live in `sql/` (`schema.sql`, `kpi_queries.sql`).

### 3. ML Model (Python / scikit-learn)
- Binary classification target: `is_default` (1 = Charged Off, 0 = Fully Paid/Current).
- Features: loan_amount, term, int_rate, installment, grade, emp_length, home_ownership, annual_income, purpose, dti, state (encoded).
- Models: Logistic Regression (baseline) + Random Forest (comparison).
- Evaluate: accuracy, precision, recall, F1, ROC-AUC, confusion matrix.
- Output: feature importance chart, and a `predicted_risk_score` / `predicted_label` column written back to a scored CSV (`data/processed/loans_scored.csv`) for use in the dashboard's Risk/Prediction page.
- Code lives in `notebooks/` or `src/model.py`.

### 4. Power BI Dashboard (3 pages)
Since Power BI has no native SQLite connector, the dashboard will read from the CSV/Parquet exports produced by steps 1–3 (`loans_clean.csv`, `loans_scored.csv`) — simplest, fully free, no ODBC driver setup required.

- **Page 1 – Summary:** Total applications, total funded amount, total amount received, good vs bad loan KPIs, month-over-month trend lines.
- **Page 2 – Overview:** Breakdowns by region/state (map), loan term, purpose, employment length, home ownership (bar/donut charts).
- **Page 3 – Risk & Prediction:** Risk tier distribution, grade vs actual default rate, model-predicted default risk distribution, top feature importances.

## Project Structure
```
Data Analyst Project/
├── data/
│   ├── raw/                 # original downloaded CSV
│   └── processed/           # cleaned + scored CSVs
├── sql/                     # schema.sql, kpi_queries.sql
├── src/                     # clean.py, load_db.py, model.py
├── dashboard/                # .pbix file
├── docs/specs/  # this design doc
└── README.md
```

## Error Handling / Edge Cases
- Missing/null values in income, emp_length, dti → imputed or flagged, not dropped blindly.
- "Current" loans (not yet resolved) excluded from the ML training target but included in descriptive KPIs.
- Class imbalance (defaults are a minority) → handled via class_weight='balanced' or stratified split, noted in model evaluation.

## Testing / Validation
- Row-count and null-count sanity checks after cleaning.
- Train/test split with stratification; report metrics on held-out test set.
- Manual spot-check of a few KPI numbers (e.g. total applications) against raw data in SQL.

## Out of Scope
- No real-time data ingestion or production deployment.
- No paid APIs, cloud databases, or paid BI licenses.
- Tableau version not built initially (can be added later as a stretch goal).
