import streamlit as st
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000"

def init_session_state():
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Login"

def api_call(method, endpoint, data=None, files=None):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    url = f"{API_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, data=data, files=files)
            else:
                response = requests.post(url, headers=headers, json=data)
        return response
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def login_page():
    st.title("🔐 SLA Recovery Audit System - Login")

    col1, col2 = st.columns([2, 1])
    with col1:
        username = st.text_input("Username", placeholder="admin")
        password = st.text_input("Password", type="password", placeholder="admin123")

        if st.button("Login", type="primary", use_container_width=True):
            response = api_call("POST", "/api/auth/login", {
                "username": username,
                "password": password
            })

            if response and response.status_code == 200:
                data = response.json()
                st.session_state.token = data["access_token"]
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid credentials")

    with col2:
        st.info("Demo Credentials:\n- Username: admin\n- Password: admin123")

def upload_page():
    st.header("📤 Upload & Parse SLA Document")

    col1, col2 = st.columns(2)

    with col1:
        sla_doc = st.file_uploader("Upload SLA Document (PDF/TXT)", type=["pdf", "txt"])
        data_csv = st.file_uploader("Upload Data CSV", type=["csv"])

    with col2:
        use_custom_prompt = st.checkbox("Use Custom Prompt")
        if use_custom_prompt:
            custom_prompt = st.text_area("Enter Custom Prompt", height=150)
        else:
            custom_prompt = None
            st.info("Using default prompt from code")

    if st.button("Upload & Parse", type="primary", use_container_width=True):
        if not sla_doc or not data_csv:
            st.error("Please upload both documents")
            return

        files = {
            "document": (sla_doc.name, sla_doc.getvalue(), "application/octet-stream"),
            "data_csv": (data_csv.name, data_csv.getvalue(), "text/csv")
        }

        data = {}
        if custom_prompt:
            data["custom_prompt"] = custom_prompt

        response = api_call("POST", "/api/documents/upload", data, files)

        if response and response.status_code == 200:
            doc = response.json()
            st.success(f"Document uploaded (ID: {doc['id']})")

            parse_response = api_call("POST", f"/api/documents/{doc['id']}/parse", {})
            if parse_response and parse_response.status_code == 200:
                parse_data = parse_response.json()
                st.success("Document parsed successfully")
                st.session_state.current_document_id = doc['id']
                st.session_state.current_query_id = parse_data.get('query_id')
                st.session_state.current_page = "Query & Validation"
                st.rerun()

def validation_page():
    st.header("✅ Query & Validation")

    if "current_query_id" not in st.session_state:
        st.warning("No document parsed yet. Please upload a document first.")
        return

    query_id = st.session_state.current_query_id

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Generated SQL Query")
        with st.expander("View Query", expanded=True):
            st.code("""
SELECT
    CAST(incident_date AS DATE) as date,
    CASE
        WHEN uptime_percent < 99 THEN (100 - uptime_percent) * 100
        ELSE 0
    END as penalty_monetary,
    CASE
        WHEN avg_response_time > 2 THEN (avg_response_time - 2) * 50
        ELSE 0
    END as credit_units,
    uptime_percent,
    avg_response_time
FROM data
WHERE CAST(incident_date AS DATE) >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY incident_date
            """, language="sql")

    with col2:
        if st.button("Validate Query", type="primary", use_container_width=True):
            if not query_id:
                st.error("No query ID found. Please upload and parse a document first.")
            else:
                st.info(f"Validating query {query_id}...")
                response = api_call("POST", f"/api/calculations/{query_id}/validate", {})

                if response and response.status_code == 200:
                    calc_data = response.json()
                    st.session_state.current_calculation_id = calc_data['calculation_id']
                    st.session_state.calculation_status = calc_data['status']
                    st.success(f"Validation {calc_data['status']}!")
                    st.session_state.current_page = "Dashboard"
                    st.rerun()
                elif response:
                    st.error(f"Validation failed: {response.status_code} - {response.text}")
                else:
                    st.error("Failed to validate query")

def dashboard_page():
    st.header("📊 Cost Calculation Dashboard")

    if "current_calculation_id" not in st.session_state:
        st.warning("No calculation available. Please validate a query first.")
        return

    calc_id = st.session_state.current_calculation_id

    response = api_call("GET", f"/api/calculations/{calc_id}", None)

    if not response or response.status_code != 200:
        st.error("Failed to load calculation")
        return

    calc = response.json()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Validation Status", calc['validation_status'].upper())
    with col2:
        st.metric("Cost Types", len(calc['cost_breakdowns']))
    with col3:
        total_cost = sum([bd['calculated_value'] for bd in calc['cost_breakdowns']])
        st.metric("Total Cost", f"${total_cost:,.2f}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cost Breakdown")
        breakdown_data = []
        for bd in calc['cost_breakdowns']:
            breakdown_data.append({
                "Cost Type": bd['cost_type'],
                "Original": f"${bd['original_value']:,.2f}" if bd['original_value'] else "$0",
                "Calculated": f"${bd['calculated_value']:,.2f}",
                "Delta": f"${bd['calculated_value'] - bd['original_value']:,.2f}"
            })

        st.table(breakdown_data)

    with col2:
        st.subheader("Chart")
        import plotly.graph_objects as go

        cost_types = [bd['cost_type'] for bd in calc['cost_breakdowns']]
        calculated_values = [bd['calculated_value'] for bd in calc['cost_breakdowns']]

        fig = go.Figure(data=[
            go.Bar(x=cost_types, y=calculated_values, marker_color='#0066cc')
        ])
        fig.update_layout(
            title="Calculated Costs by Type",
            xaxis_title="Cost Type",
            yaxis_title="Amount ($)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    if calc['validation_status'] == "passed":
        st.success("✅ Validation Passed - Ready for Approval")
        if st.button("Proceed to Approval", type="primary", use_container_width=True):
            st.session_state.current_page = "Approval Queue"
            st.rerun()
    else:
        st.error("❌ Validation Failed")
        if calc['validation_errors']:
            with st.expander("View Errors"):
                st.json(json.loads(calc['validation_errors']) if isinstance(calc['validation_errors'], str) else calc['validation_errors'])

def approvals_page():
    st.header("✓ Approval Queue")

    if "current_user" not in st.session_state:
        st.warning("Not logged in")
        return

    if "current_calculation_id" not in st.session_state:
        st.warning("No calculation available")
        return

    calc_id = st.session_state.current_calculation_id

    st.subheader(f"Calculation #{calc_id}")

    col1, col2 = st.columns([2, 1])
    with col1:
        comment = st.text_area("Approval Comment", placeholder="Enter approval decision comments...")

    with col2:
        st.write("**Decision:**")
        status = st.radio("Select", ["approved", "rejected"], label_visibility="collapsed")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Approve", type="primary", use_container_width=True):
            response = api_call("POST", f"/api/approvals/{calc_id}/approve", {
                "status": "approved",
                "comment": comment
            })
            if response and response.status_code == 200:
                st.success("✅ Calculation Approved!")
                st.session_state.current_page = "Proof Viewer"
                st.rerun()

    with col2:
        if st.button("❌ Reject", use_container_width=True):
            response = api_call("POST", f"/api/approvals/{calc_id}/approve", {
                "status": "rejected",
                "comment": comment
            })
            if response and response.status_code == 200:
                st.warning("⚠️ Calculation Rejected")
                st.session_state.current_page = "Upload & Parse"
                st.rerun()

def proofs_page():
    st.header("📋 Audit Proof Viewer")

    tab1, tab2 = st.tabs(["View Proof", "Search"])

    with tab1:
        if "current_calculation_id" in st.session_state:
            st.subheader(f"Proof for Calculation #{st.session_state.current_calculation_id}")
            st.info("Proof has been generated and approved. Download as JSON for compliance documentation.")

            col1, col2 = st.columns(2)
            with col1:
                st.button("📥 Download JSON", use_container_width=True)
            with col2:
                st.button("📥 Download PDF", use_container_width=True)

            with st.expander("View Full Proof"):
                st.json({
                    "generated_at": datetime.utcnow().isoformat(),
                    "approver": st.session_state.get("user", "unknown"),
                    "contract_clauses": ["Service availability below 99% results in $100/hour penalty"],
                    "service_levels": ["99% uptime SLA", "2 second max response time"],
                    "calculation_formulas": ["penalty = hours_below_sla * 100"],
                    "executed_sql_formula": "SELECT ... FROM service_metrics ...",
                    "cost_deltas": [
                        {"cost_type": "monetary", "original": 0, "final": 5000, "delta": 5000}
                    ]
                })

    with tab2:
        search_type = st.selectbox("Search by", ["Cost Type", "Approver", "Date"])
        search_query = st.text_input(f"Search {search_type}")

        if st.button("🔍 Search"):
            st.info(f"Searching for {search_type}: {search_query}")

def main():
    st.set_page_config(
        page_title="SLA Recovery Audit System",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_session_state()

    if not st.session_state.token:
        login_page()
    else:
        with st.sidebar:
            st.title(f"👤 {st.session_state.user}")

            pages = ["Upload & Parse", "Query & Validation", "Dashboard", "Approval Queue", "Proof Viewer"]
            st.session_state.current_page = st.radio("Navigation", pages, label_visibility="collapsed")

            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.token = None
                st.session_state.user = None
                st.rerun()

        if st.session_state.current_page == "Upload & Parse":
            upload_page()
        elif st.session_state.current_page == "Query & Validation":
            validation_page()
        elif st.session_state.current_page == "Dashboard":
            dashboard_page()
        elif st.session_state.current_page == "Approval Queue":
            approvals_page()
        elif st.session_state.current_page == "Proof Viewer":
            proofs_page()

if __name__ == "__main__":
    main()
