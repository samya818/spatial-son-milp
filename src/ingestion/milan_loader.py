import polars as pl
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MilanLoader:
    def __init__(self, raw_dir: Path, processed_dir: Path):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        
    def ingest_dense_block(self, row_range=(35, 67), col_range=(35, 67), output_name="work_1024cells.parquet"):
        """
        Ingère les données brutes de Milan en filtrant sur un bloc dense de mailles.
        Standardisé pour le pipeline 4G/LTE.
        """
        if not self.processed_dir.exists():
            self.processed_dir.mkdir(parents=True)

        raw_files = sorted(self.raw_dir.glob("sms-call-internet-mi-*.txt"))
        if not raw_files:
            raise FileNotFoundError(f"No raw files found in {self.raw_dir}")
            
        logger.info(f"Detected {len(raw_files)} raw files.")
        
        # Generation of square IDs for the contiguous block
        bloc_square_ids = []
        for i in range(row_range[0], row_range[1]):
            for j in range(col_range[0], col_range[1]):
                sid = i * 100 + j + 1
                bloc_square_ids.append(sid)
        
        logger.info(f"Processing for {len(bloc_square_ids)} cells ({row_range[1]-row_range[0]}x{col_range[1]-col_range[0]} block)...")

        lf = (
            pl.scan_csv(
                [str(p) for p in raw_files],
                separator="\t",
                has_header=False,
                schema_overrides={
                    "column_1": pl.Int32,
                    "column_2": pl.Int64,
                    "column_3": pl.Int32,
                    "column_4": pl.Float64,
                    "column_5": pl.Float64,
                    "column_6": pl.Float64,
                    "column_7": pl.Float64,
                    "column_8": pl.Float64,
                },
                null_values=[""],
                ignore_errors=True,
                rechunk=False,
            )
            .rename({
                "column_1": "square_id",
                "column_2": "t_ms",
                "column_4": "sms_in",
                "column_6": "call_in",
                "column_8": "internet_volume"
            })
            .filter(pl.col("square_id").is_in(bloc_square_ids))
            .fill_null(0.0)
            .with_columns([
                ((pl.col("t_ms") // 1000 // 1800) * 1800).alias("slot_30m")
            ])
            .group_by(["square_id", "slot_30m"])
            .agg([
                pl.col("internet_volume").sum(),
                pl.col("sms_in").sum(),
                pl.col("call_in").sum()
            ])
            .sort(["slot_30m", "square_id"])
        )

        logger.info("Executing Polars streaming pipeline...")
        df = lf.collect(streaming=True)
        
        output_path = self.processed_dir / output_name
        df.write_parquet(output_path)
        logger.info(f"Aggregated data saved to {output_path} ({len(df)} rows).")
        return output_path
