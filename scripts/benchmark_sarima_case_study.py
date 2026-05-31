import polars as pl
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.metrics import mean_absolute_error, r2_score
import pmdarima as pm
from prophet import Prophet
import warnings
import time

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'data' / 'processed' / 'features_target_600cells.parquet'
MODELS_DIR = ROOT / 'models'

def main():
    print("--- Benchmark de Rigueur Simplifié : SARIMA vs HYBRIDE (Étude de Cas) ---")
    
    df = pl.read_parquet(DATA_PATH).sort(['square_id', 'slot_30m'])
    
    # On choisit LA cellule la plus active pour éviter les données vides
    top_cell = (df.group_by('square_id')
                .agg(pl.col('internet_volume').sum())
                .sort('internet_volume', descending=True)
                .head(1)['square_id']
                .item())
    
    print(f"Cellule sélectionnée pour l'étude de cas : {top_cell}")
    
    cell_data = df.filter(pl.col('square_id') == top_cell).to_pandas()
    max_slot = cell_data['slot_30m'].max()
    split_slot = max_slot - (3 * 86400) # On teste sur les 3 derniers jours pour être sûr
    
    train_df = cell_data[cell_data['slot_30m'] <= split_slot]
    test_df = cell_data[cell_data['slot_30m'] > split_slot]
    
    print(f"Train points: {len(train_df)}, Test points: {len(test_df)}")
    
    # 1. SARIMA
    print("Entraînement SARIMA...")
    sarima_model = pm.auto_arima(train_df['internet_volume'].values[-336:], 
                                seasonal=True, m=48, 
                                start_p=0, max_p=2, 
                                start_q=0, max_q=2,
                                suppress_warnings=True)
    sarima_preds = sarima_model.predict(n_periods=len(test_df))
    
    # 2. HYBRIDE
    print("Calcul des prédictions Hybrides...")
    # XGBoost
    with open(MODELS_DIR / 'xgb_q50.pkl', 'rb') as f:
        xgb_model = pickle.load(f)
    FEATURE_COLS = [c for c in df.columns if c not in ['square_id', 'slot_30m', 'target_1h']]
    xgb_preds = xgb_model.predict(test_df[FEATURE_COLS].values)
    
    # Prophet
    base_date = pd.Timestamp('2013-11-01')
    train_prophet = train_df.copy()
    train_prophet['ds'] = base_date + pd.to_timedelta(train_prophet['slot_30m'], unit='s')
    train_prophet = train_prophet.rename(columns={'internet_volume': 'y'})
    
    m = Prophet(daily_seasonality=True).fit(train_prophet[['ds', 'y']])
    future = m.make_future_dataframe(periods=len(test_df), freq='30min')
    prophet_preds = m.predict(future).iloc[-len(test_df):]['yhat'].values
    
    hybrid_preds = (0.9 * xgb_preds) + (0.1 * prophet_preds)
    
    # 3. Résultats
    y_true = test_df['target_1h'].values
    
    print(f"\n--- RÉSULTATS ÉTUDE DE CAS (Cellule {top_cell}) ---")
    print(f"MAE SARIMA  : {mean_absolute_error(y_true, sarima_preds):.2f} Mo")
    print(f"MAE HYBRIDE : {mean_absolute_error(y_true, hybrid_preds):.2f} Mo")
    print(f"R² HYBRIDE  : {r2_score(y_true, hybrid_preds):.4f}")
    print(f"Gain : {((mean_absolute_error(y_true, sarima_preds) - mean_absolute_error(y_true, hybrid_preds))/mean_absolute_error(y_true, sarima_preds))*100:.1f}%")

if __name__ == "__main__":
    main()
