## PulseIQ Workforce Metrics API (Phase 4 | Task 16-20)

### 1. Live Deployment Links
- *Interactive Swagger UI Docs:* https://pulseiq-analytics.onrender.com/docs
- *Production Base URL:* https://pulseiq-analytics.onrender.com
- *GitHub Repository:* https://github.com/lokendrasharma3244-png/PulseIQ-analytics

---

### 2. End-to-End Data Lineage
```text
[Source Data: PulseIQ_Dataset.xlsx]
   ├── dim_employee (Active Headcount & Attrition Risk)
   ├── fact_payroll (Average Gross Pay & Total Payroll Cost)
   └── fact_attendance (Attendance Rate)
            │
            ▼
[FastAPI Backend: api.py (GitHub main branch)]
   └── Loads sheets via Pandas, filters active records, computes governed KPIs
            │
            ▼
[Cloud Hosting: Render.com Web Service]
   └── Served via Uvicorn (uvicorn api:app --host 0.0.0.0 --port $PORT)
            │
            ▼
[API Consumers: Swagger UI (/docs) & Streamlit Dashboard]
