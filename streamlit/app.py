# =============================================================
#  HR ATTRITION — STREAMLIT WEB APP
#  Run: streamlit run app.py
#  pip install streamlit scikit-learn pandas numpy pickle5
# =============================================================

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os

# ── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title="HR Attrition Risk Predictor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center;
        border-left: 4px solid #378ADD;
    }
    .risk-high   { color: #E24B4A; font-size: 48px; font-weight: 700; }
    .risk-medium { color: #EF9F27; font-size: 48px; font-weight: 700; }
    .risk-low    { color: #639922; font-size: 48px; font-weight: 700; }
    .insight-box {
        background: #fff8e6; border-left: 4px solid #EF9F27;
        padding: 12px 16px; border-radius: 6px; margin: 8px 0;
    }
    h1 { color: #1a1a2e; }
</style>
""", unsafe_allow_html=True)


# ── LOAD MODEL ────────────────────────────────────────────────
@st.cache_resource
def load_model():
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('label_encoders.pkl', 'rb') as f:
        encoders = pickle.load(f)
    with open('feature_names.pkl', 'rb') as f:
        features = pickle.load(f)
    return model, encoders, features


# ── HEADER ────────────────────────────────────────────────────
st.title("📊 HR Attrition Risk Predictor")
st.markdown("*Predict employee attrition probability using machine learning — IBM HR Analytics Dataset*")
st.divider()


# ── SIDEBAR: EDA STATS ────────────────────────────────────────
with st.sidebar:
    st.header("📈 Dataset Insights")

    stats = {
        "Total Employees": "1,470",
        "Attrition Rate":  "16.1%",
        "Avg Monthly Income": "₹6,503",
        "Avg Age": "36.9 yrs",
        "High Risk Dept": "Sales (20.6%)",
    }
    for k, v in stats.items():
        st.metric(k, v)

    st.divider()
    st.markdown("**Key Attrition Drivers**")
    drivers = {
        "OverTime (Yes)": "30.5%",
        "Job Satisfaction ≤ 2": "25.1%",
        "Tenure < 3 yrs": "28.3%",
        "Low Salary Band": "22.4%",
    }
    for k, v in drivers.items():
        st.markdown(f"• **{k}** → {v} attrition rate")

    st.divider()
    st.caption("Model: Random Forest | AUC: ~0.87")
    st.caption("Dataset: IBM HR Analytics (Kaggle)")


# ── MAIN: INPUT FORM ─────────────────────────────────────────
st.subheader("🔍 Employee Profile")
st.markdown("Adjust the sliders and dropdowns to build an employee profile:")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Personal**")
    age              = st.slider("Age", 18, 60, 28, help="Employee age")
    gender           = st.selectbox("Gender", ["Male", "Female"])
    marital_status   = st.selectbox("Marital Status", ["Single", "Married", "Divorced"])
    education        = st.slider("Education Level (1-5)", 1, 5, 3,
                                  help="1=Below College, 2=College, 3=Bachelor, 4=Master, 5=Doctor")
    education_field  = st.selectbox("Education Field",
                                     ["Life Sciences", "Medical", "Marketing",
                                      "Technical Degree", "Human Resources", "Other"])

with col2:
    st.markdown("**Job Details**")
    department       = st.selectbox("Department",
                                     ["Sales", "Research & Development", "Human Resources"])
    job_role         = st.selectbox("Job Role",
                                     ["Sales Executive", "Research Scientist", "Laboratory Technician",
                                      "Manufacturing Director", "Healthcare Representative",
                                      "Manager", "Sales Representative", "Research Director",
                                      "Human Resources"])
    job_level        = st.slider("Job Level (1-5)", 1, 5, 2)
    years_company    = st.slider("Years at Company", 0, 40, 2)
    years_role       = st.slider("Years in Current Role", 0, 18, 1)
    years_manager    = st.slider("Years with Current Manager", 0, 17, 1)

with col3:
    st.markdown("**Compensation & Satisfaction**")
    monthly_income   = st.slider("Monthly Income (₹)", 1000, 20000, 3500, step=100)
    pct_salary_hike  = st.slider("Salary Hike % (last year)", 11, 25, 14)
    overtime         = st.selectbox("Overtime", ["Yes", "No"])
    job_satisfaction = st.slider("Job Satisfaction (1-4)", 1, 4, 2,
                                  help="1=Low, 2=Medium, 3=High, 4=Very High")
    work_life_bal    = st.slider("Work-Life Balance (1-4)", 1, 4, 3)
    env_satisfaction = st.slider("Environment Satisfaction (1-4)", 1, 4, 2)
    job_involvement  = st.slider("Job Involvement (1-4)", 1, 4, 2)
    perf_rating      = st.slider("Performance Rating (3-4)", 3, 4, 3)
    business_travel  = st.selectbox("Business Travel",
                                     ["Travel_Rarely", "Travel_Frequently", "Non-Travel"])
    distance_home    = st.slider("Distance from Home (km)", 1, 30, 10)
    num_companies    = st.slider("Num Companies Worked", 0, 9, 2)
    stock_option     = st.slider("Stock Option Level (0-3)", 0, 3, 0)
    training_times   = st.slider("Training Times Last Year", 0, 6, 2)
    relationship_sat = st.slider("Relationship Satisfaction (1-4)", 1, 4, 2)
    years_promoted   = st.slider("Years Since Last Promotion", 0, 15, 1)


# ── PREDICT ──────────────────────────────────────────────────
st.divider()
predict_btn = st.button("🔮  Predict Attrition Risk", type="primary", use_container_width=True)

if predict_btn:
    try:
        model, encoders, feature_names = load_model()

        # Build input dict matching training features
        input_dict = {
            'Age':                      age,
            'BusinessTravel':           business_travel,
            'DailyRate':                int(monthly_income * 0.05),
            'Department':               department,
            'DistanceFromHome':         distance_home,
            'Education':                education,
            'EducationField':           education_field,
            'EnvironmentSatisfaction':  env_satisfaction,
            'Gender':                   gender,
            'HourlyRate':               int(monthly_income / 160),
            'JobInvolvement':           job_involvement,
            'JobLevel':                 job_level,
            'JobRole':                  job_role,
            'JobSatisfaction':          job_satisfaction,
            'MaritalStatus':            marital_status,
            'MonthlyIncome':            monthly_income,
            'MonthlyRate':              int(monthly_income * 1.2),
            'NumCompaniesWorked':       num_companies,
            'OverTime':                 overtime,
            'PercentSalaryHike':        pct_salary_hike,
            'PerformanceRating':        perf_rating,
            'RelationshipSatisfaction': relationship_sat,
            'StockOptionLevel':         stock_option,
            'TotalWorkingYears':        years_company + num_companies * 2,
            'TrainingTimesLastYear':    training_times,
            'WorkLifeBalance':          work_life_bal,
            'YearsAtCompany':           years_company,
            'YearsInCurrentRole':       years_role,
            'YearsSinceLastPromotion':  years_promoted,
            'YearsWithCurrManager':     years_manager,
        }

        # Encode categoricals
        for col, le in encoders.items():
            if col in input_dict:
                try:
                    input_dict[col] = le.transform([input_dict[col]])[0]
                except ValueError:
                    input_dict[col] = 0

        # Build feature vector in correct order
        row = [input_dict.get(f, 0) for f in feature_names]
        X_input = np.array(row).reshape(1, -1)

        prob = model.predict_proba(X_input)[0][1]
        pct  = int(prob * 100)

        # ── RESULTS ───────────────────────────────────────────
        st.subheader("📊 Prediction Result")
        r1, r2, r3 = st.columns([1, 2, 2])

        with r1:
            if pct >= 55:
                css_class = "risk-high"
                label = "🔴 HIGH RISK"
            elif pct >= 30:
                css_class = "risk-medium"
                label = "🟡 MEDIUM RISK"
            else:
                css_class = "risk-low"
                label = "🟢 LOW RISK"

            st.markdown(f'<div class="{css_class}">{pct}%</div>', unsafe_allow_html=True)
            st.markdown(f"**{label}**")
            st.caption("Attrition probability")

        with r2:
            st.markdown("**Risk Meter**")
            st.progress(pct / 100)
            st.caption(f"Probability of leaving: {pct}%")

            if pct >= 55:
                st.error("⚠️ Immediate action recommended. Review compensation, workload, and career growth opportunities.")
            elif pct >= 30:
                st.warning("⚡ Monitor this employee. Schedule a 1-on-1 to discuss satisfaction and career goals.")
            else:
                st.success("✅ Low flight risk. Continue regular engagement and recognition.")

        with r3:
            st.markdown("**Top Risk Factors for this Profile**")
            risk_factors = []
            if overtime == "Yes":
                risk_factors.append(("Overtime work", "high"))
            if job_satisfaction <= 2:
                risk_factors.append(("Low job satisfaction", "high"))
            if monthly_income < 3000:
                risk_factors.append(("Below-average salary", "high"))
            if years_company <= 2:
                risk_factors.append(("Early tenure (< 2 yrs)", "medium"))
            if work_life_bal <= 2:
                risk_factors.append(("Poor work-life balance", "medium"))
            if marital_status == "Single":
                risk_factors.append(("Single marital status", "low"))
            if distance_home > 20:
                risk_factors.append(("Long commute distance", "low"))
            if num_companies >= 4:
                risk_factors.append(("Frequent job-hopper", "medium"))

            if risk_factors:
                for factor, level in risk_factors[:5]:
                    icon = "🔴" if level == "high" else "🟡" if level == "medium" else "🔵"
                    st.markdown(f"{icon} {factor}")
            else:
                st.markdown("No major risk factors detected for this profile.")

    except FileNotFoundError:
        st.warning("""
        **Model files not found.**

        Run `notebooks/02_ml_model.py` first to train and save the model.
        The following files will be generated in the `streamlit/` folder:
        - `model.pkl`
        - `label_encoders.pkl`
        - `feature_names.pkl`
        """)
        # Demo mode
        import random
        demo_pct = random.randint(30, 80)
        st.info(f"**Demo mode:** Estimated risk = {demo_pct}% (run model training for real predictions)")


# ── FOOTER ────────────────────────────────────────────────────
st.divider()
st.caption("IBM HR Analytics Dataset | B.Tech Final Year Data Analytics Project | Built with Python, Scikit-learn & Streamlit")
