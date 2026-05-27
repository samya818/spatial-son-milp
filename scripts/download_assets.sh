#!/bin/bash
# Scripts to check for SON assets (models and matrices)
# Author: Samya Loukili & Kenza El Khaniri

echo "🛰️ Checking SON assets..."

MODELS_DIR="research/models"
OFFLINE_DIR="research/offline"

# Check for a few critical files
if [ -f "$MODELS_DIR/xgb_q80.pkl" ] && [ -f "$OFFLINE_DIR/fractions_1024.parquet" ]; then
    echo "Assets already present. Skipping download."
else
    echo "❌ Assets missing!"
    echo "Please clone the repository with git lfs or ensure research/offline/ and research/models/ are populated."
    exit 1
fi
