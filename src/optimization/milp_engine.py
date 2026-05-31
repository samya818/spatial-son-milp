import numpy as np
import polars as pl
from pathlib import Path
from pyomo.environ import (ConcreteModel, RangeSet, Var, Binary,
                          NonNegativeReals, Objective, Constraint,
                          minimize, value, SolverFactory)
from pyomo.opt import TerminationCondition

def build_H_matrices(fractions_df, antenna_preds, coverage):
    """
    Construit les matrices de transfert H_deleste et H_recv.
    """
    antennas = list(coverage.keys())
    n = len(antennas)
    # On force delta_level à être des entiers 0..K-1
    unique_levels = sorted(fractions_df['delta_level'].unique().to_list())
    K = len(unique_levels)
    ant_idx = {a: i for i, a in enumerate(antennas)}
    
    H_deleste = np.zeros((n, K))
    H_recv    = np.zeros((n, n, K))
    
    for i_a, master_id in enumerate(antennas):
        V_a = antenna_preds.get(master_id, 0.0)
        if V_a <= 0: continue
        
        # Filtrer les fractions pour ce master une seule fois
        master_fracs = fractions_df.filter(pl.col('master_id') == master_id)
        if master_fracs.is_empty(): continue
            
        n_cells = len(coverage[master_id])
        v_cell = V_a / n_cells if n_cells > 0 else 0.0
        active_cell_ids = [int(c) for c in coverage[master_id]]
        
        for k in range(K):
            k_level = unique_levels[k]
            k_fracs = master_fracs.filter((pl.col('delta_level') == k_level) & 
                                         (pl.col('square_id').is_in(active_cell_ids)))
            
            if k_fracs.is_empty():
                # Si pas de données pour ce niveau, on assume pas de délestage (conservateur)
                continue
                
            # Volume total qui reste sur le maître
            frac_stays = k_fracs.filter(pl.col('target_ant') == master_id)['fraction'].sum()
            v_stays = frac_stays * v_cell
            H_deleste[i_a, k] = max(0.0, V_a - v_stays)
            
            # Volume reçu par chaque voisin
            moves = k_fracs.filter(pl.col('target_ant') != master_id)
            if not moves.is_empty():
                v_moves = moves.group_by('target_ant').agg(pl.col('fraction').sum())
                for row in v_moves.iter_rows(named=True):
                    target_id = row['target_ant']
                    if target_id in ant_idx:
                        i_b = ant_idx[target_id]
                        H_recv[i_b, i_a, k] = row['fraction'] * v_cell
                    
    return antennas, H_deleste, H_recv

def solve_congestion_milp(antennas, antenna_stats, H_deleste, H_recv, delta_levels, time_limit=30):
    """
    Formulation MILP exacte.
    Variables : 
      - z[a, k] : Binaire, 1 si l'antenne a choisit le niveau k.
      - u[a]    : Continu, volume non satisfait (excès) sur l'antenne a.
    """
    n = len(antennas)
    K = len(delta_levels)
    
    model = ConcreteModel()
    model.A = RangeSet(0, n-1)
    model.K = RangeSet(0, K-1)
    
    model.z = Var(model.A, model.K, domain=Binary)
    model.u = Var(model.A, domain=NonNegativeReals)
    
    # Objectif : Minimiser l'excès de trafic total
    model.obj = Objective(expr=sum(model.u[a] for a in model.A), sense=minimize)
    
    # C1 : Chaque antenne doit choisir EXACTEMENT un niveau de delta
    def unique_level_rule(m, a):
        return sum(m.z[a, k] for k in m.K) == 1
    model.unique = Constraint(model.A, rule=unique_level_rule)
    
    # C2 : Définition de l'excès résiduel u[a]
    # Volume final sur a = V_a - délesté_de_a + reçu_des_voisins
    # u[a] >= Final_Volume_a - Capacité_a
    def residual_rule(m, b):
        ant_id = antennas[b]
        stats = antenna_stats.get(ant_id, {'V_a': 0.0, 'C_a': 1000.0})
        v_b = stats['V_a']
        c_b = stats['C_a']
        
        # Ce que l'antenne b elle-même déleste vers ses voisins
        self_deleste = sum(H_deleste[b, k] * m.z[b, k] for k in m.K)
        
        # Ce que l'antenne b reçoit de TOUS ses voisins a
        received = sum(H_recv[b, a, k] * m.z[a, k] for a in m.A for k in m.K)
        
        final_volume = v_b - self_deleste + received
        return m.u[b] >= final_volume - c_b
    model.residual = Constraint(model.A, rule=residual_rule)
    
    # C3 : Protection de la capacité (optionnel si on minimise u, 
    # mais ici on veut que u capture l'excès au delà de C_a)
    # Dans la version du guide, C3 est une contrainte dure : Final_V <= C_b
    # Mais si le système est globalement saturé, le MILP sera "Infeasible".
    # Pour la robustesse, on préfère minimiser l'excès (soft constraints).
    
    # Résolution
    try:
        import shutil
        cbc_exec = shutil.which('cbc')

        if not cbc_exec:
            try:
                import pulp
                cbc_exec = pulp.PULP_CBC_CMD().path
                if not Path(cbc_exec).exists():
                    cbc_exec = None
            except ImportError:
                cbc_exec = None

        if cbc_exec:
            solver = SolverFactory('cbc', executable=cbc_exec)
        else:
            # Fallback final : on espère qu'il est dans le PATH sans executable explicite
            solver = SolverFactory('cbc')

        solver.options['sec'] = time_limit
        results = solver.solve(model, tee=False)
        
        if results.solver.termination_condition == TerminationCondition.infeasible:
            return None, None
    except Exception as e:
        print(f"Erreur MILP : {e}")
        return None, None
        
    solution = {}
    try:
        obj_val = value(model.obj)
        for a in model.A:
            ant_id = antennas[a]
            for k in model.K:
                if value(model.z[a, k]) > 0.5:
                    solution[ant_id] = {
                        'delta_dB': delta_levels[k],
                        'level_idx': k,
                        'residual_u': float(value(model.u[a]))
                    }
                    break
        return solution, obj_val
    except:
        return None, None
