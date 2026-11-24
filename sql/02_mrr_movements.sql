-- ==============================================================================
-- 02_mrr_movements.sql
-- Monthly MRR Movements: New, Expansion, Contraction, Churn, and Net New MRR (MySQL 8.0+)
--
-- Logic:
-- 1. Recursive CTE calendar generates 36 months (2023-01 to 2025-12).
-- 2. Evaluates active subscription per customer at each month-end.
-- 3. Uses LAG() window function partitioned by customer to compare current vs prior MRR.
-- 4. Categorizes customer MRR delta into:
--      - New: prior MRR = 0, current MRR > 0
--      - Expansion: prior MRR > 0, current MRR > prior MRR
--      - Contraction: prior MRR > 0, 0 < current MRR < prior MRR
--      - Churned: prior MRR > 0, current MRR = 0
-- 5. Checks reconciliation: opening_mrr + net_new_mrr = closing_mrr.
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
    -- Cross product of all customers and all calendar months
    SELECT 
        c.customer_id,
        cal.month_end,
        DATE_FORMAT(cal.month_end, '%Y-%m') AS month_label
    FROM customers c
    CROSS JOIN calendar cal
),
customer_monthly_mrr AS (
    -- Find active subscription MRR per customer at month_end
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
    -- Calculate previous month MRR per customer using LAG() window function
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
customer_movements AS (
    -- Classify MRR movements
    SELECT 
        month_end,
        month_label,
        prev_mrr,
        curr_mrr,
        CASE 
            WHEN prev_mrr = 0.00 AND curr_mrr > 0.00 THEN curr_mrr 
            ELSE 0.00 
        END AS new_mrr,
        CASE 
            WHEN prev_mrr > 0.00 AND curr_mrr > prev_mrr THEN curr_mrr - prev_mrr 
            ELSE 0.00 
        END AS expansion_mrr,
        CASE 
            WHEN prev_mrr > 0.00 AND curr_mrr > 0.00 AND curr_mrr < prev_mrr THEN prev_mrr - curr_mrr 
            ELSE 0.00 
        END AS contraction_mrr,
        CASE 
            WHEN prev_mrr > 0.00 AND curr_mrr = 0.00 THEN prev_mrr 
            ELSE 0.00 
        END AS churned_mrr
    FROM customer_deltas
),
monthly_aggregated AS (
    SELECT 
        month_end,
        month_label AS month,
        ROUND(SUM(prev_mrr), 2) AS opening_mrr,
        ROUND(SUM(new_mrr), 2) AS new_mrr,
        ROUND(SUM(expansion_mrr), 2) AS expansion_mrr,
        ROUND(SUM(contraction_mrr), 2) AS contraction_mrr,
        ROUND(SUM(churned_mrr), 2) AS churned_mrr,
        ROUND(SUM(new_mrr) + SUM(expansion_mrr) - SUM(contraction_mrr) - SUM(churned_mrr), 2) AS net_new_mrr,
        ROUND(SUM(curr_mrr), 2) AS closing_mrr
    FROM customer_movements
    GROUP BY month_end, month_label
)
SELECT 
    month,
    opening_mrr,
    new_mrr,
    expansion_mrr,
    contraction_mrr,
    churned_mrr,
    net_new_mrr,
    closing_mrr,
    CASE 
        WHEN ABS((opening_mrr + net_new_mrr) - closing_mrr) < 0.01 THEN 'PASS'
        ELSE 'FAIL'
    END AS reconciliation_check
FROM monthly_aggregated
ORDER BY month_end ASC;
