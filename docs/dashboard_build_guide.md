# Power BI Dashboard Build Guide

Build the 3-page dashboard in **Power BI Desktop** (free, Microsoft Store). Allow about 1.5-2 hours. Every formula and setting is below; copy-paste as you go.

## 0. Files you need (all in this repo)

| File | Used for |
|---|---|
| `data/processed/loans_scored.csv` | Main table (has every column from `loans_clean.csv` plus the model's predictions) |
| `data/processed/feature_importance.csv` | Model drivers chart (Page 3) |
| `data/processed/model_metrics.json` | Quote the numbers in a text box (Page 3) |
| `dashboard/theme.json` | Colors and fonts (import once) |

> We load only `loans_scored.csv`. It is a superset of `loans_clean.csv`, so loading both would just duplicate data.

## 1. Load the data

1. Open Power BI Desktop, then **Home > Get data > Text/CSV**.
2. Pick `loans_scored.csv`, then **Transform Data** (not Load).
3. In Power Query, set these types (header icon > Data type):
   - `issue_date` = **Date**
   - `loan_amount`, `funded_amount`, `int_rate`, `installment`, `annual_income`, `dti`, `total_payment`, `predicted_risk_score` = **Decimal number**
   - `term`, `is_default`, `predicted_label`, `issue_month`, `issue_year`, `loan_id` = **Whole number**
   - Everything else = **Text**
4. Rename the query to `loans` (right-hand Query Settings pane).
5. **Close & Apply**.
6. Repeat **Get data > Text/CSV** for `feature_importance.csv` and **Load** it. Name it `feature_importance`.
7. **View > Themes > Browse for themes** and pick `dashboard/theme.json`.

## 2. Date table (needed for month-over-month)

**Modeling > New table**, paste:

```dax
Date =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2015, 1, 1 ), DATE ( 2017, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Month No", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM" ),
    "Year-Month", FORMAT ( [Date], "YYYY-MM" )
)
```

Then:
1. **Table tools > Mark as date table** > Date column = `Date`.
2. Select the `Month` column > **Column tools > Sort by column** > `Month No`.
3. **Model view**: drag `Date[Date]` onto `loans[issue_date]` (many-to-one, single direction).

## 3. Calculated column for ordering risk bands

Risk labels sort alphabetically by default ("High", "Low", "Medium"...). Fix with a sort key.
**Modeling > New column** on `loans`:

```dax
Risk Tier Order =
SWITCH ( loans[risk_tier], "Low", 1, "Medium", 2, "High", 3, "Very High", 4, 5 )
```

```dax
Predicted Band Order =
SWITCH ( loans[predicted_risk_band], "Low", 1, "Medium", 2, "High", 3, "Very High", 4, 5 )
```

Select `risk_tier` > **Sort by column** > `Risk Tier Order`. Select `predicted_risk_band` > **Sort by column** > `Predicted Band Order`.

## 4. Measures

Create a blank table first: **Home > Enter data**, name it `_Measures`, then right-click it > **New measure** for each of these.

```dax
Total Applications = COUNTROWS ( loans )

Total Funded Amount = SUM ( loans[funded_amount] )

Total Amount Received = SUM ( loans[total_payment] )

Avg Interest Rate = AVERAGE ( loans[int_rate] ) / 100

Avg DTI = AVERAGE ( loans[dti] ) / 100

Good Loan Applications =
CALCULATE ( [Total Applications], loans[loan_status_group] IN { "Good Loan", "Current" } )

Bad Loan Applications =
CALCULATE ( [Total Applications], loans[loan_status_group] = "Bad Loan" )

Good Loan % = DIVIDE ( [Good Loan Applications], [Total Applications] )

Bad Loan % = DIVIDE ( [Bad Loan Applications], [Total Applications] )

Good Loan Funded Amount =
CALCULATE ( [Total Funded Amount], loans[loan_status_group] IN { "Good Loan", "Current" } )

Bad Loan Funded Amount =
CALCULATE ( [Total Funded Amount], loans[loan_status_group] = "Bad Loan" )

Good Loan Amount Received =
CALCULATE ( [Total Amount Received], loans[loan_status_group] IN { "Good Loan", "Current" } )

Bad Loan Amount Received =
CALCULATE ( [Total Amount Received], loans[loan_status_group] = "Bad Loan" )

Default Rate (Resolved) =
DIVIDE (
    CALCULATE ( [Total Applications], loans[loan_status_group] = "Bad Loan" ),
    CALCULATE ( [Total Applications], loans[loan_status_group] IN { "Good Loan", "Bad Loan" } )
)

Avg Predicted Risk = AVERAGE ( loans[predicted_risk_score] )

Funded MTD = TOTALMTD ( [Total Funded Amount], 'Date'[Date] )

Funded PMTD =
CALCULATE ( [Total Funded Amount], DATEADD ( 'Date'[Date], -1, MONTH ) )

Funded MoM % = DIVIDE ( [Funded MTD] - [Funded PMTD], [Funded PMTD] )

Applications MTD = TOTALMTD ( [Total Applications], 'Date'[Date] )

Applications PMTD =
CALCULATE ( [Total Applications], DATEADD ( 'Date'[Date], -1, MONTH ) )

Applications MoM % = DIVIDE ( [Applications MTD] - [Applications PMTD], [Applications PMTD] )
```

Set formats (select measure > **Measure tools**): `Total Funded Amount`/`Total Amount Received`/`...Funded Amount`/`...Received` = **Currency, $, 0 decimals**; all `%` and `Avg...Rate/DTI` and `Default Rate` = **Percentage, 1-2 decimals**; counts = **Whole number, thousands separator**.

> **Definition note:** "Good Loan" here follows the project spec (Fully Paid **plus** Current). `Default Rate (Resolved)` is the stricter measure: bad loans out of loans with a known outcome only. Use it for model discussion; use `Bad Loan %` for the headline KPI.

## 5. Page layout (16:9, 1280 x 720)

For each page: **View > Page view > Fit to page**, rename the tab as shown, add a title text box (Segoe UI Semibold 20pt) top-left, and a thin left or top navigation row of buttons (**Insert > Buttons > Navigator > Page navigator**) so the three pages link together.

### Page 1: "Summary"

Top row of KPI **Cards** (each with a small Card visual under the number for the MTD/MoM value):

| Position | Visual | Field | Sub-label |
|---|---|---|---|
| 1 | Card | `Total Applications` | `Applications MTD`, `Applications MoM %` |
| 2 | Card | `Total Funded Amount` | `Funded MTD`, `Funded MoM %` |
| 3 | Card | `Total Amount Received` | |
| 4 | Card | `Avg Interest Rate` | |
| 5 | Card | `Avg DTI` | |

Middle:
- **Donut**: Legend = `loans[loan_status_group]`, Values = `Total Applications`. Colors: Good = green, Bad = red, Current = amber (Format > Slices > Colors).
- **Table**: a "Loan Status" grid. Rows = `loan_status_group`; Values = `Total Applications`, `Total Funded Amount`, `Total Amount Received`.
- **Cards row** for Good vs Bad: `Good Loan %`, `Bad Loan %`, `Good Loan Funded Amount`, `Bad Loan Funded Amount`, `Good Loan Amount Received`, `Bad Loan Amount Received`.

Bottom:
- **Line chart**: X = `Date[Year-Month]`, Y = `Total Funded Amount`. Add `Total Amount Received` as a second line.

Slicers (right edge): `Date[Year]` (tile style), `loans[loan_status_group]` (dropdown), `loans[term]` (tile).

### Page 2: "Overview"

Six visuals, 3 x 2 grid. All use `Total Funded Amount` unless noted; turn on **data labels**, and use "Total Applications" in the tooltip (Format > Tooltips or drag into the Tooltips well).

| Visual | Axis | Notes |
|---|---|---|
| **Filled map** (or Shape map) | `address_state` | Set Location > Data category = **State or Province**; add "US" under Location > Country if needed. If the map renders blank, fall back to a sorted bar chart. |
| **Bar chart** | `purpose` | Sort descending by value |
| **Donut** | `term` | 36 vs 60 months |
| **Column chart** | `emp_length` | Sort axis by `emp_length`; cleaner if you add a sort column (below) |
| **Bar chart** | `home_ownership` | |
| **Table or matrix** | Rows = `grade`; Values = `Total Applications`, `Avg Interest Rate`, `Bad Loan %` | Conditional formatting: data bars on `Bad Loan %` |

For a proper `emp_length` order, add this column to `loans`:

```dax
Emp Length Order =
SWITCH ( loans[emp_length],
    "< 1 year", 0, "1 year", 1, "2 years", 2, "3 years", 3, "4 years", 4,
    "5 years", 5, "6 years", 6, "7 years", 7, "8 years", 8, "9 years", 9,
    "10+ years", 10, 11 )
```

Select `emp_length` > **Sort by column** > `Emp Length Order`.

Same slicers as Page 1: sync them via **View > Sync slicers** (tick all pages for `Year` and `loan_status_group`).

### Page 3: "Risk & Prediction"

Top row: cards for `Default Rate (Resolved)`, `Avg Predicted Risk`, and a text box with the model numbers from `model_metrics.json` (best model **Logistic Regression**, ROC-AUC **0.703**, recall **61.8%**, precision **23.4%**, accuracy **66.6%**).

| Visual | Setup |
|---|---|
| **Clustered column** | Axis = `risk_tier`; Values = `Total Applications` |
| **Combo (column + line)** | Axis = `risk_tier`; Column = `Total Funded Amount`; Line = `Default Rate (Resolved)` |
| **Column chart** | Axis = `grade`; Values = `Default Rate (Resolved)` (should climb from A to G; that is the key insight) |
| **Column chart** | Axis = `predicted_risk_band`; Values = `Total Applications` |
| **Clustered column** (validation) | Axis = `predicted_risk_band`; Values = `Default Rate (Resolved)`. The rate should rise Low to Very High; this proves the model separates risk. |
| **Bar chart** | Axis = `feature_importance[feature]`; Values = Sum of `importance`. **Filters pane > Top N** = Top 15 by `importance`. Sort descending. |

Add a text box "How to read this" explaining risk tiers (Low = grades A-B, Medium = C-D, High = E, Very High = F-G) and that predicted bands come from the model.

## 6. Polish checklist

- [ ] Same slicer positions across pages
- [ ] Every visual has a clear title; axes labeled with units
- [ ] **View > Gridlines/Snap** used so visuals align
- [ ] Hover tooltips work; click a bar on each page and confirm other visuals cross-filter
- [ ] Rename pages: Summary, Overview, Risk & Prediction
- [ ] Hide `Risk Tier Order`, `Predicted Band Order`, `Emp Length Order` columns (right-click > Hide in report view)

## 7. Validate against SQL (do this before saving)

The Summary page cards must match the SQL results (these are from Phase 3):

| Metric | Expected |
|---|---|
| Total Applications | 38,000 |
| Total Funded Amount | $740,864,963 |
| Total Amount Received | $729,020,174 |
| Bad Loan applications | 4,876 (12.8%) |
| Good Loan (Fully Paid) | 30,128 |
| Current | 2,996 |

If a number differs, check the column data types from step 1.3 first.

## 8. Save and export

1. **File > Save as** `dashboard/BankLoanCreditRisk.pbix`.
2. Take a screenshot of each page for the README: **File > Export > Export to PDF**, or use Windows Snipping Tool. Save PNGs as `dashboard/page1_summary.png`, `page2_overview.png`, `page3_risk.png`.
3. Commit the files to the repository.
