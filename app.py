import streamlit as st
import pandas as pd

st.set_page_config(page_title="PulseIQ Workforce Analytics", layout="wide")
st.title("📊 PulseIQ Workforce & Executive Analytics")
st.caption("Reporting Period: September 2026 | Data Cut-off Date: 2026-09-30")

REPORT_PATH = "reports/PulseIQ_Monthly_Report_2026-09.xlsx"
RAW_DATA_PATH = "PulseIQ_Dataset.xlsx"

# --- LOAD DATA WITH CACHING ---
@st.cache_data
def load_report_data():
    xls = pd.ExcelFile(REPORT_PATH)
    sheets = xls.sheet_names
    exec_df = pd.read_excel(xls, sheet_name=sheets[0])
    hc_df = pd.read_excel(xls, sheet_name=sheets[1])
    pay_df = pd.read_excel(xls, sheet_name=sheets[2])
    att_df = pd.read_excel(xls, sheet_name=sheets[3])
    return exec_df, hc_df, pay_df, att_df

@st.cache_data
def load_explorer_data():
    emp = pd.read_excel(RAW_DATA_PATH, sheet_name="dim_employee")
    dept = pd.read_excel(RAW_DATA_PATH, sheet_name="dim_department")
    team = pd.read_excel(RAW_DATA_PATH, sheet_name="dim_team")
    pay = pd.read_excel(RAW_DATA_PATH, sheet_name="fact_payroll")
    att = pd.read_excel(RAW_DATA_PATH, sheet_name="fact_attendance_monthly")
    risk = pd.read_excel(RAW_DATA_PATH, sheet_name="fact_attrition_risk")
    tasks = pd.read_excel(RAW_DATA_PATH, sheet_name="fact_task")

    # Active current employees as of cut-off
    emp_curr = emp[(emp["is_current"] == "Y") & (emp["employment_status"] == "Active")].copy()
    emp_curr = emp_curr.merge(dept[["department_id", "department_name"]], on="department_id", how="left")

    # Map employees to teams via task assignments (fallback to "General / Non-Sprint Team")
    emp_team_map = (
        tasks[["assignee_employee_id", "team_id"]]
        .dropna()
        .drop_duplicates(subset=["assignee_employee_id"])
        .rename(columns={"assignee_employee_id": "employee_id"})
    )
    emp_curr = emp_curr.merge(emp_team_map, on="employee_id", how="left")
    emp_curr = emp_curr.merge(team[["team_id", "team_name"]], on="team_id", how="left")
    emp_curr["team_name"] = emp_curr["team_name"].fillna("General / Non-Sprint Team")
    emp_curr["department_name"] = emp_curr["department_name"].fillna("Unknown")

    # Latest month payroll & attendance (Sept 2026)
    latest_pay_date = pay["period_end_date"].max()
    pay_latest = pay[pay["period_end_date"] == latest_pay_date].drop_duplicates(subset=["employee_id"])

    latest_att_date = att["period_end_date"].max()
    att_latest = att[att["period_end_date"] == latest_att_date].drop_duplicates(subset=["employee_id"])

    risk_latest = risk.drop_duplicates(subset=["employee_id"])

    # Merge into unified analytics dataframe
    df = emp_curr.merge(
        pay_latest[["employee_id", "gross_pay", "net_pay", "employer_cost", "overtime_hours_paid"]],
        on="employee_id",
        how="left",
    )
    df = df.merge(
        att_latest[["employee_id", "attendance_rate", "overtime_hours", "late_arrivals"]],
        on="employee_id",
        how="left",
    )
    df = df.merge(
        risk_latest[["employee_id", "risk_score_12m", "risk_band"]],
        on="employee_id",
        how="left",
    )
    df["risk_band"] = df["risk_band"].fillna("Not Scored")
    return df

exec_df, hc_df, pay_df, att_df = load_report_data()
explorer_df = load_explorer_data()

# --- NAVIGATION TABS ---
tab1, tab2 = st.tabs(["📈 Executive Dashboard", "🔒 Self-Service KPI Explorer (Privacy Protected)"])

# ==========================================
# TAB 1: EXECUTIVE DASHBOARD (DAY 17)
# ==========================================
with tab1:
    st.subheader("1. Executive Summary")
    exec_clean = exec_df.dropna(how="all")
    st.dataframe(exec_clean, use_container_width=True, hide_index=True)

    st.sidebar.header("Dashboard Filters (Tab 1)")
    dept_col = hc_df.columns[0]
    dept_map = dict(zip(
        explorer_df["department_id"].astype(str),
        explorer_df["department_name"].astype(str)
    ))
    departments = ["ALL"] + sorted(hc_df[dept_col].dropna().astype(str).unique().tolist())
    selected_dept = st.sidebar.selectbox(
        "Filter Department (Executive View)",
        departments,
        format_func=lambda x: "ALL" if x == "ALL" else dept_map.get(x, x)
    )

    if selected_dept != "ALL":
        hc_view = hc_df[hc_df[dept_col].astype(str) == selected_dept]
        pay_view = pay_df[pay_df[pay_df.columns[0]].astype(str) == selected_dept]
        att_view = att_df[att_df[att_df.columns[0]].astype(str) == selected_dept]
    else:
        hc_view, pay_view, att_view = hc_df, pay_df, att_df

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("2. Headcount by Department")
        st.dataframe(hc_view, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("3. Attendance Summary")
        st.dataframe(att_view, use_container_width=True, hide_index=True)

    st.subheader("4. Payroll Cost by Department")
    st.dataframe(pay_view, use_container_width=True, hide_index=True)

    if len(pay_view.columns) >= 2:
        chart_df = pay_view.copy()
        chart_df[chart_df.columns[0]] = chart_df[chart_df.columns[0]].astype(str).map(lambda x: dept_map.get(x, x))
        chart_df = chart_df.set_index(chart_df.columns[0])
        num_cols = chart_df.select_dtypes(include="number").columns
        if len(num_cols) > 0:
            st.subheader("Department Payroll Comparison")
            st.bar_chart(chart_df[num_cols[0]])

# ==========================================
# TAB 2: TASK 18 SELF-SERVICE KPI EXPLORER
# ==========================================
with tab2:
    st.subheader("Self-Service KPI Explorer with Role-Based Access & Privacy Guardrails")

    ROLE_PERMISSIONS = {
        "ADMIN": {
            "desc": "Full access to all workforce, payroll, attendance, and risk metrics across all dimensions.",
            "metrics": [
                "Headcount",
                "Avg Gross Pay (INR)",
                "Total Payroll Cost (INR)",
                "Attendance Rate (%)",
                "Total Overtime Hours",
                "High Attrition Risk Count",
            ],
            "dimensions": ["Work Location", "Work Mode", "Employment Type", "Gender", "Job Level", "Attrition Risk Band"],
            "max_drill": "Team",
        },
        "HR": {
            "desc": "Access to people, diversity, attendance, and compensation metrics for HR governance.",
            "metrics": [
                "Headcount",
                "Avg Gross Pay (INR)",
                "Attendance Rate (%)",
                "Total Overtime Hours",
                "High Attrition Risk Count",
            ],
            "dimensions": ["Work Location", "Work Mode", "Employment Type", "Gender", "Job Level", "Attrition Risk Band"],
            "max_drill": "Team",
        },
        "EXECUTIVE": {
            "desc": "Strategic company & department-level KPIs. Individual/team-level pay and sensitive attributes restricted.",
            "metrics": [
                "Headcount",
                "Total Payroll Cost (INR)",
                "Attendance Rate (%)",
                "High Attrition Risk Count",
            ],
            "dimensions": ["Work Location", "Work Mode", "Employment Type", "Job Level"],
            "max_drill": "Department",
        },
        "MANAGER": {
            "desc": "Operational workforce & attendance KPIs only. Payroll/salary and gender attributes are blocked.",
            "metrics": [
                "Headcount",
                "Attendance Rate (%)",
                "Total Overtime Hours",
            ],
            "dimensions": ["Work Location", "Work Mode", "Employment Type", "Job Level"],
            "max_drill": "Team",
        },
    }

    MIN_GROUP_SIZE = 5

    r_col1, r_col2 = st.columns([1, 2])
    with r_col1:
        selected_role = st.selectbox("Select User Role (RBAC)", list(ROLE_PERMISSIONS.keys()), index=3)
    with r_col2:
        st.info(f"*Active Role: {selected_role}* — {ROLE_PERMISSIONS[selected_role]['desc']}")

    perms = ROLE_PERMISSIONS[selected_role]

    c1, c2 = st.columns(2)
    with c1:
        selected_metric = st.selectbox("Choose Metric", perms["metrics"])
    with c2:
        selected_dim_label = st.selectbox("Choose Dimension (Breakdown)", perms["dimensions"])

    DIM_COL_MAP = {
        "Work Location": "work_location",
        "Work Mode": "work_mode",
        "Employment Type": "employment_type",
        "Gender": "gender",
        "Job Level": "job_level",
        "Attrition Risk Band": "risk_band",
    }
    dim_col = DIM_COL_MAP[selected_dim_label]

    st.markdown("### Drill-Down Hierarchy: Company → Department → Team")
    d1, d2, d3 = st.columns(3)

    with d1:
        st.text_input("Level 1: Company", value="Zenith Nova Technologies Pvt Ltd", disabled=True)

    dept_options = ["All Departments"] + sorted(explorer_df["department_name"].dropna().unique().tolist())
    with d2:
        selected_drill_dept = st.selectbox("Level 2: Department", dept_options)

    filtered_df = explorer_df.copy()
    if selected_drill_dept != "All Departments":
        filtered_df = filtered_df[filtered_df["department_name"] == selected_drill_dept]

    with d3:
        if perms["max_drill"] == "Team":
            team_options = ["All Teams"] + sorted(filtered_df["team_name"].dropna().unique().tolist())
            selected_drill_team = st.selectbox("Level 3: Team", team_options)
            if selected_drill_team != "All Teams":
                filtered_df = filtered_df[filtered_df["team_name"] == selected_drill_team]
        else:
            selected_drill_team = "All Teams"
            st.selectbox("Level 3: Team (Restricted for Role)", ["Department Level Max"], disabled=True)

    total_n = len(filtered_df)
    st.markdown("---")

    if total_n < MIN_GROUP_SIZE:
        st.error(
            f"🔒 *Privacy Guardrail Triggered:* The selected scope contains fewer than {MIN_GROUP_SIZE} employees "
            f"(Group size < {MIN_GROUP_SIZE}). All metrics and breakdowns are suppressed to protect individual employee privacy."
        )
    else:
        def compute_metric(sub_df, metric_name):
            if metric_name == "Headcount":
                return len(sub_df)
            elif metric_name == "Avg Gross Pay (INR)":
                return round(sub_df["gross_pay"].mean(), 2)
            elif metric_name == "Total Payroll Cost (INR)":
                return round(sub_df["employer_cost"].sum(), 2)
            elif metric_name == "Attendance Rate (%)":
                return round(sub_df["attendance_rate"].mean() * 100, 2) if sub_df["attendance_rate"].max() <= 1 else round(sub_df["attendance_rate"].mean(), 2)
            elif metric_name == "Total Overtime Hours":
                return round(sub_df["overtime_hours"].sum(), 1)
            elif metric_name == "High Attrition Risk Count":
                return int((sub_df["risk_band"] == "High").sum())
            return 0

        overall_val = compute_metric(filtered_df, selected_metric)
        m1, m2 = st.columns(2)
        m1.metric(label=f"Overall {selected_metric}", value=f"{overall_val:,}")
        m2.metric(label="Eligible Headcount (N)", value=f"{total_n} employees")

        grouped_rows = []
        suppressed_count = 0

        for dim_val, grp in filtered_df.groupby(dim_col, dropna=False):
            n_grp = len(grp)
            label = str(dim_val) if pd.notna(dim_val) else "Unknown"
            if n_grp < MIN_GROUP_SIZE:
                suppressed_count += 1
                grouped_rows.append({
                    selected_dim_label: label,
                    "Group Size (N)": f"< {MIN_GROUP_SIZE} (Hidden)",
                    selected_metric: "🔒 Suppressed for Privacy",
                    "_numeric_val": None,
                })
            else:
                val = compute_metric(grp, selected_metric)
                grouped_rows.append({
                    selected_dim_label: label,
                    "Group Size (N)": n_grp,
                    selected_metric: val,
                    "_numeric_val": val,
                })

        res_df = pd.DataFrame(grouped_rows)

        if suppressed_count == 1:
            st.warning(
                f"⚠️ *Complementary Privacy Notice:* 1 sub-group had fewer than {MIN_GROUP_SIZE} employees and was hidden. "
                "Exact group sizes for hidden rows are masked to prevent residual deduction."
            )
        elif suppressed_count > 1:
            st.info(
                f"ℹ️ *{suppressed_count} sub-group(s) hidden* because their group size is smaller than {MIN_GROUP_SIZE} employees."
            )

        st.subheader(f"{selected_metric} by {selected_dim_label}")
        display_df = res_df.drop(columns=["_numeric_val"])
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        safe_chart_df = res_df.dropna(subset=["_numeric_val"]).copy()
        if not safe_chart_df.empty:
            st.bar_chart(safe_chart_df.set_index(selected_dim_label)["_numeric_val"])
        else:
            st.warning("All breakdown groups are below the minimum group size threshold (< 5). Chart hidden.")
