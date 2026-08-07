# =============================================================
#  HR ATTRITION ANALYSIS — EDA + STATISTICAL ANALYSIS
#  Dataset: IBM HR Analytics (Kaggle)
#  Author: Your Name | B.Tech Final Year Project
# =============================================================

# ── INSTALL (run once) ────────────────────────────────────────
# pip install pandas numpy matplotlib seaborn scipy scikit-learn

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from scipy import stats
from scipy.stats import chi2_contingency
import warnings
warnings.filterwarnings('ignore')

# ── PLOT STYLE ────────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor':   '#F9F9F9',
    'axes.spines.top':  False,
    'axes.spines.right':False,
    'font.family':      'DejaVu Sans',
    'axes.titlesize':   13,
    'axes.titleweight': 'bold',
})
PALETTE = {'Yes': '#E24B4A', 'No': '#378ADD'}

# =============================================================
# SECTION 1 — LOAD & INSPECT DATA
# =============================================================
# Download from: https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset
# Save as: data/ibm_hr.csv

df = pd.read_csv('../data/ibm_hr.csv')

print("=" * 55)
print("DATASET OVERVIEW")
print("=" * 55)
print(f"Shape          : {df.shape[0]} rows × {df.shape[1]} columns")
print(f"Missing values : {df.isnull().sum().sum()}")
print(f"Duplicates     : {df.duplicated().sum()}")
print(f"\nAttrition breakdown:")
print(df['Attrition'].value_counts())
print(f"\nAttrition Rate : {df['Attrition'].eq('Yes').mean()*100:.1f}%")
print("\nColumn types:")
print(df.dtypes.value_counts())


# =============================================================
# SECTION 2 — DATA CLEANING & FEATURE ENGINEERING
# =============================================================

# Encode target
df['AttritionBinary'] = (df['Attrition'] == 'Yes').astype(int)

# Drop columns with zero variance (all same value)
zero_var_cols = [c for c in df.columns if df[c].nunique() == 1]
print(f"\nDropping zero-variance columns: {zero_var_cols}")
df.drop(columns=zero_var_cols, inplace=True)

# Create useful derived features
df['SalaryBand'] = pd.cut(
    df['MonthlyIncome'],
    bins=[0, 2000, 4000, 6000, 10000, 20000],
    labels=['<2K', '2-4K', '4-6K', '6-10K', '10K+']
)

df['TenureBand'] = pd.cut(
    df['YearsAtCompany'],
    bins=[-1, 1, 3, 7, 15, 100],
    labels=['0-1 yr', '1-3 yrs', '3-7 yrs', '7-15 yrs', '15+ yrs']
)

df['AgeBand'] = pd.cut(
    df['Age'],
    bins=[17, 25, 35, 45, 55, 100],
    labels=['18-25', '26-35', '36-45', '46-55', '55+']
)

# Encode overtime for numeric analysis
df['OvertimeBinary'] = (df['OverTime'] == 'Yes').astype(int)

print("\nFeature engineering complete.")
print(df[['SalaryBand','TenureBand','AgeBand']].head(3))


# =============================================================
# SECTION 3 — UNIVARIATE EDA
# =============================================================

fig, axes = plt.subplots(2, 3, figsize=(16, 9))
fig.suptitle('Univariate Distribution of Key Features', fontsize=16, fontweight='bold', y=1.01)

num_cols = ['Age', 'MonthlyIncome', 'YearsAtCompany',
            'JobSatisfaction', 'WorkLifeBalance', 'DistanceFromHome']

for ax, col in zip(axes.flat, num_cols):
    stayed = df[df['Attrition'] == 'No'][col]
    left   = df[df['Attrition'] == 'Yes'][col]
    ax.hist(stayed, bins=20, alpha=0.6, color='#378ADD', label='Stayed', density=True)
    ax.hist(left,   bins=20, alpha=0.6, color='#E24B4A', label='Left',   density=True)
    ax.set_title(col)
    ax.set_ylabel('Density')
    ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig('../outputs/01_univariate_distributions.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: 01_univariate_distributions.png")


# =============================================================
# SECTION 4 — ATTRITION RATE BY CATEGORICAL FEATURES
# =============================================================

cat_features = ['Department', 'JobRole', 'OverTime', 'BusinessTravel',
                'MaritalStatus', 'EducationField', 'Gender']

fig, axes = plt.subplots(3, 3, figsize=(18, 14))
fig.suptitle('Attrition Rate by Categorical Features', fontsize=16, fontweight='bold')

for ax, feat in zip(axes.flat, cat_features):
    rates = (df.groupby(feat)['AttritionBinary'].mean() * 100).sort_values(ascending=True)
    colors = ['#E24B4A' if v > 20 else '#EF9F27' if v > 15 else '#378ADD' for v in rates]
    bars = ax.barh(rates.index, rates.values, color=colors, edgecolor='none')
    ax.set_xlabel('Attrition Rate (%)')
    ax.set_title(feat)
    for bar, val in zip(bars, rates.values):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}%', va='center', fontsize=9)
    ax.set_xlim(0, rates.max() + 8)

for ax in axes.flat[len(cat_features):]:
    ax.set_visible(False)

plt.tight_layout()
plt.savefig('../outputs/02_attrition_by_category.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: 02_attrition_by_category.png")


# =============================================================
# SECTION 5 — STATISTICAL HYPOTHESIS TESTING
# =============================================================

print("\n" + "=" * 55)
print("STATISTICAL HYPOTHESIS TESTS")
print("=" * 55)

# ── Chi-Square Tests (categorical vs attrition) ───────────────
cat_test_cols = ['Department', 'OverTime', 'BusinessTravel', 'MaritalStatus', 'JobRole']
print("\nChi-Square Test — Categorical Features vs Attrition")
print(f"{'Feature':<20} {'Chi2':>8} {'p-value':>10} {'Significant?':>14}")
print("-" * 56)

for col in cat_test_cols:
    ct = pd.crosstab(df[col], df['Attrition'])
    chi2, p, dof, expected = chi2_contingency(ct)
    sig = "YES ✓" if p < 0.05 else "no"
    print(f"{col:<20} {chi2:>8.2f} {p:>10.4f} {sig:>14}")

# ── T-Tests (numeric vs attrition) ───────────────────────────
num_test_cols = ['MonthlyIncome', 'Age', 'YearsAtCompany',
                 'JobSatisfaction', 'WorkLifeBalance', 'DistanceFromHome']
print("\nIndependent T-Test — Numeric Features vs Attrition")
print(f"{'Feature':<25} {'Mean(Stayed)':>13} {'Mean(Left)':>11} {'p-value':>10} {'Significant?':>14}")
print("-" * 77)

stayed = df[df['Attrition'] == 'No']
left   = df[df['Attrition'] == 'Yes']

for col in num_test_cols:
    t, p = stats.ttest_ind(stayed[col], left[col])
    sig = "YES ✓" if p < 0.05 else "no"
    print(f"{col:<25} {stayed[col].mean():>13.2f} {left[col].mean():>11.2f} {p:>10.4f} {sig:>14}")


# =============================================================
# SECTION 6 — CORRELATION HEATMAP
# =============================================================

numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
corr = df[numeric_cols].corr()['AttritionBinary'].drop('AttritionBinary').sort_values()

fig, ax = plt.subplots(figsize=(10, 8))
colors = ['#E24B4A' if v > 0 else '#378ADD' for v in corr]
bars = ax.barh(corr.index, corr.values, color=colors, edgecolor='none')
ax.axvline(0, color='gray', linewidth=0.8, linestyle='--')
ax.set_title('Feature Correlation with Attrition', fontsize=14, fontweight='bold')
ax.set_xlabel('Pearson Correlation Coefficient')
for bar, val in zip(bars, corr.values):
    x = bar.get_width() + (0.002 if val >= 0 else -0.002)
    ha = 'left' if val >= 0 else 'right'
    ax.text(x, bar.get_y() + bar.get_height()/2, f'{val:.3f}', va='center', fontsize=8, ha=ha)

plt.tight_layout()
plt.savefig('../outputs/03_correlation_with_attrition.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: 03_correlation_with_attrition.png")


# =============================================================
# SECTION 7 — SALARY & TENURE DEEP DIVE
# =============================================================

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Salary by department, split by attrition
dept_salary = df.groupby(['Department', 'Attrition'])['MonthlyIncome'].mean().unstack()
dept_salary.plot(kind='bar', ax=axes[0], color=['#378ADD', '#E24B4A'],
                 edgecolor='none', width=0.6)
axes[0].set_title('Avg Monthly Income by Department & Attrition')
axes[0].set_xlabel('')
axes[0].set_ylabel('Monthly Income (₹)')
axes[0].legend(['Stayed', 'Left'])
axes[0].tick_params(axis='x', rotation=15)
axes[0].yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'₹{x:,.0f}'))

# Attrition rate by tenure band
tenure_rate = df.groupby('TenureBand')['AttritionBinary'].mean() * 100
axes[1].bar(tenure_rate.index, tenure_rate.values,
            color=['#E24B4A' if v > 20 else '#EF9F27' if v > 12 else '#378ADD' for v in tenure_rate],
            edgecolor='none')
axes[1].set_title('Attrition Rate by Tenure Band')
axes[1].set_ylabel('Attrition Rate (%)')
axes[1].set_xlabel('Years at Company')
for i, v in enumerate(tenure_rate.values):
    axes[1].text(i, v + 0.5, f'{v:.1f}%', ha='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('../outputs/04_salary_tenure_analysis.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: 04_salary_tenure_analysis.png")


# =============================================================
# SECTION 8 — OVERTIME × SATISFACTION INTERACTION
# =============================================================

pivot = df.pivot_table(
    values='AttritionBinary',
    index='JobSatisfaction',
    columns='OverTime',
    aggfunc='mean'
) * 100

fig, ax = plt.subplots(figsize=(8, 5))
pivot.plot(kind='bar', ax=ax, color=['#378ADD', '#E24B4A'], edgecolor='none', width=0.6)
ax.set_title('Attrition Rate: Job Satisfaction × Overtime', fontsize=13, fontweight='bold')
ax.set_xlabel('Job Satisfaction (1=Low → 4=High)')
ax.set_ylabel('Attrition Rate (%)')
ax.legend(['No Overtime', 'Overtime'])
ax.tick_params(axis='x', rotation=0)

plt.tight_layout()
plt.savefig('../outputs/05_overtime_satisfaction.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: 05_overtime_satisfaction.png")


# =============================================================
# SECTION 9 — KEY INSIGHTS SUMMARY
# =============================================================

print("\n" + "=" * 55)
print("KEY INSIGHTS SUMMARY")
print("=" * 55)

total = len(df)
att_rate = df['AttritionBinary'].mean() * 100
ot_yes = df[df['OverTime']=='Yes']['AttritionBinary'].mean()*100
ot_no  = df[df['OverTime']=='No']['AttritionBinary'].mean()*100
dept_rates = df.groupby('Department')['AttritionBinary'].mean()*100
early_att = df[df['YearsAtCompany'] <= 3]['AttritionBinary'].mean()*100
income_stayed = stayed['MonthlyIncome'].mean()
income_left   = left['MonthlyIncome'].mean()

print(f"\n1. Overall attrition rate     : {att_rate:.1f}%")
print(f"2. Overtime attrition rate    : {ot_yes:.1f}% vs {ot_no:.1f}% (no OT) — {ot_yes/ot_no:.1f}x higher")
print(f"3. Early tenure attrition     : {early_att:.1f}% in first 3 years")
print(f"4. Salary gap (stayed vs left): ₹{income_stayed:,.0f} vs ₹{income_left:,.0f} (₹{income_stayed-income_left:,.0f} diff)")
print(f"5. Attrition by department:")
for dept, rate in dept_rates.sort_values(ascending=False).items():
    print(f"   {dept:<30}: {rate:.1f}%")

print("\nAll plots saved to outputs/ folder.")
print("Next: Run 02_ml_model.py for the prediction model.")
