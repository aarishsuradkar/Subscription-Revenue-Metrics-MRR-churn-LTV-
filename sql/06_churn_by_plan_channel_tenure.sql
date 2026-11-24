-- ==============================================================================
-- 06_churn_by_plan_channel_tenure.sql
-- Churn Rate Segmentation: Channel, Tenure Band, and Churn Reason (MySQL 8.0+)
--
-- Logic:
-- 1. Evaluates exposure (active subscription-months) and churned subscriptions by:
--      - Channel: organic, paid, referral
--      - Tenure band: 0-3 months, 4-6 months, 7-12 months, 13+ months
-- 2. Evaluates Churn Reasons: voluntary_churn vs involuntary_churn (count, share %, lost MRR).
-- 3. Handles low sample sizes (< 30 customers).
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
-- -----------------------------------------------------------------------------
-- SECTION A: CHURN BY ACQUISITION CHANNEL
-- -----------------------------------------------------------------------------
channel_exposure AS (
    SELECT 
        c.channel,
        COUNT(*) AS active_sub_months
    FROM subscriptions s
    JOIN customers c ON s.customer_id = c.customer_id
    JOIN calendar cal
        ON s.start_date <= cal.month_end
        AND (s.end_date IS NULL OR s.end_date > cal.month_end)
    GROUP BY c.channel
),
channel_churn AS (
    SELECT 
        c.channel,
        COUNT(DISTINCT c.customer_id) AS sample_size,
        SUM(CASE WHEN s.end_reason IN ('voluntary_churn', 'involuntary_churn') THEN 1 ELSE 0 END) AS churned_subscriptions
    FROM subscriptions s
    JOIN customers c ON s.customer_id = c.customer_id
    GROUP BY c.channel
),
churn_by_channel_summary AS (
    SELECT 
        cc.channel,
        ce.active_sub_months,
        cc.churned_subscriptions,
        ROUND(cc.churned_subscriptions * 1.0 / ce.active_sub_months, 4) AS monthly_churn_rate,
        cc.sample_size,
        CASE WHEN cc.sample_size < 30 THEN 1 ELSE 0 END AS is_low_sample
    FROM channel_churn cc
    JOIN channel_exposure ce ON cc.channel = ce.channel
),

-- -----------------------------------------------------------------------------
-- SECTION B: CHURN BY TENURE BAND
-- -----------------------------------------------------------------------------
tenure_sub_months AS (
    SELECT 
        s.customer_id,
        cal.month_end,
        TIMESTAMPDIFF(MONTH, c.signup_date, cal.month_end) AS tenure_m,
        CASE 
            WHEN TIMESTAMPDIFF(MONTH, c.signup_date, cal.month_end) <= 3 THEN '0-3 months'
            WHEN TIMESTAMPDIFF(MONTH, c.signup_date, cal.month_end) <= 6 THEN '4-6 months'
            WHEN TIMESTAMPDIFF(MONTH, c.signup_date, cal.month_end) <= 12 THEN '7-12 months'
            ELSE '13+ months'
        END AS tenure_band
    FROM subscriptions s
    JOIN customers c ON s.customer_id = c.customer_id
    JOIN calendar cal
        ON s.start_date <= cal.month_end
        AND (s.end_date IS NULL OR s.end_date > cal.month_end)
),
tenure_exposure AS (
    SELECT 
        tenure_band,
        COUNT(*) AS active_sub_months,
        COUNT(DISTINCT customer_id) AS sample_size
    FROM tenure_sub_months
    GROUP BY tenure_band
),
tenure_churn_events AS (
    SELECT 
        CASE 
            WHEN TIMESTAMPDIFF(MONTH, c.signup_date, s.end_date) <= 3 THEN '0-3 months'
            WHEN TIMESTAMPDIFF(MONTH, c.signup_date, s.end_date) <= 6 THEN '4-6 months'
            WHEN TIMESTAMPDIFF(MONTH, c.signup_date, s.end_date) <= 12 THEN '7-12 months'
            ELSE '13+ months'
        END AS tenure_band,
        COUNT(*) AS churned_subscriptions
    FROM subscriptions s
    JOIN customers c ON s.customer_id = c.customer_id
    WHERE s.end_reason IN ('voluntary_churn', 'involuntary_churn')
    GROUP BY tenure_band
),
churn_by_tenure_summary AS (
    SELECT 
        te.tenure_band,
        te.active_sub_months,
        COALESCE(tce.churned_subscriptions, 0) AS churned_subscriptions,
        ROUND(COALESCE(tce.churned_subscriptions, 0) * 1.0 / te.active_sub_months, 4) AS monthly_churn_rate,
        te.sample_size,
        CASE WHEN te.sample_size < 30 THEN 1 ELSE 0 END AS is_low_sample
    FROM tenure_exposure te
    LEFT JOIN tenure_churn_events tce ON te.tenure_band = tce.tenure_band
),

-- -----------------------------------------------------------------------------
-- SECTION C: CHURN REASONS (VOLUNTARY VS INVOLUNTARY)
-- -----------------------------------------------------------------------------
churn_reasons_summary AS (
    SELECT 
        end_reason AS reason,
        COUNT(*) AS churn_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS share_pct,
        ROUND(SUM(monthly_price), 2) AS lost_mrr_total
    FROM subscriptions
    WHERE end_reason IN ('voluntary_churn', 'involuntary_churn')
    GROUP BY end_reason
)

-- Display Channel Segmentation by default (Query can be run per section as needed)
SELECT 'CHANNEL' AS segmentation_type, channel AS segment, monthly_churn_rate, sample_size, is_low_sample 
FROM churn_by_channel_summary
UNION ALL
SELECT 'TENURE_BAND', tenure_band, monthly_churn_rate, sample_size, is_low_sample 
FROM churn_by_tenure_summary;
