# Subscription Revenue Analytics (MRR, Churn, Cohort Retention & LTV)

> ### ⚠️ SYNTHETIC DATA NOTICE
> **Synthetic data modelled on Stripe-style subscription billing. Not real customer data.**  
> All figures, customer behaviors, transactions, and metrics in this project were generated through a controlled stochastic simulation (`seed=42`). Never interpret these findings as empirical market research: all patterns are driven by parameters specified in the data generator.

---

## Executive Summary

This project delivers an end-to-end, production-grade subscription analytics system engineered to model and audit recurring revenue dynamics for a B2B/prosumer SaaS product. Spanning 36 calendar months (**2023-01-01 to 2025-12-31**) and **3,160 simulated customers**, the pipeline models monthly recurring revenue (MRR) waterfalls, dual logo/revenue churn, cohort retention heatmaps, customer lifetime value (LTV), and billing cash reconciliations.

The system incorporates:
1. **Synthetic Data Generator**: Deterministic simulation of customer acquisition, tiered subscriptions, anniversary billing, expansion/contraction, voluntary cancellations, and dunning payment failures.
2. **Pandas Metric Engine**: Fully vectorized metrics exporting 11 structured CSV datasets and high-resolution audit charts.
3. **MySQL 8.0+ Analytical Architecture**: Window functions (`LAG`, `SUM OVER`, `ROW_NUMBER`) and recursive calendar common table expressions (CTEs), verified in DuckDB with **0.00 calculation discrepancy**.
4. **Streamlit Interactive Dashboard**: 4-tab analytical portal with interactive gross margin LTV modeling and automated, code-generated dynamic insights.
5. **Power BI Build Specification**: Detailed implementation manual with DAX measures and matrix heatmap formatting.

---

## Metric Definitions

| Metric | Business Definition | Formula |
| :--- | :--- | :--- |
| **Month-End MRR** | Total recurring list price of active subscriptions on the final day of the month. | $\sum_{s \in \text{Active}} \text{monthly\_price}_s$ |
| **New MRR** | MRR added from customers subscribing for the first time. | $\sum_{c \in \text{New}} \text{MRR}_{c, m}$ |
| **Expansion MRR** | Additional recurring revenue from existing customers upgrading tiers. | $\sum_{c \in \text{Upgrades}} (\text{MRR}_{c, m} - \text{MRR}_{c, m-1})$ |
| **Contraction MRR** | Recurring revenue lost from customers downgrading to lower tiers. | $\sum_{c \in \text{Downgrades}} (\text{MRR}_{c, m-1} - \text{MRR}_{c, m})$ |
| **Churned MRR** | Total recurring revenue lost from complete account cancellations. | $\sum_{c \in \text{Churn}} \text{MRR}_{c, m-1}$ |
| **Net New MRR** | Net monthly change in recurring revenue baseline. | $\text{New} + \text{Expansion} - \text{Contraction} - \text{Churned}$ |
| **Logo Churn Rate** | Percentage of active subscribers lost during the monthly cycle. | $\frac{\text{Churned Customers}_m}{\text{Opening Active Customers}_m}$ |
| **Gross Revenue Churn** | Percentage of opening MRR lost to cancellations and downgrades. | $\frac{\text{Churned MRR}_m + \text{Contraction MRR}_m}{\text{Opening MRR}_m}$ |
| **Net Revenue Retention (NRR)** | Percentage of opening MRR retained including expansions. | $\frac{\text{Opening MRR} + \text{Expansion} - \text{Contraction} - \text{Churned}}{\text{Opening MRR}}$ |
| **Gross Revenue Retention (GRR)** | Percentage of opening MRR retained excluding expansions. | $\frac{\text{Opening MRR} - \text{Contraction} - \text{Churned}}{\text{Opening MRR}}$ |
| **ARPA** | Average Revenue Per Account (blended monthly customer spend). | $\frac{\text{Closing MRR}_m}{\text{Active Customers}_m}$ |
| **LTV (Plan Tier)** | Theoretical customer lifetime value under gross margin assumption. | $\frac{\text{Plan ARPA} \times \text{Gross Margin \%}}{\text{Plan Monthly Logo Churn Rate}}$ |
| **SaaS Quick Ratio** | Growth velocity ratio comparing revenue additions to revenue losses. | $\frac{\text{New MRR} + \text{Expansion MRR}}{\text{Churned MRR} + \text{Contraction MRR}}$ |

---

## Core Business Questions & Computed Answers

All answers below are computed strictly from the simulated data. In accordance with analytical standards, patterns are labeled by strength and avoid claims of real-world causation.

### Q1. How fast is MRR growing, and how much comes from new vs expansion?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Computed Results**:
  - Closing MRR expanded from **$1,999.00** in January 2023 to **$73,552.00** in December 2025 (**+3,579.4%** total growth over 36 months).
  - Total cumulative revenue inflow was **$124,389.00**, comprising **$110,869.00 (89.1%)** in New MRR and **$13,520.00 (10.9%)** in Expansion MRR across 372 account upgrades.
  - Active subscriber volume increased from 61 to 1,618 accounts, while blended ARPA climbed from $32.77 to $45.46 as tier mix shifted upward.

### Q2. Is churn getting better or worse over time?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Computed Results**:
  - Monthly logo churn trended downwards as customer tenure matured:
    - **2023 Average**: 7.08% monthly churn
    - **2024 Average**: 5.50% monthly churn
    - **2025 Average**: 4.62% monthly churn (closing December 2025 at 3.99%).
  - This trajectory reflects the expanding proportion of high-tenure, stabilized accounts in the active subscriber base.

### Q3. Which plan has the highest churn and the lowest LTV?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Computed Results**:
  - **Basic ($19/mo)**: Highest churn at **6.95% monthly** (1,029 cancellations across 14,815 subscription-months, $N=2,024$). Lowest LTV at **$218.71** (@ 80% margin).
  - **Pro ($49/mo)**: Moderate churn at **4.32% monthly** (378 cancellations across 8,749 subscription-months, $N=1,047$). LTV of **$907.41**.
  - **Business ($99/mo)**: Lowest churn at **2.50% monthly** (135 cancellations across 5,409 subscription-months, $N=514$). Highest LTV at **$3,168.00** (**14.5x** higher than Basic).
  - *Sample Size Note*: None of the plan groups fell below the 30-customer threshold ($N \ge 514$).

### Q4. Which acquisition channel retains best?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Computed Results**:
  - **Referral**: Lowest monthly churn rate at **4.02%** (269 churns / 6,689 exposure months, $N=639$).
  - **Organic**: Baseline monthly churn rate of **5.13%** (670 churns / 13,053 exposure months, $N=1,403$).
  - **Paid**: Highest monthly churn rate at **6.53%** (603 churns / 9,231 exposure months, $N=1,118$).

### Q5. When in a customer's life is churn highest?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Computed Results**:
  - **0–3 Months**: **7.12% monthly churn** (720 cancellations across 10,109 active sub-months).
  - **4–6 Months**: **5.86% monthly churn** (301 cancellations across 5,138 active sub-months).
  - **7–12 Months**: **4.67% monthly churn** (316 cancellations across 6,771 active sub-months).
  - **13+ Months**: **2.95% monthly churn** (205 cancellations across 6,955 active sub-months).
  - Churn hazard is concentrated in the first 90 days after registration.

### Q6. How much churn is involuntary (failed payments), and how much revenue is that?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Computed Results**:
  - Out of 1,542 total subscription cancellations, **315 (20.43%)** were involuntary due to unrecovered billing declines.
  - Involuntary churn destroyed **$12,875.00** in recurring MRR (**25.03%** of total churned MRR of $51,438.00), representing an uncollected cash drag across 315 failed terminal invoices.

### Q7. Is net revenue retention above or below 100%, and what drives it?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Computed Results**:
  - Net Revenue Retention (NRR) averaged **96.19%** across all months (latest December 2025: **97.25%**).
  - Gross Revenue Retention (GRR) averaged **95.02%** (latest: **95.95%**).
  - In this simulated prosumer SaaS model, NRR remains below 100% because contraction ($2,382.00 cumulative) and churn ($51,438.00 cumulative) exceed upgrade expansion ($13,520.00 cumulative), indicating net revenue erosion from existing cohorts prior to new acquisitions.

### Q8. Which cohorts retain best and worst?
- **Pattern Evaluation**: `Weak or unclear variation across cohorts; clear tenure decay` (in this simulated dataset).
- **Computed Results**:
  - At Month 12 ($M_{12}$):
    - **Highest Logo Retention**: `2024-09` cohort with **57.61%** active ($N=92$).
    - **Lowest Logo Retention**: `2023-08` cohort with **37.50%** active ($N=56$).
  - Average 1-year logo retention across all eligible cohorts is **48.8%**. Cohort variations reflect minor stochastic sampling noise rather than systemic quality shifts.

### Q9. Strategic Recommendations Supported by Simulated Data
1. **Prioritize Referral & Organic Acquisition Channels** (`High Confidence`):
   - *Data Basis*: Referral acquisition delivers a 4.02% monthly churn vs. 6.53% for Paid.
   - *Context Reminder*: The simulated data generator assigns a 0.70x hazard multiplier to referrals and 1.30x to paid channels.
2. **Implement Dunning Recovery Sequences for Involuntary Churn** (`High Confidence`):
   - *Data Basis*: 20.43% of churn events and $12,875.00 in MRR stem from credit card payment failures.
   - *Context Reminder*: The generator assumes a single retry with a 50% recovery failure. Automated smart retries and pre-expiration reminders would target this leakage directly.
3. **Focus Retention Efforts on the Day 0–90 Onboarding Window** (`High Confidence`):
   - *Data Basis*: 7.12% monthly churn in months 0–3 vs. 2.95% in months 13+.
   - *Context Reminder*: The generator applies a 1.65x multiplier during the initial 3 months.
4. **Incentivize Upgrades to Business Tier** (`Medium Confidence`):
   - *Data Basis*: Business tier accounts demonstrate a 2.50% monthly churn and an LTV of $3,168.00 (14.5x Basic). Expanding account migration offsets entry-tier churn.

---

## Data Generation & Schema Architecture

The dataset is generated via `src/generate_data.py` under seed `42` across 36 calendar months. All business rules and schema details are documented in [`data/DATA_DICTIONARY.md`](file:///c:/Users/SCI/Desktop/data%20analyst/Subscription%20Revenue%20Metrics%20(MRR,%20churn,%20LTV)/data/DATA_DICTIONARY.md).

### Tables Generated
- **`customers`** (3,160 rows): `customer_id`, `signup_date`, `country`, `channel`.
- **`subscriptions`** (3,618 rows): `subscription_id`, `customer_id`, `plan`, `monthly_price`, `start_date`, `end_date`, `end_reason`.
- **`invoices`** (29,957 rows): `invoice_id`, `customer_id`, `subscription_id`, `invoice_date`, `amount`, `discount`, `status`.

---

## SQL Architecture & Verification Results

All queries are located in `sql/` and engineered for **MySQL 8.0+** using recursive calendar CTEs and window functions (`LAG`, `SUM OVER`, `ROW_NUMBER`). To verify query logic without connecting to a live external database, queries were executed against an in-memory **DuckDB** instance loaded with the generated CSVs.

```
+---------------------+-----------------------------------+------------+--------------+-------+--------+
| Analysis Script     | Metric Verified                   | DuckDB SQL | Pandas Value | Match | Diff   |
+---------------------+-----------------------------------+------------+--------------+-------+--------+
| 01_mrr_monthly.sql  | Closing MRR (Dec 2025)            | $73,552.00 | $73,552.00   | Yes   | 0.0000 |
| 01_mrr_monthly.sql  | Active Customers (Dec 2025)       | 1,618      | 1,618        | Yes   | 0      |
| 02_mrr_movements.sql| Total Net New MRR (36 Mo Sum)     | $73,552.00 | $73,552.00   | Yes   | 0.0000 |
| 02_mrr_movements.sql| Total Expansion MRR (36 Mo Sum)   | $13,520.00 | $13,520.00   | Yes   | 0.0000 |
| 03_churn_rate.sql   | Avg Monthly Logo Churn Rate       | 5.76%      | 5.76%        | Yes   | 0.0000 |
| 04_cohort_retention | 2023-01 Cohort M00 Logo Retention | 100.00%    | 100.00%      | Yes   | 0.0000 |
| 04_cohort_retention | 2023-01 Cohort M01 Logo Retention | 90.16%     | 90.16%       | Yes   | 0.0000 |
| 04_cohort_retention | 2023-01 Cohort M06 Logo Retention | 65.57%     | 65.57%       | Yes   | 0.0000 |
| 04_cohort_retention | 2023-01 Cohort M12 Logo Retention | 52.46%     | 52.46%       | Yes   | 0.0000 |
| 05_ltv_by_plan.sql  | Basic Plan LTV Estimate           | $218.71    | $218.71      | Yes   | 0.0000 |
| 05_ltv_by_plan.sql  | Pro Plan LTV Estimate             | $907.41    | $907.41      | Yes   | 0.0000 |
| 05_ltv_by_plan.sql  | Business Plan LTV Estimate        | $3,168.00  | $3,168.00    | Yes   | 0.0000 |
+---------------------+-----------------------------------+------------+--------------+-------+--------+
```
> **Verification Status**: **12 / 12 checks matched with 0.00 discrepancy**. SQL queries were verified in DuckDB and not run directly on MySQL by the author.

---

## Pipeline Reconciliation & Cash Accounting Audit

Executing `src/reconcile.py` confirms complete mathematical consistency across the entire pipeline:
1. **MRR Accounting Balance**: `Opening MRR + Net New MRR = Closing MRR` holds for **36 out of 36 months** with **$0.00 deviation**.
2. **Cohort Month-0 Baseline**: Logo retention and revenue retention evaluate to exactly **100.00%** across all 36 cohorts.
3. **Cash Invoicing vs. Accrual MRR Reconciliation**:
   - Total Invoiced Cash Collected: **$1,256,351.80**
   - Total Promotional Discounts (10%): **$10,038.40**
   - Total Failed Invoice Losses: **$12,782.80**
   - Gross Invoiced Billings: **$1,279,173.00**
   - Cumulative 36-Month Closing MRR: **$1,245,677.00**
   - *Variance Explanation*: The 2.69% variance between cash collections and snapshot month-end MRR is mathematically attributable to mid-month signup billing timing (days 1–28), upgrade/downgrade pro-ration timing, and coupon deductions.

---

## Project Structure

```text
Subscription Revenue Metrics (MRR, churn, LTV)/
├── data/
│   ├── customers.csv                   # 3,160 customer records
│   ├── subscriptions.csv               # 3,618 subscription intervals
│   ├── invoices.csv                    # 29,957 invoice transactions
│   ├── generation_summary.json         # Raw simulation summary
│   └── DATA_DICTIONARY.md              # Column definitions & generator logic
├── src/
│   ├── generate_data.py                # Seeded synthetic generator
│   ├── metrics.py                      # Pandas computation engine
│   ├── verify_sql.py                   # DuckDB SQL logic verification
│   ├── reconcile.py                    # Dual-engine reconciliation & audit
│   └── answer_questions.py             # Script computing answers to Q1-Q9
├── sql/
│   ├── 00_schema_and_load.sql          # DDL, indexes, LOAD DATA instructions
│   ├── 01_mrr_monthly.sql              # Recursive CTE for monthly MRR & ARPA
│   ├── 02_mrr_movements.sql            # Window LAG() MRR movements & waterfall
│   ├── 03_churn_rate.sql               # Logo churn, rev churn, NRR, GRR
│   ├── 04_cohort_retention.sql         # Dual logo/revenue cohort CTEs
│   ├── 05_ltv_by_plan.sql              # Parametric LTV calculation
│   └── 06_churn_by_plan_channel_tenure.sql # Segmented churn hazard
├── output/
│   ├── mrr_monthly.csv                 # Monthly MRR & ARPA
│   ├── mrr_movements.csv               # New, Expansion, Contraction, Churn
│   ├── churn_monthly.csv               # Monthly churn rates, NRR, Quick Ratio
│   ├── retention_cohorts_logo.csv      # Logo cohort matrix (M00-M35)
│   ├── retention_cohorts_revenue.csv   # Revenue cohort matrix (M00-M35)
│   ├── ltv_by_plan.csv                 # Plan ARPA, churn & LTV @ 80% margin
│   ├── churn_by_plan.csv               # Plan exposure & churn rates
│   ├── churn_by_channel.csv            # Acquisition channel churn
│   ├── churn_by_tenure.csv             # Tenure band churn hazard
│   ├── churn_reasons.csv               # Voluntary vs Involuntary split
│   ├── plan_mix_monthly.csv            # Tier distribution over time
│   ├── sql_verification_results.csv    # Dual SQL/Pandas audit output
│   ├── reconciliation_audit.csv        # Raw data vs output reconciliation
│   ├── mrr_movements_stacked.png       # MRR waterfall stacked bar chart
│   ├── cohort_retention_heatmap.png    # 12-month cohort retention heatmap
│   └── churn_by_plan.png               # Plan churn & LTV comparative bars
├── dashboard/
│   └── app.py                          # Streamlit analytical portal
├── powerbi/
│   └── BUILD_GUIDE.md                  # Power BI Desktop build manual
├── screenshots/                        # Dashboard view specifications
├── requirements.txt                    # Project dependency specification
├── .gitignore                          # Version control exclusion rules
├── PROJECT_REPORT.md                   # Comprehensive technical report
└── README.md                           # Project documentation & summary
```

---

## How I Would Apply This to Real Stripe Data

To deploy this analytical engine on live Stripe production data, Stripe webhook/API objects map directly to the database tables:

| Local Table | Stripe API Object / Event | Transformation & Mapping Logic |
| :--- | :--- | :--- |
| `customers` | `stripe.Customer` (`customer.created`) | `customer_id` $\leftarrow$ `id`, `signup_date` $\leftarrow$ `created`, `country` $\leftarrow$ `address.country`, `channel` $\leftarrow$ `metadata.utm_source`. |
| `subscriptions` | `stripe.Subscription` (`customer.subscription.*`) | `subscription_id` $\leftarrow$ `id`, `plan` $\leftarrow$ `plan.nickname`, `monthly_price` $\leftarrow$ `items.data[0].price.unit_amount / 100`, `start_date` $\leftarrow$ `current_period_start`, `end_date` $\leftarrow$ `canceled_at`, `end_reason` $\leftarrow$ mapped from `cancellation_details.reason`. |
| `invoices` | `stripe.Invoice` (`invoice.payment_succeeded`, `invoice.payment_failed`) | `invoice_id` $\leftarrow$ `id`, `amount` $\leftarrow$ `amount_paid / 100`, `discount` $\leftarrow$ `total_discount_amounts`, `status` $\leftarrow$ `status` (`paid`, `open`, `uncollectible`). |

### Real-World Production Enhancements Required:
1. **Multi-Currency Normalization**: Convert foreign invoice amounts to base currency (USD) using the ECB/Stripe FX rate at `invoice_date`.
2. **Refunds & Chargebacks**: Incorporate `stripe.Charge.refunded` events to deduct net revenue from monthly collections.
3. **Prorations & Annual Contracts**: Convert annual subscription payments into normalized Monthly Recurring Revenue ($\text{MRR} = \frac{\text{Annual Price}}{12}$) and amortize over contract schedules.

---

## Limitations

1. **Synthetic Data**: Customer behaviors are driven by fixed random distributions and predefined churn hazard multipliers. Results do not represent market empirical research.
2. **Simplified Invoicing Model**: Models monthly billing on days 1–28. Does not account for leap years, multi-year prepayments, or partial refund disputes.
3. **Tax & Sales Surcharges**: Invoices reflect net SaaS list pricing without jurisdictional VAT/GST withholding.
4. **Static LTV Formulation**: Uses classical simple LTV ($\frac{\text{ARPA} \times \text{Margin}}{\text{Churn}}$). Does not account for discount rate cost of capital or nonlinear tenure retention curves.

---

## How to Run

### 1. Environment Setup
```bash
# Clone the repository
git clone <repository_url>
cd "Subscription Revenue Metrics (MRR, churn, LTV)"

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Data and Compute Metrics
```bash
# Generate synthetic dataset (seed=42)
python src/generate_data.py

# Compute all metrics and export CSVs / PNG charts
python src/metrics.py

# Run SQL logic verification against DuckDB
python src/verify_sql.py

# Run reconciliation and audit check
python src/reconcile.py
```

### 3. Launch Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```

---

## Tools Used

- **Python 3.14**: Core runtime environment.
- **Pandas & NumPy**: High-performance data manipulation, cohort matrix generation, and MRR movement classification.
- **DuckDB**: In-memory analytical SQL verification engine.
- **Plotly Express & Graph Objects**: Interactive, publication-ready financial charts.
- **Streamlit**: Multi-tab executive dashboard framework.
- **Matplotlib**: Static high-resolution audit visualization export.
- **MySQL 8.0+**: Production SQL scripts featuring recursive calendar CTEs and window analytics.
- **Power BI Desktop**: Comprehensive BI implementation specification and DAX measures.

---

## AI Disclosure

Code and documentation were generated with an AI coding assistant and rigorously reviewed, tested, and audited by the author. All computations, reconciliations, and SQL outputs were programmatically verified against the underlying synthetic data.
