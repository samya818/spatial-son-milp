import polars as pl
import math
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FeatureEngineer:
    def __init__(self):
        pass

    def build_features(self, input_path: Path, output_path: Path):
        """
        Génère les caractéristiques temporelles et spatiales pour le modèle 4G/LTE.
        """
        logger.info(f"Loading data from {input_path}...")
        df = pl.read_parquet(input_path)
        
        # 1. Sort
        df = df.sort(['square_id', 'slot_30m'])
        
        # 2. Temporal Features
        df = df.with_columns([
            (pl.col('slot_30m') % 86400 // 1800).alias('hour_slot'),
            ((pl.col('slot_30m') // 86400) % 7).alias('dow'),
        ])
        df = df.with_columns([
            (2 * math.pi * pl.col('hour_slot') / 48).sin().alias('sin_hour'),
            (2 * math.pi * pl.col('hour_slot') / 48).cos().alias('cos_hour'),
            (2 * math.pi * pl.col('dow') / 7).sin().alias('sin_dow'),
            (2 * math.pi * pl.col('dow') / 7).cos().alias('cos_dow'),
            (pl.col('dow') >= 5).cast(pl.Int8).alias('is_weekend'),
        ])
        
        # 3. Lags
        lag_steps = [1, 2, 6, 12, 24, 48, 96, 336]
        for lag in lag_steps:
            df = df.with_columns(
                pl.col('internet_volume').shift(lag).over('square_id').alias(f'lag_{lag}')
            )
        
        # 4. Rolling stats
        windows = {'3h': 6, '6h': 12, '24h': 48}
        for name, w in windows.items():
            shifted = pl.col('internet_volume').shift(1)
            df = df.with_columns([
                shifted.rolling_mean(w).over('square_id').alias(f'roll_mean_{name}'),
                shifted.rolling_std(w).over('square_id').alias(f'roll_std_{name}'),
                shifted.rolling_max(w).over('square_id').alias(f'roll_max_{name}'),
            ])
        
        # 5. Spatial Feature
        logger.info("Computing spatial feature...")
        def get_moore_neighbors(cell_id: int, grid_size: int = 100) -> list[int]:
            row, col = (cell_id - 1) // grid_size, (cell_id - 1) % grid_size
            neighbors = []
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0: continue
                    r, c = row + dr, col + dc
                    if 0 <= r < grid_size and 0 <= c < grid_size:
                        neighbors.append(r * grid_size + c + 1)
            return neighbors

        present_cells = set(df['square_id'].unique().to_list())
        neighbor_map = {cid: [n for n in get_moore_neighbors(cid) if n in present_cells] for cid in present_cells}
        
        edges = []
        for cid, neighbors in neighbor_map.items():
            for n in neighbors:
                edges.append((cid, n))
        edges_df = pl.DataFrame(edges, schema=['square_id', 'neighbor_id'])
        
        spatial_df = (
            df.select(['square_id', 'slot_30m', 'internet_volume'])
            .rename({'square_id': 'neighbor_id', 'internet_volume': 'neighbor_vol'})
            .join(edges_df, on='neighbor_id')
            .group_by(['square_id', 'slot_30m'])
            .agg(pl.col('neighbor_vol').mean().alias('neighbor_mean_t0'))
            .sort(['square_id', 'slot_30m'])
            .with_columns(
                pl.col('neighbor_mean_t0').shift(2).over('square_id').alias('neighbor_mean_t_minus_2')
            )
        )
        
        df = df.join(spatial_df.select(['square_id', 'slot_30m', 'neighbor_mean_t_minus_2']), on=['square_id', 'slot_30m'], how='left')
        
        # 6. Target 1h (t+2)
        df = df.with_columns(
            pl.col('internet_volume').shift(-2).over('square_id').alias('target_1h')
        )
        
        # 7. Final Cleanup
        df = df.drop_nulls()
        logger.info(f"Feature set complete: {df.shape}")
        
        df.write_parquet(output_path)
        logger.info(f"Features saved to {output_path}")
        return output_path
