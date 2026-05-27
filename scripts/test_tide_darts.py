import polars as pl
import pandas as pd
import numpy as np
from darts import TimeSeries
from darts.models import TiDEModel
from darts.dataprocessing.transformers import Scaler
from sklearn.metrics import mean_absolute_error, r2_score
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

ROOT = Path(r'C:\Users\hp\OneDrive\Desktop\projectTimeSeries')
DATA_PATH = ROOT / 'data' / 'processed' / 'features_target_600cells.parquet'

print("--- Chargement des données ---")
df = pl.read_parquet(DATA_PATH).sort(['square_id', 'slot_30m'])
raw_min = df['slot_30m'].min()
df = df.with_columns((((pl.col('slot_30m') - raw_min)//86400)+1).cast(pl.Int32).alias('day_idx'))

# Test on 3 cells for TiDE (it can be slow to train)
sample_cells = df['square_id'].unique().to_list()[:3]
results = []

for cid in sample_cells:
    print(f"\nEntraînement TiDE pour cellule {cid}...")
    cell_data = df.filter(pl.col('square_id') == cid).to_pandas()
    
    # Darts requires a datetime index or a RangeIndex
    # We'll use a dummy datetime starting from 2013-11-01
    base_date = pd.Timestamp('2013-11-01')
    cell_data['ds'] = base_date + pd.to_timedelta(cell_data['slot_30m'], unit='s')
    
    series = TimeSeries.from_dataframe(cell_data, 'ds', 'internet_volume', freq='30min')
    
    # Covariates: hour and weekend
    cell_data['hour'] = cell_data['ds'].dt.hour
    cell_data['is_weekend'] = (cell_data['ds'].dt.dayofweek >= 5).astype(int)
    covariates = TimeSeries.from_dataframe(cell_data, 'ds', ['hour', 'is_weekend'], freq='30min')
    
    # Split
    train_size = len(cell_data[cell_data['day_idx'] <= 48])
    train, test = series.split_before(train_size)
    train_cov, test_cov = covariates.split_before(train_size)
    
    # Scaling
    scaler = Scaler()
    train_scaled = scaler.fit_transform(train)
    test_scaled = scaler.transform(test)
    
    # TiDE Model
    model = TiDEModel(
        input_chunk_length=48, # 24h context
        output_chunk_length=2, # 1h prediction
        n_epochs=20,
        batch_size=32,
        random_state=42,
        pl_trainer_kwargs={"accelerator": "cpu", "enable_progress_bar": False}
    )
    
    model.fit(train_scaled, past_covariates=covariates)
    
    # Predict
    pred_scaled = model.predict(n=len(test), series=train_scaled, past_covariates=covariates)
    pred = scaler.inverse_transform(pred_scaled)
    
    y_true = test.values().flatten()
    y_pred = pred.values().flatten()
    
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    print(f"Cell {cid} - MAE: {mae:.2f}, R²: {r2:.4f}")
    results.append({'mae': mae, 'r2': r2})

avg_mae = np.mean([r['mae'] for r in results])
avg_r2 = np.mean([r['r2'] for r in results])

print(f"\n--- Résultats TiDE (Darts) ---")
print(f"MAE moyenne: {avg_mae:.2f} Mo")
print(f"R² moyen: {avg_r2:.4f}")
