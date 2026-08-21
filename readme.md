# SLA Recovery Audit System

Universal system for parsing SLA documents, generating SQL queries, executing analysis, and creating official proof reports.

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env: LLM_PROVIDER, OPENROUTER_API_KEY, LLM_MODEL

# 3. Start backend
python -m uvicorn backend.main:app --reload

# 4. Start frontend (new terminal)
cd frontend
streamlit run app.py

# 5. Access
# Frontend: http://localhost:8501
# API: http://localhost:8000/docs
```

## Directory Structure

```
SLA-recovery/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration
│   ├── database.py, auth.py      # Database & Auth
│   ├── models.py, prompts.py     # ORM & Prompts
│   ├── services/
│   │   ├── llm_service.py        # LLM integration
│   │   ├── document_parser.py    # Document parsing
│   │   ├── csv_utils.py          # CSV schema extraction
│   │   └── math_engine.py        # SQL execution
│   └── routers/
│       ├── auth.py, documents.py
│       ├── queries.py
│       └── calculations.py
│
├── frontend/
│   └── app.py                     # Streamlit UI
│
├── uploads/                       # Uploaded files
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Pipeline Flow

```
1. UPLOAD & PARSE
   User uploads SLA document + CSV
   ↓
   LLM extracts: Rules, SQL query, violations
   
2. QUERY & VALIDATION
   Review generated SQL
   ↓
   Validate syntax & columns
   
3. EXECUTION
   Run SQL on CSV data
   ↓
   Calculate statistics & penalties
   
4. DASHBOARD
   Display violations & penalties
   ↓
   Button: "Go to Approval"
   
5. APPROVAL QUEUE
   Admin reviews calculation
   ↓
   Options: ✅ APPROVE | ❌ REJECT | ⏳ HOLD
   
6. PROOF REPORT
   Generate official signed report
   ├─ Report ID & approval status
   ├─ Executive summary
   ├─ SLA rules violated
   ├─ Incident breakdown
   └─ Approver signature
```

## Key Features

- **Universal** - Works with any CSV and any SLA type
- **Type-Safe** - Validates columns and data types
- **Smart** - Detects numeric, date, string, boolean columns
- **Approval Workflow** - Multi-step with official reports
- **OpenRouter Compatible** - ChatGPT or Claude via OpenRouter

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI, SQLAlchemy, DuckDB |
| Frontend | Streamlit |
| Database | SQLite/PostgreSQL |
| LLM | OpenRouter (ChatGPT/Claude) |
| Data | Pandas, NumPy |

## Environment Variables

```bash
# .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
LLM_MODEL=openai/gpt-4-turbo
DATABASE_URL=sqlite:///./sla_recovery.db
API_HOST=127.0.0.1
API_PORT=8000
SECRET_KEY=your_secret_key
```

## API Endpoints

```
POST   /api/auth/login                    # Login
POST   /api/documents/upload              # Upload
POST   /api/documents/{id}/parse          # Parse with LLM
POST   /api/calculations/{id}/validate    # Validate SQL
POST   /api/calculations/{id}/execute     # Execute SQL
GET    /api/calculations/{id}             # Get results
```

## Supported Data Types

| Type | Examples | Statistics |
|------|----------|-----------|
| Numeric | int, float | min, max, mean, std |
| Date | timestamp, datetime | range, days |
| String | text | unique count, length |
| Boolean | true/false | value counts |

## Common Issues

| Issue | Solution |
|-------|----------|
| Column not found | Check CSV schema on validation page |
| LLM timeout | Increase frontend timeout (120s default) |
| Database errors | Delete sla_recovery.db and restart |
| Type mismatch | Review data types in dashboard |

## Development

```bash
# Format code
pip install black
black backend/ frontend/

# Install dev dependencies
pip install pytest

# Run tests
pytest tests/
```

## Production Deployment

For production deployment:
1. Use PostgreSQL instead of SQLite
2. Set up environment variables securely
3. Use a production ASGI server (Gunicorn + Uvicorn)
4. Enable HTTPS/TLS
5. Set up monitoring and logging
6. Configure database backups
7. Use managed services (RDS, ElastiCache, S3)

## Support

- Check logs for errors
- Review API documentation at `/api/docs`
- Check CSV schema on validation page for column issues
- Verify LLM API key is configured

## License

Internal Use Only
