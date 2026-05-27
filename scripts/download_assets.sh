#!/bin/bash
# Scripts to download pre-computed assets for Spatial SON-MILP
# Author: Samya Loukili & Kenza El Khaniri

RELEASE_URL="https://github.com/samya818/spatial-son-milp/releases/download/v1.0-assets"

echo "🛰️ Downloading SON assets (models and matrices)..."

# Directories
mkdir -p research/models
mkdir -p research/offline
mkdir -p research/data/processed

# Download files
# Models
curl -L "${RELEASE_URL}/xgb_q80.pkl" -o research/models/xgb_q80.pkl
curl -L "${RELEASE_URL}/lgbm_l2_corrector.pkl" -o research/models/lgbm_l2_corrector.pkl

# Offline matrices
curl -L "${RELEASE_URL}/fractions_1024.parquet" -o research/offline/fractions_1024.parquet
curl -L "${RELEASE_URL}/timeline_24h.parquet" -o research/offline/timeline_24h.parquet

# Processed data needed for dashboard
curl -L "${RELEASE_URL}/work_1024cells.parquet" -o research/data/processed/work_1024cells.parquet
curl -L "${RELEASE_URL}/nominal_capacities_v2.parquet" -o research/data/processed/nominal_capacities_v2.parquet
curl -L "${RELEASE_URL}/cell_antenna_map_1024.json" -o research/data/processed/cell_antenna_map_1024.json

echo "✅ All assets downloaded successfully."
