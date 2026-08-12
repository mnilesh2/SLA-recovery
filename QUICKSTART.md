# SLA Recovery Audit System - Quick Start Guide

This is a working implementation of the SLA Recovery Audit Proof Generation System described in `readme.md`. It includes a FastAPI backend, Streamlit frontend, DuckDB-based Math Engine, and SQLite database for local development.

## What's Included

✅ **Backend (FastAPI)**
- Document upload and parsing with OpenAI integration (with mock fallback)
- LLM-based SQL query generation
- DuckDB Math Engine for validation and execution
- Cost calculation engine
- Audit proof generation
- Role-based access control (Reviewer, Approver, Admin)
- Complete audit logging

✅ **Frontend (Streamlit)**
- User authentication (login/logout)
- Document upload interface
- Query validation dashboard
- Cost breakdown visualization
- HITL approval workflow
- Audit proof viewer

✅ **Database**
- SQLite (local development) - easily swappable for PostgreSQL
- Complete schema for documents, queries, calculations, approvals, proofs, audit logs

✅ **Sample Data**
- Sample SLA contract (sample_sla.txt)
- Sample billing data (sample_billing_data.csv)

## Prerequisites

- Python 3.10+
- pip

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

The `.env` file contains default values suitable for local development. To use OpenAI for document parsing (optional):

```bash
export OPENAI_API_KEY="sk-your-openai-api-key"
```

If `OPENAI_API_KEY` is not set, the system will use mock responses for testing.

## Running the System

### 3. Start the Backend API

In one terminal window:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

The system automatically:
- Creates the SQLite database on first run
- Seeds an admin user: **username:** `admin`, **password:** `admin123`

### 4. Start the Frontend

In another terminal window:

```bash
streamlit run frontend/app.py
```

The UI will open at `http://localhost:8501`

## Using the System

### Default Login Credentials

**Username:** `admin`  
**Password:** `admin123`

### Walking Through the Pipeline

1. **Upload & Parse** (`Upload & Parse` page)
   - Upload a sample SLA document and data CSV
   - Optionally provide a custom prompt
   - System parses the document and generates SQL using LLM

2. **Validate Query** (`Query & Validation` page)
   - Review the generated SQL query
   - Click "Validate Query" to execute validation
   - Math Engine checks syntax, columns, types, and runs sanity checks

3. **Review Costs** (`Dashboard` page)
   - View calculated costs by type (monetary, credits, units, custom metrics)
   - See cost breakdown table and visualization
   - Original vs. final cost comparison

4. **Approve/Reject** (`Approval Queue` page)
   - Requires Approver or Admin role
   - Add approval comments
   - Approve → generates audit proof
   - Reject → returns to refinement

5. **View Proof** (`Proof Viewer` page)
   - Review the complete audit proof
   - Download as JSON for compliance documentation

### Testing with Sample Data

Use the sample files included:

```bash
# In the Streamlit UI:
# 1. Click "Upload & Parse"
# 2. Upload: sample_data/sample_sla.txt
# 3. Upload: sample_data/sample_billing_data.csv
# 4. Click "Upload & Parse"
# 5. Click "Validate Query"
# 6. Review dashboard
# 7. Click "Proceed to Approval"
# 8. Add comment and click "Approve"
# 9. View the generated proof
```

## Architecture Overview

### Backend Components

```
backend/
├── main.py              # FastAPI app entry point
├── config.py            # Configuration settings
├── database.py          # SQLAlchemy setup
├── models.py            # Database models
├── schemas.py           # Pydantic request/response schemas
├── auth.py              # Authentication & authorization
├── prompts.py           # LLM prompts (default + custom)
├── seed.py              # Database initialization
├── services/
│   ├── document_parser.py    # OpenAI integration (with mock mode)
│   ├── math_engine.py        # DuckDB validation & execution
│   ├── cost_engine.py        # Cost type aggregation
│   ├── audit_proof.py        # Proof generation
│   └── file_storage.py       # File upload handling
└── routers/
    ├── auth_router.py        # Login/registration
    ├── documents.py          # Document upload & parsing
    ├── calculations.py       # Query validation
    ├── approvals.py          # HITL approval
    ├── proofs.py             # Proof viewing/search
    └── cost_types.py         # Cost type queries
```

### Data Flow

```
User Upload
    ↓
Document Parser (LLM: OpenAI or mock)
    ↓
Generated SQL Query
    ↓
Math Engine (DuckDB)
    ├→ Syntax validation (EXPLAIN)
    ├→ Column/type checking
    ├→ Query execution
    └→ Sanity checks
    ↓
Validation Result (PASSED/FAILED)
    ↓
[IF PASSED] Cost Engine
    ├→ Extract cost columns
    ├→ Aggregate by type
    └→ Create breakdowns
    ↓
Dashboard Display
    ↓
HITL Approval
    ├→ [APPROVED] Audit Proof Generator
    │           ↓
    │       Complete Proof (clauses, SQL, evidence, costs, signer, timestamp)
    │
    └→ [REJECTED] Return for refinement
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Documents
- `POST /api/documents/upload` - Upload SLA document + data CSV
- `GET /api/documents/{id}` - Get document details
- `POST /api/documents/{id}/parse` - Parse document with LLM

### Calculations
- `GET /api/calculations/{id}` - Get calculation details
- `POST /api/calculations/{query_id}/validate` - Run validation with Math Engine

### Approvals
- `POST /api/approvals/{calculation_id}/approve` - Approve or reject with HITL
- `GET /api/approvals/pending` - Get pending approvals queue

### Proofs
- `GET /api/proofs/{id}` - Get proof details
- `GET /api/proofs/search` - Search proofs by criteria

### Other
- `GET /api/cost-types` - List all cost types
- `GET /health` - Health check

## Customization

### Using Real OpenAI API

Set your API key:
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

The system will use real API calls instead of mock responses.

### Adding Custom Prompts

Users can provide custom prompts when uploading documents. The system:
1. Accepts custom prompt (optional text field)
2. Uses custom prompt if provided, default prompt if not
3. Saves custom prompts to history for reuse

### Using PostgreSQL Instead of SQLite

Edit `backend/config.py`:
```python
database_url: str = "postgresql://user:password@localhost:5432/sla_recovery"
```

### Scaling to Production

For production deployment, see the full `readme.md` which includes:
- Kubernetes deployment configs
- Helm charts
- Docker containerization
- Monitoring & observability setup
- Security best practices
- High availability configuration
- CI/CD pipeline examples

## Database Schema

The system tracks:
- **Users** - login credentials, roles
- **Documents** - uploaded SLA documents, metadata
- **CustomPrompts** - user-defined prompts for specialized SLA types
- **Queries** - generated SQL queries with prompt provenance
- **Calculations** - query execution results and validation status
- **CostBreakdowns** - cost aggregation by type (monetary, credits, units, custom)
- **Approvals** - HITL approval decisions and comments
- **Proofs** - complete audit proofs with all supporting evidence
- **AuditLogs** - immutable record of all actions (per compliance requirements)

## Troubleshooting

### "Failed to load CSV" error
- Ensure the CSV file is properly formatted
- Check that column names match what the SQL query expects
- Verify file is valid UTF-8 encoding

### "Invalid token" when calling API
- Token may have expired (30-minute default)
- Log out and log back in from the Streamlit UI

### Database locked error
- Only one connection to SQLite at a time
- Restart both backend and frontend
- Consider switching to PostgreSQL for concurrent access

### Mock LLM responses
- If `OPENAI_API_KEY` is not set, the system uses deterministic mock responses
- Useful for testing without API costs
- Set the environment variable to use real API

## Project Structure

```
Caps-EXL/
├── readme.md                  # Full system specification
├── QUICKSTART.md              # This file
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── backend/                   # FastAPI backend
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── prompts.py
│   ├── seed.py
│   ├── services/
│   └── routers/
├── frontend/                  # Streamlit UI
│   └── app.py
├── sample_data/               # Test data
│   ├── sample_sla.txt
│   └── sample_billing_data.csv
└── uploads/                   # Generated on first run (uploaded documents)
```

## Next Steps

After getting the system running locally:

1. **Test with your own data:**
   - Replace sample SLA with your actual contracts
   - Update billing data with your actual service metrics

2. **Customize the default prompt:**
   - Edit `backend/prompts.py` to match your SLA terminology
   - Test with different document formats

3. **Add more cost types:**
   - Modify the cost column naming conventions in `services/cost_engine.py`
   - Add support for custom metrics in `CostBreakdown` model

4. **Deploy to production:**
   - Follow the deployment section in `readme.md`
   - Set up Kubernetes, monitoring, and disaster recovery
   - Configure real database, object storage, and job queues

## Support

Refer to `readme.md` for:
- Complete system architecture
- Production deployment guide
- Security & compliance details
- Performance tuning guidelines
- Disaster recovery procedures

## License & Notes

This is an MVP implementation for demonstration and development purposes. The full production specification is in `readme.md`.
