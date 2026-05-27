import polars as pl
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.metrics import mean_absolute_error, r2_score
import pmdarima as pm
from joblib import Parallel, delayed
import warnings
import time

warnings.filterwarnings("ignore")

ROOT = Path(r'C:\Users\hp\OneDrive\Desktop\projectTimeSeries')
DATA_PATH = ROOT / 'data' / 'processed' / 'features_target_600cells.parquet'
MODELS_DIR = ROOT / 'models'

def run_sarima_cell(cid, cell_data, split_slot):
    try:
        # On utilise les 336 derniers points (1 semaine) pour SARIMA
        train_y = cell_data[cell_data['slot_30m'] <= split_slot]['internet_volume'].to_numpy()[-336:]
        test_y = cell_data[cell_data['slot_30m'] > split_slot]['internet_volume'].to_numpy()
        
        if len(train_y) < 100 or len(test_y) == 0:
            return cid, None
            
        model = pm.auto_arima(train_y, seasonal=True, m=48, 
                              max_p=1, max_q=1, max_P=1, max_Q=0,
                              error_action='ignore', suppress_warnings=True)
        preds = model.predict(n_periods=len(test_y))
        return cid, preds
    except:
        return cid, None

def main():
    start_time = time.time()
    print("--- Benchmark de Rigueur : SARIMA vs HYBRIDE ---")
    
    df = pl.read_parquet(DATA_PATH).sort(['square_id', 'slot_30m'])
    
    # On sélectionne les 20 cellules les plus actives
    top_cells = (df.group_by('square_id')
                 .agg(pl.col('internet_volume').sum())
                 .sort('internet_volume', descending=True)
                 .head(20)['square_id']
                 .to_list())
    
    # Split : les 7 derniers jours (un jour = 86400 secondes)
    max_slot = df['slot_30m'].max()
    split_slot = max_slot - (7 * 86400)
    
    print(f"Cellules actives détectées. Début entraînement SARIMA...")
    
    tasks = []
    for cid in top_cells:
        cell_data = df.filter(pl.col('square_id') == cid).to_pandas()
        tasks.append((cid, cell_data, split_slot))
    
    sarima_results = Parallel(n_jobs=-1)(delayed(run_sarima_cell)(*task) for task in tasks)
    sarima_preds_dict = {cid: preds for cid, preds in sarima_results if preds is not None}
    
    from prophet import Prophet
    def get_prophet_preds(cid, cell_data, split_slot):
        base_date = pd.Timestamp('2013-11-01')
        cell_data['ds'] = base_date + pd.to_timedelta(cell_data['slot_30m'], unit='s')
        cell_data = cell_data.rename(columns={'internet_volume': 'y'})
        m = Prophet(daily_seasonality=True).fit(cell_data[cell_data['slot_30m'] <= split_slot][['ds', 'y']])
        future_len = len(cell_data[cell_data['slot_30m'] > split_slot])
        future = m.make_future_dataframe(periods=future_len, freq='30min')
        return m.predict(future).iloc[-future_len:]['yhat'].values

    with open(MODELS_DIR / 'xgb_q50.pkl', 'rb') as f:
        xgb_model = pickle.load(f)
    
    FEATURE_COLS = [c for c in df.columns if c not in ['square_id', 'slot_30m', 'target_1h']]
    
    y_true_all, sarima_all, hybrid_all = [], [], []
    w_xgb, w_prophet = 0.9, 0.1
    
    print("Calcul des prédictions Hybrides...")
    for cid in top_cells:
        if cid not in sarima_preds_dict: continue
        
        c_full = df.filter(pl.col('square_id') == cid)
        c_test = c_full.filter(pl.col('slot_30m') > split_slot)
        y_true = c_test['target_1h'].to_numpy()
        
        if len(y_true) == 0: continue
        
        c_xgb_preds = xgb_model.predict(c_test.select(FEATURE_COLS).to_numpy())
        c_prophet_preds = get_prophet_preds(cid, c_full.to_pandas(), split_slot)
        
        min_len = min(len(y_true), len(c_xgb_preds), len(c_prophet_preds), len(sarima_preds_dict[cid]))
        
        y_true_all.extend(y_true[:min_len])
        sarima_all.extend(sarima_preds_dict[cid][:min_len])
        hybrid_all.extend((w_xgb * c_xgb_preds[:min_len] + w_prophet * c_prophet_preds[:min_len]))

    print(f"\n--- RÉSULTATS DU BENCHMARK ---")
    print(f"MODELE SARIMA  : MAE = {mean_absolute_error(y_true_all, sarima_all):.2f} Mo")
    print(f"MODELE HYBRIDE : MAE = {mean_absolute_error(y_true_all, hybrid_all):.2f} Mo")
    print(f"R² Hybride : {r2_score(y_true_all, hybrid_all):.4f}")
    print(f"Gain Hybride : {((mean_absolute_error(y_true_all, sarima_all) - mean_absolute_error(y_true_all, hybrid_all))/mean_absolute_error(y_true_all, sarima_all))*100:.1f}%")

if __name__ == "__main__":
    main()
