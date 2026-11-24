-- ==============================================================================
-- 01_mrr_monthly.sql
-- Monthly Recurring Revenue (MRR), Active Customers, and ARPA (MySQL 8.0+)
--
-- Logic:
-- 1. Uses a RECURSIVE CTE to build a calendar of 36 months (2023-01 to 2025-12).
-- 2. Evaluates active subscriptions at each month-end date:
--    start_date <= month_end AND (end_date IS NULL OR end_date > month_end)
-- 3. Computes Total MRR, Active Customer count, and Average Revenue Per Account (ARPA).
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
)
SELECT 
    DATE_FORMAT(c.month_end, '%Y-%m') AS month,
    ROUND(COALESCE(SUM(s.monthly_price), 0.00), 2) AS mrr,
    COUNT(DISTINCT s.customer_id) AS active_customers,
    ROUND(
        CASE 
            WHEN COUNT(DISTINCT s.customer_id) > 0 
            THEN SUM(s.monthly_price) / COUNT(DISTINCT s.customer_id)
            ELSE 0.00 
        END, 
        2
    ) AS arpa
FROM calendar c
LEFT JOIN subscriptions s 
    ON s.start_date <= c.month_end 
    AND (s.end_date IS NULL OR s.end_date > c.month_end)
GROUP BY c.month_end
ORDER BY month ASC;
