import pandas as pd
import json

df_mrr = pd.read_csv('output/mrr_monthly.csv')
df_mov = pd.read_csv('output/mrr_movements.csv')
df_churn = pd.read_csv('output/churn_monthly.csv')
df_c_logo = pd.read_csv('output/retention_cohorts_logo.csv')
df_c_rev = pd.read_csv('output/retention_cohorts_revenue.csv')
df_ltv = pd.read_csv('output/ltv_by_plan.csv')
df_cp = pd.read_csv('output/churn_by_plan.csv')
df_ch = pd.read_csv('output/churn_by_channel.csv')
df_tb = pd.read_csv('output/churn_by_tenure.csv')
df_cr = pd.read_csv('output/churn_reasons.csv')

print('--- Q1: MRR Growth & Inflow ---')
mrr_start = df_mrr.iloc[0]['mrr']
mrr_end = df_mrr.iloc[-1]['mrr']
tot_new = df_mov['new_mrr'].sum()
tot_exp = df_mov['expansion_mrr'].sum()
growth_pct = (mrr_end - mrr_start) / mrr_start * 100
print(f"Start MRR (Jan 23): ${mrr_start:,.2f}, End MRR (Dec 25): ${mrr_end:,.2f}, Growth: {growth_pct:.1f}%")
print(f"Total New MRR: ${tot_new:,.2f} ({tot_new/(tot_new+tot_exp)*100:.1f}%), Total Exp MRR: ${tot_exp:,.2f} ({tot_exp/(tot_new+tot_exp)*100:.1f}%)")

print('\n--- Q2: Churn Over Time ---')
c_early = df_churn.iloc[1:13]['logo_churn_rate'].mean() * 100
c_mid = df_churn.iloc[13:25]['logo_churn_rate'].mean() * 100
c_late = df_churn.iloc[25:]['logo_churn_rate'].mean() * 100
print(f"2023 Avg Churn: {c_early:.2f}%, 2024 Avg Churn: {c_mid:.2f}%, 2025 Avg Churn: {c_late:.2f}%")

print('\n--- Q3: Plan Churn & LTV ---')
print(df_cp)
print(df_ltv)

print('\n--- Q4: Channel Retention ---')
print(df_ch)

print('\n--- Q5: Tenure Band ---')
print(df_tb)

print('\n--- Q6: Involuntary Churn ---')
print(df_cr)

print('\n--- Q7: NRR & GRR ---')
avg_nrr = df_churn.iloc[1:]['nrr'].mean() * 100
avg_grr = df_churn.iloc[1:]['grr'].mean() * 100
latest_nrr = df_churn.iloc[-1]['nrr'] * 100
latest_grr = df_churn.iloc[-1]['grr'] * 100
print(f"Avg NRR: {avg_nrr:.2f}%, Latest NRR: {latest_nrr:.2f}%, Avg GRR: {avg_grr:.2f}%, Latest GRR: {latest_grr:.2f}%")

print('\n--- Q8: Cohort Retention (M12) ---')
df_m12 = df_c_logo[['cohort_month', 'cohort_size', 'M12']].dropna()
best_c = df_m12.loc[df_m12['M12'].idxmax()]
worst_c = df_m12.loc[df_m12['M12'].idxmin()]
print(f"Best M12 cohort: {best_c['cohort_month']} with {best_c['M12']}% (size {int(best_c['cohort_size'])})")
print(f"Worst M12 cohort: {worst_c['cohort_month']} with {worst_c['M12']}% (size {int(worst_c['cohort_size'])})")
