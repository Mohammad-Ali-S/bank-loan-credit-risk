-- Total applications, funded amount, received amount
SELECT
    COUNT(*) AS total_applications,
    SUM(funded_amount) AS total_funded_amount,
    SUM(total_payment) AS total_amount_received
FROM loans;

-- Good vs Bad loan split (count and amount)
SELECT
    loan_status_group,
    COUNT(*) AS num_loans,
    SUM(funded_amount) AS funded_amount
FROM loans
GROUP BY loan_status_group;

-- Risk tier breakdown
SELECT risk_tier, COUNT(*) AS num_loans, AVG(int_rate) AS avg_int_rate
FROM loans
GROUP BY risk_tier
ORDER BY avg_int_rate;

-- Monthly trend
SELECT issue_year, issue_month, COUNT(*) AS num_loans, SUM(funded_amount) AS funded_amount
FROM loans
GROUP BY issue_year, issue_month
ORDER BY issue_year, issue_month;

-- Breakdown by state / purpose / term / home_ownership
SELECT address_state, COUNT(*) AS num_loans, SUM(funded_amount) AS funded_amount
FROM loans GROUP BY address_state ORDER BY funded_amount DESC;

SELECT purpose, COUNT(*) AS num_loans, SUM(funded_amount) AS funded_amount
FROM loans GROUP BY purpose ORDER BY funded_amount DESC;

SELECT term, COUNT(*) AS num_loans, SUM(funded_amount) AS funded_amount
FROM loans GROUP BY term;

SELECT home_ownership, COUNT(*) AS num_loans, SUM(funded_amount) AS funded_amount
FROM loans GROUP BY home_ownership ORDER BY funded_amount DESC;
