-- ==============================================================================
-- 05_ltv_by_plan.sql
-- Customer Lifetime Value (LTV) and Logo Churn by Plan (MySQL 8.0+)
--
-- Logic:
-- 1. Evaluates total exposure (active subscription-months) and churned subscriptions by plan.
-- 2. Uses explicit parameter CTE for Gross Margin (default 80% / 0.80).
-- 3. Computes:
--      - Monthly Churn Rate = churned_subscriptions / active_sub_months
--      - LTV Estimate = (ARPA * Gross Margin) / Monthly Churn Rate
-- 4. Flags low sample groups (< 30 distinct customers) and reports 'not estimable'
--    if monthly churn rate is zero.
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
gross_margin_param AS (
    -- Configurable gross margin parameter
    SELECT 0.80 AS gross_margin
),
plan_metadata AS (
    SELECT 'Basic' AS plan, 19.00 AS arpa
    UNION ALL
    SELECT 'Pro' AS plan, 49.00 AS arpa
    UNION ALL
    SELECT 'Business' AS plan, 99.00 AS arpa
),
plan_exposure AS (
    -- Calculate active subscription-months per plan across calendar
    SELECT 
        s.plan,
        COUNT(*) AS active_sub_months
    FROM subscriptions s
    JOIN calendar cal
        ON s.start_date <= cal.month_end
        AND (s.end_date IS NULL OR s.end_date > cal.month_end)
    GROUP BY s.plan
),
plan_churn_events AS (
    -- Count churn events and unique customers per plan
    SELECT 
        plan,
        COUNT(DISTINCT customer_id) AS sample_size,
        SUM(CASE WHEN end_reason IN ('voluntary_churn', 'involuntary_churn') THEN 1 ELSE 0 END) AS churned_subscriptions
    FROM subscriptions
    GROUP BY plan
),
plan_metrics AS (
    SELECT 
        pm.plan,
        pm.arpa,
        gmp.gross_margin,
        ROUND(gmp.gross_margin * 100, 1) AS gross_margin_pct,
        pce.sample_size,
        COALESCE(pe.active_sub_months, 0) AS active_sub_months,
        COALESCE(pce.churned_subscriptions, 0) AS churned_subscriptions,
        CASE 
            WHEN COALESCE(pe.active_sub_months, 0) > 0 
            THEN ROUND(pce.churned_subscriptions * 1.0 / pe.active_sub_months, 4)
            ELSE 0.0000 
        END AS monthly_churn_rate
    FROM plan_metadata pm
    CROSS JOIN gross_margin_param gmp
    LEFT JOIN plan_exposure pe ON pm.plan = pe.plan
    LEFT JOIN plan_churn_events pce ON pm.plan = pce.plan
)
SELECT 
    plan,
    arpa,
    gross_margin_pct,
    monthly_churn_rate,
    sample_size,
    CASE 
        WHEN sample_size < 30 THEN 1 
        ELSE 0 
    END AS is_low_sample,
    CASE 
        WHEN monthly_churn_rate > 0 
        THEN CAST(ROUND((arpa * gross_margin) / monthly_churn_rate, 2) AS CHAR)
        ELSE 'not estimable'
    END AS ltv_estimate
FROM plan_metrics
ORDER BY arpa ASC;
