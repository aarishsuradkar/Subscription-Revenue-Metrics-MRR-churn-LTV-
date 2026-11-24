# Dashboard & Report Screenshots Guide

This directory holds key visual exports and reference captures for the **Subscription Revenue Analytics** project.

> **DISCLAIMER**: **Synthetic data modelled on Stripe-style subscription billing.** Not real customer data.

---

## 1. Static Reference Charts (Included)
The following publication-grade charts are pre-generated from the Pandas metrics pipeline:
1. `mrr_movements_stacked.png`: Stacked bar chart showing monthly New MRR, Expansion MRR, Contraction MRR, Churned MRR, and Net New MRR trajectory.
2. `cohort_retention_heatmap.png`: High-density cohort retention heatmap across 12 completed months since signup.
3. `churn_by_plan.png`: Comparative side-by-side bar chart of monthly logo churn rate (%) and estimated LTV ($) across Basic, Pro, and Business tiers.

---

## 2. Recommended Live Dashboard Captures (Streamlit / Power BI)
To capture full-browser screenshots of the live interactive interface:

1. **Launch the dashboard**:
   ```bash
   streamlit run dashboard/app.py
   ```
2. **Recommended Capture Views**:
   - **`tab1_overview.png`**:
     - *View*: Overview tab showing the 4 top KPI cards (Closing MRR: $73,552.00, Active Subscriptions: 1,618, Blended ARPA: $45.46, Latest Net New: $2,833.00), the MRR growth area chart, and the MRR bridge bar chart.
   - **`tab2_churn_retention.png`**:
     - *View*: Churn & Retention tab displaying the Logo Churn vs. Gross Revenue Churn line trends, NRR/GRR trajectory (with 100% baseline), interactive cohort heatmap, and churn segmentation by plan, channel, and tenure band.
   - **`tab3_unit_economics.png`**:
     - *View*: Unit Economics tab highlighting the interactive Gross Margin slider (set to 80%), LTV by plan tier comparative column chart, and SaaS Quick Ratio trend.
   - **`tab4_method_verification.png`**:
     - *View*: Method & Data tab displaying the dual-engine verification table (DuckDB SQL vs. Pandas 12/12 match) and generator parameters.
