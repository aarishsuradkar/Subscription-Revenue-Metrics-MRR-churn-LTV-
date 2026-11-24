# Data Dictionary: Synthetic Subscription Revenue Dataset

> **DISCLAIMER**: **Synthetic data modelled on Stripe-style subscription billing.** Not real customer data. All figures and events represent a controlled stochastic simulation designed for revenue metrics modeling (MRR, Churn, Cohort Retention, and LTV).

---

## 1. Executive Overview & Simulation Framework

This dataset simulates 36 months of B2B/prosumer SaaS subscription billing from **2023-01-01 to 2025-12-31**, comprising approximately 3,000 customers. The simulation mimics real-world subscription mechanics observed in Stripe billing environments, including recurring calendar charges, expansion and contraction lifecycle events, voluntary cancellations, and dunning (payment failure / retry) flows.

### Simulation Parameters & Assumptions
- **Time Horizon**: 2023-01-01 through 2025-12-31 (36 calendar months).
- **Customer Volume**: 3,000 simulated accounts created across the 3-year period.
- **Acquisition Growth & Seasonality**: Signup volume expands steadily over time with seasonal peaks (Q4 end-of-year enterprise buying and January new-year adoption, with mid-summer dips).
- **Acquisition Channels**:
  - `organic`: High product-led intent, baseline churn.
  - `paid`: Paid ad acquisition; higher initial churn sensitivity.
  - `referral`: High trust and word-of-mouth; lowest churn rate.
- **Geographic Markets**: US, UK, CA, DE, FR, AU.
- **Pricing & Plans**:
  - **Basic**: $19 / month (Entry-level prosumer; highest churn, lowest LTV).
  - **Pro**: $49 / month (Professional / small team tier).
  - **Business**: $99 / month (Advanced tier; lowest churn, highest LTV).
  - **Initial Plan Distribution**: Weighted toward entry tier (~60% Basic, ~28% Pro, ~12% Business).
- **Billing Mechanics**:
  - Monthly subscription billing occurs on the signup day of each month.
  - Days 29–31 are capped at **day 28** to avoid end-of-month Gregorian discrepancies and align with standard billing practice.
- **Discounts & Coupons**:
  - 25% of customers acquired through the `paid` channel receive an introductory promotional discount of 10% off recurring invoices.
  - The discount applies to the `invoices.amount` (e.g. $19 plan -> $17.10 invoiced, $1.90 discount). The `subscriptions.monthly_price` retains the nominal list price ($19, $49, $99) to preserve standard MRR reporting while reconciling against cash collections.
- **Voluntary Churn Mechanics**:
  - Hazard rate per month is parameterized by:
    - **Plan type**: Basic (5.0%/mo baseline) > Pro (3.0%/mo baseline) > Business (1.5%/mo baseline).
    - **Tenure curve**: Steepest in the initial onboarding window (tenure 0–3 months: 1.6x multiplier), easing between months 4–12 (1.0x), and plateauing for mature accounts (tenure 13+: 0.65x).
    - **Channel affinity**: Paid (1.3x) > Organic (1.0x) > Referral (0.7x).
- **Involuntary Churn & Dunning Mechanics**:
  - A payment failure rate of ~2.5% occurs monthly across active billing attempts (representing expired credit cards, insufficient funds, or banking declines).
  - Failed payments enter an automated dunning flow with 1 retry attempt:
    - **50% recovery**: Payment retry succeeds; invoice is collected as paid; subscription continues.
    - **50% unrecovered**: Retry fails; subscription is terminated immediately as `involuntary_churn`; the terminal invoice status is marked as `failed`.
- **Expansion & Contraction (Upgrades & Downgrades)**:
  - Active accounts have a monthly probability of upgrading (Basic → Pro, Pro → Business) of ~1.5%, or downgrading (Business → Pro, Pro → Basic) of ~0.7%.
  - When a plan transition occurs, the current subscription row is terminated on the transition date with `end_reason = 'upgrade'` or `'downgrade'`. A subsequent subscription row commences immediately on that date with the new tier and price.
- **Active Subscriptions**:
  - Accounts active as of 2025-12-31 have `end_date = NULL` and `end_reason = NULL`.

---

## 2. Table Specifications

### Table 1: `customers`
Stores high-level customer profile and acquisition metadata.

| Column Name | Data Type | Nullable | Description / Business Logic |
| :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR(36)` | No | Primary key. Unique customer identifier (e.g. `CUST-00001`). |
| `signup_date` | `DATE` | No | Date when the user registered and started their first subscription. Between `2023-01-01` and `2025-12-31`. |
| `country` | `VARCHAR(10)` | No | Customer ISO country code (`US`, `UK`, `CA`, `DE`, `FR`, `AU`). |
| `channel` | `VARCHAR(20)` | No | Acquisition marketing channel: `organic`, `paid`, or `referral`. |

---

### Table 2: `subscriptions`
Stores subscription lifecycle intervals. A customer can have multiple subscription records if they upgrade or downgrade over time.

| Column Name | Data Type | Nullable | Description / Business Logic |
| :--- | :--- | :--- | :--- |
| `subscription_id` | `VARCHAR(36)` | No | Primary key. Unique subscription interval identifier (e.g. `SUB-00001-01`). |
| `customer_id` | `VARCHAR(36)` | No | Foreign key referencing `customers.customer_id`. |
| `plan` | `VARCHAR(20)` | No | Subscription plan tier: `Basic`, `Pro`, or `Business`. |
| `monthly_price` | `DECIMAL(10,2)`| No | Nominal monthly recurring list price in USD (`19.00`, `49.00`, `99.00`). |
| `start_date` | `DATE` | No | Effective start date of this plan subscription interval. |
| `end_date` | `DATE` | Yes | Effective cancellation or plan switch date. `NULL` if subscription is still active at simulation end (2025-12-31). |
| `end_reason` | `VARCHAR(30)` | Yes | Reason for subscription termination. `NULL` if active. Values: `upgrade`, `downgrade`, `voluntary_churn`, `involuntary_churn`. |

---

### Table 3: `invoices`
Stores monthly billing transactions generated on the customer's recurring billing date.

| Column Name | Data Type | Nullable | Description / Business Logic |
| :--- | :--- | :--- | :--- |
| `invoice_id` | `VARCHAR(36)` | No | Primary key. Unique invoice identifier (e.g. `INV-000001`). |
| `customer_id` | `VARCHAR(36)` | No | Foreign key referencing `customers.customer_id`. |
| `subscription_id`| `VARCHAR(36)` | No | Foreign key referencing `subscriptions.subscription_id`. |
| `invoice_date` | `DATE` | No | Date invoice was issued (aligned with recurring monthly billing day). |
| `amount` | `DECIMAL(10,2)`| No | Final invoiced amount in USD after any applied discount. |
| `discount` | `DECIMAL(10,2)`| No | Discount amount in USD deducted from monthly price (e.g. `1.90` for 10% coupon on $19 plan; `0.00` if no coupon). |
| `status` | `VARCHAR(20)` | No | Payment collection status: `paid` (successful) or `failed` (unrecovered dunning failure). |

---

## 3. Metric Alignment Notes

- **MRR Calculation**: Active subscriptions at any month-end evaluate: `start_date <= month_end AND (end_date IS NULL OR end_date > month_end)`.
- **Cash vs MRR Reconciliation**:
  $$\text{Invoice Amount} = \text{monthly\_price} - \text{discount}$$
  $$\sum \text{Paid Invoices (Month } m\text{)} \approx \text{Average MRR}_m - \sum \text{Discounts} - \sum \text{Failed Invoices}$$
  Any difference between monthly invoice cash collected and month-end MRR is mathematically explained by prorations/calendar timing, coupon discounts, and failed invoice losses.
