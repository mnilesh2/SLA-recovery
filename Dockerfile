# Multi-stage build for SLA Recovery Audit System

# Stage 1: Backend Base
FROM python:3.12-slim as backend-base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Expose backend port
EXPOSE 8000

# Stage 2: Backend Runtime
FROM backend-base as backend

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Stage 3: Frontend Runtime
FROM backend-base as frontend

# Streamlit requires additional setup
RUN mkdir -p /app/frontend

COPY frontend/ ./frontend/
COPY sample_data/ ./sample_data/
COPY .env.example ./.env

# Expose Streamlit port
EXPOSE 8501

# Create Streamlit config
RUN mkdir -p ~/.streamlit && \
    echo "[server]" > ~/.streamlit/config.toml && \
    echo "headless = true" >> ~/.streamlit/config.toml && \
    echo "port = 8501" >> ~/.streamlit/config.toml && \
    echo "enableXsrfProtection = false" >> ~/.streamlit/config.toml

CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]


# Stage 4: Combined Runtime (Single Container)
FROM backend-base as production

# Install supervisor to run both services
RUN pip install supervisor

# Copy all project files
COPY . .

# Create supervisor config
RUN mkdir -p /etc/supervisor/conf.d && \
    echo "[supervisord]" > /etc/supervisor/conf.d/app.conf && \
    echo "nodaemon=true" >> /etc/supervisor/conf.d/app.conf && \
    echo "" >> /etc/supervisor/conf.d/app.conf && \
    echo "[program:backend]" >> /etc/supervisor/conf.d/app.conf && \
    echo "command=uvicorn backend.main:app --host 0.0.0.0 --port 8000" >> /etc/supervisor/conf.d/app.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/app.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/app.conf && \
    echo "stderr_logfile=/var/log/backend.err.log" >> /etc/supervisor/conf.d/app.conf && \
    echo "stdout_logfile=/var/log/backend.out.log" >> /etc/supervisor/conf.d/app.conf && \
    echo "" >> /etc/supervisor/conf.d/app.conf && \
    echo "[program:frontend]" >> /etc/supervisor/conf.d/app.conf && \
    echo "command=streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0" >> /etc/supervisor/conf.d/app.conf && \
    echo "autostart=true" >> /etc/supervisor/conf.d/app.conf && \
    echo "autorestart=true" >> /etc/supervisor/conf.d/app.conf && \
    echo "stderr_logfile=/var/log/frontend.err.log" >> /etc/supervisor/conf.d/app.conf && \
    echo "stdout_logfile=/var/log/frontend.out.log" >> /etc/supervisor/conf.d/app.conf

EXPOSE 8000 8501

CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
