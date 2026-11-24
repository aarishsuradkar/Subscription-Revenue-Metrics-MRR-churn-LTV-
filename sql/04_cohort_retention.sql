-- ==============================================================================
-- 04_cohort_retention.sql
-- Cohort Retention: Logo Retention and Revenue Retention (MySQL 8.0+)
--
-- Logic:
-- 1. Identifies each customer's cohort month based on signup_date.
-- 2. Identifies initial cohort size and initial cohort starting MRR at month 0.
-- 3. Evaluates active subscriptions for each cohort across months-since-signup (tenure months).
-- 4. Uses CTEs and window functions to compute:
--      - Logo retention % = active_customers_at_tenure / cohort_size * 100
--      - Revenue retention % = active_mrr_at_tenure / cohort_initial_mrr * 100
-- 5. Month 0 retention is 100% by definition.
--
-- DISCLAIMER: Synthetic data modelled on Stripe-style subscription billing.
-- ==============================================================================

USE subscription_analytics;

WITH RECURSIVE calendar AS (
    SELECT 
        CAST('2023-01-01' AS DATE) AS month_start,
        LAST_DAY(CAST('2023-01-01' AS DATE)) AS month_end
    UNION ALL
    SELECT 
        DATE_ADD(month_start, INTERVAL 1 MONTH),
        LAST_DAY(DATE_ADD(month_start, INTERVAL 1 MONTH))
    FROM calendar
    WHERE month_start < CAST('2025-12-01' AS DATE)
),
customer_cohorts AS (
    -- Customer cohort assignment & initial starting price
    SELECT 
        c.customer_id,
        DATE_FORMAT(c.signup_date, '%Y-%m') AS cohort_month,
        DATE_FORMAT(c.signup_date, '%Y-%m-01') AS cohort_start_date,
        s.monthly_price AS initial_mrr,
        ROW_NUMBER() OVER (
            PARTITION BY c.customer_id 
            ORDER BY s.start_date ASC
        ) AS rn
    FROM customers c
    JOIN subscriptions s ON c.customer_id = s.customer_id
),
first_subscriptions AS (
    SELECT 
        customer_id,
        cohort_month,
        CAST(cohort_start_date AS DATE) AS cohort_start_date,
        initial_mrr
    FROM customer_cohorts
    WHERE rn = 1
),
cohort_summaries AS (
    SELECT 
        cohort_month,
        cohort_start_date,
        COUNT(DISTINCT customer_id) AS cohort_size,
        SUM(initial_mrr) AS cohort_initial_mrr
    FROM first_subscriptions
    GROUP BY cohort_month, cohort_start_date
),
cohort_calendar_tenure AS (
    -- Cross join cohorts with calendar months where month >= cohort_start
    SELECT 
        cs.cohort_month,
        cs.cohort_size,
        cs.cohort_initial_mrr,
        cal.month_end,
        -- Calculate tenure in completed months
        TIMESTAMPDIFF(MONTH, cs.cohort_start_date, cal.month_start) AS tenure_months
    FROM cohort_summaries cs
    JOIN calendar cal 
        ON cal.month_start >= cs.cohort_start_date
),
cohort_active_at_tenure AS (
    SELECT 
        cct.cohort_month,
        cct.cohort_size,
        cct.cohort_initial_mrr,
        cct.tenure_months,
        cct.month_end,
        COUNT(DISTINCT s.customer_id) AS active_customers,
        COALESCE(SUM(s.monthly_price), 0.00) AS active_mrr
    FROM cohort_calendar_tenure cct
    JOIN first_subscriptions fs 
        ON fs.cohort_month = cct.cohort_month
    LEFT JOIN subscriptions s
        ON s.customer_id = fs.customer_id
        AND s.start_date <= cct.month_end
        AND (s.end_date IS NULL OR s.end_date > cct.month_end)
    GROUP BY 
        cct.cohort_month,
        cct.cohort_size,
        cct.cohort_initial_mrr,
        cct.tenure_months,
        cct.month_end
)
SELECT 
    cohort_month,
    cohort_size,
    cohort_initial_mrr,
    tenure_months,
    CASE 
        WHEN tenure_months = 0 THEN 100.00
        ELSE ROUND(active_customers * 100.0 / cohort_size, 2)
    END AS logo_retention_pct,
    CASE 
        WHEN tenure_months = 0 THEN 100.00
        WHEN cohort_initial_mrr > 0 THEN ROUND(active_mrr * 100.0 / cohort_initial_mrr, 2)
        ELSE 0.00
    END AS revenue_retention_pct
FROM cohort_active_at_tenure
ORDER BY cohort_month ASC, tenure_months ASC;
