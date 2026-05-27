import polars as pl
from pathlib import Path
import os

def run_ingestion():
    ROOT = Path.cwd()
    RAW_DIR = ROOT / "data" / "raw"
    PROCESSED_DIR = ROOT / "data" / "processed"
    OUTPUT_PATH = PROCESSED_DIR / "work_1024cells.parquet"
    
    if not PROCESSED_DIR.exists():
        PROCESSED_DIR.mkdir(parents=True)

    raw_files = sorted(RAW_DIR.glob("sms-call-internet-mi-*.txt"))
    print(f"Fichiers détectés: {len(raw_files)}")
    
    # Square IDs for 32x32 block (rows 35-66, cols 35-66)
    bloc_square_ids = []
    for i in range(35, 67):
        for j in range(35, 67):
            sid = i * 100 + j + 1
            bloc_square_ids.append(sid)
    
    print(f"Traitement pour {len(bloc_square_ids)} cellules (bloc 32x32)...")

    # Ingestion avec filtrage immédiat pour économiser la RAM
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
        # Filtrage précoce
        .filter(pl.col("square_id").is_in(bloc_square_ids))
        .fill_null(0.0)
        # Slot 30 min
        .with_columns([
            ((pl.col("t_ms") // 1000 // 1800) * 1800).alias("slot_30m")
        ])
        # Agrégation
        .group_by(["square_id", "slot_30m"])
        .agg([
            pl.col("internet_volume").sum(),
            pl.col("sms_in").sum(),
            pl.col("call_in").sum()
        ])
        .sort(["slot_30m", "square_id"])
    )

    print("Exécution du pipeline Polars (streaming)...")
    df = lf.collect(streaming=True)
    print(f"Lignes après agrégation: {len(df)}")
    
    df.write_parquet(OUTPUT_PATH)
    print(f"Sauvegardé dans {OUTPUT_PATH}")

if __name__ == "__main__":
    run_ingestion()
