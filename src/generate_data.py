"""
generate_data.py
Synthetic Subscription Data Generator
Modelled on Stripe-style subscription billing.

Period: 2023-01-01 to 2025-12-31 (36 calendar months)
Target: ~3,000 customers
Outputs:
  - data/customers.csv
  - data/subscriptions.csv
  - data/invoices.csv
  - data/generation_summary.json / printed summary
"""

import os
import json
import random
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np

def add_months(base_date, months):
    """Adds months to a date where day is <= 28."""
    total_months = base_date.year * 12 + (base_date.month - 1) + months
    new_year = total_months // 12
    new_month = (total_months % 12) + 1
    return date(new_year, new_month, base_date.day)

# Set fixed seeds for deterministic generation
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

START_DATE = date(2023, 1, 1)
END_DATE = date(2025, 12, 31)

PLANS = {
    'Basic': 19.00,
    'Pro': 49.00,
    'Business': 99.00
}

PLAN_UPGRADES = {
    'Basic': 'Pro',
    'Pro': 'Business',
    'Business': None
}

PLAN_DOWNGRADES = {
    'Business': 'Pro',
    'Pro': 'Basic',
    'Basic': None
}

COUNTRIES = ['US', 'UK', 'CA', 'DE', 'FR', 'AU']
COUNTRY_WEIGHTS = [0.45, 0.20, 0.12, 0.10, 0.08, 0.05]

CHANNELS = ['organic', 'paid', 'referral']
CHANNEL_WEIGHTS = [0.45, 0.35, 0.20]

CHANNEL_CHURN_MULTIPLIERS = {
    'paid': 1.30,
    'organic': 1.00,
    'referral': 0.70
}

PLAN_BASE_CHURN = {
    'Basic': 0.050,
    'Pro': 0.030,
    'Business': 0.015
}

def get_tenure_multiplier(tenure_months):
    if tenure_months <= 2:  # 0, 1, 2 (first 3 months)
        return 1.65
    elif tenure_months <= 5:  # 3, 4, 5 (months 4-6)
        return 1.10
    elif tenure_months <= 11: # 6 to 11 (months 7-12)
        return 0.85
    else:
        return 0.60

def generate_monthly_signups():
    """Generates customer signups month-by-month with growth and seasonality."""
    signups_by_month = []
    current_month = START_DATE.replace(day=1)
    month_idx = 0
    
    while current_month <= END_DATE:
        cal_month = current_month.month
        # Growth trend
        base_volume = 52.0 + (month_idx * 1.85)
        
        # Seasonality factors
        seasonality = 1.0
        if cal_month in (10, 11, 12):
            seasonality = 1.18  # Q4 surge
        elif cal_month == 1:
            seasonality = 1.15  # January new year surge
        elif cal_month in (7, 8):
            seasonality = 0.90  # Summer lull
            
        noise = random.uniform(0.94, 1.06)
        count = int(round(base_volume * seasonality * noise))
        signups_by_month.append((current_month, count))
        
        current_month = add_months(current_month, 1)
        month_idx += 1
        
    return signups_by_month

def simulate_dataset():
    monthly_schedule = generate_monthly_signups()
    
    customers = []
    subscriptions = []
    invoices = []
    
    cust_counter = 1
    sub_counter = 1
    inv_counter = 1
    
    for month_start, count in monthly_schedule:
        for _ in range(count):
            cust_id = f"CUST-{cust_counter:05d}"
            cust_counter += 1
            
            # Signup day capped at 28 to avoid month-end date rollover discrepancies
            day = random.randint(1, 28)
            signup_date = date(month_start.year, month_start.month, day)
            if signup_date > END_DATE:
                continue
                
            country = random.choices(COUNTRIES, weights=COUNTRY_WEIGHTS)[0]
            channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
            
            # Paid coupon discount: 25% of paid-channel customers get 10% coupon
            has_coupon = (channel == 'paid' and random.random() < 0.25)
            discount_pct = 0.10 if has_coupon else 0.00
            
            customers.append({
                'customer_id': cust_id,
                'signup_date': signup_date.isoformat(),
                'country': country,
                'channel': channel
            })
            
            # Initial plan selection
            initial_plan = random.choices(['Basic', 'Pro', 'Business'], weights=[0.62, 0.26, 0.12])[0]
            current_plan = initial_plan
            current_price = PLANS[current_plan]
            
            sub_id = f"SUB-{sub_counter:06d}"
            sub_counter += 1
            sub_start_date = signup_date
            
            # Track customer billing simulation
            is_active = True
            months_active = 0
            
            while is_active:
                current_billing_date = add_months(signup_date, months_active)
                if current_billing_date > END_DATE:
                    break
                
                # Check for involuntary payment failure (on months > 0, signup invoice is always collected)
                involuntary_churn = False
                if months_active > 0 and random.random() < 0.024:  # ~2.4% payment failure chance
                    # Payment failed. Dunning retry with 50% recovery
                    if random.random() < 0.50:
                        # Recovered via retry! Invoiced as paid
                        inv_status = 'paid'
                    else:
                        # Recovery failed -> Involuntary churn
                        inv_status = 'failed'
                        involuntary_churn = True
                else:
                    inv_status = 'paid'
                
                # Calculate invoice amount & discount
                nominal_amount = current_price
                disc_amount = round(nominal_amount * discount_pct, 2)
                billed_amount = round(nominal_amount - disc_amount, 2)
                
                # Record Invoice
                inv_id = f"INV-{inv_counter:07d}"
                inv_counter += 1
                invoices.append({
                    'invoice_id': inv_id,
                    'customer_id': cust_id,
                    'subscription_id': sub_id,
                    'invoice_date': current_billing_date.isoformat(),
                    'amount': billed_amount,
                    'discount': disc_amount,
                    'status': inv_status
                })
                
                # Handle Involuntary Churn
                if involuntary_churn:
                    subscriptions.append({
                        'subscription_id': sub_id,
                        'customer_id': cust_id,
                        'plan': current_plan,
                        'monthly_price': current_price,
                        'start_date': sub_start_date.isoformat(),
                        'end_date': current_billing_date.isoformat(),
                        'end_reason': 'involuntary_churn'
                    })
                    is_active = False
                    break
                
                # If paid successfully, check for voluntary churn before next cycle
                next_billing_date = add_months(signup_date, months_active + 1)
                
                base_churn = PLAN_BASE_CHURN[current_plan]
                tenure_mult = get_tenure_multiplier(months_active)
                channel_mult = CHANNEL_CHURN_MULTIPLIERS[channel]
                monthly_churn_prob = base_churn * tenure_mult * channel_mult
                
                if random.random() < monthly_churn_prob:
                    # Voluntary cancellation happens between this billing cycle and next
                    days_in_month = (next_billing_date - current_billing_date).days
                    cancel_day_offset = random.randint(1, max(1, days_in_month - 1))
                    cancel_date = current_billing_date + timedelta(days=cancel_day_offset)
                    
                    if cancel_date <= END_DATE:
                        subscriptions.append({
                            'subscription_id': sub_id,
                            'customer_id': cust_id,
                            'plan': current_plan,
                            'monthly_price': current_price,
                            'start_date': sub_start_date.isoformat(),
                            'end_date': cancel_date.isoformat(),
                            'end_reason': 'voluntary_churn'
                        })
                    else:
                        # Cancel falls after simulation period; active through simulation end
                        subscriptions.append({
                            'subscription_id': sub_id,
                            'customer_id': cust_id,
                            'plan': current_plan,
                            'monthly_price': current_price,
                            'start_date': sub_start_date.isoformat(),
                            'end_date': None,
                            'end_reason': None
                        })
                    is_active = False
                    break
                
                # Check for expansion / contraction at next billing cycle
                if next_billing_date <= END_DATE:
                    # Upgrade probability ~1.6%
                    # Downgrade probability ~0.7%
                    plan_change = None
                    if random.random() < 0.016 and PLAN_UPGRADES[current_plan]:
                        plan_change = ('upgrade', PLAN_UPGRADES[current_plan])
                    elif random.random() < 0.007 and PLAN_DOWNGRADES[current_plan]:
                        plan_change = ('downgrade', PLAN_DOWNGRADES[current_plan])
                        
                    if plan_change:
                        change_reason, new_plan = plan_change
                        # Close current subscription on next billing date
                        subscriptions.append({
                            'subscription_id': sub_id,
                            'customer_id': cust_id,
                            'plan': current_plan,
                            'monthly_price': current_price,
                            'start_date': sub_start_date.isoformat(),
                            'end_date': next_billing_date.isoformat(),
                            'end_reason': change_reason
                        })
                        # Start new subscription immediately
                        sub_id = f"SUB-{sub_counter:06d}"
                        sub_counter += 1
                        current_plan = new_plan
                        current_price = PLANS[current_plan]
                        sub_start_date = next_billing_date
                
                months_active += 1
            
            # If still active at end of simulation, record open subscription
            if is_active:
                subscriptions.append({
                    'subscription_id': sub_id,
                    'customer_id': cust_id,
                    'plan': current_plan,
                    'monthly_price': current_price,
                    'start_date': sub_start_date.isoformat(),
                    'end_date': None,
                    'end_reason': None
                })

    df_customers = pd.DataFrame(customers)
    df_subscriptions = pd.DataFrame(subscriptions)
    df_invoices = pd.DataFrame(invoices)
    
    return df_customers, df_subscriptions, df_invoices

def main():
    print("=" * 70)
    print("Generating Synthetic Subscription Revenue Dataset (2023-2025)...")
    print("=" * 70)
    
    df_customers, df_subscriptions, df_invoices = simulate_dataset()
    
    os.makedirs('data', exist_ok=True)
    df_customers.to_csv('data/customers.csv', index=False)
    df_subscriptions.to_csv('data/subscriptions.csv', index=False)
    df_invoices.to_csv('data/invoices.csv', index=False)
    
    # Compute summary statistics directly from generated data
    total_customers = len(df_customers)
    total_subscriptions = len(df_subscriptions)
    total_invoices = len(df_invoices)
    
    date_min = df_customers['signup_date'].min()
    date_max = df_customers['signup_date'].max()
    
    plan_counts = df_subscriptions['plan'].value_counts()
    plan_mix = (plan_counts / len(df_subscriptions) * 100).round(2).to_dict()
    
    churn_df = df_subscriptions[df_subscriptions['end_reason'].isin(['voluntary_churn', 'involuntary_churn'])]
    total_churns = len(churn_df)
    churn_by_reason = churn_df['end_reason'].value_counts()
    churn_reason_share = (churn_by_reason / total_churns * 100).round(2).to_dict()
    
    upgrades_count = int((df_subscriptions['end_reason'] == 'upgrade').sum())
    downgrades_count = int((df_subscriptions['end_reason'] == 'downgrade').sum())
    active_at_end = int(df_subscriptions['end_date'].isna().sum())
    
    summary = {
        'total_customers': int(total_customers),
        'total_subscriptions': int(total_subscriptions),
        'total_invoices': int(total_invoices),
        'signup_date_min': date_min,
        'signup_date_max': date_max,
        'plan_mix_pct': plan_mix,
        'total_churned_subscriptions': int(total_churns),
        'churn_reasons_share_pct': churn_reason_share,
        'upgrades_count': upgrades_count,
        'downgrades_count': downgrades_count,
        'active_subscriptions_at_end': active_at_end,
        'total_invoiced_gross_usd': float(df_invoices['amount'].sum().round(2)),
        'total_discounts_usd': float(df_invoices['discount'].sum().round(2)),
        'failed_invoices_count': int((df_invoices['status'] == 'failed').sum())
    }
    
    with open('data/generation_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
        
    print(f"Generated {total_customers:,} customers ({date_min} to {date_max})")
    print(f"Generated {total_subscriptions:,} subscription periods")
    print(f"Generated {total_invoices:,} invoices")
    print("\nPlan Mix across all subscription records:")
    for plan, pct in plan_mix.items():
        print(f"  - {plan}: {pct}%")
    print(f"\nChurn Breakdown ({total_churns:,} churned subscriptions):")
    for reason, pct in churn_reason_share.items():
        print(f"  - {reason}: {pct}%")
    print(f"\nUpgrades: {upgrades_count:,} | Downgrades: {downgrades_count:,}")
    print(f"Active subscriptions at 2025-12-31: {active_at_end:,}")
    print(f"Total cash invoiced: ${summary['total_invoiced_gross_usd']:,.2f}")
    print(f"Total discounts applied: ${summary['total_discounts_usd']:,.2f}")
    print(f"Failed invoices: {summary['failed_invoices_count']:,}")
    print("=" * 70)
    print("Synthetic data saved to data/ directory successfully.")

if __name__ == '__main__':
    main()
