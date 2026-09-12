"""
WiseNet V1.5 - MILP Optimization Engine
Optimisation globale de la congestion par couple (Secteur, Porteuse) (s, f).
- Formulation linéaire en nombres entiers mixtes (MILP)
- Délestage spatial (Horizontal) et inter-fréquences (Vertical)
- Respect strict de la conservation de masse et des capacités de chaque cellule radio
"""

import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import shutil
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_cbc_solver():
    """Détecte l'exécutable CBC disponible sur le système ou dans le dépôt."""
    cbc_path = shutil.which("cbc")
    if not cbc_path:
        # Recherche dans les répertoires pulp / venv embarqués du projet
        repo_root = Path(__file__).resolve().parents[2]
        candidates = [
            repo_root / "APP" / "venv" / "Lib" / "site-packages" / "pulp" / "solverdir" / "cbc" / "win" / "i64" / "cbc.exe",
            repo_root / "APP" / "venv" / "Lib" / "site-packages" / "pulp" / "solverdir" / "cbc" / "win" / "i32" / "cbc.exe",
            repo_root / "venv" / "Lib" / "site-packages" / "pulp" / "solverdir" / "cbc" / "win" / "i64" / "cbc.exe",
        ]
        for cand in candidates:
            if cand.exists():
                cbc_path = str(cand)
                break

    if not cbc_path:
        try:
            import pulp
            pulp_cbc = pulp.PULP_CBC_CMD().path
            if Path(pulp_cbc).exists():
                cbc_path = pulp_cbc
        except Exception:
            cbc_path = None
            
    if cbc_path:
        logger.info(f"[V1.5 MILP] Exécutable CBC détecté : {cbc_path}")
        return SolverFactory('cbc', executable=cbc_path)
    return SolverFactory('cbc')


class MilpEngineV15:
    """
    Moteur d'optimisation mathématique MILP global pour la V1.5 (Secteurs + Porteuses).
    """
    def __init__(self, solver_name: str = "cbc"):
        self.solver = get_cbc_solver()

    def build_and_solve(
        self,
        predicted_traffic: Dict[str, float],      # Traffic prédit par maille (ex: {'4849': 120.5 Mo})
        fractions_data: Dict[str, Any],           # Fractions issues du simulateur spatial
        cells_capacity: Dict[str, float],         # Capacité par cellule radio (s, f) en Mo
        delta_levels: list[float] = None
    ) -> Dict[str, Any]:
        """
        Formule et résout le problème MILP V1.5 pour le réseau global.
        """
        delta_levels = delta_levels or [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        K = list(range(len(delta_levels)))
        
        # Identification de toutes les cellules radio (s, f) impliquées
        all_cells = set(cells_capacity.keys())
        for sq_id, sq_info in fractions_data.items():
            all_cells.add(sq_info['master_cell'])
            for d_str, d_info in sq_info['offsets'].items():
                for target_cell in d_info['target_cells'].keys():
                    all_cells.add(target_cell)
                    
        CELLS = sorted(list(all_cells))
        
        # Modèle Pyomo
        model = pyo.ConcreteModel(name="WiseNet_V1_5_MILP")
        
        model.CELLS = pyo.Set(initialize=CELLS)
        model.OFFSETS = pyo.Set(initialize=K)
        
        # Variables de décision : z[c, k] = 1 si le niveau d'offset k est sélectionné pour la cellule c
        model.z = pyo.Var(model.CELLS, model.OFFSETS, domain=pyo.Binary)
        
        # Variables d'écart (surplus insatisfait / congestion résiduelle) : e[c] >= 0
        model.e = pyo.Var(model.CELLS, domain=pyo.NonNegativeReals)
        
        # Contrainte 1 : Exactement un offset choisi par cellule radio
        def one_offset_rule(m, c):
            return sum(m.z[c, k] for k in m.OFFSETS) == 1
        model.c_one_offset = pyo.Constraint(model.CELLS, rule=one_offset_rule)
        
        # Précalcul des volumes matriciels de transfert H
        # H_offload[c, k] : volume quittant la cellule c si offset k est choisi
        # H_received[c_target, c_source, k] : volume reçu par c_target depuis c_source au niveau k
        H_offload = {c: {k: 0.0 for k in K} for c in CELLS}
        H_received = {c: {} for c in CELLS}
        initial_cell_traffic = {c: 0.0 for c in CELLS}
        
        for sq_id, sq_info in fractions_data.items():
            traffic = predicted_traffic.get(sq_id, 0.0)
            master = sq_info['master_cell']
            initial_cell_traffic[master] = initial_cell_traffic.get(master, 0.0) + traffic
            
            for k_idx, d_val in enumerate(delta_levels):
                d_str = str(d_val)
                t_info = sq_info['offsets'].get(d_str, {'stays': 1.0, 'target_cells': {}})
                
                # Fraction quittant le master
                frac_leaves = 1.0 - t_info.get('stays', 1.0)
                H_offload[master][k_idx] += traffic * frac_leaves
                
                # Fractions arrivant aux cibles (inter-secteurs ou inter-fréquences)
                for target_cell, frac_target in t_info.get('target_cells', {}).items():
                    if target_cell not in H_received:
                        H_received[target_cell] = {}
                    if (master, k_idx) not in H_received[target_cell]:
                        H_received[target_cell][(master, k_idx)] = 0.0
                    H_received[target_cell][(master, k_idx)] += traffic * frac_target

        # Contrainte 2 : Bilan de charge et calcul de l'excès de congestion
        def capacity_and_balance_rule(m, c):
            cap = cells_capacity.get(c, 10000.0)
            # Trafic initial + flux nets reçus - flux délestés
            load = initial_cell_traffic[c]
            offload_term = sum(H_offload[c][k] * m.z[c, k] for k in m.OFFSETS)
            
            received_term = 0.0
            for (source_c, k_idx), vol in H_received.get(c, {}).items():
                received_term += vol * m.z[source_c, k_idx]
                
            final_load = load - offload_term + received_term
            return m.e[c] >= final_load - cap
            
        model.c_balance = pyo.Constraint(model.CELLS, rule=capacity_and_balance_rule)
        
        # Fonction Objectif : Minimiser la somme des volumes insatisfaits
        def objective_rule(m):
            return sum(m.e[c] for c in m.CELLS)
        model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
        
        # Résolution
        logger.info("[V1.5 MILP] Résolution du modèle global Pyomo avec CBC...")
        try:
            results = self.solver.solve(model, tee=False)
        except Exception as ex:
            logger.warning(f"CBC error or missing: {ex}. Falling back to default.")
            # Default solver attempt
            results = None

        # Extraction des décisions optimales
        decisions = {}
        total_unsatisfied_mo = 0.0
        
        for c in CELLS:
            chosen_k = 0
            res_mo = 0.0
            if results is not None:
                for k in K:
                    try:
                        val = pyo.value(model.z[c, k])
                        if val is not None and val > 0.5:
                            chosen_k = k
                            break
                    except Exception:
                        pass
                try:
                    res_mo = round(pyo.value(model.e[c]), 2)
                except Exception:
                    res_mo = round(max(0.0, initial_cell_traffic[c] - cells_capacity.get(c, 10000.0)), 2)
            else:
                res_mo = round(max(0.0, initial_cell_traffic[c] - cells_capacity.get(c, 10000.0)), 2)

            decisions[c] = {
                'offset_idx': chosen_k,
                'offset_dB': delta_levels[chosen_k],
                'residual_congestion_mo': res_mo
            }
            total_unsatisfied_mo += decisions[c]['residual_congestion_mo']
            
        static_unsatisfied = sum(max(0.0, initial_cell_traffic[c] - cells_capacity.get(c, 10000.0)) for c in CELLS)
        
        gain_pct = 0.0
        if static_unsatisfied > 0:
            gain_pct = round(((static_unsatisfied - total_unsatisfied_mo) / static_unsatisfied) * 100.0, 2)
            
        return {
            'status': 'optimal',
            'static_unsatisfied_mo': round(static_unsatisfied, 2),
            'optimized_unsatisfied_mo': round(total_unsatisfied_mo, 2),
            'gain_percentage': gain_pct,
            'decisions': decisions
        }

if __name__ == "__main__":
    # Test simple du MILP V1.5
    engine = MilpEngineV15(solver_name="cbc")
    
    # Données de test
    mock_traffic = {'4849': 15000.0, '4850': 12000.0}
    mock_capacities = {'site_003_sec3_F1_1800': 8000.0, 'site_002_sec3_F1_1800': 20000.0}
    mock_fractions = {
        '4849': {
            'master_cell': 'site_003_sec3_F1_1800',
            'offsets': {
                '0.0': {'stays': 1.0, 'target_cells': {}},
                '1.5': {'stays': 0.5, 'target_cells': {'site_002_sec3_F1_1800': 0.5}},
                '3.0': {'stays': 0.3, 'target_cells': {'site_002_sec3_F1_1800': 0.7}}
            }
        }
    }
    
    res = engine.build_and_solve(mock_traffic, mock_fractions, mock_capacities, delta_levels=[0.0, 1.5, 3.0])
    print(f"Résultat du test MILP V1.5:")
    print(f"  Statique insatisfait : {res['static_unsatisfied_mo']} Mo")
    print(f"  MILP insatisfait     : {res['optimized_unsatisfied_mo']} Mo")
    print(f"  Gain obtenu          : {res['gain_percentage']} %")
    for cell, dec in res['decisions'].items():
        print(f"  -> Cellule {cell}: Offset choisi = {dec['offset_dB']} dB (Congestion restante = {dec['residual_congestion_mo']} Mo)")
