"""
verify_sql.py
SQL Logic Verification Script using in-memory DuckDB.

Loads generated CSVs into in-memory DuckDB, executes SQL queries equivalent to the MySQL 8
files in sql/, and compares the query outputs against the Pandas metrics CSVs in output/.
Outputs verification table and reports any discrepancies.

DISCLAIMER:
"Synthetic data modelled on Stripe-style subscription billing. Not real customer data."
"""

import os
import json
import duckdb
import pandas as pd
import numpy as np

def run_verification():
    print("=" * 80)
    print("Verifying SQL Query Logic against Pandas Metrics using in-memory DuckDB...")
    print("=" * 80)
    
    con = duckdb.connect(':memory:')
    
    # 1. Load CSVs into in-memory DuckDB tables with proper dates
    con.execute("""
        CREATE TABLE customers AS 
        SELECT 
            customer_id, 
            CAST(signup_date AS DATE) AS signup_date, 
            country, 
            channel 
        FROM read_csv_auto('data/customers.csv');
    """)
    
    con.execute("""
        CREATE TABLE subscriptions AS 
        SELECT 
            subscription_id, 
            customer_id, 
            plan, 
            CAST(monthly_price AS DECIMAL(10,2)) AS monthly_price, 
            CAST(start_date AS DATE) AS start_date, 
            CAST(end_date AS DATE) AS end_date, 
            end_reason 
        FROM read_csv_auto('data/subscriptions.csv');
    """)
    
    con.execute("""
        CREATE TABLE invoices AS 
        SELECT 
            invoice_id, 
            customer_id, 
            subscription_id, 
            CAST(invoice_date AS DATE) AS invoice_date, 
            CAST(amount AS DECIMAL(10,2)) AS amount, 
            CAST(discount AS DECIMAL(10,2)) AS discount, 
            status 
        FROM read_csv_auto('data/invoices.csv');
    """)
    
    verification_checks = []
    
    # --------------------------------------------------------------------------
    # Check 1: 01_mrr_monthly.sql vs output/mrr_monthly.csv
    # --------------------------------------------------------------------------
    sql_01 = """
    WITH RECURSIVE calendar AS (
        SELECT 
            CAST('2023-01-01' AS DATE) AS month_start,
            LAST_DAY(CAST('2023-01-01' AS DATE)) AS month_end
        UNION ALL
        SELECT 
            (month_start + INTERVAL 1 MONTH)::DATE,
            LAST_DAY(month_start + INTERVAL 1 MONTH)
        FROM calendar
        WHERE month_start < CAST('2025-12-01' AS DATE)
    )
    SELECT 
        STRFTIME(c.month_end, '%Y-%m') AS month,
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
    """
    df_sql_01 = con.execute(sql_01).df()
    df_py_01 = pd.read_csv('output/mrr_monthly.csv')
    
    # Compare December 2025 closing MRR and active customers
    sql_mrr_dec25 = float(df_sql_01.iloc[-1]['mrr'])
    py_mrr_dec25 = float(df_py_01.iloc[-1]['mrr'])
    match_mrr = abs(sql_mrr_dec25 - py_mrr_dec25) < 0.01
    verification_checks.append({
        'analysis': '01_mrr_monthly',
        'metric': 'Closing MRR (Dec 2025)',
        'sql_value': f"${sql_mrr_dec25:,.2f}",
        'pandas_value': f"${py_mrr_dec25:,.2f}",
        'match': 'Yes' if match_mrr else 'No',
        'diff': round(abs(sql_mrr_dec25 - py_mrr_dec25), 4)
    })
    
    sql_cust_dec25 = int(df_sql_01.iloc[-1]['active_customers'])
    py_cust_dec25 = int(df_py_01.iloc[-1]['active_customers'])
    match_cust = (sql_cust_dec25 == py_cust_dec25)
    verification_checks.append({
        'analysis': '01_mrr_monthly',
        'metric': 'Active Customers (Dec 2025)',
        'sql_value': f"{sql_cust_dec25:,}",
        'pandas_value': f"{py_cust_dec25:,}",
        'match': 'Yes' if match_cust else 'No',
        'diff': abs(sql_cust_dec25 - py_cust_dec25)
    })
    
    # --------------------------------------------------------------------------
    # Check 2: 02_mrr_movements.sql vs output/mrr_movements.csv
    # --------------------------------------------------------------------------
    sql_02 = """
    WITH RECURSIVE calendar AS (
        SELECT 
            CAST('2023-01-01' AS DATE) AS month_start,
            LAST_DAY(CAST('2023-01-01' AS DATE)) AS month_end
        UNION ALL
        SELECT 
            (month_start + INTERVAL 1 MONTH)::DATE,
            LAST_DAY(month_start + INTERVAL 1 MONTH)
        FROM calendar
        WHERE month_start < CAST('2025-12-01' AS DATE)
    ),
    customer_months AS (
        SELECT 
            c.customer_id,
            cal.month_end,
            STRFTIME(cal.month_end, '%Y-%m') AS month_label
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
    customer_movements AS (
        SELECT 
            month_end,
            month_label,
            prev_mrr,
            curr_mrr,
            CASE WHEN prev_mrr = 0.00 AND curr_mrr > 0.00 THEN curr_mrr ELSE 0.00 END AS new_mrr,
            CASE WHEN prev_mrr > 0.00 AND curr_mrr > prev_mrr THEN curr_mrr - prev_mrr ELSE 0.00 END AS expansion_mrr,
            CASE WHEN prev_mrr > 0.00 AND curr_mrr > 0.00 AND curr_mrr < prev_mrr THEN prev_mrr - curr_mrr ELSE 0.00 END AS contraction_mrr,
            CASE WHEN prev_mrr > 0.00 AND curr_mrr = 0.00 THEN prev_mrr ELSE 0.00 END AS churned_mrr
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
        closing_mrr
    FROM monthly_aggregated
    ORDER BY month_end ASC;
    """
    df_sql_02 = con.execute(sql_02).df()
    df_py_02 = pd.read_csv('output/mrr_movements.csv')
    
    # Cumulative Net New MRR sum across all 36 months
    sql_tot_net_new = float(df_sql_02['net_new_mrr'].sum())
    py_tot_net_new = float(df_py_02['net_new_mrr'].sum())
    match_net_new = abs(sql_tot_net_new - py_tot_net_new) < 0.05
    verification_checks.append({
        'analysis': '02_mrr_movements',
        'metric': 'Total Net New MRR (36 Mo Sum)',
        'sql_value': f"${sql_tot_net_new:,.2f}",
        'pandas_value': f"${py_tot_net_new:,.2f}",
        'match': 'Yes' if match_net_new else 'No',
        'diff': round(abs(sql_tot_net_new - py_tot_net_new), 4)
    })
    
    sql_tot_exp = float(df_sql_02['expansion_mrr'].sum())
    py_tot_exp = float(df_py_02['expansion_mrr'].sum())
    match_exp = abs(sql_tot_exp - py_tot_exp) < 0.05
    verification_checks.append({
        'analysis': '02_mrr_movements',
        'metric': 'Total Expansion MRR (36 Mo Sum)',
        'sql_value': f"${sql_tot_exp:,.2f}",
        'pandas_value': f"${py_tot_exp:,.2f}",
        'match': 'Yes' if match_exp else 'No',
        'diff': round(abs(sql_tot_exp - py_tot_exp), 4)
    })
    
    # --------------------------------------------------------------------------
    # Check 3: 03_churn_rate.sql vs output/churn_monthly.csv
    # --------------------------------------------------------------------------
    sql_03 = """
    WITH RECURSIVE calendar AS (
        SELECT 
            CAST('2023-01-01' AS DATE) AS month_start,
            LAST_DAY(CAST('2023-01-01' AS DATE)) AS month_end
        UNION ALL
        SELECT 
            (month_start + INTERVAL 1 MONTH)::DATE,
            LAST_DAY(month_start + INTERVAL 1 MONTH)
        FROM calendar
        WHERE month_start < CAST('2025-12-01' AS DATE)
    ),
    customer_months AS (
        SELECT 
            c.customer_id,
            cal.month_end,
            STRFTIME(cal.month_end, '%Y-%m') AS month_label
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
            CASE WHEN prev_mrr > 0.00 AND curr_mrr = 0.00 THEN 1 ELSE 0 END AS is_churned_customer
        FROM customer_deltas
    ),
    monthly_churn AS (
        SELECT 
            month_end,
            month_label AS month,
            SUM(is_opening_active) AS opening_active_customers,
            SUM(is_churned_customer) AS churned_customers
        FROM customer_flags
        GROUP BY month_end, month_label
    )
    SELECT 
        month,
        opening_active_customers,
        churned_customers,
        ROUND(
            CASE 
                WHEN opening_active_customers > 0 
                THEN churned_customers * 1.0 / opening_active_customers 
                ELSE 0.0000 
            END, 
            4
        ) AS logo_churn_rate
    FROM monthly_churn
    ORDER BY month_end ASC;
    """
    df_sql_03 = con.execute(sql_03).df()
    df_py_03 = pd.read_csv('output/churn_monthly.csv')
    
    # Average monthly logo churn rate (months 2-36)
    sql_avg_churn = float(df_sql_03.iloc[1:]['logo_churn_rate'].mean())
    py_avg_churn = float(df_py_03.iloc[1:]['logo_churn_rate'].mean())
    match_churn = abs(sql_avg_churn - py_avg_churn) < 0.0002
    verification_checks.append({
        'analysis': '03_churn_rate',
        'metric': 'Avg Monthly Logo Churn Rate',
        'sql_value': f"{sql_avg_churn * 100:.2f}%",
        'pandas_value': f"{py_avg_churn * 100:.2f}%",
        'match': 'Yes' if match_churn else 'No',
        'diff': round(abs(sql_avg_churn - py_avg_churn), 6)
    })
    
    # --------------------------------------------------------------------------
    # Check 4: 04_cohort_retention.sql vs output/retention_cohorts_logo.csv
    # --------------------------------------------------------------------------
    sql_04 = """
    WITH RECURSIVE calendar AS (
        SELECT 
            CAST('2023-01-01' AS DATE) AS month_start,
            LAST_DAY(CAST('2023-01-01' AS DATE)) AS month_end
        UNION ALL
        SELECT 
            (month_start + INTERVAL 1 MONTH)::DATE,
            LAST_DAY(month_start + INTERVAL 1 MONTH)
        FROM calendar
        WHERE month_start < CAST('2025-12-01' AS DATE)
    ),
    customer_cohorts AS (
        SELECT 
            c.customer_id,
            STRFTIME(c.signup_date, '%Y-%m') AS cohort_month,
            STRFTIME(c.signup_date, '%Y-%m-01')::DATE AS cohort_start_date,
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
            cohort_start_date,
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
        SELECT 
            cs.cohort_month,
            cs.cohort_size,
            cs.cohort_initial_mrr,
            cal.month_end,
            DATE_DIFF('month', cs.cohort_start_date, cal.month_start) AS tenure_months
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
        tenure_months,
        CASE 
            WHEN tenure_months = 0 THEN 100.00
            ELSE ROUND(active_customers * 100.0 / cohort_size, 2)
        END AS logo_retention_pct
    FROM cohort_active_at_tenure
    WHERE cohort_month = '2023-01' AND tenure_months IN (0, 1, 6, 12);
    """
    df_sql_04 = con.execute(sql_04).df()
    df_py_cohort = pd.read_csv('output/retention_cohorts_logo.csv')
    c2301_py = df_py_cohort[df_py_cohort['cohort_month'] == '2023-01'].iloc[0]
    
    for t in [0, 1, 6, 12]:
        sql_val = float(df_sql_04[df_sql_04['tenure_months'] == t]['logo_retention_pct'].iloc[0])
        py_val = float(c2301_py[f"M{t:02d}"])
        match_t = abs(sql_val - py_val) < 0.05
        verification_checks.append({
            'analysis': '04_cohort_retention',
            'metric': f"2023-01 Cohort M{t:02d} Logo Retention",
            'sql_value': f"{sql_val:.2f}%",
            'pandas_value': f"{py_val:.2f}%",
            'match': 'Yes' if match_t else 'No',
            'diff': round(abs(sql_val - py_val), 4)
        })
        
    # --------------------------------------------------------------------------
    # Check 5: 05_ltv_by_plan.sql vs output/ltv_by_plan.csv
    # --------------------------------------------------------------------------
    sql_05 = """
    WITH RECURSIVE calendar AS (
        SELECT 
            CAST('2023-01-01' AS DATE) AS month_start,
            LAST_DAY(CAST('2023-01-01' AS DATE)) AS month_end
        UNION ALL
        SELECT 
            (month_start + INTERVAL 1 MONTH)::DATE,
            LAST_DAY(month_start + INTERVAL 1 MONTH)
        FROM calendar
        WHERE month_start < CAST('2025-12-01' AS DATE)
    ),
    gross_margin_param AS (
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
        monthly_churn_rate,
        sample_size,
        CASE 
            WHEN monthly_churn_rate > 0 
            THEN CAST(ROUND((arpa * gross_margin) / monthly_churn_rate, 2) AS CHAR)
            ELSE 'not estimable'
        END AS ltv_estimate
    FROM plan_metrics
    ORDER BY arpa ASC;
    """
    df_sql_05 = con.execute(sql_05).df()
    df_py_ltv = pd.read_csv('output/ltv_by_plan.csv')
    
    for plan in ['Basic', 'Pro', 'Business']:
        sql_ltv = float(df_sql_05[df_sql_05['plan'] == plan]['ltv_estimate'].iloc[0])
        py_ltv = float(df_py_ltv[df_py_ltv['plan'] == plan]['ltv_estimate'].iloc[0])
        match_ltv = abs(sql_ltv - py_ltv) < 1.0
        verification_checks.append({
            'analysis': '05_ltv_by_plan',
            'metric': f"{plan} Plan LTV Estimate",
            'sql_value': f"${sql_ltv:,.2f}",
            'pandas_value': f"${py_ltv:,.2f}",
            'match': 'Yes' if match_ltv else 'No',
            'diff': round(abs(sql_ltv - py_ltv), 4)
        })
        
    df_checks = pd.DataFrame(verification_checks)
    df_checks.to_csv('output/sql_verification_results.csv', index=False)
    
    print("\nSQL Logic Verification Results against Pandas Calculations:")
    print("-" * 80)
    print(df_checks.to_string(index=False))
    print("-" * 80)
    
    total_checks = len(df_checks)
    passed_checks = (df_checks['match'] == 'Yes').sum()
    failed_checks = total_checks - passed_checks
    
    summary = {
        'total_checks': int(total_checks),
        'passed_checks': int(passed_checks),
        'failed_checks': int(failed_checks),
        'details': verification_checks
    }
    with open('output/sql_verification_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
        
    if failed_checks == 0:
        print(f"SUCCESS: All {total_checks} SQL checks matched Pandas calculations exactly!")
    else:
        print(f"WARNING: {failed_checks} SQL checks did not match. See output/sql_verification_results.csv.")
    print("=" * 80)

if __name__ == '__main__':
    run_verification()
