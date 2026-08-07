# HR Attrition — Power BI Dashboard Guide
## Step-by-step layout and DAX measures

---

## STEP 1: Load Data into Power BI

1. Open Power BI Desktop
2. Get Data → Text/CSV → select `ibm_hr.csv`
3. In Power Query Editor:
   - Change `Attrition` column: Add Column → Custom Column:
     ```
     = if [Attrition] = "Yes" then 1 else 0
     ```
     Name it: `AttritionBinary`
   - Close & Apply

---

## STEP 2: Create DAX Measures

In the Model view, create a new table called "Measures" and add:

```dax
-- Total Employees
Total Employees = COUNTROWS(employees)

-- Total Attrition
Total Attrition = SUM(employees[AttritionBinary])

-- Attrition Rate %
Attrition Rate % =
    DIVIDE([Total Attrition], [Total Employees]) * 100

-- Average Monthly Income
Avg Income = AVERAGE(employees[MonthlyIncome])

-- Avg Income (Left)
Avg Income Left =
    CALCULATE(
        AVERAGE(employees[MonthlyIncome]),
        employees[Attrition] = "Yes"
    )

-- Avg Income (Stayed)
Avg Income Stayed =
    CALCULATE(
        AVERAGE(employees[MonthlyIncome]),
        employees[Attrition] = "No"
    )

-- Attrition by Department %
Dept Attrition % =
    DIVIDE(
        CALCULATE([Total Attrition]),
        CALCULATE([Total Employees])
    ) * 100
```

---

## STEP 3: Dashboard Layout (Page 1 — Overview)

```
┌─────────────────────────────────────────────────────────────┐
│  HR ATTRITION ANALYSIS DASHBOARD          [Department ▼]    │
│                                           [Job Role   ▼]    │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  Total   │Attrition │  Avg     │  Avg Age │  Employees Left │
│  1,470   │  16.1%   │ $6,503   │   36.9   │     237         │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                                                             │
│  [Clustered Bar Chart]          [Donut Chart]               │
│  Attrition Rate by Department   Attrition by Gender         │
│                                                             │
│  Sales    ████████ 20.6%        ● Male   60%                │
│  HR       ███████ 19.0%         ● Female 40%                │
│  R&D      █████ 13.8%                                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Line Chart]                   [Stacked Bar]               │
│  Attrition Rate by Age Group    Salary Band vs Attrition    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Visuals to add (Page 1):
1. **Card visuals** (top row): Total Employees, Attrition Rate %, Avg Income, Avg Age, Employees Left
2. **Clustered Bar Chart**: X=Department, Y=Attrition Rate % (sorted descending)
3. **Donut Chart**: Legend=Gender, Values=Total Attrition
4. **Line Chart**: X=AgeBand (create using custom column), Y=Attrition Rate %
5. **Stacked Bar**: X=SalaryBand, Y=Total Employees, Legend=Attrition

---

## STEP 4: Dashboard Layout (Page 2 — Deep Dive)

```
┌─────────────────────────────────────────────────────────────┐
│  DEEP DIVE — ATTRITION DRIVERS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Matrix/Heatmap]               [Scatter Plot]              │
│  JobSatisfaction × OverTime     MonthlyIncome vs Age        │
│  (colored by attrition rate)    (colored by Attrition)      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Bar Chart]                    [100% Stacked Bar]          │
│  Top 8 Job Roles by             Attrition by                │
│  Attrition Rate                 Business Travel             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  [Slicer: Department] [Slicer: OverTime] [Slicer: Gender]   │
└─────────────────────────────────────────────────────────────┘
```

### Custom columns to create in Power Query:

```m
// Age Band
= if [Age] <= 25 then "18-25"
  else if [Age] <= 35 then "26-35"
  else if [Age] <= 45 then "36-45"
  else if [Age] <= 55 then "46-55"
  else "55+"

// Salary Band
= if [MonthlyIncome] <= 2000 then "<$2K"
  else if [MonthlyIncome] <= 4000 then "$2-4K"
  else if [MonthlyIncome] <= 6000 then "$4-6K"
  else if [MonthlyIncome] <= 10000 then "$6-10K"
  else "$10K+"

// Tenure Band
= if [YearsAtCompany] <= 1 then "0-1 yr"
  else if [YearsAtCompany] <= 3 then "1-3 yrs"
  else if [YearsAtCompany] <= 7 then "3-7 yrs"
  else if [YearsAtCompany] <= 15 then "7-15 yrs"
  else "15+ yrs"
```

---

## STEP 5: Formatting Tips (Make It Look Professional)

- **Theme**: Use "Executive" or "Tidal" built-in themes, OR import custom JSON
- **Colors**: Red (#E24B4A) for high attrition, Blue (#378ADD) for low
- **Font**: Segoe UI throughout; headers 14-16px bold
- **Card visuals**: Add conditional formatting — red if attrition > 18%
- **Tooltips**: Enable "report page tooltip" for hover details on charts
- **Background**: Light gray (#F5F5F5) page background, white cards

---

## STEP 6: Slicers to Add (Filters)

Add these slicers to BOTH pages in a top filter bar:
- Department (dropdown)
- Job Role (list)
- OverTime (Yes/No toggle)
- Gender (list)
- AgeBand (range slider)

---

## STEP 7: Publish & Share

1. File → Publish → Publish to Power BI Service
2. Share link or embed in portfolio website
3. For Tableau: export cleaned CSV from Python, connect to Tableau Public (free), recreate the same layout

---

## Tableau Public Alternative (Free)

If you don't have Power BI Pro, use **Tableau Public** (100% free):
1. Download: public.tableau.com
2. Connect → Text file → ibm_hr_clean.csv (exported from Python)
3. Create same charts, publish to Tableau Public
4. Add Tableau Public link to GitHub README and LinkedIn

---

*This dashboard, combined with your Python EDA and Streamlit app,
covers: Python, Statistics, EDA, SQL, Excel, Power BI, Gen AI/ML — all in one project.*
