"""
metrics.py
Subscription Revenue Metrics Computation (MRR, Churn, Cohort Retention, LTV)
Calculates all SaaS metrics from generated synthetic data and writes CSVs and PNG charts to output/.

SYNTHETIC DATA DISCLAIMER:
"Synthetic data modelled on Stripe-style subscription billing. Not real customer data."
"""

import os
import calendar
from datetime import datetime, date
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

def get_month_end_date(year, month):
    _, last_day = calendar.monthrange(year, month)
    return date(year, month, last_day)

def generate_calendar_months(start_year=2023, end_year=2025):
    months = []
    for yr in range(start_year, end_year + 1):
        for m in range(1, 13):
            month_str = f"{yr:04d}-{m:02d}"
            end_dt = get_month_end_date(yr, m)
            months.append((month_str, end_dt))
    return months

def load_data():
    df_customers = pd.read_csv('data/customers.csv')
    df_subscriptions = pd.read_csv('data/subscriptions.csv')
    df_invoices = pd.read_csv('data/invoices.csv')
    
    # Parse dates
    df_customers['signup_date'] = pd.to_datetime(df_customers['signup_date']).dt.date
    df_subscriptions['start_date'] = pd.to_datetime(df_subscriptions['start_date']).dt.date
    df_subscriptions['end_date'] = pd.to_datetime(df_subscriptions['end_date']).dt.date
    df_invoices['invoice_date'] = pd.to_datetime(df_invoices['invoice_date']).dt.date
    
    return df_customers, df_subscriptions, df_invoices

def compute_monthly_mrr_and_movements(df_customers, df_subscriptions):
    cal_months = generate_calendar_months(2023, 2025)
    
    # Build a customer x month panel of active subscriptions
    # For each month end, find each customer's active subscription (if any)
    customer_ids = df_customers['customer_id'].unique()
    
    # Pre-filter subscriptions for speed
    sub_records = df_subscriptions.to_dict('records')
    
    mrr_monthly_rows = []
    mrr_movement_rows = []
    churn_monthly_rows = []
    plan_mix_rows = []
    
    # Map customer_id -> previous month MRR
    prev_customer_mrr = {cid: 0.0 for cid in customer_ids}
    prev_total_mrr = 0.0
    prev_active_cids = set()
    
    for month_str, month_end in cal_months:
        # Determine active subscription per customer at month_end
        # start_date <= month_end and (end_date is null or end_date > month_end)
        curr_customer_mrr = {}
        curr_customer_plan = {}
        
        for sub in sub_records:
            s_start = sub['start_date']
            s_end = sub['end_date']
            if s_start <= month_end and (s_end is None or pd.isna(s_end) or s_end > month_end):
                cid = sub['customer_id']
                curr_customer_mrr[cid] = sub['monthly_price']
                curr_customer_plan[cid] = sub['plan']
                
        curr_active_cids = set(curr_customer_mrr.keys())
        curr_total_mrr = round(sum(curr_customer_mrr.values()), 2)
        active_customer_count = len(curr_active_cids)
        arpa = round(curr_total_mrr / active_customer_count, 2) if active_customer_count > 0 else 0.0
        
        # Monthly MRR row
        mrr_monthly_rows.append({
            'month': month_str,
            'mrr': curr_total_mrr,
            'active_customers': active_customer_count,
            'arpa': arpa
        })
        
        # Plan mix for this month
        plan_counts = {}
        plan_mrrs = {}
        for plan in ['Basic', 'Pro', 'Business']:
            plan_counts[plan] = 0
            plan_mrrs[plan] = 0.0
            
        for cid, plan in curr_customer_plan.items():
            plan_counts[plan] += 1
            plan_mrrs[plan] += curr_customer_mrr[cid]
            
        for plan in ['Basic', 'Pro', 'Business']:
            p_cnt = plan_counts[plan]
            p_mrr = round(plan_mrrs[plan], 2)
            share_cnt = round((p_cnt / active_customer_count * 100), 2) if active_customer_count > 0 else 0.0
            share_mrr = round((p_mrr / curr_total_mrr * 100), 2) if curr_total_mrr > 0 else 0.0
            plan_mix_rows.append({
                'month': month_str,
                'plan': plan,
                'active_subscriptions': p_cnt,
                'mrr': p_mrr,
                'share_of_active_pct': share_cnt,
                'share_of_mrr_pct': share_mrr
            })
            
        # Compute movements from prev month
        new_mrr = 0.0
        expansion_mrr = 0.0
        contraction_mrr = 0.0
        churned_mrr = 0.0
        
        new_customers = 0
        churned_customers = 0
        
        for cid in customer_ids:
            p_mrr = prev_customer_mrr.get(cid, 0.0)
            c_mrr = curr_customer_mrr.get(cid, 0.0)
            
            if p_mrr == 0.0 and c_mrr > 0.0:
                new_mrr += c_mrr
                new_customers += 1
            elif p_mrr > 0.0 and c_mrr > 0.0:
                if c_mrr > p_mrr:
                    expansion_mrr += (c_mrr - p_mrr)
                elif c_mrr < p_mrr:
                    contraction_mrr += (p_mrr - c_mrr)
            elif p_mrr > 0.0 and c_mrr == 0.0:
                churned_mrr += p_mrr
                churned_customers += 1
                
        new_mrr = round(new_mrr, 2)
        expansion_mrr = round(expansion_mrr, 2)
        contraction_mrr = round(contraction_mrr, 2)
        churned_mrr = round(churned_mrr, 2)
        net_new_mrr = round(new_mrr + expansion_mrr - contraction_mrr - churned_mrr, 2)
        
        # Check identity: opening_mrr + net_new_mrr = closing_mrr
        expected_closing = round(prev_total_mrr + net_new_mrr, 2)
        reconciled = (abs(expected_closing - curr_total_mrr) < 0.01)
        
        mrr_movement_rows.append({
            'month': month_str,
            'opening_mrr': prev_total_mrr,
            'new_mrr': new_mrr,
            'expansion_mrr': expansion_mrr,
            'contraction_mrr': contraction_mrr,
            'churned_mrr': churned_mrr,
            'net_new_mrr': net_new_mrr,
            'closing_mrr': curr_total_mrr,
            'reconciliation_check': 'PASS' if reconciled else 'FAIL'
        })
        
        # Churn & retention metrics
        opening_active = len(prev_active_cids)
        logo_churn_rate = round(churned_customers / opening_active, 4) if opening_active > 0 else 0.0
        gross_rev_churn_rate = round((churned_mrr + contraction_mrr) / prev_total_mrr, 4) if prev_total_mrr > 0 else 0.0
        grr = round((prev_total_mrr - contraction_mrr - churned_mrr) / prev_total_mrr, 4) if prev_total_mrr > 0 else 1.0
        nrr = round((prev_total_mrr + expansion_mrr - contraction_mrr - churned_mrr) / prev_total_mrr, 4) if prev_total_mrr > 0 else 1.0
        
        # Quick ratio: (New + Expansion) / (Churned + Contraction)
        churn_and_contraction = churned_mrr + contraction_mrr
        quick_ratio = round((new_mrr + expansion_mrr) / churn_and_contraction, 2) if churn_and_contraction > 0 else np.nan
        
        churn_monthly_rows.append({
            'month': month_str,
            'opening_active_customers': opening_active,
            'new_customers': new_customers,
            'churned_customers': churned_customers,
            'closing_active_customers': active_customer_count,
            'logo_churn_rate': logo_churn_rate,
            'gross_revenue_churn_rate': gross_rev_churn_rate,
            'nrr': nrr,
            'grr': grr,
            'quick_ratio': quick_ratio
        })
        
        # Update trackers
        prev_customer_mrr = {cid: curr_customer_mrr.get(cid, 0.0) for cid in customer_ids}
        prev_total_mrr = curr_total_mrr
        prev_active_cids = curr_active_cids
        
    df_mrr_monthly = pd.DataFrame(mrr_monthly_rows)
    df_mrr_movements = pd.DataFrame(mrr_movement_rows)
    df_churn_monthly = pd.DataFrame(churn_monthly_rows)
    df_plan_mix = pd.DataFrame(plan_mix_rows)
    
    return df_mrr_monthly, df_mrr_movements, df_churn_monthly, df_plan_mix

def compute_cohort_retention(df_customers, df_subscriptions):
    # Customer signup month
    df_customers['cohort_month'] = pd.to_datetime(df_customers['signup_date']).dt.strftime('%Y-%m')
    cohort_groups = df_customers.groupby('cohort_month')
    
    # Prepare initial cohort sizes and initial MRR
    first_sub = df_subscriptions.sort_values('start_date').groupby('customer_id').first().reset_index()
    cust_first_mrr = dict(zip(first_sub['customer_id'], first_sub['monthly_price']))
    
    cal_months = [m[0] for m in generate_calendar_months(2023, 2025)]
    month_to_idx = {m: i for i, m in enumerate(cal_months)}
    
    logo_retention_records = []
    rev_retention_records = []
    
    # Pre-parse subscription dates for checking active status
    subs_by_cust = {}
    for sub in df_subscriptions.to_dict('records'):
        subs_by_cust.setdefault(sub['customer_id'], []).append(sub)
        
    for cohort_month, grp in cohort_groups:
        cohort_cids = grp['customer_id'].tolist()
        cohort_size = len(cohort_cids)
        cohort_initial_mrr = sum(cust_first_mrr.get(cid, 0.0) for cid in cohort_cids)
        
        cohort_start_idx = month_to_idx[cohort_month]
        
        logo_row = {'cohort_month': cohort_month, 'cohort_size': cohort_size}
        rev_row = {'cohort_month': cohort_month, 'cohort_initial_mrr': round(cohort_initial_mrr, 2)}
        
        for tenure in range(36):
            target_idx = cohort_start_idx + tenure
            col_name = f"M{tenure:02d}"
            
            if target_idx >= len(cal_months):
                logo_row[col_name] = np.nan
                rev_row[col_name] = np.nan
                continue
                
            if tenure == 0:
                # Month-0 retention is 100% by definition
                logo_row[col_name] = 100.0
                rev_row[col_name] = 100.0
                continue
                
            target_month_str, target_end_date = generate_calendar_months(2023, 2025)[target_idx]
            
            active_count = 0
            active_mrr = 0.0
            
            for cid in cohort_cids:
                user_subs = subs_by_cust.get(cid, [])
                for sub in user_subs:
                    if sub['start_date'] <= target_end_date and (sub['end_date'] is None or pd.isna(sub['end_date']) or sub['end_date'] > target_end_date):
                        active_count += 1
                        active_mrr += sub['monthly_price']
                        break
                        
            logo_pct = round(active_count / cohort_size * 100.0, 2)
            rev_pct = round(active_mrr / cohort_initial_mrr * 100.0, 2) if cohort_initial_mrr > 0 else 0.0
            
            logo_row[col_name] = logo_pct
            rev_row[col_name] = rev_pct
            
        logo_retention_records.append(logo_row)
        rev_retention_records.append(rev_row)
        
    df_cohort_logo = pd.DataFrame(logo_retention_records)
    df_cohort_rev = pd.DataFrame(rev_retention_records)
    
    return df_cohort_logo, df_cohort_rev

def compute_plan_churn_and_ltv(df_subscriptions, gross_margin=0.80):
    # Calculate monthly churn rate per plan
    # Total churn events on each plan vs total exposure (subscription-months)
    plans = ['Basic', 'Pro', 'Business']
    plan_prices = {'Basic': 19.00, 'Pro': 49.00, 'Business': 99.00}
    
    # Calculate exposure: for each month a subscription was active
    cal_months = generate_calendar_months(2023, 2025)
    
    exposure_counts = {p: 0 for p in plans}
    churn_counts = {p: 0 for p in plans}
    unique_custs = {p: set() for p in plans}
    
    for sub in df_subscriptions.to_dict('records'):
        p = sub['plan']
        unique_custs[p].add(sub['customer_id'])
        if sub['end_reason'] in ['voluntary_churn', 'involuntary_churn']:
            churn_counts[p] += 1
            
        for _, month_end in cal_months:
            if sub['start_date'] <= month_end and (sub['end_date'] is None or pd.isna(sub['end_date']) or sub['end_date'] > month_end):
                exposure_counts[p] += 1
                
    rows_churn = []
    rows_ltv = []
    
    for p in plans:
        exp = exposure_counts[p]
        churn = churn_counts[p]
        sample_size = len(unique_custs[p])
        is_low_sample = (sample_size < 30)
        
        # Monthly churn rate = churn events / total active sub-months
        monthly_churn = round(churn / exp, 4) if exp > 0 else 0.0
        
        rows_churn.append({
            'plan': p,
            'active_sub_months': exp,
            'churned_subscriptions': churn,
            'monthly_churn_rate': monthly_churn,
            'sample_size': sample_size,
            'is_low_sample': is_low_sample
        })
        
        arpa = plan_prices[p]
        if monthly_churn > 0:
            ltv = round((arpa * gross_margin) / monthly_churn, 2)
            ltv_str = str(ltv)
        else:
            ltv = np.nan
            ltv_str = "not estimable"
            
        rows_ltv.append({
            'plan': p,
            'arpa': arpa,
            'gross_margin_pct': round(gross_margin * 100, 1),
            'monthly_churn_rate': monthly_churn,
            'ltv_estimate': ltv_str,
            'sample_size': sample_size,
            'is_low_sample': is_low_sample
        })
        
    df_churn_plan = pd.DataFrame(rows_churn)
    df_ltv = pd.DataFrame(rows_ltv)
    return df_churn_plan, df_ltv

def compute_segment_churn(df_customers, df_subscriptions):
    # Churn by channel
    cal_months = generate_calendar_months(2023, 2025)
    cust_channel = dict(zip(df_customers['customer_id'], df_customers['channel']))
    
    channel_exposure = {'organic': 0, 'paid': 0, 'referral': 0}
    channel_churn = {'organic': 0, 'paid': 0, 'referral': 0}
    channel_custs = {'organic': set(), 'paid': set(), 'referral': set()}
    
    for sub in df_subscriptions.to_dict('records'):
        ch = cust_channel.get(sub['customer_id'])
        if not ch:
            continue
        channel_custs[ch].add(sub['customer_id'])
        if sub['end_reason'] in ['voluntary_churn', 'involuntary_churn']:
            channel_churn[ch] += 1
            
        for _, month_end in cal_months:
            if sub['start_date'] <= month_end and (sub['end_date'] is None or pd.isna(sub['end_date']) or sub['end_date'] > month_end):
                channel_exposure[ch] += 1
                
    rows_channel = []
    for ch in ['organic', 'paid', 'referral']:
        exp = channel_exposure[ch]
        churn = channel_churn[ch]
        sample = len(channel_custs[ch])
        rate = round(churn / exp, 4) if exp > 0 else 0.0
        rows_channel.append({
            'channel': ch,
            'active_sub_months': exp,
            'churned_subscriptions': churn,
            'monthly_churn_rate': rate,
            'sample_size': sample,
            'is_low_sample': (sample < 30)
        })
    df_churn_channel = pd.DataFrame(rows_channel)
    
    # Churn by tenure band
    # Bands: '0-3 months', '4-6 months', '7-12 months', '13+ months'
    # For every active subscription-month, what tenure band was the customer in?
    cust_signup = dict(zip(df_customers['customer_id'], df_customers['signup_date']))
    
    def get_tenure_band(months):
        if months <= 3:
            return '0-3 months'
        elif months <= 6:
            return '4-6 months'
        elif months <= 12:
            return '7-12 months'
        else:
            return '13+ months'
            
    tenure_bands = ['0-3 months', '4-6 months', '7-12 months', '13+ months']
    tenure_exposure = {tb: 0 for tb in tenure_bands}
    tenure_churn = {tb: 0 for tb in tenure_bands}
    tenure_custs = {tb: set() for tb in tenure_bands}
    
    for sub in df_subscriptions.to_dict('records'):
        cid = sub['customer_id']
        s_date = cust_signup.get(cid)
        if not s_date:
            continue
            
        if sub['end_reason'] in ['voluntary_churn', 'involuntary_churn']:
            end_d = sub['end_date']
            # Tenure in months at cancellation
            tenure_m = (end_d.year - s_date.year) * 12 + (end_d.month - s_date.month)
            tb = get_tenure_band(tenure_m)
            tenure_churn[tb] += 1
            tenure_custs[tb].add(cid)
            
        for _, month_end in cal_months:
            if sub['start_date'] <= month_end and (sub['end_date'] is None or pd.isna(sub['end_date']) or sub['end_date'] > month_end):
                tenure_m = (month_end.year - s_date.year) * 12 + (month_end.month - s_date.month)
                tb = get_tenure_band(tenure_m)
                tenure_exposure[tb] += 1
                tenure_custs[tb].add(cid)
                
    rows_tenure = []
    for tb in tenure_bands:
        exp = tenure_exposure[tb]
        churn = tenure_churn[tb]
        sample = len(tenure_custs[tb])
        rate = round(churn / exp, 4) if exp > 0 else 0.0
        rows_tenure.append({
            'tenure_band': tb,
            'active_sub_months': exp,
            'churned_subscriptions': churn,
            'monthly_churn_rate': rate,
            'sample_size': sample,
            'is_low_sample': (sample < 30)
        })
    df_churn_tenure = pd.DataFrame(rows_tenure)
    
    # Churn reasons
    churn_subs = df_subscriptions[df_subscriptions['end_reason'].isin(['voluntary_churn', 'involuntary_churn'])]
    total_churn_count = len(churn_subs)
    
    reasons_summary = []
    for r in ['voluntary_churn', 'involuntary_churn']:
        sub_r = churn_subs[churn_subs['end_reason'] == r]
        cnt = len(sub_r)
        share = round(cnt / total_churn_count * 100, 2) if total_churn_count > 0 else 0.0
        lost_mrr = round(sub_r['monthly_price'].sum(), 2)
        reasons_summary.append({
            'reason': r,
            'churn_count': cnt,
            'share_pct': share,
            'lost_mrr_total': lost_mrr
        })
    df_churn_reasons = pd.DataFrame(reasons_summary)
    
    return df_churn_channel, df_churn_tenure, df_churn_reasons

def generate_charts(df_mrr_movements, df_cohort_logo, df_churn_plan, df_ltv):
    os.makedirs('output', exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    # Chart 1: MRR Movements Stacked Bars
    fig, ax = plt.subplots(figsize=(14, 7))
    months = df_mrr_movements['month']
    x = np.arange(len(months))
    
    new_mrr = df_mrr_movements['new_mrr']
    expansion_mrr = df_mrr_movements['expansion_mrr']
    contraction_mrr = -df_mrr_movements['contraction_mrr']
    churned_mrr = -df_mrr_movements['churned_mrr']
    net_new = df_mrr_movements['net_new_mrr']
    
    # Positive stacks
    ax.bar(x, new_mrr, label='New MRR', color='#2ca02c', alpha=0.85, width=0.6)
    ax.bar(x, expansion_mrr, bottom=new_mrr, label='Expansion MRR', color='#1f77b4', alpha=0.85, width=0.6)
    
    # Negative stacks
    ax.bar(x, contraction_mrr, label='Contraction MRR', color='#ff7f0e', alpha=0.85, width=0.6)
    ax.bar(x, churned_mrr, bottom=contraction_mrr, label='Churned MRR', color='#d62728', alpha=0.85, width=0.6)
    
    # Net new line
    ax.plot(x, net_new, color='#333333', linewidth=2.5, marker='o', label='Net New MRR')
    ax.axhline(0, color='black', linewidth=1, linestyle='--')
    
    ax.set_title('Monthly MRR Movements: New, Expansion, Contraction & Churn (2023–2025)', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('MRR Movement (USD)', fontsize=12)
    ax.set_xticks(x[::2])
    ax.set_xticklabels(months[::2], rotation=45, ha='right')
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax.legend(loc='upper left', frameon=True)
    
    caption_text = "Synthetic data modelled on Stripe-style subscription billing. Not real customer data."
    fig.text(0.5, 0.01, caption_text, ha='center', fontsize=10, style='italic', color='#555555')
    
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig('output/mrr_movements_stacked.png', dpi=300)
    plt.close()
    
    # Chart 2: Cohort Retention Heatmap
    fig, ax = plt.subplots(figsize=(14, 8))
    m_cols = [f"M{i:02d}" for i in range(13)]  # First 12 months for readable heatmap
    cohort_matrix = df_cohort_logo.set_index('cohort_month')[m_cols].dropna(how='all')
    
    cax = ax.matshow(cohort_matrix, cmap='YlGnBu', aspect='auto', vmin=0, vmax=100)
    fig.colorbar(cax, ax=ax, label='% Logo Retention')
    
    ax.set_xticks(range(len(m_cols)))
    ax.set_xticklabels([f"Month {i}" for i in range(13)], rotation=30, ha='left')
    ax.set_yticks(range(len(cohort_matrix)))
    ax.set_yticklabels(cohort_matrix.index)
    
    # Annotate values
    for i in range(len(cohort_matrix)):
        for j in range(len(m_cols)):
            val = cohort_matrix.iloc[i, j]
            if not np.isnan(val):
                text_color = 'white' if val > 65 else 'black'
                ax.text(j, i, f"{val:.0f}%", ha='center', va='center', color=text_color, fontsize=8)
                
    ax.set_title('Customer Cohort Logo Retention Heatmap (% Active over Months Since Signup)', fontsize=14, fontweight='bold', pad=20)
    fig.text(0.5, 0.01, caption_text, ha='center', fontsize=10, style='italic', color='#555555')
    
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig('output/cohort_retention_heatmap.png', dpi=300)
    plt.close()
    
    # Chart 3: Churn by Plan and LTV
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    plans = df_churn_plan['plan']
    churn_rates = df_churn_plan['monthly_churn_rate'] * 100
    
    colors = ['#ff9999', '#66b3ff', '#99ff99']
    bars = ax1.bar(plans, churn_rates, color=colors, edgecolor='black', linewidth=1)
    ax1.set_title('Monthly Logo Churn Rate by Plan Tier', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Monthly Churn Rate (%)', fontsize=11)
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., h + 0.1, f"{h:.2f}%", ha='center', va='bottom', fontweight='bold')
        
    # LTV
    ltv_vals = [float(v) if v != 'not estimable' else 0 for v in df_ltv['ltv_estimate']]
    bars2 = ax2.bar(plans, ltv_vals, color=['#e6550d', '#3182bd', '#31a354'], edgecolor='black', linewidth=1)
    ax2.set_title('Estimated Customer Lifetime Value (LTV) @ 80% Margin', fontsize=13, fontweight='bold')
    ax2.set_ylabel('Estimated LTV (USD)', fontsize=11)
    ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., h + 20, f"${h:,.0f}", ha='center', va='bottom', fontweight='bold')
        
    fig.text(0.5, 0.01, caption_text, ha='center', fontsize=10, style='italic', color='#555555')
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig('output/churn_by_plan.png', dpi=300)
    plt.close()

def main():
    print("=" * 70)
    print("Computing Subscription Revenue Metrics (MRR, Churn, Cohorts, LTV)...")
    print("=" * 70)
    
    df_customers, df_subscriptions, df_invoices = load_data()
    
    df_mrr_monthly, df_mrr_movements, df_churn_monthly, df_plan_mix = compute_monthly_mrr_and_movements(df_customers, df_subscriptions)
    df_cohort_logo, df_cohort_rev = compute_cohort_retention(df_customers, df_subscriptions)
    df_churn_plan, df_ltv = compute_plan_churn_and_ltv(df_subscriptions, gross_margin=0.80)
    df_churn_channel, df_churn_tenure, df_churn_reasons = compute_segment_churn(df_customers, df_subscriptions)
    
    os.makedirs('output', exist_ok=True)
    df_mrr_monthly.to_csv('output/mrr_monthly.csv', index=False)
    df_mrr_movements.to_csv('output/mrr_movements.csv', index=False)
    df_churn_monthly.to_csv('output/churn_monthly.csv', index=False)
    df_cohort_logo.to_csv('output/retention_cohorts_logo.csv', index=False)
    df_cohort_rev.to_csv('output/retention_cohorts_revenue.csv', index=False)
    df_ltv.to_csv('output/ltv_by_plan.csv', index=False)
    df_churn_plan.to_csv('output/churn_by_plan.csv', index=False)
    df_churn_channel.to_csv('output/churn_by_channel.csv', index=False)
    df_churn_tenure.to_csv('output/churn_by_tenure.csv', index=False)
    df_churn_reasons.to_csv('output/churn_reasons.csv', index=False)
    df_plan_mix.to_csv('output/plan_mix_monthly.csv', index=False)
    
    print("Exported 11 metric CSV files to output/ directory.")
    
    # Generate Charts
    generate_charts(df_mrr_movements, df_cohort_logo, df_churn_plan, df_ltv)
    print("Generated 3 visualization PNGs in output/ directory.")
    
    # Print key summary metrics
    latest_mrr = df_mrr_monthly.iloc[-1]
    print(f"\nClosing Performance (Dec 2025):")
    print(f"  - Closing MRR: ${latest_mrr['mrr']:,.2f}")
    print(f"  - Active Customers: {latest_mrr['active_customers']:,}")
    print(f"  - ARPA: ${latest_mrr['arpa']:,.2f}")
    
    fail_reconcile = (df_mrr_movements['reconciliation_check'] == 'FAIL').sum()
    print(f"\nMRR Movements Reconciliation: {fail_reconcile} failures out of {len(df_mrr_movements)} months.")
    print("=" * 70)

if __name__ == '__main__':
    main()
