"""
Data loading and caching module for the SON Dashboard - Recruiter Edition.
Optimized for 1024 cells only. Includes robust error handling.
"""
import streamlit as st
import polars as pl
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from scripts.dashboard.config import config
from scripts.dashboard.telemetry import telemetry
from scripts.dashboard.resilience import retry

logger = logging.getLogger(__name__)

def _handle_missing_file(path: Path):
    """Affiche un message d'erreur Streamlit clair pour les fichiers manquants."""
    msg = f"🔍 Fichier introuvable : `{path.name}`"
    st.error(f"{msg}\n\n**Action requise** : Veuillez d'abord exécuter le pipeline de génération de données ou vérifier le dossier `research/`.")
    logger.error(f"Missing critical file: {path}")

def _enforce_types(df: pl.DataFrame) -> pl.DataFrame:
    """Rigorous type enforcement for shared columns."""
    cols = df.columns
    casts = []
    if "square_id" in cols: casts.append(pl.col("square_id").cast(pl.Int64))
    if "slot_30m" in cols: casts.append(pl.col("slot_30m").cast(pl.Int64))
    if "master_id" in cols: casts.append(pl.col("master_id").cast(pl.String))
    if "target_ant" in cols: casts.append(pl.col("target_ant").cast(pl.String))
    if "ant_id" in cols: casts.append(pl.col("ant_id").cast(pl.String))
    
    # Volumes and Metrics
    for c in ["internet_volume", "nominal_capacity", "capacity_mo", "fraction", "target_1h", "preds"]:
        if c in cols: casts.append(pl.col(c).cast(pl.Float64))
    
    return df.with_columns(casts) if casts else df

@st.cache_data(ttl=3600)
@telemetry.track_latency("io")
def load_traffic_data() -> pl.DataFrame:
    """Loads ACTUAL aggregated traffic data (1024 cells)."""
    path = config.DATA_DIR / config.TRAFFIC_FILE
    if path.exists():
        df = pl.read_parquet(path)
        return _enforce_types(df)
    _handle_missing_file(path)
    return pl.DataFrame(schema={"square_id": pl.Int64, "slot_30m": pl.Int64, "internet_volume": pl.Float64})

@st.cache_data(ttl=3600)
def load_cell_to_antenna_map() -> Dict[int, str]:
    """Loads square_id -> ant_id mapping."""
    path = config.DATA_DIR / config.ANTENNA_MAP_FILE
    if path.exists():
        with open(path, "r") as f:
            data = json.load(f)
            if not data: return {}
            first_key = list(data.keys())[0]
            if isinstance(data[first_key], list):
                return {int(sq): str(ant_id) for ant_id, squares in data.items() for sq in squares}
            else:
                return {int(sq): str(ant_id) for sq, ant_id in data.items()}
    return {}

@st.cache_data(ttl=3600)
def load_nominal_capacities() -> pl.DataFrame:
    """Loads P90 thresholds."""
    path = config.DATA_DIR / config.CAPACITIES_FILE
    cell_to_ant = load_cell_to_antenna_map()
    if path.exists() and cell_to_ant:
        cap_df = _enforce_types(pl.read_parquet(path))
        mapping_df = _enforce_types(pl.DataFrame({
            "square_id": list(cell_to_ant.keys()),
            "ant_id": list(cell_to_ant.values())
        }))
        return cap_df.join(mapping_df, on="square_id").group_by(["plage", "is_weekend", "ant_id"]).agg(pl.col("nominal_capacity").sum())
    return pl.DataFrame()

@st.cache_data(ttl=3600)
def load_physical_capacities() -> pl.DataFrame:
    """Loads hard physical capacities."""
    topo = load_topology()
    ants = topo.get("antennas", {})
    if not ants: return pl.DataFrame()
    return _enforce_types(pl.DataFrame({
        "ant_id": [str(k) for k in ants.keys()],
        "capacity_mo": [float(v.get("capacity_mo", 1000.0)) for v in ants.values()]
    }))

@st.cache_data(ttl=3600)
def load_fractions() -> pl.DataFrame:
    """Loads spatial transfer fractions (1024 cells)."""
    path = config.OFFLINE_DIR / config.FRACTIONS_FILE
    if path.exists():
        return _enforce_types(pl.read_parquet(path))
    _handle_missing_file(path)
    return pl.DataFrame()

@st.cache_data(ttl=3600)
def load_timeline_24h() -> pl.DataFrame:
    """Loads precomputed 24h timeline results."""
    path = config.OFFLINE_DIR / "timeline_24h.parquet"
    if path.exists():
        return _enforce_types(pl.read_parquet(path))
    _handle_missing_file(path)
    return pl.DataFrame(schema={"slot_30m": pl.Int64, "static": pl.Float64, "greedy": pl.Float64, "milp": pl.Float64})

@st.cache_resource
def load_topology() -> Dict[str, Any]:
    path = config.CONFIG_DIR / config.TOPOLOGY_FILE
    if path.exists():
        with open(path, "r") as f: return yaml.safe_load(f)
    _handle_missing_file(path)
    return {"antennas": {}}

def compute_antenna_aggregates(traffic_df: pl.DataFrame, cell_to_ant: Dict[int, str]) -> pl.DataFrame:
    """Aggregates cell-level traffic to antenna-level traffic."""
    if traffic_df.is_empty() or not cell_to_ant:
        return pl.DataFrame(schema={"ant_id": pl.String, "internet_volume": pl.Float64})
    
    mapping_df = _enforce_types(pl.DataFrame({
        "square_id": list(cell_to_ant.keys()),
        "ant_id": list(cell_to_ant.values())
    }))
    
    df = _enforce_types(traffic_df)
    return df.join(mapping_df, on="square_id").group_by("ant_id").agg(pl.col("internet_volume").sum())
