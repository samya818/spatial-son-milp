"""
WiseNet V1.5 - Greedy Engine (Heuristique Gloutonne Réaliste avec Conservation de Masse)
- Décision locale cellule par cellule (triées par congestion décroissante)
- Respect strict de la physique : le trafic délesté est REÇU par les cellules cibles
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class GreedyEngineV15:
    """
    Heuristique gloutonne pour V1.5 — référence de comparaison face au MILP.
    """
    def solve(
        self,
        predicted_traffic: Dict[str, float],
        fractions_data: Dict[str, Any],
        cells_capacity: Dict[str, float],
        delta_levels: list = None
    ) -> Dict[str, Any]:
        delta_levels = delta_levels or [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        
        # 1. Calcul de la charge initiale
        initial_traffic = {c: 0.0 for c in cells_capacity}
        for sq_id, sq_info in fractions_data.items():
            master = sq_info['master_cell']
            traf = predicted_traffic.get(sq_id, 0.0)
            if master in initial_traffic:
                initial_traffic[master] += traf

        # 2. Heuristique de sélection : chaque cellule surchargée choisit le delta qui maximise son délestage
        sorted_cells = sorted(
            cells_capacity.keys(),
            key=lambda c: max(0.0, initial_traffic.get(c, 0.0) - cells_capacity[c]),
            reverse=True
        )

        chosen_offsets = {c: 0 for c in cells_capacity}

        for cell in sorted_cells:
            cap = cells_capacity[cell]
            load = initial_traffic[cell]
            if load <= cap:
                continue

            # Trouver le meilleur offset local
            best_k = 0
            best_reduction = 0.0
            for k_idx, delta in enumerate(delta_levels):
                d_str = str(delta)
                offload_vol = 0.0
                for sq_id, sq_info in fractions_data.items():
                    if sq_info['master_cell'] == cell:
                        sq_traf = predicted_traffic.get(sq_id, 0.0)
                        t_info = sq_info['offsets'].get(d_str, {'stays': 1.0})
                        offload_vol += sq_traf * (1.0 - t_info.get('stays', 1.0))
                if offload_vol > best_reduction:
                    best_reduction = offload_vol
                    best_k = k_idx

            chosen_offsets[cell] = best_k

        # 3. Calcul RIGOUROUX du bilan de masse final (Conservation de masse exacte)
        final_loads = {c: initial_traffic[c] for c in cells_capacity}

        for sq_id, sq_info in fractions_data.items():
            master = sq_info['master_cell']
            traf = predicted_traffic.get(sq_id, 0.0)
            k = chosen_offsets.get(master, 0)
            d_str = str(delta_levels[k])
            t_info = sq_info['offsets'].get(d_str, {'stays': 1.0, 'target_cells': {}})
            
            # Trafic qui quitte le maître
            frac_leaves = 1.0 - t_info.get('stays', 1.0)
            final_loads[master] -= traf * frac_leaves
            
            # Trafic reçu par les cellules cibles
            for target_cell, frac_target in t_info.get('target_cells', {}).items():
                if target_cell in final_loads:
                    final_loads[target_cell] += traf * frac_target

        # 4. Calcul de l'insatisfait total
        decisions = {}
        total_unsatisfied = 0.0
        static_unsatisfied = sum(max(0.0, initial_traffic[c] - cells_capacity[c]) for c in cells_capacity)

        for cell, cap in cells_capacity.items():
            res = max(0.0, final_loads[cell] - cap)
            total_unsatisfied += res
            decisions[cell] = {
                'offset_idx': chosen_offsets[cell],
                'offset_dB': delta_levels[chosen_offsets[cell]],
                'residual_congestion_mo': round(res, 2)
            }

        gain_pct = 0.0
        if static_unsatisfied > 0:
            gain_pct = round(((static_unsatisfied - total_unsatisfied) / static_unsatisfied) * 100.0, 2)

        return {
            'status': 'greedy',
            'static_unsatisfied_mo': round(static_unsatisfied, 2),
            'optimized_unsatisfied_mo': round(total_unsatisfied, 2),
            'gain_percentage': gain_pct,
            'decisions': decisions
        }
