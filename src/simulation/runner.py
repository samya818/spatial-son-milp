import polars as pl
import numpy as np
import pickle
import json
import yaml
import logging
from pathlib import Path
from tqdm import tqdm
from pydantic import BaseModel, Field

# Configuration du logging structuré
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SON.Simulation")

class SimConfig(BaseModel):
    policy: str = "dynamic"
    model_name: str = "xgb_q80"
    threshold: float = 1.0
    cells: int = 1024
    root: Path = Field(default_factory=lambda: Path.cwd() / "research")

class SONSimulator:
    """
    Simulateur de réseau SON (Self-Organizing Network) de grade industriel pour 4G/LTE.
    Gère la prédiction de trafic, l'optimisation MILP et la réalisation spatiale.
    """
    def __init__(self, config: SimConfig):
        self.config = config
        self.load_assets()
        self.reset()

    def load_assets(self):
        logger.info(f"Loading assets for {self.config.cells} cells cluster...")
        
        # Chemins vers les fichiers de données (à adapter selon la structure src/)
        data_dir = self.config.root / 'data' / 'processed'
        models_dir = self.config.root / 'models'
        offline_dir = self.config.root / 'offline'
        config_dir = self.config.root / 'config'

        with open(models_dir / f'{self.config.model_name}.pkl', 'rb') as f:
            self.model = pickle.load(f)
        
        self.fractions_df = pl.read_parquet(offline_dir / f'fractions_{self.config.cells}.parquet')
        
        with open(config_dir / f'network_topology_{self.config.cells}.yaml', 'r') as f:
            self.topology = yaml.safe_load(f)
        with open(data_dir / f'cell_antenna_map_{self.config.cells}.json', 'r') as f:
            self.coverage = json.load(f)
            
        self.cell_to_ant = {int(c): ant for ant, cells in self.coverage.items() for c in cells}
            
        full_df = pl.read_parquet(data_dir / f'features_target_{self.config.cells}cells.parquet')
        max_slot = full_df['slot_30m'].max()
        test_start_slot = max_slot - (48 * 1800)
        
        # Filtrage Polars optimisé
        self.df_raw = (full_df.filter(pl.col('slot_30m') >= test_start_slot)
                       .sort(['slot_30m', 'square_id']))
        
        unique_slots = self.df_raw['slot_30m'].unique().sort().to_list()[:48]
        self.df_raw = self.df_raw.filter(pl.col('slot_30m').is_in(unique_slots))
        
        self.delta_levels = sorted(self.fractions_df['delta_dB'].unique().to_list())
        
        # Import dynamique pour éviter les dépendances circulaires
        from src.ml.predictor import TrafficPredictor
        self.FEATURE_COLS = TrafficPredictor().feature_cols

    def reset(self):
        self.current_offsets = {ant_id: 0.0 for ant_id in self.coverage.keys()}
        self.total_unsatisfied = 0.0
        self.decisions_count = 0

    def run(self):
        from src.optimization.milp_engine import build_H_matrices, solve_congestion_milp
        
        slots = sorted(self.df_raw['slot_30m'].unique().to_list())
        logger.info(f"Starting simulation: {len(slots)} slots, policy={self.config.policy}")

        for slot in tqdm(slots, desc=f"SON Simulation ({self.config.policy})"):
            slot_df = self.df_raw.filter(pl.col('slot_30m') == slot)
            
            # 1. PRÉDICTION
            X_slot = slot_df.select(self.FEATURE_COLS).to_numpy()
            preds = self.model.predict(X_slot)
            
            antenna_preds = {}
            for i, row in enumerate(slot_df.iter_rows(named=True)):
                ant_id = self.cell_to_ant.get(row['square_id'])
                if ant_id:
                    antenna_preds[ant_id] = antenna_preds.get(ant_id, 0.0) + float(preds[i])
            
            ant_stats = {a: {'V_a': v, 'C_a': self.topology['antennas'][a]['capacity_mo']} 
                         for a, v in antenna_preds.items()}
            
            # 2. DÉCISION (MILP)
            if self.config.policy == 'dynamic':
                congested = [a for a, s in ant_stats.items() if s['V_a'] > s['C_a'] * self.config.threshold]
                if congested:
                    h_antennas, H_deleste, H_recv = build_H_matrices(self.fractions_df, antenna_preds, self.coverage)
                    solution, _ = solve_congestion_milp(h_antennas, ant_stats, H_deleste, H_recv, self.delta_levels)
                    if solution:
                        self.decisions_count += 1
                        for ant_id, res in solution.items():
                            self.current_offsets[ant_id] = res['delta_dB']
                else:
                    # Reset offsets if no congestion predicted
                    for ant_id in self.current_offsets: self.current_offsets[ant_id] = 0.0

            # 3. RÉALISATION (Spatial)
            current_ant_volumes = {ant_id: 0.0 for ant_id in self.coverage.keys()}
            
            # Groupement par delta pour optimiser le filtrage Polars
            for delta in self.delta_levels:
                ants_with_delta = [a for a, d in self.current_offsets.items() if d == delta]
                if not ants_with_delta: continue
                
                m_fracs = self.fractions_df.filter((pl.col('master_id').is_in(ants_with_delta)) & (pl.col('delta_dB') == delta))
                
                # Jointure Polars pour la réalisation (plus rapide que des boucles Python)
                # Note: On garde l'approche itérative simple pour l'instant pour assurer la correction
                for m_id in ants_with_delta:
                    cells_in_ant = self.coverage[m_id]
                    sub_df = slot_df.filter(pl.col('square_id').is_in(cells_in_ant))
                    ant_delta_fracs = m_fracs.filter(pl.col('master_id') == m_id)
                    
                    for row in sub_df.iter_rows(named=True):
                        v_cell = row['internet_volume']
                        cell_fracs = ant_delta_fracs.filter(pl.col('square_id') == row['square_id'])
                        for f_row in cell_fracs.iter_rows(named=True):
                            t = f_row['target_ant']
                            if t in current_ant_volumes:
                                current_ant_volumes[t] += v_cell * f_row['fraction']

            # 4. ÉVALUATION
            for ant_id, v_final in current_ant_volumes.items():
                cap = self.topology['antennas'][ant_id]['capacity_mo']
                self.total_unsatisfied += max(0.0, v_final - cap)

        return {
            'policy': self.config.policy,
            'total_unsatisfied': self.total_unsatisfied,
            'decisions_made': self.decisions_count
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Industrial SON Simulator Runner")
    parser.add_argument("--cells", type=int, default=1024, help="Number of cells (1024)")
    parser.add_argument("--policy", type=str, default="dynamic", choices=["static", "dynamic"], help="Control policy")
    args = parser.parse_args()

    config = SimConfig(policy=args.policy, cells=args.cells)
    sim = SONSimulator(config)
    results = sim.run()
    
    print(f"\n--- Simulation Complete ---")
    print(f"Policy: {results['policy']}")
    print(f"Total Unsatisfied Volume: {results['total_unsatisfied']:.2f} Mo")
    print(f"Decisions Made: {results['decisions_made']}")
