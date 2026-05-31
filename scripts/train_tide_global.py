import polars as pl
import pandas as pd
import numpy as np
from darts import TimeSeries
from darts.models import TiDEModel
from darts.dataprocessing.transformers import Scaler
from sklearn.metrics import mean_absolute_error, r2_score
from pathlib import Path
import warnings
import torch

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'data' / 'processed' / 'features_target_600cells.parquet'

print("--- Chargement et Préparation des Données Globales ---")
df = pl.read_parquet(DATA_PATH).sort(['square_id', 'slot_30m'])
raw_min = df['slot_30m'].min()
df = df.with_columns((((pl.col('slot_30m') - raw_min)//86400)+1).cast(pl.Int32).alias('day_idx'))

# On utilise les 31 features expertes
FEATURE_COLS = [c for c in df.columns if c not in ['square_id', 'slot_30m', 'day_idx', 'target_1h']]
TARGET = 'target_1h'

# Pour un entraînement global avec Darts, on doit créer une liste de TimeSeries (une par cellule)
all_series = []
all_covariates = []

# On limite à 100 cellules pour garder un temps d'entraînement raisonnable pour ce test (600 serait trop long ici)
unique_cells = df['square_id'].unique().sort().to_list()[:100]
print(f"Préparation de {len(unique_cells)} cellules pour entraînement global...")

for cid in unique_cells:
    cell_data = df.filter(pl.col('square_id') == cid).to_pandas()
    # Dummy datetime
    base_date = pd.Timestamp('2013-11-01')
    cell_data['ds'] = base_date + pd.to_timedelta(cell_data['slot_30m'], unit='s')
    
    # Target series
    series = TimeSeries.from_dataframe(cell_data, 'ds', 'internet_volume', freq='30min')
    all_series.append(series)
    
    # Covariates series (les 31 features)
    covs = TimeSeries.from_dataframe(cell_data, 'ds', FEATURE_COLS, freq='30min')
    all_covariates.append(covs)

# Split temporel (Jour 48)
train_series = []
test_series = []
train_covs = []

for s, c in zip(all_series, all_covariates):
    # Trouver l'index du jour 48
    # Approximativement (48 jours * 48 slots/jour)
    split_idx = 48 * 48
    tr_s, te_s = s.split_before(split_idx)
    tr_c, te_c = c.split_before(split_idx)
    train_series.append(tr_s)
    test_series.append(te_s)
    train_covs.append(c) # On donne toute l'histoire des covs

# Scaling Global
scaler = Scaler()
train_series_scaled = scaler.fit_transform(train_series)

print("\n--- Entraînement GLOBAL de TiDE (100 cellules, 31 features) ---")
model = TiDEModel(
    input_chunk_length=48, # 24h de contexte
    output_chunk_length=2, # 1h de prédiction
    n_epochs=10,           # Réduit pour la démo
    batch_size=256,        # Gros batch pour l'entraînement global
    random_state=42,
    pl_trainer_kwargs={"accelerator": "cpu", "enable_progress_bar": True}
)

model.fit(train_series_scaled, past_covariates=train_covs)

print("\n--- Évaluation sur un échantillon de test ---")
# On teste sur les 5 premières cellules du test set
test_results = []
for i in range(5):
    pred_scaled = model.predict(n=len(test_series[i]), series=train_series_scaled[i], past_covariates=train_covs[i])
    pred = scaler.inverse_transform(pred_scaled)
    
    y_true = test_series[i].values().flatten()
    y_pred = pred.values().flatten()
    
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    test_results.append({'mae': mae, 'r2': r2})
    print(f"Cellule {unique_cells[i]} - MAE: {mae:.2f}, R²: {r2:.4f}")

avg_mae = np.mean([r['mae'] for r in test_results])
avg_r2 = np.mean([r['r2'] for r in test_results])

print(f"\n--- SCORE FINAL TIDE GLOBAL ---")
print(f"MAE moyenne: {avg_mae:.2f} Mo")
print(f"R² moyen: {avg_r2:.4f}")
