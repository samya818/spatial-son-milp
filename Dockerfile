# Multi-stage Dockerfile for SON Dashboard
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements-dashboard.txt .
RUN pip install --user --no-cache-dir -r requirements-dashboard.txt

FROM python:3.11-slim

WORKDIR /app
# Install system dependencies (CBC solver for MILP)
RUN apt-get update && apt-get install -y coinor-cbc curl && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src ./src
COPY scripts/dashboard ./scripts/dashboard
COPY research/data/processed ./research/data/processed
COPY research/config ./research/config
COPY research/offline ./research/offline
COPY research/models ./research/models

# Create logs directory
RUN mkdir -p logs

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "scripts/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
