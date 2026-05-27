import polars as pl
import numpy as np
import pickle
import json
import yaml
from pathlib import Path
import sys
from tqdm import tqdm

# Ajout du root au path pour importer les modules src
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.optimization.milp_engine import build_H_matrices, solve_congestion_milp
from src.ml.predictor import TrafficPredictor

# --- CONFIGURATION ---
ROOT = Path(__file__).parent.parent.parent
DATA_PATH = ROOT / 'research' / 'data' / 'processed' / 'features_target_600cells.parquet'
FRACTIONS_PATH = ROOT / 'research' / 'offline' / 'fractions.parquet'
NOMINAL_CAPS_PATH = ROOT / 'research' / 'data' / 'processed' / 'nominal_capacities.parquet'
TOPOLOGY_PATH = ROOT / 'research' / 'config' / 'network_topology.yaml'
MAP_PATH = ROOT / 'research' / 'data' / 'processed' / 'cell_antenna_map_600.json'
MODELS_DIR = ROOT / 'research' / 'models'

class SONSimulator:
    def __init__(self, policy='dynamic', model_name='xgb_q80'):
        self.policy = policy
        self.model_name = model_name
        self.load_assets()
        self.reset()

    def load_assets(self):
        print(f"--- Chargement des assets ({self.policy}/{self.model_name}) ---")
        with open(MODELS_DIR / f'{self.model_name}.pkl', 'rb') as f:
            self.model = pickle.load(f)
        
        self.fractions_df = pl.read_parquet(FRACTIONS_PATH)
        self.nominal_caps = pl.read_parquet(NOMINAL_CAPS_PATH)
        
        with open(TOPOLOGY_PATH, 'r') as f:
            self.topology = yaml.safe_load(f)
        with open(MAP_PATH, 'r') as f:
            self.coverage_600 = json.load(f)
            
        # Mapping cellule -> antenne maître
        self.cell_to_ant = {}
        for ant_id, cells in self.coverage_600.items():
            for c in cells: self.cell_to_ant[int(c)] = ant_id
            
        # Données de test
        full_df = pl.read_parquet(DATA_PATH)
        max_slot = full_df['slot_30m'].max()
        # Simulation sur 48 slots (24h)
        self.test_start_slot = max_slot - (48 * 1800)
        self.df_raw = full_df.filter(pl.col('slot_30m') >= self.test_start_slot).sort(['slot_30m', 'square_id'])
        
        unique_slots = self.df_raw['slot_30m'].unique().sort().to_list()[:48]
        self.df_raw = self.df_raw.filter(pl.col('slot_30m').is_in(unique_slots))
        
        self.delta_levels = sorted(self.fractions_df['delta_dB'].unique().to_list())
        self.FEATURE_COLS = [c for c in self.df_raw.columns if c not in ['square_id', 'slot_30m', 'day_idx', 'target_1h']]

    def reset(self):
        self.current_offsets = {ant_id: 0.0 for ant_id in self.coverage_600.keys()}
        self.observed_volumes = {} # (square_id, slot) -> volume_effective
        self.total_unsatisfied = 0.0
        self.decisions_count = 0

    def compute_all_effective_volumes(self, slot_df, slot):
        """
        Calcule les volumes effectifs de TOUTES les cellules d'un coup pour respecter
        la conservation de masse.
        V_final(c) = V_local(c) * P_stay(c, delta_maitre) 
                     + SOMME_{voisin v} [ V_voisin(c) * P_from_v(c, delta_voisin) ]
        """
        # 1. Volume local par cellule
        volumes_dict = {row['square_id']: row['internet_volume'] for row in slot_df.iter_rows(named=True)}
        
        # 2. Initialisation des volumes effectifs à 0
        eff_volumes = {sid: 0.0 for sid in volumes_dict.keys()}
        
        # 3. Répartition du trafic master par master
        for master_id, current_delta in self.current_offsets.items():
            # On récupère toutes les fractions où cette antenne est le master
            master_fracs = self.fractions_df.filter(
                (pl.col('master_id') == master_id) & 
                (pl.col('delta_dB') == current_delta)
            )
            
            for row in master_fracs.iter_rows(named=True):
                sid = row['square_id']
                target_ant = row['target_ant']
                fraction = row['fraction']
                
                if sid in volumes_dict:
                    # Le volume de la cellule 'sid' (appartenant à master_id)
                    # est envoyé vers 'target_ant' selon la 'fraction'
                    # Problème : dans notre modèle, target_ant est une ANTENNE.
                    # On assume que le volume envoyé à une antenne voisine est absorbé par elle.
                    
                    if target_ant == master_id:
                        # Reste sur place
                        eff_volumes[sid] += volumes_dict[sid] * fraction
                    else:
                        # Part vers un voisin. Dans la simu par cellule, on considère que
                        # ce volume est "sorti" de la cellule locale mais il doit être compté 
                        # dans le volume total de l'antenne cible.
                        pass # On traitera l'agrégation par antenne après

        return eff_volumes, volumes_dict

    def run(self):
        slots = sorted(self.df_raw['slot_30m'].unique().to_list())
        
        for slot in tqdm(slots, desc=f"Simulation {self.policy}"):
            slot_df = self.df_raw.filter(pl.col('slot_30m') == slot)
            
            # Prédiction
            X_slot = slot_df.select(self.FEATURE_COLS).to_numpy()
            preds_1h = self.model.predict(X_slot)
            
            # Agrégation prédictive par antenne
            ant_stats = {}
            for i, row in enumerate(slot_df.iter_rows(named=True)):
                ant_id = self.cell_to_ant.get(row['square_id'])
                if ant_id:
                    if ant_id not in ant_stats:
                        ant_stats[ant_id] = {'V_a': 0.0, 'C_a': self.topology['antennas'][ant_id]['capacity_mo']}
                    ant_stats[ant_id]['V_a'] += float(preds_1h[i])
            
            # Décision
            if self.policy == 'dynamic':
                congested = [a for a, s in ant_stats.items() if s['V_a'] > s['C_a'] * 0.9]
                if congested:
                    h_antennas, H_deleste, H_recv = build_H_matrices(self.fractions_df, {a: s['V_a'] for a, s in ant_stats.items()}, self.coverage_600)
                    solution, _ = solve_congestion_milp(h_antennas, ant_stats, H_deleste, H_recv, self.delta_levels)
                    if solution:
                        self.decisions_count += 1
                        for ant_id, res in solution.items():
                            self.current_offsets[ant_id] = res['delta_dB']
                else:
                    for ant_id in self.current_offsets: self.current_offsets[ant_id] = 0.0

            # RÉALISATION (Conservation de masse)
            # v_ant_final = V_local_total - V_partant + V_arrivant
            current_ant_volumes = {ant_id: 0.0 for ant_id in self.coverage_600.keys()}
            
            for master_id, current_delta in self.current_offsets.items():
                master_fracs = self.fractions_df.filter(
                    (pl.col('master_id') == master_id) & (pl.col('delta_dB') == current_delta)
                )
                
                # Volume total de cette antenne avant transfert
                # On utilise internet_volume réel du dataset
                for row in slot_df.filter(pl.col('square_id').is_in(self.coverage_600[master_id])).iter_rows(named=True):
                    sid = row['square_id']
                    v_cell = row['internet_volume']
                    
                    # Répartition de v_cell
                    cell_fracs = master_fracs.filter(pl.col('square_id') == sid)
                    for f_row in cell_fracs.iter_rows(named=True):
                        target_ant = f_row['target_ant']
                        if target_ant in current_ant_volumes:
                            current_ant_volumes[target_ant] += v_cell * f_row['fraction']

            # Calcul de l'insatisfaction
            if slot == slots[0]:
                print(f"\n=== DEBUG Slot {slot} ===")
                total_v_orig = sum(slot_df['internet_volume'])
                total_v_final = sum(current_ant_volumes.values())
                print(f"Total V_orig={total_v_orig:.1f}, Total V_final={total_v_final:.1f}, System Loss={total_v_orig - total_v_final:.1f}")
                
                # Print for top 3 antennas by volume
                top_ants = sorted(current_ant_volumes.items(), key=lambda x: x[1], reverse=True)[:3]
                for ant_id, v_final in top_ants:
                    v_orig = sum(slot_df.filter(pl.col('square_id').is_in(self.coverage_600[ant_id]))['internet_volume'])
                    cap = self.topology['antennas'][ant_id]['capacity_mo']
                    print(f"{ant_id}: V_orig={v_orig:.1f}, V_final={v_final:.1f}, C={cap:.1f}, Delta={self.current_offsets[ant_id]}")

            for ant_id, v_final in current_ant_volumes.items():
                cap = self.topology['antennas'][ant_id]['capacity_mo']
                self.total_unsatisfied += max(0.0, v_final - cap)

        return {
            'policy': self.policy,
            'total_unsatisfied': self.total_unsatisfied,
            'decisions_made': self.decisions_count
        }

if __name__ == "__main__":
    sim_static = SONSimulator(policy='static', model_name='xgb_q80')
    res_static = sim_static.run()
    
    sim_dynamic = SONSimulator(policy='dynamic', model_name='xgb_q80')
    res_dynamic = sim_dynamic.run()
    
    print("\n" + "="*40)
    print("RÉSULTATS APRÈS CORRECTION (MASSE CONSERVÉE)")
    print("="*40)
    print(f"STATIQUE : {res_static['total_unsatisfied']:.2f} Mo")
    print(f"DYNAMIQUE: {res_dynamic['total_unsatisfied']:.2f} Mo")
    gain = (res_static['total_unsatisfied'] - res_dynamic['total_unsatisfied']) / (res_static['total_unsatisfied'] + 1e-6) * 100
    print(f"AMÉLIORATION RÉELLE : {gain:.2f}%")
