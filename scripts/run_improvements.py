import polars as pl
import xgboost as xgb
import lightgbm as lgb
import numpy as np
import pickle
from pathlib import Path
from sklearn.metrics import mean_absolute_error
from prophet import Prophet
import pandas as pd
import os

# Configuration
ROOT = Path(r'C:\Users\hp\OneDrive\Desktop\projectTimeSeries')
DATA_PATH = ROOT / 'data' / 'processed' / 'features_target_600cells.parquet'
MODELS_DIR = ROOT / 'models'
MODELS_DIR.mkdir(exist_ok=True)

print("--- Chargement des données ---")
df = pl.read_parquet(DATA_PATH).sort(['square_id', 'slot_30m'])

# Recalcul de day_idx
raw_min = df['slot_30m'].min()
df = df.with_columns((((pl.col('slot_30m') - raw_min)//86400)+1).cast(pl.Int32).alias('day_idx'))

days = df['day_idx'].unique().sort().to_list()
print(f"Jours disponibles: {min(days)} à {max(days)}")

# Ajustement du split car le dataset s'arrête au jour 55
# On prend les 7 derniers jours pour le test
max_day = max(days)
SPLIT_DAY = max_day - 7
print(f"Split au jour {SPLIT_DAY} (Train <= {SPLIT_DAY}, Test > {SPLIT_DAY})")

train_df = df.filter(pl.col('day_idx') <= SPLIT_DAY)
test_df = df.filter(pl.col('day_idx') > SPLIT_DAY)

FEATURE_COLS = [c for c in df.columns if c not in ['square_id', 'slot_30m', 'day_idx', 'target_1h']]
TARGET = 'target_1h'

X_train = train_df.select(FEATURE_COLS).to_numpy()
y_train = train_df[TARGET].to_numpy()
X_test = test_df.select(FEATURE_COLS).to_numpy()
y_test = test_df[TARGET].to_numpy()

print(f"Train size: {len(train_df)}, Test size: {len(test_df)}")

print("\n--- Section A: Quantile Regression (XGBoost) ---")
quantiles = {'q20': 0.20, 'q50': 0.50, 'q80': 0.80}
models = {}

for name, alpha in quantiles.items():
    print(f"Entraînement modèle {name} (alpha={alpha})...")
    model = xgb.XGBRegressor(
        objective='reg:quantileerror',
        quantile_alpha=alpha,
        n_estimators=50,
        learning_rate=0.1,
        max_depth=6,
        n_jobs=-1,
        random_state=42
    )
    model.fit(X_train, y_train)
    models[name] = model
    with open(MODELS_DIR / f'xgb_{name}.pkl', 'wb') as f:
        pickle.dump(model, f)

preds_q20 = models['q20'].predict(X_test)
preds_q80 = models['q80'].predict(X_test)
coverage = np.mean((y_test >= preds_q20) & (y_test <= preds_q80))
print(f"Couverture intervalle [q20, q80]: {coverage:.3f}")

print("\n--- Section B: Stacking L2 (LightGBM Correcteur) ---")
preds_l1_train = models['q50'].predict(X_train)
residuals_train = y_train - preds_l1_train
X_train_l2 = np.column_stack([X_train, preds_l1_train])
X_test_l2 = np.column_stack([X_test, models['q50'].predict(X_test)])

corrector = lgb.LGBMRegressor(n_estimators=50, random_state=42)
corrector.fit(X_train_l2, residuals_train)

preds_l1_test = models['q50'].predict(X_test)
correction = corrector.predict(X_test_l2)
preds_final = preds_l1_test + correction
print(f"Gain Stacking: {(mean_absolute_error(y_test, preds_l1_test) - mean_absolute_error(y_test, preds_final))/mean_absolute_error(y_test, preds_l1_test)*100:.1f}%")

with open(MODELS_DIR / 'lgbm_l2_corrector.pkl', 'wb') as f:
    pickle.dump(corrector, f)

print("\n--- Section D: Prophet ---")
sample_cell = df['square_id'].unique().to_list()[0]
cell_data = df.filter(pl.col('square_id') == sample_cell).to_pandas()
base_date = pd.Timestamp('2013-11-01')
cell_data['ds'] = base_date + pd.to_timedelta(cell_data['slot_30m'], unit='s')
cell_data = cell_data.rename(columns={'internet_volume': 'y'})
m = Prophet(daily_seasonality=True).fit(cell_data[cell_data['day_idx'] <= SPLIT_DAY][['ds', 'y']])
print("Prophet test complete.")

print("\n--- Section E: Capacités Nominales ---")
def get_time_slot_type(hour_slot):
    h = hour_slot / 2
    if h < 6: return 0
    elif h < 12: return 1
    elif h < 19: return 2
    else: return 3

nominal_caps = (
    df.with_columns([
        (pl.col('slot_30m') % 86400 // 1800).alias('hour_slot'),
        ((pl.col('day_idx') % 7) >= 6).cast(pl.Int8).alias('is_weekend'),
    ])
    .with_columns(pl.col('hour_slot').map_elements(get_time_slot_type, return_dtype=pl.Int8).alias('plage'))
    .group_by(['square_id', 'plage', 'is_weekend'])
    .agg(pl.col('internet_volume').quantile(0.90).alias('nominal_capacity'))
)
nominal_caps.write_parquet(ROOT / 'data' / 'processed' / 'nominal_capacities.parquet')
print(f"Capacités sauvegardées: {len(nominal_caps)} lignes.")
