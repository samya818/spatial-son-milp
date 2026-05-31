"""
Interface between the dashboard and the decoupled SimulationEngine.
Robust and handles engine failures gracefully.
"""
import streamlit as st
import polars as pl
import logging
from typing import Dict, Any, List
from scripts.dashboard.config import config
from scripts.dashboard.telemetry import telemetry
from scripts.dashboard.resilience import milp_cb, milp_fallback
from src.simulation.engine import SimulationEngine, SimulationResult

logger = logging.getLogger(__name__)

class MILPConnector:
    """Interface between the dashboard UI and the decoupled SimulationEngine."""
    
    def __init__(self, fractions_df: pl.DataFrame, topology: dict):
        self.engine = SimulationEngine(fractions_df, topology)
        self.topology = topology
        self.antennas = topology.get("antennas", {})
        
    def _simulate_impl(self, 
                       slot_df: pl.DataFrame, 
                       delta_level: int = 0,
                       capacities_df: pl.DataFrame = None,
                       policy: str = "dynamic",
                       threshold_factor: float = 1.0) -> SimulationResult:
        """Executes simulation via the SimulationEngine with error handling."""
        
        try:
            # 1. Prepare Thresholds (Dashboard-specific logic for threshold_factor)
            physical_caps = {}
            trigger_thresholds = {}
            for ant_id in self.antennas.keys():
                ant_id_str = str(ant_id)
                p_cap = float(self.antennas.get(ant_id_str, {}).get("capacity_mo", 1000.0)) * threshold_factor
                physical_caps[ant_id_str] = p_cap
                
                t_thresh = p_cap
                if capacities_df is not None and not capacities_df.is_empty():
                    ant_nom = capacities_df.filter(pl.col("ant_id") == ant_id_str)
                    if not ant_nom.is_empty(): 
                        t_thresh = float(ant_nom["nominal_capacity"][0]) * threshold_factor
                trigger_thresholds[ant_id_str] = t_thresh

            # 2. Call Engine
            result = self.engine.run_slot(slot_df, policy, delta_level, physical_caps, trigger_thresholds)
            
            if result is None:
                raise ValueError("Le moteur de simulation a retourné un résultat vide.")
                
            return result
            
        except Exception as e:
            logger.error(f"Simulation Engine Failure: {e}")
            
            # Calculer le volume total pour le fallback si possible
            total_vol = slot_df["internet_volume"].sum() if not slot_df.is_empty() else 0.0
            
            # Retour gracieux : On montre au moins le volume de base si on peut pas optimiser
            return SimulationResult(
                policy=policy,
                status=f"error: {str(e)}",
                unsatisfied=0.0, 
                unsatisfied_baseline=0.0,
                n_congested=0,
                n_congested_baseline=0,
                mass_error=0.0,
                leakage=0.0,
                decisions=0,
                antenna_results=pl.DataFrame(),
                total_vol=total_vol
            )

    @telemetry.track_latency("milp")
    def simulate_slot(self, 
                      slot_df: pl.DataFrame, 
                      delta_level: int = 0,
                      capacities_df: pl.DataFrame = None,
                      policy: str = "dynamic",
                      threshold_factor: float = 1.0) -> SimulationResult:
        """Runs simulation wrapped in Circuit Breaker."""
        telemetry.log_call("milp")
        # On utilise le circuit breaker pour la résilience
        return milp_cb.call(self._simulate_impl, milp_fallback, slot_df, delta_level, capacities_df, policy, threshold_factor)
