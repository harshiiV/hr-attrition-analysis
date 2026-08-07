# =============================================================
#  HR ATTRITION — ML MODEL TRAINING & EVALUATION
#  Models: Logistic Regression, Random Forest, XGBoost
#  Author: Your Name | B.Tech Final Year Project
# =============================================================

# pip install scikit-learn xgboost imbalanced-learn matplotlib seaborn

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pickle
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, roc_curve, ConfusionMatrixDisplay
)
from sklearn.pipeline import Pipeline
from sklearn.inspection import permutation_importance
from imblearn.over_sampling import SMOTE

plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor':   '#F9F9F9',
    'axes.spines.top':  False,
    'axes.spines.right':False,
})


# =============================================================
# STEP 1 — LOAD & PREPROCESS
# =============================================================

df = pd.read_csv('../data/ibm_hr.csv')

# Encode target
df['AttritionBinary'] = (df['Attrition'] == 'Yes').astype(int)

# Drop useless / leaky cols
DROP_COLS = ['Attrition', 'EmployeeNumber', 'EmployeeCount',
             'StandardHours', 'Over18']
df.drop(columns=[c for c in DROP_COLS if c in df.columns], inplace=True)

# Encode all categoricals
label_encoders = {}
cat_cols = df.select_dtypes(include='object').columns.tolist()

for col in cat_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    label_encoders[col] = le

print(f"Encoded {len(cat_cols)} categorical columns: {cat_cols}")
print(f"Final feature matrix: {df.shape}")

# Split features / target
X = df.drop('AttritionBinary', axis=1)
y = df['AttritionBinary']

print(f"\nClass distribution: {y.value_counts().to_dict()}")
print(f"Attrition rate: {y.mean()*100:.1f}%")


# =============================================================
# STEP 2 — TRAIN / TEST SPLIT + SMOTE BALANCING
# =============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# SMOTE to handle class imbalance
smote = SMOTE(random_state=42)
X_train_bal, y_train_bal = smote.fit_resample(X_train, y_train)

print(f"\nAfter SMOTE — Train: {X_train_bal.shape[0]} samples")
print(f"Class balance: {pd.Series(y_train_bal).value_counts().to_dict()}")


# =============================================================
# STEP 3 — TRAIN 3 MODELS
# =============================================================

models = {
    'Logistic Regression': Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000, random_state=42, C=0.5))
    ]),
    'Random Forest': RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_leaf=5,
        class_weight='balanced', random_state=42
    ),
    'Gradient Boosting': GradientBoostingClassifier(
        n_estimators=150, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=42
    )
}

results = {}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print("\n" + "=" * 60)
print("MODEL TRAINING & CROSS-VALIDATION")
print("=" * 60)

for name, model in models.items():
    model.fit(X_train_bal, y_train_bal)
    cv_scores = cross_val_score(model, X_train_bal, y_train_bal,
                                cv=cv, scoring='roc_auc')
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    auc     = roc_auc_score(y_test, y_proba)

    results[name] = {
        'model':    model,
        'cv_mean':  cv_scores.mean(),
        'cv_std':   cv_scores.std(),
        'test_auc': auc,
        'y_pred':   y_pred,
        'y_proba':  y_proba,
    }

    print(f"\n{name}")
    print(f"  CV AUC   : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"  Test AUC : {auc:.4f}")
    print(classification_report(y_test, y_pred, target_names=['Stayed','Left'], indent=4))


# =============================================================
# STEP 4 — PICK BEST MODEL
# =============================================================

best_name = max(results, key=lambda k: results[k]['test_auc'])
best      = results[best_name]
print(f"\nBest model: {best_name} (AUC = {best['test_auc']:.4f})")


# =============================================================
# STEP 5 — VISUALISATIONS
# =============================================================

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle('Model Evaluation', fontsize=15, fontweight='bold')

# ── ROC Curves ────────────────────────────────────────────────
colors = ['#378ADD', '#E24B4A', '#639922']
for (name, res), color in zip(results.items(), colors):
    fpr, tpr, _ = roc_curve(y_test, res['y_proba'])
    axes[0].plot(fpr, tpr, label=f"{name} (AUC={res['test_auc']:.3f})", color=color, linewidth=2)
axes[0].plot([0,1],[0,1],'k--', linewidth=1, alpha=0.4)
axes[0].set_xlabel('False Positive Rate')
axes[0].set_ylabel('True Positive Rate')
axes[0].set_title('ROC Curves — All Models')
axes[0].legend(fontsize=9)

# ── Confusion Matrix (best model) ─────────────────────────────
cm = confusion_matrix(y_test, best['y_pred'])
disp = ConfusionMatrixDisplay(cm, display_labels=['Stayed','Left'])
disp.plot(ax=axes[1], colorbar=False, cmap='Blues')
axes[1].set_title(f'Confusion Matrix — {best_name}')

# ── CV Score Comparison ───────────────────────────────────────
names  = list(results.keys())
means  = [results[n]['cv_mean'] for n in names]
stds   = [results[n]['cv_std']  for n in names]
bar_colors = ['#378ADD','#E24B4A','#639922']
axes[2].barh(names, means, xerr=stds, color=bar_colors, edgecolor='none', capsize=5)
axes[2].set_xlabel('Cross-Validation AUC')
axes[2].set_title('CV AUC Comparison')
axes[2].set_xlim(0.5, 1.0)
for i, (m, s) in enumerate(zip(means, stds)):
    axes[2].text(m + s + 0.005, i, f'{m:.3f}', va='center', fontsize=10)

plt.tight_layout()
plt.savefig('../outputs/06_model_evaluation.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: 06_model_evaluation.png")


# =============================================================
# STEP 6 — FEATURE IMPORTANCE
# =============================================================

# Use Random Forest for feature importance
rf_model = results['Random Forest']['model']
importances = rf_model.feature_importances_
feat_imp = pd.DataFrame({
    'feature': X.columns,
    'importance': importances
}).sort_values('importance', ascending=True).tail(15)

fig, ax = plt.subplots(figsize=(10, 7))
colors = ['#E24B4A' if v > 0.05 else '#378ADD' for v in feat_imp['importance']]
ax.barh(feat_imp['feature'], feat_imp['importance'], color=colors, edgecolor='none')
ax.set_title('Top 15 Feature Importances — Random Forest', fontsize=13, fontweight='bold')
ax.set_xlabel('Importance Score')

high_patch = mpatches.Patch(color='#E24B4A', label='High importance (>5%)')
low_patch  = mpatches.Patch(color='#378ADD', label='Moderate importance')
ax.legend(handles=[high_patch, low_patch], fontsize=9)

plt.tight_layout()
plt.savefig('../outputs/07_feature_importance.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: 07_feature_importance.png")

print("\nTop 10 features:")
print(feat_imp.tail(10)[['feature','importance']].sort_values('importance', ascending=False).to_string(index=False))


# =============================================================
# STEP 7 — SAVE MODEL & ENCODERS
# =============================================================

best_model = results[best_name]['model']
feature_names = list(X.columns)

with open('../streamlit/model.pkl', 'wb') as f:
    pickle.dump(best_model, f)

with open('../streamlit/label_encoders.pkl', 'wb') as f:
    pickle.dump(label_encoders, f)

with open('../streamlit/feature_names.pkl', 'wb') as f:
    pickle.dump(feature_names, f)

print(f"\nModel saved: streamlit/model.pkl")
print(f"Encoders saved: streamlit/label_encoders.pkl")
print(f"Best model: {best_name} | Test AUC: {best['test_auc']:.4f}")
print("\nNext: Run streamlit/app.py to launch the predictor!")
