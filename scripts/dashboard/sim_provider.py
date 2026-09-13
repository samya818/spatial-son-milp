import polars as pl
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from scripts.dashboard.config import config
from scripts.dashboard.resilience import milp_cb, milp_fallback

SIM_48H_DIR = Path(config.RESEARCH_DIR) / "reports" / "sim48h"
SIM_1H_PATH = Path(config.RESEARCH_DIR) / "reports" / "simulation_1h_camara_metrics.json"

class SimResultsProvider:
    """Provides validated multi-policy metrics and slot profiles for the dashboard."""
    
    def __init__(self):
        self.sim48h_slots: Optional[pl.DataFrame] = None
        self.sim48h_summary: Optional[Dict[str, Any]] = None
        self.sim1h_metrics: Optional[Dict[str, Any]] = None
        self._load_data()
        
    def _load_data(self):
        slots_path = SIM_48H_DIR / "sim48h_slots.csv"
        if slots_path.exists():
            try:
                self.sim48h_slots = pl.read_csv(slots_path)
            except Exception as e:
                print(f"Warning reading sim48h_slots: {e}")
                
        summary_path = SIM_48H_DIR / "sim48h_summary.json"
        if summary_path.exists():
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    self.sim48h_summary = json.load(f)
            except Exception as e:
                print(f"Warning reading sim48h_summary: {e}")

        if SIM_1H_PATH.exists():
            try:
                with open(SIM_1H_PATH, "r", encoding="utf-8") as f:
                    self.sim1h_metrics = json.load(f)
            except Exception as e:
                print(f"Warning reading sim1h_metrics: {e}")

    def get_slot_profile(self, slot_idx: int) -> Dict[str, Any]:
        """
        Retrieves real metrics for a given slot index (0 to 47 for 24h day).
        Uses sim48h peak day (Day 1) data for realism.
        """
        if self.sim48h_slots is not None and not self.sim48h_slots.is_empty():
            idx_1_based = (slot_idx % 48) + 1
            row_df = self.sim48h_slots.filter(pl.col("slot_idx") == idx_1_based)
            if not row_df.is_empty():
                row = row_df.to_dicts()[0]
                return {
                    "slot_idx": slot_idx,
                    "time": row.get("time", f"{slot_idx//2:02d}:{(slot_idx%2)*30:02d}"),
                    "v_real_mo": float(row.get("v_real_mo", 0.0)),
                    "u_static_mo": float(row.get("u_static_mo", 0.0)),
                    "u_milp_mo": float(row.get("u_milp_mo", 0.0)),
                    "u_oracle_mo": float(row.get("u_oracle_mo", 0.0)),
                    "gain_milp_pct": float(row.get("gain_milp_pct", 0.0)),
                    "regret_mo": float(row.get("regret_mo", 0.0)),
                    "mae_prediction_mo": float(row.get("mae_prediction_mo", 0.0)),
                    "milp_solve_s": float(row.get("milp_solve_s", 0.5)),
                    "source": "sim48h_verified"
                }

        # Fallback if CSV not loaded
        h = slot_idx // 2
        m = (slot_idx % 2) * 30
        return {
            "slot_idx": slot_idx,
            "time": f"{h:02d}:{m:02d}",
            "v_real_mo": 1250000.0,
            "u_static_mo": 240000.0,
            "u_milp_mo": 196000.0,
            "u_oracle_mo": 193000.0,
            "gain_milp_pct": 18.3,
            "regret_mo": 3000.0,
            "mae_prediction_mo": 160.0,
            "milp_solve_s": 0.58,
            "source": "default_baseline"
        }

sim_provider = SimResultsProvider()
