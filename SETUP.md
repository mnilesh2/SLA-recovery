# Installation & Setup Guide

## System Requirements

- **Python**: 3.10 or higher
- **OS**: Linux, macOS, or Windows
- **RAM**: 2GB minimum (4GB recommended)
- **Disk Space**: 500MB for dependencies + uploads

## Step 1: Install Python Dependencies

```bash
# Navigate to project directory
cd Caps-EXL

# Install all required packages
pip install -r requirements.txt
```

This installs:
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **DuckDB** - SQL execution engine
- **Pydantic** - Data validation
- **Streamlit** - Frontend framework
- **OpenAI** - LLM integration (optional)
- Plus testing, auth, and utility libraries

### Troubleshooting Installation

If you encounter issues:

```bash
# Use a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Then install requirements
pip install -r requirements.txt
```

## Step 2: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env if needed (optional for local development)
# Default values work out-of-the-box for local testing
```

### Optional: Enable OpenAI API

To use real LLM parsing instead of mock responses:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-actual-key-here"

# Or add it to .env file:
# OPENAI_API_KEY=sk-your-actual-key-here
```

## Step 3: Start the Backend API

Open a terminal and run:

```bash
uvicorn backend.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete
```

The backend automatically:
- Creates SQLite database: `sla_recovery.db`
- Initializes all tables
- Seeds admin user: `admin` / `admin123`

### Verify Backend is Running

Open another terminal:
```bash
curl http://localhost:8000/health
# Expected response: {"status":"healthy"}
```

Or visit: http://localhost:8000/docs for interactive API documentation

## Step 4: Start the Frontend

Open a new terminal and run:

```bash
streamlit run frontend/app.py
```

Expected output:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://xxx.xxx.x.xxx:8501
```

The browser will automatically open to the Streamlit interface.

## Step 5: Log In

Use the default admin credentials:

- **Username**: `admin`
- **Password**: `admin123`

## Complete Setup Verification

Check all components are working:

```bash
# 1. Verify Python
python --version  # Should be 3.10+

# 2. Verify requirements installed
python -c "import fastapi; import streamlit; import duckdb; print('✓ All packages installed')"

# 3. Check database exists (after starting backend once)
ls -la sla_recovery.db

# 4. Test API connectivity
curl -s http://localhost:8000/health | grep healthy && echo "✓ API running"

# 5. Check uploads directory created
ls -la uploads/
```

## Directory Structure After Setup

```
Caps-EXL/
├── sla_recovery.db           # Created on first run
├── uploads/                  # Created on first run
│   ├── sample_sla.txt
│   └── sample_billing_data.csv
├── .env                      # Environment config
├── requirements.txt
├── QUICKSTART.md
├── SETUP.md
├── readme.md
├── backend/
│   ├── main.py
│   ├── [database, models, auth, etc.]
│   ├── services/
│   ├── routers/
│   └── __pycache__/
├── frontend/
│   └── app.py
└── sample_data/
    ├── sample_sla.txt
    └── sample_billing_data.csv
```

## Running Tests (Optional)

The system includes test utilities. To run basic tests:

```bash
# Test imports
python -c "from backend.main import app; print('✓ Backend imports OK')"
python -c "from backend.models import User; print('✓ Models import OK')"

# Quick validation test
python -c "
from backend.services.math_engine import MathEngine
import tempfile
import csv
import os

# Create test CSV
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'value_monetary'])
    writer.writerow([1, 100])
    writer.writerow([2, 200])
    csv_path = f.name

try:
    # Test math engine
    engine = MathEngine(csv_path)
    engine.load_csv()
    
    # Test query
    result = engine.validate_and_execute('SELECT id, value_monetary FROM data')
    if result['status'] == 'passed':
        print('✓ Math Engine working')
    else:
        print('✗ Math Engine validation failed')
finally:
    os.unlink(csv_path)
"
```

## Troubleshooting Setup Issues

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Solution**: Run `pip install -r requirements.txt` again

### Issue: "Port 8000 already in use"
**Solution**: Change the port:
```bash
uvicorn backend.main:app --port 8001
# Then update FRONTEND to http://localhost:8001
```

### Issue: "Port 8501 already in use"
**Solution**: Run Streamlit on a different port:
```bash
streamlit run frontend/app.py --server.port 8502
```

### Issue: "Database is locked"
**Solution**: 
- Close all other connections to the database
- Delete `sla_recovery.db` and restart (recreates fresh)

### Issue: "Permission denied" when creating files
**Solution**:
```bash
chmod +x backend/
chmod +x frontend/
mkdir -p uploads/
chmod 755 uploads/
```

### Issue: "OPENAI_API_KEY" errors
**Solution**: 
- The system works fine without it (uses mock responses)
- Only needed if you want real LLM parsing
- If not set, system provides mock SLA parsing

## Next Steps

After successful setup:

1. **Read QUICKSTART.md** - Walk through using the system
2. **Try sample flow** - Upload sample SLA and billing data
3. **Customize** - Modify prompts and cost types
4. **Scale** - See readme.md for production deployment

## Network Access

### Local Machine Only (Default)
```bash
Backend: http://localhost:8000
Frontend: http://localhost:8501
```

### Access from Other Machines
To allow access from other machines, update `.env`:
```bash
API_HOST=0.0.0.0        # Listen on all interfaces
FRONTEND_PORT=8501      # Streamlit listens on all by default
```

Then access from another machine:
```
Backend: http://<your-machine-ip>:8000
Frontend: http://<your-machine-ip>:8501
```

## Performance Notes

- **First startup**: Takes ~5 seconds (creating database)
- **Document parsing**: 10-30 seconds (depends on document size)
- **SQL validation**: <1 second (DuckDB is fast)
- **Dashboard load**: <2 seconds

## Uninstalling

To completely remove the system:

```bash
# Remove the project directory
rm -rf Caps-EXL/

# Remove Python virtual environment (if created)
rm -rf venv/

# Remove Python packages (optional)
# pip uninstall -r requirements.txt -y
```

## Getting Help

- **API Documentation**: http://localhost:8000/docs (when backend running)
- **Code Issues**: Check syntax with `python -m py_compile <file.py>`
- **Runtime Issues**: Check `.env` configuration
- **Feature Questions**: See `readme.md` and `QUICKSTART.md`
