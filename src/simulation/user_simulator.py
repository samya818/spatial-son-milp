import numpy as np
import polars as pl
from pathlib import Path

def simulate_user_series(n_cells=600, n_slots=2976, base_users=50, peak_factor=3.0, seed=42):
    """
    Simule une série temporelle réaliste de n_users pour chaque cellule.
    Patterns : Journalier (pics midi/soir), Hebdomadaire (weekend), Bruit.
    """
    rng   = np.random.default_rng(seed)
    slots = np.arange(n_slots)
    hours = (slots % 48) / 2
    days  = slots // 48
    
    # Pattern journalier : deux pics (12h et 20h)
    daily_pattern = 1 + peak_factor * (
        np.exp(-((hours - 20)**2) / 8) + 0.3 * np.exp(-((hours - 12)**2) / 4)
    )
    
    # Boost weekend
    weekend_boost = 1 + 0.3 * ((days % 7) >= 5)
    
    # Chargement des square_ids réels pour rester cohérent avec le pipeline
    # Si le fichier n'existe pas, on utilise des IDs génériques
    try:
        work_600 = pl.read_parquet('data/processed/work_600cells.parquet')['square_id'].unique().to_list()
        n_cells = len(work_600)
    except:
        work_600 = list(range(n_cells))
        
    cell_base = base_users * (0.5 + rng.random(n_cells))
    
    all_data = []
    for i, square_id in enumerate(work_600):
        # Combinaison des patterns
        users = cell_base[i] * daily_pattern * weekend_boost
        # Ajout de bruit gaussien (10%)
        users = users + rng.normal(0, users * 0.1)
        # Minimum 1 utilisateur
        users = np.maximum(users, 1).astype(int)
        
        # Création des colonnes pour Polars
        cell_df = pl.DataFrame({
            'square_id': [int(square_id)] * n_slots,
            'slot_30m': slots.astype(int),
            'n_users': users
        })
        all_data.append(cell_df)
    
    return pl.concat(all_data)

print("Simulation du nombre d'utilisateurs...")
df_users = simulate_user_series()

output_path = Path('data/simulated/n_users_600cells.parquet')
output_path.parent.mkdir(parents=True, exist_ok=True)
df_users.write_parquet(output_path)

print(f"Simulation terminée : {len(df_users)} lignes générées dans {output_path}.")
