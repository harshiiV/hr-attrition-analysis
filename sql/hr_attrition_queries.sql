-- =============================================================
--  HR ATTRITION ANALYSIS — SQL QUERIES
--  Database: SQLite / MySQL / PostgreSQL compatible
--  Table: employees  (load ibm_hr.csv using Python or DB tool)
-- =============================================================

-- ── HOW TO LOAD DATA (Python snippet) ────────────────────────
-- import sqlite3, pandas as pd
-- df = pd.read_csv('data/ibm_hr.csv')
-- conn = sqlite3.connect('hr_attrition.db')
-- df.to_sql('employees', conn, if_exists='replace', index=False)


-- =============================================================
-- QUERY 1: Overall attrition summary
-- =============================================================
SELECT
    COUNT(*)                                              AS total_employees,
    SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)   AS employees_left,
    SUM(CASE WHEN Attrition = 'No'  THEN 1 ELSE 0 END)   AS employees_stayed,
    ROUND(
        SUM(CASE WHEN Attrition = 'Yes' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2
    )                                                     AS attrition_rate_pct
FROM employees;


-- =============================================================
-- QUERY 2: Attrition rate by department (ranked)
-- =============================================================
SELECT
    Department,
    COUNT(*)                                                       AS total,
    SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)            AS left_count,
    ROUND(
        SUM(CASE WHEN Attrition = 'Yes' THEN 1.0 ELSE 0 END)
        / COUNT(*) * 100, 2
    )                                                              AS attrition_rate_pct,
    ROUND(AVG(MonthlyIncome), 2)                                   AS avg_monthly_income
FROM employees
GROUP BY Department
ORDER BY attrition_rate_pct DESC;


-- =============================================================
-- QUERY 3: Salary comparison — employees who left vs stayed
-- =============================================================
SELECT
    Attrition,
    COUNT(*)                              AS employee_count,
    ROUND(AVG(MonthlyIncome), 2)          AS avg_monthly_income,
    ROUND(MIN(MonthlyIncome), 2)          AS min_income,
    ROUND(MAX(MonthlyIncome), 2)          AS max_income,
    ROUND(AVG(PercentSalaryHike), 2)      AS avg_salary_hike_pct
FROM employees
GROUP BY Attrition
ORDER BY Attrition DESC;


-- =============================================================
-- QUERY 4: Overtime impact on attrition
-- =============================================================
SELECT
    OverTime,
    COUNT(*)                                                        AS total,
    SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)             AS left_count,
    ROUND(
        SUM(CASE WHEN Attrition = 'Yes' THEN 1.0 ELSE 0 END)
        / COUNT(*) * 100, 2
    )                                                               AS attrition_rate_pct
FROM employees
GROUP BY OverTime
ORDER BY attrition_rate_pct DESC;


-- =============================================================
-- QUERY 5: Top 10 job roles with highest attrition
-- =============================================================
SELECT
    JobRole,
    Department,
    COUNT(*)                                                        AS total,
    SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)             AS left_count,
    ROUND(
        SUM(CASE WHEN Attrition = 'Yes' THEN 1.0 ELSE 0 END)
        / COUNT(*) * 100, 2
    )                                                               AS attrition_rate_pct,
    ROUND(AVG(JobSatisfaction), 2)                                  AS avg_job_satisfaction
FROM employees
GROUP BY JobRole, Department
ORDER BY attrition_rate_pct DESC
LIMIT 10;


-- =============================================================
-- QUERY 6: Attrition by age group (using CASE banding)
-- =============================================================
SELECT
    CASE
        WHEN Age BETWEEN 18 AND 25 THEN '18-25'
        WHEN Age BETWEEN 26 AND 35 THEN '26-35'
        WHEN Age BETWEEN 36 AND 45 THEN '36-45'
        WHEN Age BETWEEN 46 AND 55 THEN '46-55'
        ELSE '55+'
    END                                                             AS age_group,
    COUNT(*)                                                        AS total,
    SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)             AS left_count,
    ROUND(
        SUM(CASE WHEN Attrition = 'Yes' THEN 1.0 ELSE 0 END)
        / COUNT(*) * 100, 2
    )                                                               AS attrition_rate_pct,
    ROUND(AVG(MonthlyIncome), 2)                                    AS avg_income
FROM employees
GROUP BY age_group
ORDER BY MIN(Age);


-- =============================================================
-- QUERY 7: Job satisfaction vs attrition heatmap data
-- =============================================================
SELECT
    JobSatisfaction,
    OverTime,
    COUNT(*)                                                         AS total,
    SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)              AS left_count,
    ROUND(
        SUM(CASE WHEN Attrition = 'Yes' THEN 1.0 ELSE 0 END)
        / COUNT(*) * 100, 2
    )                                                                AS attrition_rate_pct
FROM employees
GROUP BY JobSatisfaction, OverTime
ORDER BY JobSatisfaction, OverTime;


-- =============================================================
-- QUERY 8: Tenure analysis — early vs experienced employees
-- =============================================================
SELECT
    CASE
        WHEN YearsAtCompany BETWEEN 0  AND 1  THEN '0-1 year'
        WHEN YearsAtCompany BETWEEN 2  AND 3  THEN '1-3 years'
        WHEN YearsAtCompany BETWEEN 4  AND 7  THEN '3-7 years'
        WHEN YearsAtCompany BETWEEN 8  AND 15 THEN '7-15 years'
        ELSE '15+ years'
    END                                                              AS tenure_band,
    COUNT(*)                                                         AS total,
    SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)              AS left_count,
    ROUND(
        SUM(CASE WHEN Attrition = 'Yes' THEN 1.0 ELSE 0 END)
        / COUNT(*) * 100, 2
    )                                                                AS attrition_rate_pct,
    ROUND(AVG(MonthlyIncome), 2)                                     AS avg_income,
    ROUND(AVG(JobSatisfaction), 2)                                   AS avg_satisfaction
FROM employees
GROUP BY tenure_band
ORDER BY MIN(YearsAtCompany);


-- =============================================================
-- QUERY 9: Window function — rank employees by attrition risk
--          (based on salary below dept avg + low satisfaction)
-- =============================================================
WITH dept_avg AS (
    SELECT
        Department,
        AVG(MonthlyIncome) AS dept_avg_income
    FROM employees
    GROUP BY Department
),
risk_scores AS (
    SELECT
        e.EmployeeNumber,
        e.Department,
        e.JobRole,
        e.MonthlyIncome,
        e.JobSatisfaction,
        e.OverTime,
        e.YearsAtCompany,
        d.dept_avg_income,
        -- Risk score: low salary + low satisfaction + overtime = higher score
        (
            CASE WHEN e.MonthlyIncome < d.dept_avg_income * 0.8 THEN 3 ELSE 0 END +
            CASE WHEN e.JobSatisfaction <= 2                     THEN 3 ELSE 0 END +
            CASE WHEN e.OverTime = 'Yes'                         THEN 2 ELSE 0 END +
            CASE WHEN e.YearsAtCompany <= 2                      THEN 2 ELSE 0 END
        ) AS risk_score
    FROM employees e
    JOIN dept_avg d ON e.Department = d.Department
),
ranked AS (
    SELECT *,
        RANK() OVER (PARTITION BY Department ORDER BY risk_score DESC) AS dept_risk_rank
    FROM risk_scores
)
SELECT
    EmployeeNumber,
    Department,
    JobRole,
    MonthlyIncome,
    JobSatisfaction,
    OverTime,
    YearsAtCompany,
    risk_score,
    dept_risk_rank
FROM ranked
WHERE dept_risk_rank <= 5
ORDER BY Department, dept_risk_rank;


-- =============================================================
-- QUERY 10: Business travel frequency vs attrition
-- =============================================================
SELECT
    BusinessTravel,
    COUNT(*)                                                          AS total,
    SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END)               AS left_count,
    ROUND(
        SUM(CASE WHEN Attrition = 'Yes' THEN 1.0 ELSE 0 END)
        / COUNT(*) * 100, 2
    )                                                                 AS attrition_rate_pct,
    ROUND(AVG(MonthlyIncome), 2)                                      AS avg_income,
    ROUND(AVG(WorkLifeBalance), 2)                                    AS avg_work_life_balance
FROM employees
GROUP BY BusinessTravel
ORDER BY attrition_rate_pct DESC;
