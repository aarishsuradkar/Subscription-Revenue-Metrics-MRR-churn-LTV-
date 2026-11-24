-- ==============================================================================
-- 03_churn_rate.sql
-- Monthly Logo Churn, Gross Revenue Churn, NRR, GRR, and Quick Ratio (MySQL 8.0+)
--
-- Logic:
-- 1. Evaluates active customer counts and MRR at each month-end.
-- 2. Compares against prior month using LAG() window functions.
-- 3. Computes:
--      - Logo Churn Rate: Churned Customers / Opening Active Customers
--      - Gross Revenue Churn Rate: (Churned MRR + Contraction MRR) / Opening MRR
--      - Net Revenue Retention (NRR): (Opening MRR + Expansion - Contraction - Churned) / Opening MRR
--      - Gross Revenue Retention (GRR): (Opening MRR - Contraction - Churned) / Opening MRR
--      - Quick Ratio: (New MRR + Expansion MRR) / (Churned MRR + Contraction MRR)
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
customer_months AS (
    SELECT 
        c.customer_id,
        cal.month_end,
        DATE_FORMAT(cal.month_end, '%Y-%m') AS month_label
    FROM customers c
    CROSS JOIN calendar cal
),
customer_monthly_mrr AS (
    SELECT 
        cm.customer_id,
        cm.month_end,
        cm.month_label,
        COALESCE(s.monthly_price, 0.00) AS curr_mrr
    FROM customer_months cm
    LEFT JOIN subscriptions s
        ON s.customer_id = cm.customer_id
        AND s.start_date <= cm.month_end
        AND (s.end_date IS NULL OR s.end_date > cm.month_end)
),
customer_deltas AS (
    SELECT 
        customer_id,
        month_end,
        month_label,
        curr_mrr,
        COALESCE(LAG(curr_mrr, 1, 0.00) OVER (
            PARTITION BY customer_id 
            ORDER BY month_end
        ), 0.00) AS prev_mrr
    FROM customer_monthly_mrr
),
customer_flags AS (
    SELECT 
        month_end,
        month_label,
        prev_mrr,
        curr_mrr,
        CASE WHEN prev_mrr > 0.00 THEN 1 ELSE 0 END AS is_opening_active,
        CASE WHEN curr_mrr > 0.00 THEN 1 ELSE 0 END AS is_closing_active,
        CASE WHEN prev_mrr = 0.00 AND curr_mrr > 0.00 THEN 1 ELSE 0 END AS is_new_customer,
        CASE WHEN prev_mrr > 0.00 AND curr_mrr = 0.00 THEN 1 ELSE 0 END AS is_churned_customer,
        CASE WHEN prev_mrr = 0.00 AND curr_mrr > 0.00 THEN curr_mrr ELSE 0.00 END AS new_mrr,
        CASE WHEN prev_mrr > 0.00 AND curr_mrr > prev_mrr THEN curr_mrr - prev_mrr ELSE 0.00 END AS expansion_mrr,
        CASE WHEN prev_mrr > 0.00 AND curr_mrr > 0.00 AND curr_mrr < prev_mrr THEN prev_mrr - curr_mrr ELSE 0.00 END AS contraction_mrr,
        CASE WHEN prev_mrr > 0.00 AND curr_mrr = 0.00 THEN prev_mrr ELSE 0.00 END AS churned_mrr
    FROM customer_deltas
),
monthly_metrics AS (
    SELECT 
        month_end,
        month_label AS month,
        SUM(is_opening_active) AS opening_active_customers,
        SUM(is_new_customer) AS new_customers,
        SUM(is_churned_customer) AS churned_customers,
        SUM(is_closing_active) AS closing_active_customers,
        SUM(prev_mrr) AS opening_mrr,
        SUM(new_mrr) AS new_mrr,
        SUM(expansion_mrr) AS expansion_mrr,
        SUM(contraction_mrr) AS contraction_mrr,
        SUM(churned_mrr) AS churned_mrr
    FROM customer_flags
    GROUP BY month_end, month_label
)
SELECT 
    month,
    opening_active_customers,
    new_customers,
    churned_customers,
    closing_active_customers,
    ROUND(
        CASE 
            WHEN opening_active_customers > 0 
            THEN churned_customers / opening_active_customers 
            ELSE 0.0000 
        END, 
        4
    ) AS logo_churn_rate,
    ROUND(
        CASE 
            WHEN opening_mrr > 0 
            THEN (churned_mrr + contraction_mrr) / opening_mrr 
            ELSE 0.0000 
        END, 
        4
    ) AS gross_revenue_churn_rate,
    ROUND(
        CASE 
            WHEN opening_mrr > 0 
            THEN (opening_mrr + expansion_mrr - contraction_mrr - churned_mrr) / opening_mrr 
            ELSE 1.0000 
        END, 
        4
    ) AS nrr,
    ROUND(
        CASE 
            WHEN opening_mrr > 0 
            THEN (opening_mrr - contraction_mrr - churned_mrr) / opening_mrr 
            ELSE 1.0000 
        END, 
        4
    ) AS grr,
    ROUND(
        CASE 
            WHEN (churned_mrr + contraction_mrr) > 0 
            THEN (new_mrr + expansion_mrr) / (churned_mrr + contraction_mrr) 
            ELSE NULL 
        END, 
        2
    ) AS quick_ratio
FROM monthly_metrics
ORDER BY month_end ASC;
