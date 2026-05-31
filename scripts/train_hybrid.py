import polars as pl
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.metrics import mean_absolute_error, r2_score
from prophet import Prophet
import xgboost as xgb
import warnings

warnings.filterwarnings("ignore")

# Configuration
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'data' / 'processed' / 'features_target_600cells.parquet'
MODELS_DIR = ROOT / 'models'
MODELS_DIR.mkdir(exist_ok=True)

print("--- Chargement des données pour le Modèle Hybride ---")
df = pl.read_parquet(DATA_PATH).sort(['square_id', 'slot_30m'])
raw_min = df['slot_30m'].min()
df = df.with_columns((((pl.col('slot_30m') - raw_min)//86400)+1).cast(pl.Int32).alias('day_idx'))

# Split (48 jours train, reste test)
train_df = df.filter(pl.col('day_idx') <= 48)
test_df = df.filter(pl.col('day_idx') > 48)

FEATURE_COLS = [c for c in df.columns if c not in ['square_id', 'slot_30m', 'day_idx', 'target_1h']]
TARGET = 'target_1h'

print(f"Train size: {len(train_df)}, Test size: {len(test_df)}")

# --- 1. Prédictions XGBoost (Nominal q50) ---
print("\n[1/3] Récupération des prédictions XGBoost...")
xgb_model_path = MODELS_DIR / 'xgb_q50.pkl'
if xgb_model_path.exists():
    with open(xgb_model_path, 'rb') as f:
        xgb_model = pickle.load(f)
else:
    # Ré-entraînement rapide si absent
    xgb_model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=6, n_jobs=-1)
    xgb_model.fit(train_df.select(FEATURE_COLS).to_numpy(), train_df[TARGET].to_numpy())

xgb_preds = xgb_model.predict(test_df.select(FEATURE_COLS).to_numpy())

# --- 2. Prédictions Prophet (Sur un échantillon significatif pour le poids) ---
print("[2/3] Calcul des prédictions Prophet (échantillon de 20 cellules)...")
sample_cells = df['square_id'].unique().sort().to_list()[:20]
prophet_preds_map = {}

for cid in sample_cells:
    cell_data = df.filter(pl.col('square_id') == cid).to_pandas()
    base_date = pd.Timestamp('2013-11-01')
    cell_data['ds'] = base_date + pd.to_timedelta(cell_data['slot_30m'], unit='s')
    cell_data = cell_data.rename(columns={'internet_volume': 'y'})
    
    m = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
    m.fit(cell_data[cell_data['day_idx'] <= 48][['ds', 'y']])
    
    future = m.make_future_dataframe(periods=len(cell_data[cell_data['day_idx'] > 48]), freq='30min')
    forecast = m.predict(future)
    prophet_preds_map[cid] = forecast.iloc[-len(y_true):]['yhat'].values if 'y_true' in locals() else forecast.iloc[-(len(cell_data)-len(cell_data[cell_data['day_idx'] <= 48])):]['yhat'].values

# --- 3. Hybridation (Weighted Ensemble) ---
print("[3/3] Optimisation de l'Ensemble Hybride...")

# On aligne XGB et Prophet sur l'échantillon pour trouver le poids optimal
y_true_all = []
xgb_preds_sample = []
prophet_preds_sample = []

for cid in sample_cells:
    c_test = test_df.filter(pl.col('square_id') == cid)
    y_true_all.extend(c_test[TARGET].to_list())
    
    # XGB preds pour cette cellule
    idx = test_df.with_row_index().filter(pl.col('square_id') == cid)['index'].to_list()
    xgb_preds_sample.extend(xgb_preds[idx])
    
    prophet_preds_sample.extend(prophet_preds_map[cid])

y_true_all = np.array(y_true_all)
xgb_preds_sample = np.array(xgb_preds_sample)
prophet_preds_sample = np.array(prophet_preds_sample)

# Recherche du meilleur poids (Simple grid search)
best_mae = float('inf')
best_w = 0.8

for w in np.linspace(0, 1, 11):
    hybrid_val = (w * xgb_preds_sample) + ((1 - w) * prophet_preds_sample)
    mae = mean_absolute_error(y_true_all, hybrid_val)
    if mae < best_mae:
        best_mae = mae
        best_w = w

print(f"\n--- SCORE FINAL HYBRIDE (w_xgb={best_w:.1f}, w_prophet={1-best_w:.1f}) ---")
print(f"MAE Hybride: {best_mae:.2f} Mo")

# Sauvegarde de la configuration hybride
hybrid_config = {
    'best_weight_xgb': best_w,
    'model_xgb_path': 'xgb_q50.pkl',
    'mae_val': best_mae
}

with open(MODELS_DIR / 'hybrid_config.pkl', 'wb') as f:
    pickle.dump(hybrid_config, f)

print(f"Configuration hybride sauvegardée dans {MODELS_DIR / 'hybrid_config.pkl'}")
