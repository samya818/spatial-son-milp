import polars as pl
from pathlib import Path

def get_time_slot_type(hour_slot):
    # hour_slot is 0-47
    h = hour_slot / 2
    if h < 6: return 0    # Nuit
    elif h < 12: return 1 # Matin
    elif h < 19: return 2 # Après-midi
    else: return 3        # Soir

def run_nominal():
    ROOT = Path.cwd()
    input_path = ROOT / 'data' / 'processed' / 'work_1024cells.parquet'
    output_path = ROOT / 'data' / 'processed' / 'nominal_capacities_1024.parquet'
    
    print(f"Chargement de {input_path}...")
    df = pl.read_parquet(input_path)
    
    nominal_caps = (
        df.with_columns([
            (pl.col('slot_30m') % 86400 // 1800).alias('hour_slot'),
            ((pl.col('slot_30m') // 86400) % 7 >= 5).cast(pl.Int8).alias('is_weekend'),
        ])
        .with_columns(
            pl.col('hour_slot').map_elements(get_time_slot_type, return_dtype=pl.Int8).alias('plage')
        )
        .group_by(['square_id', 'plage', 'is_weekend'])
        .agg(pl.col('internet_volume').quantile(0.90).alias('nominal_capacity'))
    )
    
    nominal_caps.write_parquet(output_path)
    print(f"{len(nominal_caps)} seuils calculés et sauvegardés dans {output_path}")

if __name__ == "__main__":
    run_nominal()
