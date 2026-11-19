import os
import pandas as pd
from fastapi import FastAPI

app = FastAPI(
    title="PulseIQ Workforce Metrics API",
    description="REST API exposing 5 governed HR & Workforce KPIs with definitions, sources, and data freshness.",
    version="1.0.0"
)

DATA_PATH = "Data/PulseIQ_Dataset.xlsx" if os.path.exists("Data/PulseIQ_Dataset.xlsx") else "PulseIQ_Dataset.xlsx"
DATA_FRESHNESS = "2026-09-30 (Monthly Cut-off | Refreshed Monthly)"

def get_unified_df():
    emp = pd.read_excel(DATA_PATH, sheet_name="dim_employee")
    pay = pd.read_excel(DATA_PATH, sheet_name="fact_payroll")
    att = pd.read_excel(DATA_PATH, sheet_name="fact_attendance_monthly")
    risk = pd.read_excel(DATA_PATH, sheet_name="fact_attrition_risk")

    emp_curr = emp[(emp["is_current"] == "Y") & (emp["employment_status"] == "Active")].copy()
    pay_latest = pay[pay["period_end_date"] == pay["period_end_date"].max()].drop_duplicates(subset=["employee_id"])
    att_latest = att[att["period_end_date"] == att["period_end_date"].max()].drop_duplicates(subset=["employee_id"])
    risk_latest = risk.drop_duplicates(subset=["employee_id"])

    df = emp_curr.merge(pay_latest[["employee_id", "gross_pay", "employer_cost"]], on="employee_id", how="left")
    df = df.merge(att_latest[["employee_id", "attendance_rate", "overtime_hours"]], on="employee_id", how="left")
    df = df.merge(risk_latest[["employee_id", "risk_band"]], on="employee_id", how="left")
    return df

# Helper function: avoids repeating the same keys 5 times
def format_metric(name, value, unit, definition, source):
    return {
        "metric": name,
        "value": value,
        "unit": unit,
        "definition": definition,
        "source": source,
        "last_refresh": DATA_FRESHNESS
    }

@app.get("/")
def home():
    return {
        "service": "PulseIQ Metrics API",
        "status": "Live",
        "data_freshness": DATA_FRESHNESS,
        "endpoints": [
            "/metrics/headcount",
            "/metrics/avg-gross-pay",
            "/metrics/total-payroll-cost",
            "/metrics/attendance-rate",
            "/metrics/high-attrition-risk"
        ]
    }

@app.get("/metrics/headcount")
def headcount():
    df = get_unified_df()
    return format_metric(
        "Active Headcount", int(len(df)), "employees",
        "Total count of active current employees (is_current = 'Y' AND employment_status = 'Active').",
        "PulseIQ_Dataset.xlsx -> dim_employee"
    )

@app.get("/metrics/avg-gross-pay")
def avg_gross_pay():
    df = get_unified_df()
    return format_metric(
        "Average Gross Pay", round(float(df["gross_pay"].mean()), 2), "INR",
        "Mean monthly gross salary across active employees for the latest payroll period.",
        "PulseIQ_Dataset.xlsx -> dim_employee + fact_payroll (gross_pay)"
    )

@app.get("/metrics/total-payroll-cost")
def total_payroll_cost():
    df = get_unified_df()
    return format_metric(
        "Total Monthly Payroll Cost", round(float(df["employer_cost"].sum()), 2), "INR",
        "Total employer payroll cost for active employees in the latest reporting period.",
        "PulseIQ_Dataset.xlsx -> dim_employee + fact_payroll (employer_cost)"
    )

@app.get("/metrics/attendance-rate")
def attendance_rate():
    df = get_unified_df()
    raw_mean = float(df["attendance_rate"].mean())
    val = round(raw_mean * 100, 2) if raw_mean <= 1.0 else round(raw_mean, 2)
    return format_metric(
        "Average Attendance Rate", val, "%",
        "Average monthly attendance percentage across active employees in the latest period.",
        "PulseIQ_Dataset.xlsx -> dim_employee + fact_attendance_monthly (attendance_rate)"
    )

@app.get("/metrics/high-attrition-risk")
def high_attrition_risk():
    df = get_unified_df()
    return format_metric(
        "High Attrition Risk Headcount", int((df["risk_band"] == "High").sum()), "employees",
        "Count of active employees classified in the 'High' attrition risk band.",
        "PulseIQ_Dataset.xlsx -> dim_employee + fact_attrition_risk (risk_band)"
    )