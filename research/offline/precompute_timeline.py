"""
Offline precomputation of the 24h timeline for the SON Dashboard.
Runs all 3 policies (Static, Greedy, MILP) across 48 slots.
"""
import polars as pl
import yaml
import json
import sys
from pathlib import Path
from tqdm import tqdm

# Add root to sys.path
ROOT = Path(__file__).parents[2]
sys.path.append(str(ROOT))

from src.simulation.engine import SimulationEngine

def precompute():
    print("--- Starting Offline Precomputation (24h Timeline) ---")
    
    # Paths
    RESEARCH_DIR = ROOT / "research"
    DATA_DIR = RESEARCH_DIR / "data" / "processed"
    OFFLINE_DIR = RESEARCH_DIR / "offline"
    CONFIG_DIR = RESEARCH_DIR / "config"
    
    fractions_path = OFFLINE_DIR / "fractions_1024.parquet"
    traffic_path = DATA_DIR / "work_1024cells.parquet"
    topology_path = CONFIG_DIR / "network_topology_1024.yaml"
    capacities_path = DATA_DIR / "nominal_capacities_v2.parquet"
    map_path = DATA_DIR / "cell_antenna_map_1024.json"
    
    # Load assets
    fractions_df = pl.read_parquet(fractions_path).with_columns(pl.col("square_id").cast(pl.Int64))
    traffic_df = pl.read_parquet(traffic_path).with_columns(pl.col("square_id").cast(pl.Int64))
    with open(topology_path, "r") as f:
        topology = yaml.safe_load(f)
    capacities_df = pl.read_parquet(capacities_path).with_columns(pl.col("square_id").cast(pl.Int64))
    with open(map_path, "r") as f:
        cell_to_ant = json.load(f)
    
    # Map square_id -> ant_id for capacities grouping
    # cell_to_ant is {ant_id: [squares]} or {square: ant}
    if isinstance(list(cell_to_ant.values())[0], list):
        flat_map = {int(sq): str(ant) for ant, sqs in cell_to_ant.items() for sq in sqs}
    else:
        flat_map = {int(sq): str(ant) for sq, ant in cell_to_ant.items()}
    
    mapping_df = pl.DataFrame({
        "square_id": [int(k) for k in flat_map.keys()],
        "ant_id": [str(v) for v in flat_map.values()]
    }).with_columns(pl.col("square_id").cast(pl.Int64))
    
    # Group capacities by ant_id
    ant_caps = capacities_df.join(mapping_df, on="square_id").group_by(["plage", "is_weekend", "ant_id"]).agg(pl.col("nominal_capacity").sum())
    
    # Physical capacities
    physical_caps = {str(k): float(v.get("capacity_mo", 1000.0)) for k, v in topology.get("antennas", {}).items()}
    
    # Initialize Engine
    engine = SimulationEngine(fractions_df, topology)
    
    # 48 slots
    unique_slots = sorted(traffic_df["slot_30m"].unique().to_list())
    slots = unique_slots[:48]
    
    results = []
    
    for slot in tqdm(slots, desc="Processing slots"):
        slot_data = traffic_df.filter(pl.col("slot_30m") == slot)
        day_of_week = ((slot // 48) + 4) % 7 
        is_weekend = 1 if day_of_week >= 5 else 0
        plage = int(slot % 48) // 12
        
        slot_caps = ant_caps.filter((pl.col("plage") == plage) & (pl.col("is_weekend") == is_weekend))
        trigger_thresholds = {row["ant_id"]: row["nominal_capacity"] for row in slot_caps.iter_rows(named=True)}
        # Fill missing thresholds with physical cap
        for ant_id in physical_caps:
            if ant_id not in trigger_thresholds:
                trigger_thresholds[ant_id] = physical_caps[ant_id]

        # Run 3 policies
        # Use default delta_level = 3 (max for 1024 cells usually)
        res_s = engine.run_slot(slot_data, "static", 0, physical_caps, trigger_thresholds)
        res_g = engine.run_slot(slot_data, "greedy", 3, physical_caps, trigger_thresholds)
        res_m = engine.run_slot(slot_data, "dynamic", 3, physical_caps, trigger_thresholds)
        
        results.append({
            "slot_30m": int(slot),
            "static": float(res_s.unsatisfied),
            "greedy": float(res_g.unsatisfied),
            "milp": float(res_m.unsatisfied)
        })
    
    # Save
    out_path = OFFLINE_DIR / "timeline_24h.parquet"
    pl.DataFrame(results).write_parquet(out_path)
    print(f"--- Precomputation complete. Saved to {out_path} ---")

if __name__ == "__main__":
    precompute()
