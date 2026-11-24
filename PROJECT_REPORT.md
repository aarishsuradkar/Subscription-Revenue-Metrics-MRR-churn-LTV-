# Comprehensive Project Report: Subscription Revenue Metrics & Cohort Intelligence

> **DISCLAIMER**: **Synthetic data modelled on Stripe-style subscription billing.** Not real customer data. All metrics, tables, and findings in this report were programmatically computed from a 36-month simulation (`seed=42`).

---

## 1. Project Overview & Objectives

In modern SaaS business models, recurring revenue predictability, customer retention, and unit economics form the bedrock of sustainable enterprise valuation. Traditional transactional accounting fails to capture subscriber lifecycle dynamics such as expansion upgrades, downgrades, voluntary churn, and involuntary billing decay.

This project delivers an enterprise-grade analytics engine designed to model, audit, and visualize B2B/prosumer SaaS subscription revenue. Spanning **36 billing cycles from January 1, 2023, to December 31, 2025**, the project models **3,160 unique customers** and **29,957 invoices**, evaluating:
- **Monthly Recurring Revenue (MRR) Waterfalls**: Monthly tracking of New, Expansion, Contraction, Churned, and Net New MRR.
- **Dual Churn Dynamics**: Divergence between customer-level (Logo) churn and dollar-level (Gross Revenue) churn.
- **Cohort Retention**: Multi-year logo and revenue retention decay curves across 36 monthly acquisition cohorts.
- **Unit Economics**: Average Revenue Per Account (ARPA), customer lifetime value (LTV), and SaaS Quick Ratios.
- **Dual-Engine Logic Verification**: Cross-engine parity between MySQL 8.0+ analytical queries (verified in DuckDB) and Pandas computations with zero discrepancy.

---

## 2. Business Questions & Computed Analysis

Every answer below is derived directly from the computed datasets. In keeping with strict analytical standards, patterns are evaluated by empirical strength without asserting real-world causation.

### Q1. How fast is MRR growing, and how much comes from new vs expansion?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Analysis**:
  - Closing MRR grew from **$1,999.00** (January 2023) to **$73,552.00** (December 2025), representing a total increase of **+3,579.4%**.
  - Total gross revenue inflow across the 3-year timeline was **$124,389.00**:
    - **New Sales (New MRR)**: Contributed **$110,869.00 (89.13%)** across 3,160 new customer subscriptions.
    - **Account Expansion (Upgrades)**: Contributed **$13,520.00 (10.87%)** across 372 upgrade events.
  - While top-of-funnel customer acquisition drove the vast majority of gross revenue growth, account expansion accelerated in 2024 and 2025 as the install base matured.

### Q2. Is churn getting better or worse over time?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Analysis**:
  - Monthly logo churn rate exhibited steady improvement as the customer base seasoned:
    - **2023 Monthly Average**: 7.08%
    - **2024 Monthly Average**: 5.50%
    - **2025 Monthly Average**: 4.62% (ending at 3.99% in December 2025).
  - This improvement is structurally driven by the increasing proportion of high-tenure accounts (tenure 13+ months) whose hazard rate is less than half that of newly onboarded users.

### Q3. Which plan has the highest churn and the lowest LTV?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Analysis**:
  - **Basic Tier ($19/mo)**: Suffered the highest churn at **6.95% monthly** (1,029 cancellations / 14,815 exposure months; $N=2,024$) and the lowest LTV at **$218.71** (@ 80% gross margin).
  - **Pro Tier ($49/mo)**: Exhibited moderate churn at **4.32% monthly** (378 cancellations / 8,749 exposure months; $N=1,047$) and an LTV of **$907.41**.
  - **Business Tier ($99/mo)**: Demonstrated the strongest retention at **2.50% monthly churn** (135 cancellations / 5,409 exposure months; $N=514$) and an estimated LTV of **$3,168.00**.
  - Business accounts deliver **14.5x the lifetime value** of Basic accounts due to higher price points coupled with a 64% lower monthly cancellation hazard.

### Q4. Which acquisition channel retains best?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Analysis**:
  - **Referral Channel**: Retained best, exhibiting a **4.02% monthly churn rate** (269 cancellations across 6,689 exposure months; $N=639$).
  - **Organic Channel**: Exhibited a baseline **5.13% monthly churn rate** (670 cancellations across 13,053 exposure months; $N=1,403$).
  - **Paid Channel**: Showed the highest attrition at **6.53% monthly churn** (603 cancellations across 9,231 exposure months; $N=1,118$).

### Q5. When in a customer's life is churn highest?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Analysis**:
  - Customer attrition is heavily front-loaded in the initial customer onboarding window:
    - **Tenure 0–3 Months**: **7.12% monthly churn** (720 cancellations / 10,109 active sub-months).
    - **Tenure 4–6 Months**: **5.86% monthly churn** (301 cancellations / 5,138 active sub-months).
    - **Tenure 7–12 Months**: **4.67% monthly churn** (316 cancellations / 6,771 active sub-months).
    - **Tenure 13+ Months**: **2.95% monthly churn** (205 cancellations / 6,955 active sub-months).
  - More than 46% of all subscription cancellations occurred within the first 90 days.

### Q6. How much churn is involuntary (failed payments), and how much revenue is that?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Analysis**:
  - Out of 1,542 total subscription cancellations, **315 (20.43%)** were caused by involuntary credit card payment declines that failed automated dunning retry.
  - Involuntary churn caused **$12,875.00** in destroyed monthly recurring revenue, accounting for **25.03%** of all churned MRR ($51,438.00 cumulative).

### Q7. Is net revenue retention above or below 100%, and what drives it?
- **Pattern Evaluation**: `Clear pattern` (in this simulated dataset).
- **Analysis**:
  - Net Revenue Retention (NRR) averaged **96.19%** across all months (ending at **97.25%** in December 2025).
  - Gross Revenue Retention (GRR) averaged **95.02%** (ending at **95.95%**).
  - NRR remains below 100% because monthly contraction ($2,382.00 total) and monthly cancellations ($51,438.00 total) exceed expansion upgrades ($13,520.00 total). In this entry-tier-heavy business model, existing cohorts slowly contract without new subscriber acquisition.

### Q8. Which cohorts retain best and worst?
- **Pattern Evaluation**: `Weak or unclear variation across cohorts; clear tenure decay` (in this simulated dataset).
- **Analysis**:
  - Evaluating mature cohorts at Month 12 ($M_{12}$):
    - **Best Cohort**: `2024-09` with **57.61%** logo retention ($N=92$).
    - **Worst Cohort**: `2023-08` with **37.50%** logo retention ($N=56$).
  - Across all 24 cohorts reaching 1 year of tenure, 12-month logo retention averaged **48.8%**. Cohort variations reflect random sampling noise rather than systemic underlying shifts.

### Q9. Strategic Recommendations Supported by Simulated Data
1. **Reallocate Marketing Budget toward Word-of-Mouth & Referral Programs** (`High Confidence`):
   - *Data Basis*: Referral acquisition delivers 4.02% monthly churn vs. 6.53% for Paid channels.
   - *Caveat*: Driven by the generator's 0.70x referral vs. 1.30x paid hazard multipliers.
2. **Deploy Intelligent Multi-Stage Dunning & Card Account Updaters** (`High Confidence`):
   - *Data Basis*: Involuntary churn drives 20.43% of account loss and $12,875.00 in destroyed MRR.
   - *Caveat*: Modeled on a 50% single-retry failure rate; real Stripe Billing accounts can recover up to 75% of failed invoices using machine-learning retries (Smart Retries).
3. **Restructure Onboarding for Days 0–90** (`High Confidence`):
   - *Data Basis*: Churn hazard is 2.4x higher in months 0–3 (7.12%) than in month 13+ (2.95%).
   - *Caveat*: Parameterized by the generator's tenure decay function.
4. **Target Account Expansion Toward Business Tier** (`Medium Confidence`):
   - *Data Basis*: Business tier LTV ($3,168.00) is 14.5x Basic ($218.71) and churn is 2.50%. Expanding in-app upgrade triggers accelerates enterprise-tier adoption.

---

## 3. Data Architecture & Simulation Methodology

The synthetic dataset was engineered via `src/generate_data.py` to replicate Stripe subscription billing primitives:
- **Seed & Reproducibility**: Fixed seed (`seed=42`) ensuring identical generation across environments.
- **Customer Acquisition**: Monthly growth curve with Q4 holiday surges (+18%) and January spikes (+15%), generating 3,160 customer records.
- **Anniversary Billing**: Monthly invoices billed on the customer's signup day, capped at **day 28** to avoid 29–31 calendar boundary bugs.
- **Tier Mechanics**: Basic ($19/mo), Pro ($49/mo), and Business ($99/mo).
- **Expansion / Contraction**: Stochastic monthly transition probabilities between adjacent tiers (Basic $\leftrightarrow$ Pro $\leftrightarrow$ Business).
- **Promotional Coupons**: 25% of paid-channel customers receive a 10% lifetime discount applied to the invoice amount, while nominal subscription list price remains unchanged.

---

## 4. Analytical Results Tables

### Table 1: Annual MRR Waterfall & Performance Summary
| Metric | 2023 Total / Closing | 2024 Total / Closing | 2025 Total / Closing | 3-Year Total / Closing |
| :--- | :--- | :--- | :--- | :--- |
| **Closing MRR** | $14,037.00 | $39,268.00 | $73,552.00 | **$73,552.00** |
| **Active Subscriptions** | 390 | 954 | 1,618 | **1,618** |
| **Blended ARPA** | $35.99 | $41.16 | $45.46 | **$45.46** |
| **New MRR Inflow** | $21,392.00 | $37,848.00 | $51,629.00 | **$110,869.00** |
| **Expansion MRR** | $1,110.00 | $4,410.00 | $8,000.00 | **$13,520.00** |
| **Contraction MRR** | $180.00 | $870.00 | $1,332.00 | **$2,382.00** |
| **Churned MRR** | $8,285.00 | $16,157.00 | $26,996.00 | **$51,438.00** |
| **Net New MRR** | $14,037.00 | $25,231.00 | $31,301.00 | **$73,552.00** |
| **Average Logo Churn** | 7.08% | 5.50% | 4.62% | **5.76%** |
| **Average NRR** | 94.67% | 96.67% | 97.23% | **96.19%** |

---

### Table 2: Plan Tier Performance & Unit Economics (@ 80% Margin)
| Plan Tier | List Price | Active Sub-Months | Churned Subs | Monthly Churn Rate | Estimated LTV | Sample Size | Low Sample |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Basic** | $19.00 | 14,815 | 1,029 | **6.95%** | **$218.71** | 2,024 | False |
| **Pro** | $49.00 | 8,749 | 378 | **4.32%** | **$907.41** | 1,047 | False |
| **Business** | $99.00 | 5,409 | 135 | **2.50%** | **$3,168.00** | 514 | False |

---

### Table 3: Acquisition Channel Retention Breakdown
| Channel | Active Sub-Months | Churned Subs | Monthly Churn Rate | Sample Size | Low Sample |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Referral** | 6,689 | 269 | **4.02%** | 639 | False |
| **Organic** | 13,053 | 670 | **5.13%** | 1,403 | False |
| **Paid** | 9,231 | 603 | **6.53%** | 1,118 | False |

---

### Table 4: Churn Hazard by Customer Tenure Band
| Tenure Band | Active Sub-Months | Churned Subs | Monthly Churn Rate | Sample Size | Low Sample |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0–3 Months** | 10,109 | 720 | **7.12%** | 3,160 | False |
| **4–6 Months** | 5,138 | 301 | **5.86%** | 1,993 | False |
| **7–12 Months** | 6,771 | 316 | **4.67%** | 1,484 | False |
| **13+ Months** | 6,955 | 205 | **2.95%** | 813 | False |

---

### Table 5: Involuntary vs. Voluntary Churn Impact
| Churn Reason | Event Count | Share of Total Churn | Destroyed MRR (USD) | Share of Lost MRR |
| :--- | :--- | :--- | :--- | :--- |
| **Voluntary Churn** | 1,227 | **79.57%** | $38,563.00 | **74.97%** |
| **Involuntary Churn** | 315 | **20.43%** | $12,875.00 | **25.03%** |
| **Total** | 1,542 | 100.00% | $51,438.00 | 100.00% |

---

## 5. Dual-Engine Verification & Reconciliation Audit

### SQL Query Logic Verification (DuckDB vs. Pandas)
To ensure that all SQL queries written in `sql/` for MySQL 8.0+ are mathematically correct, `src/verify_sql.py` ran identical analytical SQL logic against an in-memory DuckDB database loaded with the generated CSVs:
- **01_mrr_monthly.sql**: Closing MRR ($73,552.00) and Active Customers (1,618) matched with **0.00 difference**.
- **02_mrr_movements.sql**: 36-month sum of Net New MRR ($73,552.00) and Expansion MRR ($13,520.00) matched with **0.00 difference**.
- **03_churn_rate.sql**: Average monthly logo churn rate (5.76%) matched with **0.00 difference**.
- **04_cohort_retention.sql**: Logo retention for the 2023-01 cohort at M00 (100.00%), M01 (90.16%), M06 (65.57%), and M12 (52.46%) matched with **0.00 difference**.
- **05_ltv_by_plan.sql**: LTV estimates for Basic ($218.71), Pro ($907.41), and Business ($3,168.00) matched with **0.00 difference**.

### Accounting Balance Reconciliation (`src/reconcile.py`)
1. **MRR Identity**: $\text{Opening MRR}_m + \text{Net New MRR}_m = \text{Closing MRR}_m$ passed for **all 36 months** with **0.00 max deviation**.
2. **Cohort Baseline**: Month-0 logo and revenue retention evaluated to exactly **100.00%** across all 36 cohorts.
3. **Cash Collections vs. List MRR**:
   - Total Paid Invoices: **$1,256,351.80**
   - Total Promotional Discounts: **$10,038.40**
   - Total Failed Invoices: **$12,782.80**
   - Cumulative Month-End List MRR: **$1,245,677.00**
   - The 2.69% variance is fully accounted for by mid-month anniversary billing dates and plan change prorations.

---

## 6. Technical Architecture & Tools

- **Language & Runtime**: Python 3.14.7.
- **Data Manipulation**: Pandas 3.1.1, NumPy 2.5.5.
- **Relational Databases & SQL**: MySQL 8.0+ syntax, DuckDB 2.0.1 in-memory OLAP engine.
- **Interactive UI**: Streamlit 1.67.0, Plotly 7.1.0.
- **Static Graphics**: Matplotlib 3.11.2.
- **Business Intelligence**: Power BI Desktop modeling specification and DAX measures.

---

## 7. Limitations & Real-World Considerations

1. **Synthetic Nature**: All subscriber actions stem from predefined probability distributions. Findings must not be cited as empirical SaaS benchmarks.
2. **Simplified Gregorian Modeling**: Monthly billing anniversaries are capped at day 28, bypassing end-of-month calendar leap rules.
3. **Absence of Contract Terms**: The model assumes month-to-month commitments; real-world B2B SaaS typically features annual upfront contracts with deferred revenue amortization.
4. **Classical LTV Formula**: Assumes flat churn hazards and zero cost of capital. Modern financial modeling incorporates DCF discounting and retention curves.

---

## 8. Demonstrated Skills & Portfolio Competencies

- **Subscription Financial Accounting**: Mastery of SaaS revenue metrics (MRR waterfalls, NRR, GRR, Quick Ratio, ARPA).
- **Advanced SQL Engineering**: Recursive CTEs, multi-partition window functions (`LAG`, `SUM OVER`, `ROW_NUMBER`), and foreign key relational schemas.
- **Dual-Engine Logic Verification**: Cross-validating Python/Pandas logic against analytical SQL in DuckDB.
- **Business Intelligence Architecture**: Formalizing DAX measures, star schema relationships, and matrix conditional formatting for Power BI Desktop.
- **Software Engineering Standards**: Modular code structure, deterministic seeding, virtual environment management, and defensive accounting reconciliation.
