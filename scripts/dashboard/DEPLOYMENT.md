# Deployment Guide: SON Industrial Dashboard

## 📋 Prerequisites
- Docker & Docker Compose
- 2 CPU, 4GB RAM (Min)
- Access to network data Parquet files (automatically bundled in Docker build)

## 🚀 Quick Start
1. **Clone the repository**
2. **Build and start the container**:
   ```bash
   docker-compose up --build -d
   ```
3. **Access the dashboard**: `http://localhost:8501`

## 🔐 Security Configuration
- **Antenna ID Masking**: Controlled by `SON_SECRET_2026` environment variable. Change this in `docker-compose.yml` for each environment.
- **Audit Logs**: Stored in `./logs/audit.log`. Ensure this volume is backed up.
- **Rate Limiting**: Defaulted to 10 simulations/min per session.

## 🩺 Monitoring & Maintenance
- **System Health**: Access the "System Health" tab in Expert Mode to monitor latencies and error rates.
- **Logs**:
  - `logs/dashboard.log`: Operational logs (rotated).
  - `logs/audit.log`: User action trail.
- **Circuit Breakers**:
  - ML Engine: Resets after 120s of sustained failures.
  - MILP Engine: Resets after 60s of sustained failures.

## 🏗️ CI/CD Workflow
The project uses GitHub Actions (`.github/workflows/ci.yml`) to:
1. Lint the codebase with Ruff.
2. Run unit tests on data aggregation logic.
3. Build a production Docker image.
