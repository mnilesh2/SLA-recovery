import streamlit as st
import requests
import json
from datetime import datetime
from io import BytesIO

API_URL = "http://localhost:8000"

def init_session_state():
    defaults = {
        "token": None,
        "user": None,
        "role": None,
        "step": "upload",
        "document_id": None,
        "query_id": None,
        "sql_query": None,
        "extracted_terms": None,
        "calculation_id": None,
        "proof_data": None,
        "validation_status": None,
        "cost_breakdowns": None
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

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

def reset_wizard():
    st.session_state.step = "upload"
    st.session_state.document_id = None
    st.session_state.query_id = None
    st.session_state.sql_query = None
    st.session_state.extracted_terms = None
    st.session_state.calculation_id = None
    st.session_state.proof_data = None
    st.session_state.validation_status = None
    st.session_state.cost_breakdowns = None

def render_stepper():
    steps = ["Upload", "Validate", "Review", "Proof"]
    step_index = {"upload": 0, "validate": 1, "review": 2, "proof": 3}.get(st.session_state.step, 0)

    col_widths = [2, 1, 2, 1, 2, 1, 2]
    cols = st.columns(col_widths)

    colors = {
        "done": "✅",
        "current": "▶️",
        "upcoming": "⭕"
    }

    for i, step in enumerate(steps):
        if i < step_index:
            status = colors["done"]
        elif i == step_index:
            status = colors["current"]
        else:
            status = colors["upcoming"]

        with cols[i * 2]:
            st.markdown(f"<h3 style='text-align: center;'>{status}<br>{step}</h3>", unsafe_allow_html=True)

def login_page():
    st.set_page_config(page_title="SLA Recovery Audit - Login", page_icon="🔐", layout="centered")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("# 🔐 SLA Recovery Audit System")
        st.markdown("---")

        with st.container(border=True):
            st.markdown("### Login")
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

                    me_response = api_call("GET", "/api/auth/me", None)
                    if me_response and me_response.status_code == 200:
                        me_data = me_response.json()
                        st.session_state.role = me_data.get("role", "reviewer")

                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Try admin/admin123")

        st.markdown("---")
        with st.expander("ℹ️ Demo Credentials"):
            st.markdown("**Username:** `admin`\n**Password:** `admin123`")

def step_upload():
    st.markdown("### 📤 Step 1: Upload & Parse")
    st.markdown("Upload your SLA document and billing data to get started.")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### Documents")
            sla_doc = st.file_uploader("📄 SLA Document (PDF/TXT)", type=["pdf", "txt"], key="sla_uploader")
            data_csv = st.file_uploader("📊 Billing Data (CSV)", type=["csv"], key="csv_uploader")

    with col2:
        with st.container(border=True):
            st.markdown("#### Options")
            use_custom_prompt = st.checkbox("Use Custom Prompt")
            if use_custom_prompt:
                custom_prompt = st.text_area("Custom Prompt", height=120, placeholder="Enter your custom prompt...")
            else:
                custom_prompt = None
                st.info("📝 Using default SLA parsing prompt")

    if st.button("Upload & Parse", type="primary", use_container_width=True, key="upload_btn"):
        if not sla_doc or not data_csv:
            st.error("❌ Please upload both documents")
            return

        with st.spinner("Uploading documents..."):
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
                st.session_state.document_id = doc['id']
                st.success(f"✅ Document uploaded (ID: {doc['id']})")

                with st.spinner("Parsing document with LLM..."):
                    parse_response = api_call("POST", f"/api/documents/{doc['id']}/parse", {})
                    if parse_response and parse_response.status_code == 200:
                        parse_data = parse_response.json()
                        st.session_state.query_id = parse_data.get('query_id')
                        st.session_state.sql_query = parse_data.get('sql_query')
                        st.session_state.extracted_terms = parse_data.get('extracted_terms')
                        st.success("✅ Document parsed successfully!")
                        st.session_state.step = "validate"
                        st.rerun()
                    else:
                        st.error(f"❌ Parse failed: {parse_response.text if parse_response else 'Unknown error'}")
            else:
                st.error(f"❌ Upload failed: {response.text if response else 'Unknown error'}")

def step_validate():
    st.markdown("### ✅ Step 2: Query Verification")
    st.markdown("Review the generated SQL query before validation.")

    if not st.session_state.query_id:
        st.error("❌ No query found. Please upload a document first.")
        if st.button("← Go Back"):
            reset_wizard()
            st.rerun()
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.container(border=True):
            st.markdown("#### Generated SQL Query")
            if st.session_state.sql_query:
                st.code(st.session_state.sql_query, language="sql")
            else:
                st.warning("No SQL query generated")

    with col2:
        with st.container(border=True):
            st.markdown("#### Extracted Terms")
            if st.session_state.extracted_terms:
                try:
                    terms = json.loads(st.session_state.extracted_terms) if isinstance(st.session_state.extracted_terms, str) else st.session_state.extracted_terms
                    st.json(terms)
                except:
                    st.write(st.session_state.extracted_terms)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Confirm & Validate", type="primary", use_container_width=True):
            with st.spinner("Validating query..."):
                response = api_call("POST", f"/api/calculations/{st.session_state.query_id}/validate", {})

                if response and response.status_code == 200:
                    calc_data = response.json()
                    st.session_state.calculation_id = calc_data['calculation_id']
                    st.session_state.validation_status = calc_data['status']
                    st.session_state.cost_breakdowns = calc_data['cost_breakdowns']
                    st.success("✅ Validation passed!")
                    st.session_state.step = "review"
                    st.rerun()
                else:
                    st.error(f"❌ Validation failed: {response.text if response else 'Unknown error'}")

    with col2:
        if st.button("← Back to Upload", use_container_width=True):
            reset_wizard()
            st.rerun()

def step_review():
    st.markdown("### 📊 Step 3: Cost Review & Approval")
    st.markdown("Review the calculated costs and provide your approval decision.")

    if not st.session_state.calculation_id:
        st.error("❌ No calculation found. Please validate a query first.")
        if st.button("← Go Back"):
            reset_wizard()
            st.rerun()
        return

    response = api_call("GET", f"/api/calculations/{st.session_state.calculation_id}", None)

    if not response or response.status_code != 200:
        st.error("❌ Failed to load calculation")
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
        with st.container(border=True):
            st.markdown("#### Cost Breakdown")
            breakdown_data = []
            for bd in calc['cost_breakdowns']:
                breakdown_data.append({
                    "Type": bd['cost_type'],
                    "Original": f"${bd.get('original_value', 0):,.2f}",
                    "Calculated": f"${bd['calculated_value']:,.2f}",
                    "Delta": f"${bd['calculated_value'] - bd.get('original_value', 0):,.2f}"
                })
            st.table(breakdown_data)

    with col2:
        with st.container(border=True):
            st.markdown("#### Cost Chart")
            import plotly.graph_objects as go

            cost_types = [bd['cost_type'] for bd in calc['cost_breakdowns']]
            calculated_values = [bd['calculated_value'] for bd in calc['cost_breakdowns']]

            fig = go.Figure(data=[
                go.Bar(x=cost_types, y=calculated_values, marker_color='#0066cc')
            ])
            fig.update_layout(
                title="Costs by Type",
                xaxis_title="Cost Type",
                yaxis_title="Amount ($)",
                height=350,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    if st.session_state.role in ["approver", "admin"]:
        with st.container(border=True):
            st.markdown("#### Approval Decision")

            col1, col2 = st.columns([2, 1])
            with col1:
                comment = st.text_area("Comments", placeholder="Enter approval decision comments...", height=100)

            with col2:
                st.write("**Status:**")
                status = st.radio("Select", ["approved", "rejected"], label_visibility="collapsed")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", type="primary", use_container_width=True):
                    response = api_call("POST", f"/api/approvals/{st.session_state.calculation_id}/approve", {
                        "status": "approved",
                        "comment": comment
                    })
                    if response and response.status_code == 200:
                        st.success("✅ Calculation approved!")

                        proof_response = api_call("GET", f"/api/proofs/by-calculation/{st.session_state.calculation_id}", None)
                        if proof_response and proof_response.status_code == 200:
                            st.session_state.proof_data = proof_response.json().get('proof_data')
                            st.session_state.step = "proof"
                            st.rerun()
                    else:
                        st.error(f"❌ Approval failed: {response.text if response else 'Unknown error'}")

            with col2:
                if st.button("❌ Reject", use_container_width=True):
                    response = api_call("POST", f"/api/approvals/{st.session_state.calculation_id}/approve", {
                        "status": "rejected",
                        "comment": comment
                    })
                    if response and response.status_code == 200:
                        st.warning("⚠️ Calculation rejected and returned for revision.")
                        reset_wizard()
                        st.rerun()
                    else:
                        st.error(f"❌ Rejection failed: {response.text if response else 'Unknown error'}")

    else:
        with st.container(border=True):
            st.info("⏳ Waiting for approver review... Your role is 'reviewer'. Ask an approver to review this calculation.")

def step_proof():
    st.markdown("### 📋 Step 4: Audit Proof Generated")
    st.markdown("Your SLA audit proof has been successfully generated.")

    if not st.session_state.proof_data:
        st.error("❌ No proof data found.")
        if st.button("← Go Back"):
            reset_wizard()
            st.rerun()
        return

    proof_data = st.session_state.proof_data if isinstance(st.session_state.proof_data, dict) else json.loads(st.session_state.proof_data)

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.container(border=True):
            st.markdown("#### Proof Summary")
            st.markdown(f"**Generated:** {proof_data.get('generated_at', 'N/A')}")
            st.markdown(f"**Approver:** {proof_data.get('approver', 'N/A')}")
            st.markdown(f"**Status:** ✅ Approved")

    with col2:
        with st.container(border=True):
            st.markdown("#### Download")
            proof_json = json.dumps(proof_data, indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=proof_json,
                file_name=f"proof_{st.session_state.calculation_id}.json",
                mime="application/json",
                use_container_width=True
            )

    with st.expander("📄 View Full Proof"):
        st.json(proof_data)

    st.divider()

    if st.button("🔄 Start New Submission", type="primary", use_container_width=True):
        reset_wizard()
        st.rerun()

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
            st.markdown("# 📋 SLA Audit System")
            st.divider()

            st.markdown(f"**User:** {st.session_state.user}")
            st.markdown(f"**Role:** {st.session_state.role or 'unknown'}")
            st.divider()

            st.markdown("### Progress")
            steps = ["Upload", "Validate", "Review", "Proof"]
            step_map = {"upload": 0, "validate": 1, "review": 2, "proof": 3}
            current_step_index = step_map.get(st.session_state.step, 0)

            for i, step in enumerate(steps):
                if i < current_step_index:
                    st.markdown(f"✅ {step}")
                elif i == current_step_index:
                    st.markdown(f"▶️ **{step}** (current)")
                else:
                    st.markdown(f"⭕ {step}")

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 New", use_container_width=True):
                    reset_wizard()
                    st.rerun()

            with col2:
                if st.button("🚪 Logout", use_container_width=True):
                    st.session_state.token = None
                    st.session_state.user = None
                    st.session_state.role = None
                    reset_wizard()
                    st.rerun()

        if st.session_state.step == "upload":
            step_upload()
        elif st.session_state.step == "validate":
            step_validate()
        elif st.session_state.step == "review":
            step_review()
        elif st.session_state.step == "proof":
            step_proof()

if __name__ == "__main__":
    main()
