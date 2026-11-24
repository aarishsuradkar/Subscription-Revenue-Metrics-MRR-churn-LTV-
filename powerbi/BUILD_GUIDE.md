# Power BI Build Guide: Subscription Revenue Intelligence

> **DISCLAIMER**: **Synthetic data modelled on Stripe-style subscription billing.** Not real customer data.

This comprehensive guide details the step-by-step instructions to recreate the complete **Subscription Revenue Analytics** report in **Power BI Desktop** using the CSV exports in `output/`.

---

## 1. Architecture & Data Model

### Data Sources
Load the following CSV files from `output/` using **Get Data > Text/CSV**:
1. `mrr_monthly.csv`
2. `mrr_movements.csv`
3. `churn_monthly.csv`
4. `retention_cohorts_logo.csv`
5. `retention_cohorts_revenue.csv`
6. `ltv_by_plan.csv`
7. `churn_by_plan.csv`
8. `churn_by_channel.csv`
9. `churn_by_tenure.csv`
10. `churn_reasons.csv`
11. `plan_mix_monthly.csv`

---

## 2. Power Query Data Transformations & Types

Open **Power Query Editor** (`Home > Transform Data`) and verify/set the data types:

| Table | Column | Type | Formatting / Note |
| :--- | :--- | :--- | :--- |
| `mrr_monthly` | `month` | Text / Date | Format as `YYYY-MM` or convert to first of month Date |
| `mrr_monthly` | `mrr`, `arpa` | Fixed Decimal Number | Currency ($) |
| `mrr_monthly` | `active_customers` | Whole Number | Integer |
| `mrr_movements`| `opening_mrr`, `new_mrr`, `expansion_mrr`, `contraction_mrr`, `churned_mrr`, `net_new_mrr`, `closing_mrr` | Fixed Decimal Number | Currency ($) |
| `churn_monthly`| `logo_churn_rate`, `gross_revenue_churn_rate`, `nrr`, `grr` | Decimal Number | Percentage (`0.0%`) |
| `churn_monthly`| `quick_ratio` | Decimal Number | Decimal (`0.00x`) |
| `retention_cohorts_logo` | `M00` through `M35` | Decimal Number | Percentage (`0.0%`) |
| `retention_cohorts_revenue` | `M00` through `M35` | Decimal Number | Percentage (`0.0%`) |
| `ltv_by_plan` | `arpa` | Fixed Decimal Number | Currency ($) |
| `ltv_by_plan` | `monthly_churn_rate`, `gross_margin_pct` | Decimal Number | Percentage (`0.0%`) |

### Optional: Unpivoting Cohort Retention for Matrix Modeling
To build an interactive matrix of cohorts:
1. Select `retention_cohorts_logo`.
2. Select columns `cohort_month` and `cohort_size`.
3. Right-click and choose **Unpivot Other Columns**.
4. Rename `Attribute` to `Tenure Month` and `Value` to `Logo Retention Pct`.
5. Repeat for `retention_cohorts_revenue` to produce `Revenue Retention Pct`.

---

## 3. DAX Measures Library

Create a dedicated calculation table `_Measures` (`Modeling > New Table`: `_Measures = {0}`). Add the following DAX measures:

### Core Revenue Measures
```dax
Closing MRR = 
CALCULATE(
    MAX('mrr_monthly'[mrr]),
    LASTNONBLANK('mrr_monthly'[month], [mrr])
)
```

```dax
New MRR = SUM('mrr_movements'[new_mrr])
```

```dax
Expansion MRR = SUM('mrr_movements'[expansion_mrr])
```

```dax
Contraction MRR = SUM('mrr_movements'[contraction_mrr])
```

```dax
Churned MRR = SUM('mrr_movements'[churned_mrr])
```

```dax
Net New MRR = [New MRR] + [Expansion MRR] - [Contraction MRR] - [Churned MRR]
```

### Churn & Retention Measures
```dax
Active Subscriptions = 
CALCULATE(
    MAX('mrr_monthly'[active_customers]),
    LASTNONBLANK('mrr_monthly'[month], [active_customers])
)
```

```dax
Blended ARPA = 
DIVIDE([Closing MRR], [Active Subscriptions], 0)
```

```dax
Monthly Logo Churn Rate = 
DIVIDE(
    SUM('churn_monthly'[churned_customers]), 
    SUM('churn_monthly'[opening_active_customers]), 
    0
)
```

```dax
Net Revenue Retention (NRR) = 
DIVIDE(
    SUM('churn_monthly'[opening_mrr]) + [Expansion MRR] - [Contraction MRR] - [Churned MRR],
    SUM('churn_monthly'[opening_mrr]),
    1.0
)
```

```dax
Gross Revenue Retention (GRR) = 
DIVIDE(
    SUM('churn_monthly'[opening_mrr]) - [Contraction MRR] - [Churned MRR],
    SUM('churn_monthly'[opening_mrr]),
    1.0
)
```

```dax
Quick Ratio = 
DIVIDE(
    [New MRR] + [Expansion MRR],
    [Churned MRR] + [Contraction MRR],
    BLANK()
)
```

### Unit Economics & Dynamic LTV
Create a **What-If Parameter** for Gross Margin:
- Go to `Modeling > New Parameter > Numeric Range`.
- Name: `Gross Margin %`
- Minimum: `50`, Maximum: `95`, Increment: `5`, Default: `80`.

Add the dynamic LTV measure:
```dax
Dynamic LTV = 
VAR MarginVal = 'Gross Margin %'[Gross Margin % Value] / 100.0
VAR ChurnVal = [Monthly Logo Churn Rate]
RETURN
IF(
    ChurnVal > 0,
    DIVIDE([Blended ARPA] * MarginVal, ChurnVal),
    BLANK()
)
```

---

## 4. Visual Layout & Page Building

### Page 1: Executive Overview
- **Header**: Title "Subscription Revenue Intelligence" with subtitle `Synthetic data modelled on Stripe-style subscription billing.`
- **KPI Cards (Top Banner)**:
  - Card 1: `Closing MRR` ($)
  - Card 2: `Active Subscriptions` (#)
  - Card 3: `Blended ARPA` ($)
  - Card 4: `Latest Net New MRR` ($)
- **Visual 1 (Area Chart)**:
  - X-axis: `mrr_monthly[month]`
  - Y-axis: `[Closing MRR]`
  - Color: Royal Blue (`#1f77b4`)
- **Visual 2 (Stacked Column Chart - MRR Movements)**:
  - X-axis: `mrr_movements[month]`
  - Y-axis: `New MRR`, `Expansion MRR`, `Contraction MRR`, `Churned MRR`
  - Line overlay: `Net New MRR`
- **Visual 3 (100% Stacked Area Chart - Plan Mix)**:
  - X-axis: `plan_mix_monthly[month]`
  - Y-axis: `plan_mix_monthly[mrr]`
  - Legend: `plan_mix_monthly[plan]`

### Page 2: Churn & Retention Analytics
- **Visual 1 (Line Chart - Churn Trajectory)**:
  - X-axis: `churn_monthly[month]`
  - Values: `[Monthly Logo Churn Rate]`, `churn_monthly[gross_revenue_churn_rate]`
- **Visual 2 (Line Chart - NRR & GRR)**:
  - X-axis: `churn_monthly[month]`
  - Values: `[Net Revenue Retention (NRR)]`, `[Gross Revenue Retention (GRR)]`
  - Reference Line: Y = 1.0 (100% Baseline)
- **Visual 3 (Matrix Visual - Cohort Retention Heatmap)**:
  - Rows: `cohort_month`
  - Columns: `Tenure Month` (`M00`, `M01`, ..., `M18`)
  - Values: `Average of Logo Retention Pct`
  - **Conditional Formatting**: Background color > Rules/Gradient (3-color: 0% Red `#f8d7da`, 50% Amber `#fff3cd`, 100% Green `#d4edda`).
- **Visual 4 (Bar Charts - Segmentation)**:
  - Bar 1: `churn_by_plan[plan]` vs `monthly_churn_rate`
  - Bar 2: `churn_by_channel[channel]` vs `monthly_churn_rate`
  - Bar 3: `churn_by_tenure[tenure_band]` vs `monthly_churn_rate`
- **Visual 5 (Donut Chart - Churn Reason Share)**:
  - Category: `churn_reasons[reason]`
  - Values: `churn_reasons[lost_mrr_total]`

### Page 3: Unit Economics (LTV & ARPA)
- **Slicer**: `Gross Margin % Value` slider (50% to 95%).
- **Visual 1 (Clustered Column Chart)**:
  - X-axis: `ltv_by_plan[plan]`
  - Y-axis: `[Dynamic LTV]`
  - Data Labels: Enabled ($)
- **Visual 2 (Line Chart - Quick Ratio)**:
  - X-axis: `churn_monthly[month]`
  - Y-axis: `[Quick Ratio]`
  - Reference Line: Y = 4.0 (Healthy SaaS benchmark line)

---

## 5. Critical Pitfalls & Common Mistakes in SaaS Power BI Modeling

1. **Never Sum Rates or Ratios**:
   - ❌ `SUM(churn_monthly[logo_churn_rate])`: Mathematically incorrect.
   - ✅ Always use `DIVIDE(SUM(churned_customers), SUM(opening_active_customers))`.
2. **Reconciliation Check**:
   - Ensure `[Opening MRR] + [Net New MRR] = [Closing MRR]` holds across all visual slices.
3. **Handling Discontinued Plans or 0 Churn**:
   - Always guard LTV calculations with `IF(ChurnVal > 0, ...)` to avoid divide-by-zero errors (`#DIV/0!`).
4. **Report Footers**:
   - Place this caption on all pages: *"Synthetic data modelled on Stripe-style subscription billing. Not real customer data."*
