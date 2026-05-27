"""
Simulation engine for the SON Dashboard.
Decoupled logic for running network simulations with different policies.
"""
import polars as pl
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List
from src.optimization.milp_engine import build_H_matrices, solve_congestion_milp

@dataclass
class SimulationResult:
    policy: str
    status: str
    unsatisfied: float
    unsatisfied_baseline: float
    n_congested: int
    n_congested_baseline: int
    mass_error: float
    leakage: float
    decisions: int
    antenna_results: pl.DataFrame
    total_vol: float

class SimulationEngine:
    def __init__(self, fractions_df: pl.DataFrame, topology: dict):
        self.fractions = fractions_df
        self.topology = topology
        self.coverage = {}
        if not fractions_df.is_empty():
            # Inversion du mapping square_id -> master_id
            unique_mapping = fractions_df.select(["square_id", "master_id"]).unique()
            for row in unique_mapping.iter_rows():
                self.coverage.setdefault(row[1], []).append(row[0])

    def _empty_result(self, policy: str) -> SimulationResult:
        return SimulationResult(
            policy=policy, status="empty_slot",
            unsatisfied=0.0, unsatisfied_baseline=0.0,
            n_congested=0, n_congested_baseline=0,
            mass_error=0.0, leakage=0.0, decisions=0,
            antenna_results=pl.DataFrame(schema={
                "ant_id": pl.String, 
                "capacity": pl.Float64, 
                "final_volume": pl.Float64, 
                "original_volume": pl.Float64, 
                "offset_applied": pl.Int64, 
                "unsatisfied": pl.Float64, 
                "unsatisfied_baseline": pl.Float64
            }), 
            total_vol=0.0
        )

    def run_slot(self, slot_df: pl.DataFrame, policy: str, delta_level: int, 
                 physical_caps: Dict[str, float], trigger_thresholds: Dict[str, float]) -> SimulationResult:
        """
        Exécute la simulation pour un slot temporel donné.
        """
        if slot_df.is_empty() or self.fractions.is_empty():
            return self._empty_result(policy)

        # 1. Mapping & Baseline
        # Enforce types to avoid SchemaError
        slot_df = slot_df.with_columns(pl.col("square_id").cast(pl.Int64))
        mapping = self.fractions.select(["square_id", "master_id"]).unique().with_columns(pl.col("square_id").cast(pl.Int64))
        df = slot_df.join(mapping, on="square_id")
        
        antennas_vol = df.group_by("master_id").agg(pl.col("internet_volume").sum())
        ant_vol_dict = dict(zip(antennas_vol["master_id"], antennas_vol["internet_volume"]))
        
        total_vol = slot_df["internet_volume"].sum()
        all_antennas = list(physical_caps.keys())
        
        # 2. Politique de décision
        status = "success"
        decisions = 0
        chosen_levels = {ant_id: 0 for ant_id in all_antennas}
        
        if policy == "static":
            for ant_id in all_antennas:
                chosen_levels[ant_id] = delta_level
            decisions = len([a for a in chosen_levels.values() if a > 0])
            
        elif policy == "dynamic":
            antenna_stats = {
                ant_id: {'V_a': ant_vol_dict.get(ant_id, 0.0), 'C_a': physical_caps.get(ant_id, 1000.0)}
                for ant_id in all_antennas
            }
            
            # Limiter aux fractions autorisées (0..delta_level)
            allowed_fractions = self.fractions.filter(pl.col("delta_level") <= delta_level)
            unique_levels = sorted(allowed_fractions["delta_level"].unique().to_list())
            
            ants_list, H_deleste, H_recv = build_H_matrices(allowed_fractions, ant_vol_dict, self.coverage)
            solution, obj_val = solve_congestion_milp(ants_list, antenna_stats, H_deleste, H_recv, unique_levels)
            
            if solution:
                for ant_id, sol in solution.items():
                    chosen_levels[ant_id] = sol['level_idx']
                decisions = len([v for v in chosen_levels.values() if v > 0])
            else:
                status = "milp_failed"
        
        elif policy == "greedy":
            for ant_id in all_antennas:
                vol = ant_vol_dict.get(ant_id, 0.0)
                thresh = trigger_thresholds.get(ant_id, physical_caps.get(ant_id, 1000.0))
                if vol > thresh:
                    chosen_levels[ant_id] = delta_level
                else:
                    chosen_levels[ant_id] = 0
            decisions = len([v for v in chosen_levels.values() if v > 0])

        # 3. Calcul des volumes finaux
        chosen_levels_df = pl.DataFrame({
            "master_id": list(chosen_levels.keys()),
            "offset_applied": list(chosen_levels.values())
        })
        
        # Application des fractions selon le niveau choisi par chaque maître
        final_moves = (self.fractions
                       .join(chosen_levels_df, left_on=["master_id", "delta_level"], right_on=["master_id", "offset_applied"])
                       .join(slot_df, on="square_id")
                       .with_columns((pl.col("internet_volume") * pl.col("fraction")).alias("moved_vol")))
        
        # Leakage : Volume allant vers des antennes hors de notre zone (1024 cells)
        all_ant_set = set(all_antennas)
        leakage_df = final_moves.filter(~pl.col("target_ant").is_in(all_ant_set))
        leakage = leakage_df["moved_vol"].sum() if not leakage_df.is_empty() else 0.0
        
        # Volume final par antenne
        ant_results = (final_moves
                       .filter(pl.col("target_ant").is_in(all_ant_set))
                       .group_by("target_ant")
                       .agg(pl.col("moved_vol").sum().alias("final_volume"))
                       .rename({"target_ant": "ant_id"}))
        
        # Compléter avec toutes les antennes et ajouter les stats
        orig_vol_df = antennas_vol.rename({"master_id": "ant_id", "internet_volume": "original_volume"})
        caps_df = pl.DataFrame({"ant_id": all_antennas, "capacity": [physical_caps[a] for a in all_antennas]})
        
        ant_results = (caps_df
                       .join(ant_results, on="ant_id", how="left").fill_null(0.0)
                       .join(orig_vol_df, on="ant_id", how="left").fill_null(0.0)
                       .join(chosen_levels_df.rename({"master_id": "ant_id"}), on="ant_id", how="left"))
        
        # Métriques agrégées
        ant_results = ant_results.with_columns([
            (pl.max_horizontal([pl.col("final_volume") - pl.col("capacity"), 0.0])).alias("unsatisfied"),
            (pl.max_horizontal([pl.col("original_volume") - pl.col("capacity"), 0.0])).alias("unsatisfied_baseline")
        ])
        
        unsatisfied = ant_results["unsatisfied"].sum()
        unsatisfied_baseline = ant_results["unsatisfied_baseline"].sum()
        n_congested = (ant_results["final_volume"] > ant_results["capacity"]).sum()
        n_congested_baseline = (ant_results["original_volume"] > ant_results["capacity"]).sum()
        
        final_total_vol = ant_results["final_volume"].sum() + leakage
        mass_error = float(abs(final_total_vol - total_vol) / (total_vol + 1e-9))
        
        return SimulationResult(
            policy=policy,
            status=status,
            unsatisfied=float(unsatisfied),
            unsatisfied_baseline=float(unsatisfied_baseline),
            n_congested=int(n_congested),
            n_congested_baseline=int(n_congested_baseline),
            mass_error=mass_error,
            leakage=float(leakage),
            decisions=decisions,
            antenna_results=ant_results,
            total_vol=float(total_vol)
        )
