# Release Notes - PulseIQ Workforce Metrics (v1.0.0)

*Release Date:* November 19, 2026  
*Data Cut-off:* September 2026 (2026-09-30)  
*Live API Link:* https://pulseiq-analytics.onrender.com/docs  

---

## 1. What is Included in v1.0.0
- *Live FastAPI Backend (api.py):* Deployed on Render with 5 working endpoints for Active Headcount, Average Gross Pay, Total Payroll Cost, Attendance Rate, and High Attrition Risk.
- *Clear Metric Details:* Every API output shows the exact formula, Excel sheet source (PulseIQ_Dataset.xlsx), and last refresh date so anyone can verify the numbers.
- *Streamlit Dashboard (app.py):* Interactive dashboard to view company-wide and department-level HR & payroll metrics.
- *Monthly Report Generator (build_report.py):* Creates summary Excel reports and charts in the /reports folder.
- *Data Quality Check:* Verified live API numbers against the source Excel file (for example, Active Headcount = 441).

---

## 2. What is Not Included
- *Live HRMS Connection:* Data is loaded from the monthly Excel file (PulseIQ_Dataset.xlsx), not directly connected to a live HR software.
- *User Login / Authentication:* API endpoints are currently open for read-only testing and dashboard use.
- *Machine Learning Prediction:* Attrition risk is based on defined risk bands (High), not a trained ML prediction model.

---

## 3. Known Limits
- *Render Free Tier Delay:* Since the API is hosted on Render's free plan, it goes to sleep after 15 minutes of inactivity and takes around 30–50 seconds to wake up on the first request.
- *Single Month Data:* The dataset covers one monthly cut-off (2026-09-30), so multi-year seasonal trends cannot be analyzed yet.

---

## 4. Think for Yourself: Recommendation Not Given Yet
- *What we should NOT recommend yet:* We should not recommend changing salaries across departments or taking strict HR action against employees based only on the current High Attrition Risk flag.
- *Why:* Our current dataset is only a single month's snapshot (2026-09-30). We do not have multi-month trend data, exit-interview reasons, or manager feedback yet—making big salary or team decisions on one month's data can lead to wrong conclusions.

