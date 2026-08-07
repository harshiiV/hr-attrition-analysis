# =============================================================
#  HR ATTRITION — SQL RUNNER
#  Loads CSV into SQLite and executes all analysis queries
# =============================================================

import sqlite3
import pandas as pd
import os

DB_PATH  = '../data/hr_attrition.db'
CSV_PATH = '../data/ibm_hr.csv'
SQL_PATH = 'hr_attrition_queries.sql'


def load_data():
    """Load CSV into SQLite database."""
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found.")
        print("Download from: https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset")
        return None

    df = pd.read_csv(CSV_PATH)
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('employees', conn, if_exists='replace', index=False)
    print(f"Loaded {len(df)} rows into '{DB_PATH}' → table 'employees'")
    return conn


def run_queries(conn):
    """Run all named queries and print results."""
    queries = {
        "Overall Attrition Summary": """
            SELECT
                COUNT(*) AS total_employees,
                SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS employees_left,
                ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1.0 ELSE 0 END)/COUNT(*)*100,2) AS attrition_rate_pct
            FROM employees
        """,
        "Attrition by Department": """
            SELECT Department,
                COUNT(*) AS total,
                SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS left_count,
                ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1.0 ELSE 0 END)/COUNT(*)*100,2) AS attrition_rate_pct,
                ROUND(AVG(MonthlyIncome),2) AS avg_income
            FROM employees
            GROUP BY Department ORDER BY attrition_rate_pct DESC
        """,
        "Salary Comparison (Stayed vs Left)": """
            SELECT Attrition,
                COUNT(*) AS count,
                ROUND(AVG(MonthlyIncome),2) AS avg_income,
                ROUND(MIN(MonthlyIncome),2) AS min_income,
                ROUND(MAX(MonthlyIncome),2) AS max_income
            FROM employees GROUP BY Attrition
        """,
        "Overtime Impact": """
            SELECT OverTime, COUNT(*) AS total,
                SUM(CASE WHEN Attrition='Yes' THEN 1 ELSE 0 END) AS left,
                ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1.0 ELSE 0 END)/COUNT(*)*100,2) AS attrition_pct
            FROM employees GROUP BY OverTime
        """,
        "Attrition by Age Group": """
            SELECT
                CASE WHEN Age<=25 THEN '18-25' WHEN Age<=35 THEN '26-35'
                     WHEN Age<=45 THEN '36-45' WHEN Age<=55 THEN '46-55' ELSE '55+' END AS age_group,
                COUNT(*) AS total,
                ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1.0 ELSE 0 END)/COUNT(*)*100,2) AS attrition_pct
            FROM employees GROUP BY age_group ORDER BY MIN(Age)
        """,
        "Attrition by Tenure Band": """
            SELECT
                CASE WHEN YearsAtCompany<=1 THEN '0-1 yr' WHEN YearsAtCompany<=3 THEN '1-3 yrs'
                     WHEN YearsAtCompany<=7 THEN '3-7 yrs' WHEN YearsAtCompany<=15 THEN '7-15 yrs'
                     ELSE '15+ yrs' END AS tenure_band,
                COUNT(*) AS total,
                ROUND(SUM(CASE WHEN Attrition='Yes' THEN 1.0 ELSE 0 END)/COUNT(*)*100,2) AS attrition_pct,
                ROUND(AVG(MonthlyIncome),2) AS avg_income
            FROM employees GROUP BY tenure_band ORDER BY MIN(YearsAtCompany)
        """,
    }

    for title, query in queries.items():
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
        result = pd.read_sql_query(query, conn)
        print(result.to_string(index=False))


if __name__ == '__main__':
    conn = load_data()
    if conn:
        run_queries(conn)
        conn.close()
        print(f"\nDatabase saved: {DB_PATH}")
        print("Open hr_attrition_queries.sql in DB Browser for SQLite for visual exploration.")
