import os
import pandas as pd
import matplotlib.pyplot as plt
from openpyxl.drawing.image import Image as XLImage

DATA_PATH = os.path.join("Data", "PulseIQ_Dataset.xlsx")
CUTOFF_DATE = "2026-09-30"
TARGET_MONTH = "2026-09"
OUTPUT_DIR = "reports"

os.makedirs(OUTPUT_DIR, exist_ok=True)
xls = pd.ExcelFile(DATA_PATH)

depts = pd.read_excel(xls, "dim_department")[["department_id", "department_name"]]
hc = pd.read_excel(xls, "fact_headcount_monthly")
pay = pd.read_excel(xls, "fact_payroll")
att = pd.read_excel(xls, "fact_attendance_monthly")
inv = pd.read_excel(xls, "fact_invoice")
exp = pd.read_excel(xls, "fact_expense")
task = pd.read_excel(xls, "fact_task")
budget = pd.read_excel(xls, "budget_payroll_dept_month")

pay = pay.drop_duplicates(subset=["employee_id", "run_id"])
pay = pay[pay["gross_pay"] >= 0]
att = att.drop_duplicates(subset=["employee_id", "period_end_date"])

def map_department(df):
    merged = df.merge(depts, on="department_id", how="left")
    merged["department_name"] = merged["department_name"].fillna(
        "Unmapped Dept (" + merged["department_id"].astype(str) + ")"
    )
    return merged

hc["ym"] = pd.to_datetime(hc["month_start_date"]).dt.strftime("%Y-%m")
pay["ym"] = pd.to_datetime(pay["period_end_date"]).dt.strftime("%Y-%m")
att["ym"] = pd.to_datetime(att["period_end_date"]).dt.strftime("%Y-%m")
inv["ym"] = pd.to_datetime(inv["invoice_date"]).dt.strftime("%Y-%m")
exp["ym"] = pd.to_datetime(exp["expense_date"]).dt.strftime("%Y-%m")
task["ym"] = pd.to_datetime(task["created_date"]).dt.strftime("%Y-%m")
budget["ym"] = pd.to_datetime(budget["month"]).dt.strftime("%Y-%m")

t1 = map_department(hc[hc["ym"] == TARGET_MONTH])[
    ["department_id", "department_name", "headcount_start", "hires", "exits", "headcount_end", "attrition_rate_monthly_pct"]
]

pay_m = pay[pay["ym"] == TARGET_MONTH].groupby("department_id", as_index=False).agg(
    actual_payroll_cost=("employer_cost", "sum"),
    total_gross_pay=("gross_pay", "sum"),
    employees_paid=("employee_id", "nunique"),
)
bud_m = budget[budget["ym"] == TARGET_MONTH][["department_id", "budget_payroll_cost"]]
t2 = map_department(pay_m.merge(bud_m, on="department_id", how="outer"))
t2["actual_payroll_cost"] = t2["actual_payroll_cost"].fillna(0)
t2["budget_payroll_cost"] = t2["budget_payroll_cost"].fillna(0)
t2["variance"] = t2["actual_payroll_cost"] - t2["budget_payroll_cost"]

att_m = att[att["ym"] == TARGET_MONTH].groupby("department_id", as_index=False).agg(
    avg_attendance_rate=("attendance_rate", "mean"),
    total_overtime_hours=("overtime_hours", "sum"),
    unpaid_absence_days=("unpaid_absence_days", "sum"),
)
t3 = map_department(att_m)

inv_m = inv[inv["ym"] == TARGET_MONTH]
exp_m = exp[exp["ym"] == TARGET_MONTH]
t4 = pd.DataFrame({
    "Metric": [
        "Total Invoiced Revenue (INR)",
        "Total Cash Collected (INR)",
        "Outstanding Balance Due (INR)",
        "Total Operating Expenses (INR)",
        "Net Operating Cash Margin (INR)",
    ],
    "Amount": [
        round(inv_m["total_amount"].sum(), 2),
        round(inv_m["amount_paid"].sum(), 2),
        round(inv_m["balance_due"].sum(), 2),
        round(exp_m["total_amount"].sum(), 2),
        round(inv_m["amount_paid"].sum() - exp_m["total_amount"].sum(), 2),
    ],
})

task_m = task[task["ym"] == TARGET_MONTH]
t5 = task_m.groupby("status", as_index=False).agg(
    task_count=("task_id", "count"),
    total_story_points=("story_points", "sum"),
    avg_cycle_time_days=("cycle_time_days", "mean"),
)

chart1_path = os.path.join(OUTPUT_DIR, f"chart_payroll_{TARGET_MONTH}.png")
fig, ax = plt.subplots(figsize=(9, 4.5))
x = range(len(t2))
ax.bar([i - 0.2 for i in x], t2["budget_payroll_cost"] / 1e5, width=0.4, label="Budget (Lakhs)", color="#4A90E2")
ax.bar([i + 0.2 for i in x], t2["actual_payroll_cost"] / 1e5, width=0.4, label="Actual (Lakhs)", color="#E67E22")
ax.set_xticks(list(x))
ax.set_xticklabels(t2["department_name"], rotation=35, ha="right")
ax.set_ylabel("INR (in Lakhs)")
ax.set_title(f"Payroll Actual vs Budget ({TARGET_MONTH}) | Cut-off: {CUTOFF_DATE}")
ax.legend()
plt.tight_layout()
plt.savefig(chart1_path, dpi=150)
plt.close()

chart2_path = os.path.join(OUTPUT_DIR, f"chart_headcount_{TARGET_MONTH}.png")
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(t1["department_name"], t1["headcount_end"], color="#2ECC71")
ax.set_xticklabels(t1["department_name"], rotation=35, ha="right")
ax.set_ylabel("Active Headcount")
ax.set_title(f"Ending Headcount by Department ({TARGET_MONTH}) | Cut-off: {CUTOFF_DATE}")
plt.tight_layout()
plt.savefig(chart2_path, dpi=150)
plt.close()

out_file = os.path.join(OUTPUT_DIR, f"PulseIQ_Monthly_Report_{TARGET_MONTH}.xlsx")
with pd.ExcelWriter(out_file, engine="openpyxl") as writer:
    meta = pd.DataFrame({
        "Report Field": ["Report Title", "Reporting Period (Month)", "Data Cut-off Date", "Source Dataset"],
        "Value": [
            "PulseIQ Monthly Management Report Pack",
            TARGET_MONTH,
            CUTOFF_DATE,
            "Zenith Nova Master Warehouse (Clean Extract)",
        ],
    })
    meta.to_excel(writer, sheet_name="Executive_Summary", index=False, startrow=0)
    t4.to_excel(writer, sheet_name="Executive_Summary", index=False, startrow=7)
    t5.to_excel(writer, sheet_name="Executive_Summary", index=False, startrow=15)

    t1.to_excel(writer, sheet_name="1_Headcount_Attrition", index=False)
    t2.to_excel(writer, sheet_name="2_Payroll_vs_Budget", index=False)
    t3.to_excel(writer, sheet_name="3_Attendance_Overtime", index=False)

    ws_charts = writer.book.create_sheet(title="4_Visual_Charts")
    ws_charts.add_image(XLImage(chart1_path), "B2")
    ws_charts.add_image(XLImage(chart2_path), "B26")

print("SUCCESS! Report ban gayi:", out_file)