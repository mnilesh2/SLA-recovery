import streamlit as st
import requests
import json
from datetime import datetime
import os

# Disable proxy for local connections
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,0.0.0.0'

API_URL = "http://127.0.0.1:8000"

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

    # Disable proxy for local connections
    proxies = {
        "http": None,
        "https": None,
    }

    # Longer timeout for LLM operations (parsing, validation, execution)
    timeout = 120 if '/parse' in endpoint or '/execute' in endpoint or '/validate' in endpoint else 30

    try:
        print(f"[DEBUG] Making {method} request to {url}")
        print(f"[DEBUG] Headers: {headers}")
        print(f"[DEBUG] Timeout: {timeout}s")

        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout, proxies=proxies)
        elif method == "POST":
            if files:
                print(f"[DEBUG] Uploading files: {list(files.keys())}")
                response = requests.post(url, headers=headers, data=data, files=files, timeout=timeout, proxies=proxies)
            else:
                print(f"[DEBUG] Sending JSON data: {data}")
                response = requests.post(url, headers=headers, json=data, timeout=timeout, proxies=proxies)

        print(f"[DEBUG] Response status: {response.status_code}")
        return response

    except requests.exceptions.Timeout:
        st.error(f"❌ Request timeout after {timeout} seconds. Backend might be slow or processing large data.")
        st.error(f"URL: {url}")
        st.info("💡 Tip: Parsing large files with LLM can take time. Please wait...")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"❌ Cannot connect to backend at {API_URL}")
        st.error(f"Make sure the backend is running on port 8000")
        st.error(f"Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ API Error: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
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
            elif response:
                st.error(f"Login failed (Status {response.status_code}): {response.text}")
            else:
                st.error("Connection error - Backend might not be running")

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

        with st.spinner("📤 Uploading documents..."):
            response = api_call("POST", "/api/documents/upload", data, files)

        if response and response.status_code == 200:
            doc = response.json()
            st.success(f"✅ Document uploaded (ID: {doc['id']})")

            with st.spinner("🔍 Parsing document with LLM (this may take 30-60 seconds for large files)..."):
                parse_response = api_call("POST", f"/api/documents/{doc['id']}/parse", {})

            if parse_response and parse_response.status_code == 200:
                parse_data = parse_response.json()
                st.success("✅ Document parsed successfully")
                st.session_state.current_document_id = doc['id']
                st.session_state.current_query_id = parse_data.get('query_id')
                st.session_state.current_page = "Query & Validation"
                st.info("🔄 Redirecting to validation page...")
                st.rerun()
            elif parse_response:
                st.error(f"❌ Parsing failed (Status {parse_response.status_code})")
                st.error(f"Details: {parse_response.text}")
                st.info("💡 Tip: Large CSV files or complex SLA documents may take longer. Check backend logs for details.")
            else:
                st.error("❌ Parsing failed - Connection error")
                st.warning("⏱️ If you see this, the parsing request timed out. The backend may still be processing. Please wait and try again.")
        elif response:
            st.error(f"❌ Upload failed (Status {response.status_code}): {response.text}")
        else:
            st.error("❌ Upload failed - Connection error")

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
        col2a, col2b = st.columns(2)

        with col2a:
            if st.button("Validate Query", type="primary", use_container_width=True):
                if not query_id:
                    st.error("No query ID found. Please upload and parse a document first.")
                else:
                    st.info(f"Validating query {query_id}...")
                    response = api_call("POST", f"/api/calculations/{query_id}/validate", {})

                    if response and response.status_code == 200:
                        calc_data = response.json()
                        st.session_state.validation_status = calc_data.get('validation_status', 'valid')
                        st.session_state.is_valid = calc_data.get('is_valid', False)
                        st.session_state.query_id = query_id

                        if calc_data.get('is_valid'):
                            st.success(f"✅ Validation Passed!")
                            st.info("Query is valid and ready to execute. Click 'Execute Query' to run it.")
                        else:
                            st.error(f"❌ Validation Failed: {calc_data.get('error', 'Unknown error')}")
                        st.rerun()
                    elif response:
                        error_msg = response.json().get('detail', response.text) if response.status_code != 404 else "Calculation endpoint not found"
                        st.error(f"Validation failed: {error_msg}")
                    else:
                        st.error("Failed to validate query")

        with col2b:
            if st.session_state.get('is_valid', False):
                if st.button("Execute Query", type="secondary", use_container_width=True):
                    st.info(f"Executing query {query_id}...")
                    response = api_call("POST", f"/api/calculations/{query_id}/execute", {})

                    if response and response.status_code == 200:
                        exec_data = response.json()
                        st.session_state.current_calculation_id = exec_data.get('calculation_id')
                        st.session_state.calculation_status = exec_data.get('status')
                        st.success(f"✅ Query Executed Successfully! ({exec_data.get('rows_count', 0)} rows)")
                        st.session_state.current_page = "Dashboard"
                        st.rerun()
                    elif response:
                        error_msg = response.json().get('detail', response.text)
                        st.error(f"Execution failed: {error_msg}")
                    else:
                        st.error("Failed to execute query")

def dashboard_page():
    st.header("📊 Cost Calculation Dashboard")

    if "current_calculation_id" not in st.session_state or not st.session_state.get('current_calculation_id'):
        st.warning("⚠️ No calculation available. Please validate and execute a query first.")
        st.info("Steps: 1) Upload & Parse Document → 2) Validate Query → 3) Execute Query → 4) View Dashboard")
        return

    calc_id = st.session_state.current_calculation_id

    try:
        response = api_call("GET", f"/api/calculations/{calc_id}", None)

        if not response:
            st.error("Failed to connect to API")
            return

        if response.status_code == 404:
            st.error(f"Calculation {calc_id} not found. Please execute a query first.")
            return

        if response.status_code != 200:
            st.error(f"Failed to load calculation: {response.text}")
            return

        calc = response.json()

    except Exception as e:
        st.error(f"Error loading calculation: {str(e)}")
        return

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Calculation ID", calc.get('id', 'N/A'))
    with col2:
        st.metric("Status", calc.get('status', 'unknown').upper())
    with col3:
        st.metric("Rows", calc.get('result_rows', 0))
    with col4:
        st.metric("Columns", len(calc.get('result_columns', [])))

    st.divider()

    # Show SLA Rules if available
    sla_rules = calc.get('sla_rules', [])
    if sla_rules:
        st.subheader("📋 SLA Rules Extracted")
        for i, rule in enumerate(sla_rules):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**{rule.get('rule_id', f'RULE_{i+1}')}**\n{rule.get('metric', 'N/A')}")
            with col2:
                threshold = rule.get('threshold', 'N/A')
                operator = rule.get('threshold_operator', '<')
                st.info(f"**Threshold**\n{operator} {threshold}")
            with col3:
                penalty = rule.get('penalty_percentage', 0)
                st.info(f"**Penalty**\n{penalty}%")
        st.divider()

    # Display results data
    st.subheader("📊 Query Results & Incidents")

    sample_data = calc.get('sample_data', [])
    if sample_data:
        # Calculate penalties and violations
        penalty_columns = [col for col in calc.get('result_columns', []) if 'penalty' in col.lower()]

        # Show detailed results with violations highlighted
        display_data = []
        total_penalty = 0
        violation_count = 0

        for row in sample_data:
            display_row = dict(row)

            # Calculate row penalty
            row_penalty = 0
            for penalty_col in penalty_columns:
                penalty_val = row.get(penalty_col, 0)
                if isinstance(penalty_val, (int, float)) and penalty_val > 0:
                    row_penalty += penalty_val

            if row_penalty > 0:
                violation_count += 1
                total_penalty += row_penalty
                display_row['Total Penalty'] = row_penalty

            display_data.append(display_row)

        # Display the data table
        st.dataframe(display_data, use_container_width=True)

        # Show penalty summary
        st.write("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🚨 Violations Found", violation_count)
        with col2:
            st.metric("💰 Total Penalty", f"${total_penalty:,.2f}")
        with col3:
            st.metric("📊 Rows Analyzed", len(sample_data))
    else:
        st.info("No sample data available")

    st.divider()

    # Display statistics
    st.subheader("📈 Statistics")
    stats = calc.get('summary_statistics', {})

    if stats:
        # Numeric statistics
        if stats.get('numeric'):
            st.write("**Numeric Columns:**")
            numeric_stats = []
            for col_name, col_stats in stats['numeric'].items():
                numeric_stats.append({
                    "Column": col_name,
                    "Min": f"{col_stats.get('min', 'N/A'):.2f}" if isinstance(col_stats.get('min'), (int, float)) else str(col_stats.get('min', 'N/A')),
                    "Max": f"{col_stats.get('max', 'N/A'):.2f}" if isinstance(col_stats.get('max'), (int, float)) else str(col_stats.get('max', 'N/A')),
                    "Mean": f"{col_stats.get('mean', 'N/A'):.2f}" if isinstance(col_stats.get('mean'), (int, float)) else str(col_stats.get('mean', 'N/A'))
                })
            if numeric_stats:
                st.dataframe(numeric_stats, use_container_width=True, hide_index=True)

        # Datetime statistics
        if stats.get('datetime'):
            st.write("**Date/Time Columns:**")
            datetime_stats = []
            for col_name, col_stats in stats['datetime'].items():
                datetime_stats.append({
                    "Column": col_name,
                    "Min Date": str(col_stats.get('min', 'N/A')),
                    "Max Date": str(col_stats.get('max', 'N/A')),
                    "Range (days)": col_stats.get('range_days', 'N/A')
                })
            if datetime_stats:
                st.dataframe(datetime_stats, use_container_width=True, hide_index=True)

        # String statistics
        if stats.get('string'):
            st.write("**String Columns:**")
            string_stats = []
            for col_name, col_stats in stats['string'].items():
                string_stats.append({
                    "Column": col_name,
                    "Unique Values": col_stats.get('unique_values', 'N/A'),
                    "Max Length": col_stats.get('max_length', 'N/A')
                })
            if string_stats:
                st.dataframe(string_stats, use_container_width=True, hide_index=True)
    else:
        st.info("No statistics available")

    st.divider()

    # Display sanity checks
    st.subheader("✓ Data Quality Checks")
    sanity_check = calc.get('sanity_check', {})

    if sanity_check.get('warnings'):
        st.warning(f"⚠️ **Warnings ({len(sanity_check['warnings'])}):**")
        for warning in sanity_check['warnings']:
            st.write(f"- {warning}")
    else:
        st.success("✅ No warnings")

    if sanity_check.get('info'):
        with st.expander("ℹ️ Additional Info"):
            for info in sanity_check['info']:
                st.write(f"- {info}")

    st.divider()

    # Metadata
    st.subheader("📁 Metadata")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Table:** `{calc.get('table_name', 'N/A')}`")
    with col2:
        st.write(f"**Source:** {calc.get('source_file', 'N/A')}")
    with col3:
        st.write(f"**Created:** {calc.get('created_at', 'N/A')}")

    st.divider()

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Go to Approval", type="primary", use_container_width=True, key="to_approval_btn"):
            st.session_state.current_page = "Approval Queue"
            st.rerun()
    with col2:
        if st.button("⟲ Refresh", use_container_width=True, key="refresh_btn"):
            st.rerun()

def approvals_page():
    st.header("✓ Approval Queue")

    if "user" not in st.session_state:
        st.warning("Not logged in")
        return

    if "current_calculation_id" not in st.session_state:
        st.warning("No calculation available. Please execute a query first.")
        return

    calc_id = st.session_state.current_calculation_id

    # Fetch calculation details
    response = api_call("GET", f"/api/calculations/{calc_id}", None)
    if not response or response.status_code != 200:
        st.error(f"❌ Failed to load calculation {calc_id}")
        st.info("Try going back to Dashboard and refreshing")
        if st.button("← Back to Dashboard"):
            st.session_state.current_page = "Dashboard"
            st.rerun()
        return

    calc = response.json()

    st.subheader(f"📋 Calculation #{calc_id} - Pending Approval")

    # Display calculation summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Status", calc.get('status', 'unknown').upper())
    with col2:
        st.metric("Rows Analyzed", calc.get('result_rows', 0))
    with col3:
        st.metric("Columns", len(calc.get('result_columns', [])))
    with col4:
        st.metric("Table", calc.get('table_name', 'N/A'))

    st.divider()

    # Show detailed results
    st.subheader("📊 Query Results Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Source File:** `{calc.get('source_file', 'N/A')}`")
        st.write(f"**Total Rows:** {calc.get('result_rows', 0)}")
        st.write(f"**Columns:** {', '.join(calc.get('result_columns', []))}")
    with col2:
        stats = calc.get('summary_statistics', {})
        if stats:
            st.write("**Data Statistics Available:** ✅")
            if 'numeric' in stats and stats['numeric']:
                st.write(f"  - Numeric columns: {len(stats['numeric'])}")
            if 'datetime' in stats and stats['datetime']:
                st.write(f"  - Date columns: {len(stats['datetime'])}")
            if 'string' in stats and stats['string']:
                st.write(f"  - String columns: {len(stats['string'])}")

    st.divider()

    # Show SLA rules in approval context
    sla_rules = calc.get('sla_rules', [])
    if sla_rules:
        st.subheader("📋 SLA Rules Being Applied")
        for i, rule in enumerate(sla_rules, 1):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Rule {i}:** {rule.get('rule_id', 'N/A')}")
            with col2:
                st.write(f"**Metric:** {rule.get('metric', 'N/A')}")
            with col3:
                st.write(f"**Penalty:** {rule.get('penalty_percentage', 0)}%")
            st.caption(rule.get('description', 'N/A'))
    else:
        st.info("No SLA rules extracted")

    st.divider()

    # Approval decision section
    st.subheader("⚖️ Approval Decision")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        approval_comment = st.text_area(
            "📝 Comments (optional)",
            placeholder="Add approval comments, notes, or reasons...",
            height=100
        )
    with col2:
        st.write("**Approver:**")
        st.info(f"👤 {st.session_state.user or 'Admin'}")
        st.write(f"**Created:** {calc.get('created_at', 'N/A')[:10]}")

    st.divider()

    # Approval decision buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ APPROVE", type="primary", use_container_width=True, key="approve_btn"):
            st.session_state.approval_status = "approved"
            st.session_state.approval_comment = approval_comment
            st.session_state.approval_by = st.session_state.user or "Admin"
            st.success("✅ Approved! Generating proof report...")
            st.session_state.current_page = "Proof Viewer"
            import time
            time.sleep(1)
            st.rerun()

    with col2:
        if st.button("❌ REJECT", type="secondary", use_container_width=True, key="reject_btn"):
            st.session_state.approval_status = "rejected"
            st.session_state.approval_comment = approval_comment
            st.warning(f"❌ Rejected by {st.session_state.user or 'Admin'}")
            if approval_comment:
                st.info(f"**Reason:** {approval_comment}")
            st.session_state.current_page = "Upload & Parse"
            import time
            time.sleep(1)
            st.rerun()

    with col3:
        if st.button("⏳ HOLD", use_container_width=True, key="hold_btn"):
            st.info("⏳ Calculation held for further review. It will remain in the approval queue.")
            st.caption("You can come back to this later or ask another approver to review.")

    with col4:
        if st.button("← BACK", use_container_width=True, key="back_btn"):
            st.session_state.current_page = "Dashboard"
            st.rerun()

def proofs_page():
    st.header("📋 SLA Recovery Proof Report")

    if "current_calculation_id" not in st.session_state:
        st.warning("No calculation available")
        return

    calc_id = st.session_state.current_calculation_id

    # Fetch calculation details
    response = api_call("GET", f"/api/calculations/{calc_id}", None)
    if not response or response.status_code != 200:
        st.error(f"Failed to load calculation {calc_id}")
        return

    calc = response.json()

    # Get approval info from session
    approval_status = st.session_state.get('approval_status', 'approved')
    approval_by = st.session_state.get('approval_by', 'Unknown')
    approval_comment = st.session_state.get('approval_comment', '')

    # Report header
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Report ID", calc.get('id', 'N/A'))
    with col2:
        st.metric("Status", "✅ APPROVED" if approval_status == "approved" else "❌ REJECTED")
    with col3:
        st.metric("Approved By", approval_by)
    with col4:
        st.metric("Generated", calc.get('created_at', 'N/A')[:10])

    st.divider()

    # Executive Summary
    st.subheader("📊 Executive Summary")

    penalty_columns = [col for col in calc.get('result_columns', []) if 'penalty' in col.lower()]
    total_penalty = 0
    violation_count = 0

    for row in calc.get('sample_data', []):
        for penalty_col in penalty_columns:
            penalty_val = row.get(penalty_col, 0)
            if isinstance(penalty_val, (int, float)) and penalty_val > 0:
                violation_count += 1
                total_penalty += penalty_val

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚨 Total Violations", violation_count)
    with col2:
        st.metric("💰 Total Penalty", f"${total_penalty:,.2f}")
    with col3:
        st.metric("📊 Records Analyzed", len(calc.get('sample_data', [])))
    with col4:
        violation_rate = (violation_count / max(len(calc.get('sample_data', [])), 1)) * 100
        st.metric("📈 Violation Rate", f"{violation_rate:.1f}%")

    st.divider()

    # SLA Rules Violated
    st.subheader("⚠️ SLA Rules Violated")
    sla_rules = calc.get('sla_rules', [])

    if sla_rules:
        for rule in sla_rules:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**{rule.get('rule_id', 'N/A')}**\n{rule.get('metric', 'N/A')}")
            with col2:
                st.write(f"**Threshold**\n{rule.get('threshold_operator', '<')} {rule.get('threshold', 'N/A')}")
            with col3:
                st.write(f"**Penalty**\n{rule.get('penalty_percentage', 0)}% ({rule.get('penalty_type', 'N/A')})")

            with st.expander(f"📖 {rule.get('description', 'N/A')}"):
                st.write(f"- **Period:** {rule.get('applicable_period', 'N/A')}")
    else:
        st.info("No SLA rules found")

    st.divider()

    # Detailed Incident Report
    st.subheader("🔍 Detailed Incident Report")

    violation_details = []
    for idx, row in enumerate(calc.get('sample_data', []), 1):
        row_penalty = 0
        violated_rules = []

        for penalty_col in penalty_columns:
            penalty_val = row.get(penalty_col, 0)
            if isinstance(penalty_val, (int, float)) and penalty_val > 0:
                row_penalty += penalty_val
                if 'uptime' in penalty_col.lower():
                    violated_rules.append('Uptime SLA')
                elif 'response' in penalty_col.lower():
                    violated_rules.append('Response Time SLA')
                elif 'error' in penalty_col.lower():
                    violated_rules.append('Error Rate SLA')

        violation_details.append({
            "Date": str(row.get('incident_date', 'N/A')),
            "Violated Rules": ', '.join(violated_rules) if violated_rules else 'No violations',
            "Penalty": f"${row_penalty:,.2f}" if row_penalty > 0 else "$0",
            "Status": "🚨 VIOLATION" if row_penalty > 0 else "✅ Compliant"
        })

    st.dataframe(violation_details, use_container_width=True, hide_index=True)

    st.divider()

    # Approval Section
    st.subheader("✍️ Approval Authority")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Status:** {approval_status.upper()}")
        st.write(f"**Approved By:** {approval_by}")
        if approval_comment:
            st.write(f"**Comments:** {approval_comment}")
    with col2:
        from datetime import datetime
        st.write(f"**Date & Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"**Document Type:** SLA Recovery Proof")

    st.divider()

    # Footer
    st.success("✅ This is an official SLA Recovery Report signed and approved for compliance.")
    st.info("📧 This report can be exported, printed, or shared with stakeholders.")

    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.current_page = "Dashboard"
            st.rerun()
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = "Upload & Parse"
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
            st.title(f"👤 {st.session_state.user}")

            pages = ["Upload & Parse", "Query & Validation", "Dashboard", "Approval Queue", "Proof Viewer"]

            # Get current index
            try:
                current_index = pages.index(st.session_state.current_page)
            except ValueError:
                current_index = 0

            selected_page = st.radio("Navigation", pages, index=current_index, label_visibility="collapsed")

            # Only update if user manually selected (don't override programmatic changes)
            if selected_page != st.session_state.current_page:
                st.session_state.current_page = selected_page

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
