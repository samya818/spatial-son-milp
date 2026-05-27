import polars as pl
from prophet import Prophet
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score
from pathlib import Path

ROOT = Path(r'C:\Users\hp\OneDrive\Desktop\projectTimeSeries')
DATA_PATH = ROOT / 'data' / 'processed' / 'features_target_600cells.parquet'

df = pl.read_parquet(DATA_PATH).sort(['square_id', 'slot_30m'])
raw_min = df['slot_30m'].min()
df = df.with_columns((((pl.col('slot_30m') - raw_min)//86400)+1).cast(pl.Int32).alias('day_idx'))

# Test on 10 cells to get a good average
sample_cells = df['square_id'].unique().to_list()[:10]
results = []

print(f"Évaluation de Prophet sur {len(sample_cells)} cellules...")

for cid in sample_cells:
    cell_data = df.filter(pl.col('square_id') == cid).to_pandas()
    base_date = pd.Timestamp('2013-11-01')
    cell_data['ds'] = base_date + pd.to_timedelta(cell_data['slot_30m'], unit='s')
    cell_data = cell_data.rename(columns={'internet_volume': 'y'})
    
    train = cell_data[cell_data['day_idx'] <= 48]
    test = cell_data[cell_data['day_idx'] > 48]
    
    if len(test) == 0: continue
    
    m = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
    m.fit(train[['ds', 'y']])
    
    future = m.make_future_dataframe(periods=len(test), freq='30min')
    forecast = m.predict(future)
    
    y_true = test['y'].values
    y_pred = forecast.iloc[-len(test):]['yhat'].values
    
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    results.append({'mae': mae, 'r2': r2})

avg_mae = np.mean([r['mae'] for r in results])
avg_r2 = np.mean([r['r2'] for r in results])

print(f"\n--- Résultats Prophet ---")
print(f"MAE moyenne: {avg_mae:.2f} Mo")
print(f"R² moyen: {avg_r2:.4f}")
