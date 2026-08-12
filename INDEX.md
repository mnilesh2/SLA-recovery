# SLA Recovery Audit System - Complete Index

This document provides a complete guide to all files and documentation in this project.

## 📚 Documentation (Start Here)

Read in this order for best understanding:

1. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** ← **START HERE**
   - High-level overview of what was built
   - What's included vs. what's not (yet)
   - Architecture summary
   - Key features and capabilities

2. **[SETUP.md](SETUP.md)**
   - Step-by-step installation guide
   - Dependency installation
   - Configuration instructions
   - Verification checklist
   - Troubleshooting common issues

3. **[QUICKSTART.md](QUICKSTART.md)**
   - How to run the system (backend + frontend)
   - Default login credentials
   - Walking through the pipeline with sample data
   - Customization options
   - API endpoints reference

4. **[readme.md](readme.md)**
   - Complete system specification (original)
   - Enterprise deployment architecture
   - Production Kubernetes/Helm deployment
   - Full technology stack for production
   - Security, compliance, and monitoring details
   - Cost optimization strategies
   - Runbooks and incident response

5. **[INDEX.md](INDEX.md)** (this file)
   - File organization guide
   - Component descriptions

## 🗂️ Project Structure

```
Caps-EXL/
├── 📖 Documentation
│   ├── readme.md                 # Original full specification
│   ├── PROJECT_SUMMARY.md        # MVP implementation overview
│   ├── SETUP.md                  # Installation guide
│   ├── QUICKSTART.md             # How to run and use
│   └── INDEX.md                  # This file
│
├── ⚙️ Configuration
│   ├── requirements.txt           # Python dependencies (18 packages)
│   ├── .env.example               # Environment configuration template
│   └── .env                       # Created on first run
│
├── 🔧 Backend (FastAPI)
│   └── backend/
│       ├── main.py               # FastAPI app entry point
│       ├── config.py             # Load settings from .env
│       ├── database.py           # SQLAlchemy setup & ORM
│       ├── models.py             # 10 database models
│       ├── schemas.py            # Pydantic request/response schemas
│       ├── auth.py               # JWT auth + RBAC
│       ├── prompts.py            # Default LLM prompt + resolution
│       ├── seed.py               # Database initialization
│       ├── __init__.py           # Package marker
│       │
│       ├── services/             # Core business logic
│       │   ├── document_parser.py    # LLM parsing (OpenAI with mock fallback)
│       │   ├── math_engine.py        # DuckDB validation & execution
│       │   ├── cost_engine.py        # Cost aggregation
│       │   ├── audit_proof.py        # Proof generation
│       │   ├── file_storage.py       # File upload & text extraction
│       │   └── __init__.py
│       │
│       └── routers/              # API endpoints
│           ├── auth_router.py        # POST /auth/login, /register
│           ├── documents.py          # POST /upload, GET /{id}, POST /{id}/parse
│           ├── calculations.py       # GET /{id}, POST /{id}/validate
│           ├── approvals.py          # POST /{id}/approve, GET /pending
│           ├── proofs.py             # GET /{id}, GET /search
│           ├── cost_types.py         # GET /
│           └── __init__.py
│
├── 🎨 Frontend (Streamlit)
│   └── frontend/
│       └── app.py                # Complete Streamlit UI (500+ lines)
│           ├── Login page
│           ├── Upload & Parse page
│           ├── Query & Validation page
│           ├── Dashboard page
│           ├── Approval Queue page
│           └── Proof Viewer page
│
├── 📊 Sample Data
│   └── sample_data/
│       ├── sample_sla.txt        # Example SLA contract (complete with all clauses)
│       └── sample_billing_data.csv  # Example service metrics (31 days)
│
└── 📁 Auto-Created Directories (on first run)
    ├── uploads/                  # Document uploads
    ├── __pycache__/              # Python cache
    └── sla_recovery.db           # SQLite database
```

## 🔑 Key Files by Purpose

### Core Pipeline Files

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `backend/main.py` | FastAPI app startup | `app`, startup_event, health_check |
| `backend/models.py` | Database schema | 10 models: User, Document, Query, Calculation, etc. |
| `backend/prompts.py` | LLM prompts | `DEFAULT_PROMPT`, `resolve_prompt()` |
| `services/document_parser.py` | Document → SQL | `parse_document_with_llm()`, mock responses |
| `services/math_engine.py` | Validation | `MathEngine` class, EXPLAIN validation, sanity checks |
| `services/cost_engine.py` | Cost aggregation | `CostEngine` class, cost type extraction |
| `services/audit_proof.py` | Proof generation | `AuditProofGenerator` class |

### API Routes

| Router | Endpoints | Purpose |
|--------|-----------|---------|
| `auth_router.py` | `/api/auth/login`, `/register` | Authentication |
| `documents.py` | `/api/documents/upload`, `/{id}`, `/{id}/parse` | Document handling |
| `calculations.py` | `/api/calculations/{id}`, `/{id}/validate` | Query validation |
| `approvals.py` | `/api/approvals/{id}/approve`, `/pending` | HITL approval |
| `proofs.py` | `/api/proofs/{id}`, `/search` | Proof retrieval |
| `cost_types.py` | `/api/cost-types/` | Cost type listing |

### Database Models

| Model | Purpose | Key Fields |
|-------|---------|-----------|
| `User` | User accounts & roles | username, hashed_password, role |
| `Document` | Uploaded SLA documents | filename, file_path, document_text, data_csv_path |
| `CustomPrompt` | User-defined prompts | prompt_text, name |
| `Query` | Generated SQL queries | sql_query, extracted_terms, prompt_used, used_custom_prompt |
| `Calculation` | Query results & validation | validation_status, validation_errors, raw_result_rows |
| `CostBreakdown` | Cost aggregation | cost_type, original_value, calculated_value |
| `Approval` | HITL decisions | status, comment, approver_id |
| `Proof` | Audit proofs | proof_data (JSON) |
| `AuditLog` | Action history | action, entity_type, entity_id, details |
| `CustomPrompt` | User prompts | prompt_text, user_id |

### Configuration Files

| File | Purpose | When Used |
|------|---------|-----------|
| `.env.example` | Template for config | Copy to `.env` to customize |
| `.env` | Environment variables | Read by `config.py` |
| `requirements.txt` | Python dependencies | `pip install -r requirements.txt` |

## 📋 How to Use This Documentation

### For Getting Started (5 minutes)
1. Read: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) (overview)
2. Run: [SETUP.md](SETUP.md) (installation)
3. Run: [QUICKSTART.md](QUICKSTART.md) (first use)

### For Deployment (1-2 hours)
1. Read: [readme.md](readme.md) (full spec)
2. Copy Kubernetes configs from readme
3. Follow production deployment section

### For Development (extending system)
1. Study: Backend architecture in [backend/main.py](backend/main.py)
2. Add routes to [backend/routers/](backend/routers/)
3. Add models to [backend/models.py](backend/models.py)
4. Add services to [backend/services/](backend/services/)

### For Troubleshooting
1. Check: [SETUP.md troubleshooting section](SETUP.md#troubleshooting-setup-issues)
2. Check: [QUICKSTART.md troubleshooting section](QUICKSTART.md#troubleshooting)
3. Run: Syntax checks: `python -m py_compile backend/*.py`

## 🚀 Quick Reference

### Installation
```bash
pip install -r requirements.txt
cp .env.example .env  # Optional: customize if needed
```

### Running
```bash
# Terminal 1: Backend
uvicorn backend.main:app --reload

# Terminal 2: Frontend
streamlit run frontend/app.py
```

### Login
- **Username**: admin
- **Password**: admin123

### Testing Pipeline
```bash
# Use sample data
# Upload: sample_data/sample_sla.txt
# Upload: sample_data/sample_billing_data.csv
# Follow the UI through: Parse → Validate → Dashboard → Approve → View Proof
```

## 📊 Component Relationships

```
┌─────────────────────────────────────────────────────┐
│                Streamlit Frontend                   │
│   (Login, Upload, Validate, Dashboard, Approve)     │
└──────────────────────┬──────────────────────────────┘
                       │
                       │ HTTP Requests
                       │
┌──────────────────────▼──────────────────────────────┐
│              FastAPI Backend API                    │
│  (6 routers × ~2-3 endpoints each)                  │
└──────┬──────────────┬─────────────┬────────────────┘
       │              │             │
       │ ORM          │ Services    │
       │              │             │
    SQLAlchemy    Document Parser  Audit Log
    10 Models     Math Engine      Auth
                  Cost Engine
                  Audit Proof
                  File Storage
                       │
                       │
┌──────────────────────▼──────────────────────────────┐
│           Data Storage & Processing                 │
│                                                     │
│  SQLite Database      CSV Input      LLM API       │
│  (sla_recovery.db)    (Data)         (OpenAI)      │
│                                                     │
│  DuckDB              File Storage                  │
│  (SQL Validation)    (uploads/)                    │
└─────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

```
User (Streamlit)
    ↓
Upload SLA Document + Data CSV
    ↓ [documents.py]
Validate file, extract text, store Document record
    ↓ [documents.py]
Parse with LLM (document_parser.py)
    ↓
Extract terms, Generate SQL, Store Query record
    ↓ [calculations.py]
Validate with DuckDB (math_engine.py)
    ├→ Syntax check (EXPLAIN)
    ├→ Column check (schema)
    ├→ Execute query
    └→ Sanity checks
    ↓
Aggregate costs (cost_engine.py)
    ↓
Store Calculation + CostBreakdown records
    ↓ [Frontend Dashboard]
Display costs, chart, breakdown
    ↓ [approvals.py]
HITL approval decision
    ├→ APPROVED
    │   ├→ Generate proof (audit_proof.py)
    │   └→ Store Proof record
    │
    └→ REJECTED
        └→ Return to document refinement
    ↓
Audit log entry (all actions)
```

## 📁 File Locations Summary

| What | Where | Lines |
|------|-------|-------|
| API Entry Point | `backend/main.py` | 40 |
| Database Models | `backend/models.py` | 170 |
| Authentication | `backend/auth.py` | 70 |
| Document Parser | `backend/services/document_parser.py` | 50 |
| Math Engine | `backend/services/math_engine.py` | 120 |
| Streamlit UI | `frontend/app.py` | 500+ |
| Sample Data | `sample_data/` | 35 + 31 |
| **Total Python** | **backend/ + frontend/** | **~2500 lines** |

## ✅ Verification Checklist

After installation, verify:

- [ ] Python 3.10+ installed: `python --version`
- [ ] Dependencies installed: `pip list | grep fastapi`
- [ ] Backend syntax OK: `python -m py_compile backend/main.py`
- [ ] Frontend syntax OK: `python -m py_compile frontend/app.py`
- [ ] Backend runs: `uvicorn backend.main:app --reload` (Ctrl+C to stop)
- [ ] Frontend runs: `streamlit run frontend/app.py` (Ctrl+C to stop)
- [ ] Can login: admin / admin123
- [ ] Sample data accessible: `ls sample_data/`
- [ ] Can walk through pipeline: Upload → Parse → Validate → Approve

## 🎯 Next Steps

1. **Learn the System**
   - Start with PROJECT_SUMMARY.md
   - Follow QUICKSTART.md with sample data
   
2. **Customize**
   - Edit `backend/prompts.py` for your SLA terminology
   - Modify cost columns in `services/cost_engine.py`
   - Add new cost types
   
3. **Scale**
   - Follow production deployment in readme.md
   - Switch to PostgreSQL (update DATABASE_URL)
   - Add Kubernetes configs (templates in readme)
   - Set up monitoring (Prometheus/ELK from readme)

4. **Deploy**
   - Build Docker images (Dockerfiles in readme)
   - Create Kubernetes manifests (examples in readme)
   - Configure Helm charts (in readme)
   - Set up CI/CD pipeline (GitHub Actions example in readme)

## 🆘 Getting Help

| Issue | Reference |
|-------|-----------|
| "How do I install?" | → [SETUP.md](SETUP.md) |
| "How do I run the system?" | → [QUICKSTART.md](QUICKSTART.md) |
| "What's the architecture?" | → [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) |
| "How do I deploy to production?" | → [readme.md](readme.md) (section: Production Deployment) |
| "What files were created?" | → [INDEX.md](INDEX.md) (this file) |
| "How does the pipeline work?" | → [readme.md](readme.md) (section: System Architecture & Data Flow) |
| "What's the API?" | → [QUICKSTART.md](QUICKSTART.md) (section: API Endpoints) |

## 📄 File Manifest

**Complete list of all created files:**

```
✓ requirements.txt                    (18 packages)
✓ .env.example                        (config template)
✓ INDEX.md                            (this file)
✓ PROJECT_SUMMARY.md                  (overview)
✓ SETUP.md                            (installation)
✓ QUICKSTART.md                       (usage guide)

Backend (15 files):
✓ backend/__init__.py
✓ backend/main.py
✓ backend/config.py
✓ backend/database.py
✓ backend/models.py
✓ backend/schemas.py
✓ backend/auth.py
✓ backend/prompts.py
✓ backend/seed.py
✓ backend/services/__init__.py
✓ backend/services/document_parser.py
✓ backend/services/math_engine.py
✓ backend/services/cost_engine.py
✓ backend/services/audit_proof.py
✓ backend/services/file_storage.py
✓ backend/routers/__init__.py
✓ backend/routers/auth_router.py
✓ backend/routers/documents.py
✓ backend/routers/calculations.py
✓ backend/routers/approvals.py
✓ backend/routers/proofs.py
✓ backend/routers/cost_types.py

Frontend (1 file):
✓ frontend/app.py

Sample Data (2 files):
✓ sample_data/sample_sla.txt
✓ sample_data/sample_billing_data.csv

Auto-Created (on first run):
✓ sla_recovery.db                     (SQLite database)
✓ uploads/                            (directory)
```

**Total: 32 files created + 1 doc included (readme.md) = 33 files**

---

**You're all set!** Start with [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) → [SETUP.md](SETUP.md) → [QUICKSTART.md](QUICKSTART.md).
