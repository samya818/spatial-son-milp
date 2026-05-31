import polars as pl
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.metrics import mean_absolute_error, r2_score
from prophet import Prophet
import xgboost as xgb
from joblib import Parallel, delayed
import warnings
import time

warnings.filterwarnings("ignore")

# Configuration
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'data' / 'processed' / 'features_target_600cells.parquet'
MODELS_DIR = ROOT / 'models'

def train_predict_prophet(cid, cell_data, split_day):
    try:
        # Preparation
        base_date = pd.Timestamp('2013-11-01')
        cell_data['ds'] = base_date + pd.to_timedelta(cell_data['slot_30m'], unit='s')
        cell_data = cell_data.rename(columns={'internet_volume': 'y'})
        
        train = cell_data[cell_data['day_idx'] <= split_day][['ds', 'y']]
        test = cell_data[cell_data['day_idx'] > split_day]
        
        if len(train) < 10 or len(test) == 0:
            return cid, np.zeros(len(test))
            
        m = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
        m.fit(train)
        
        future = m.make_future_dataframe(periods=len(test), freq='30min')
        forecast = m.predict(future)
        return cid, forecast.iloc[-len(test):]['yhat'].values
    except Exception as e:
        return cid, None

def main():
    start_time = time.time()
    print("--- Lancement de l'Évaluation Hybride Globale (499 cellules) ---")
    
    df = pl.read_parquet(DATA_PATH).sort(['square_id', 'slot_30m'])
    raw_min = df['slot_30m'].min()
    df = df.with_columns((((pl.col('slot_30m') - raw_min)//86400)+1).cast(pl.Int32).alias('day_idx'))
    
    # Correction du split dynamique
    max_day = df['day_idx'].max()
    split_day = max_day - 7
    print(f"Split: Jours 1-{split_day} (Train), Jours {split_day+1}-{max_day} (Test)")
    
    train_df = df.filter(pl.col('day_idx') <= split_day)
    test_df = df.filter(pl.col('day_idx') > split_day)
    
    FEATURE_COLS = [c for c in df.columns if c not in ['square_id', 'slot_30m', 'day_idx', 'target_1h']]
    TARGET = 'target_1h'
    
    # 1. XGBoost
    print("Étape 1: Prédictions XGBoost...")
    with open(MODELS_DIR / 'xgb_q50.pkl', 'rb') as f:
        xgb_model = pickle.load(f)
    xgb_preds = xgb_model.predict(test_df.select(FEATURE_COLS).to_numpy())
    
    # 2. Prophet (Parallélisé)
    print(f"Étape 2: Calcul Prophet pour {df['square_id'].n_unique()} cellules (Parallélisation active)...")
    unique_cells = df['square_id'].unique().sort().to_list()
    
    # Préparation des données pour chaque tâche
    tasks = []
    for cid in unique_cells:
        cell_data = df.filter(pl.col('square_id') == cid).to_pandas()
        tasks.append((cid, cell_data, split_day))
    
    # Exécution parallèle (N_jobs=-1 utilise tous les coeurs)
    results = Parallel(n_jobs=-1)(delayed(train_predict_prophet)(*task) for task in tasks)
    
    prophet_preds_dict = {cid: preds for cid, preds in results if preds is not None}
    
    # 3. Aggregation et Scoring
    print("Étape 3: Fusion et Calcul des Métriques...")
    y_true_all = []
    hybrid_preds_all = []
    
    w_xgb = 0.9
    w_prophet = 0.1
    
    for cid in unique_cells:
        if cid not in prophet_preds_dict: continue
        
        c_test = test_df.filter(pl.col('square_id') == cid)
        y_true = c_test[TARGET].to_numpy()
        
        # XGB preds pour cette cellule (extraction par index)
        idx = test_df.with_row_index().filter(pl.col('square_id') == cid)['index'].to_list()
        c_xgb_preds = xgb_preds[idx]
        
        c_prophet_preds = prophet_preds_dict[cid]
        
        # Vérification taille (parfois Prophet peut avoir un léger décalage si slots manquants)
        min_len = min(len(y_true), len(c_xgb_preds), len(c_prophet_preds))
        y_true = y_true[:min_len]
        c_hybrid = (w_xgb * c_xgb_preds[:min_len]) + (w_prophet * c_prophet_preds[:min_len])
        
        y_true_all.extend(y_true)
        hybrid_preds_all.extend(c_hybrid)
    
    y_true_all = np.array(y_true_all)
    hybrid_preds_all = np.array(hybrid_preds_all)
    
    final_mae = mean_absolute_error(y_true_all, hybrid_preds_all)
    final_r2 = r2_score(y_true_all, hybrid_preds_all)
    
    elapsed = (time.time() - start_time) / 60
    print(f"\n--- SCORE FINAL RÉSEAU COMPLET (499 cellules) ---")
    print(f"MAE Hybride: {final_mae:.2f} Mo")
    print(f"R² Hybride: {final_r2:.4f}")
    print(f"Temps total d'exécution: {elapsed:.2f} minutes")

if __name__ == "__main__":
    main()
