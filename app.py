import streamlit as st
import pandas as pd 

st.set_page_config(page_title="PulseIQ Dashboard", layout="wide")
st.title("📊 PulseIQ Workforce & Finance Dashboard")
st.caption("📅 Reporting Period: September 2026 | Data Cut-off Date: 2026-09-30 | Source: Zenith Nova Clean Aggregates")

REPORT_PATH = "reports/PulseIQ_Monthly_Report_2026-09.xlsx"
exec_df = pd.read_excel(REPORT_PATH, sheet_name="Executive_Summary")
hc_df = pd.read_excel(REPORT_PATH, sheet_name="1_Headcount_Attrition")
pay_df = pd.read_excel(REPORT_PATH, sheet_name="2_Payroll_vs_Budget")
att_df = pd.read_excel(REPORT_PATH, sheet_name="3_Attendance_Overtime")

st.subheader("1. Executive Summary")
exec_df = exec_df.iloc[:, :2].dropna(how="all")
st.dataframe(exec_df, use_container_width=True, hide_index=True)

st.sidebar.header("Filter option")
dept_col = hc_df.columns[1]
departments = ["All Departments"] + sorted(hc_df[dept_col].dropna().unique().tolist())
selected_dept = st.sidebar.selectbox("Select Department", departments)

if selected_dept != "All Departments":
    hc_view = hc_df[hc_df["department_name"] == selected_dept]
    pay_view = pay_df[pay_df["department_name"] == selected_dept]
    att_view = att_df[att_df["department_name"] == selected_dept]
else:
    hc_view, pay_view, att_view = hc_df, pay_df, att_df

st.subheader("2. Headcount & Attrition")
st.dataframe(hc_view, use_container_width=True, hide_index=True)

st.subheader("3. Payroll vs Budget")
st.dataframe(pay_view, use_container_width=True, hide_index=True)

st.subheader("4. Attendance & Overtime")
st.dataframe(att_view, use_container_width=True, hide_index=True)

st.subheader("5. Department Payroll Comparison Chart")
hart_df = pay_view.set_index("department_name")[["actual_payroll_cost", "budget_payroll_cost"]]
st.bar_chart(chart_df)    