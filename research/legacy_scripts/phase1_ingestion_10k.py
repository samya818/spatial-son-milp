import polars as pl
from pathlib import Path
import gc
import os

def run_ingestion_10k():
    ROOT = Path.cwd()
    RAW_DIR = ROOT / "data" / "raw"
    PROCESSED_DIR = ROOT / "data" / "processed"
    OUTPUT_PATH = PROCESSED_DIR / "work_10000cells.parquet"
    
    if not PROCESSED_DIR.exists():
        PROCESSED_DIR.mkdir(parents=True)

    raw_files = sorted(RAW_DIR.glob("sms-call-internet-mi-*.txt"))
    print(f"Fichiers détectés: {len(raw_files)}")
    
    # 1. Pipeline d'agrégation initial (Lazy)
    # On définit le schéma pour éviter les types mixtes
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
    )

    print("Phase 1.1 : Calcul de la complétude des cellules...")
    # On a besoin de savoir combien de slots chaque cellule possède
    # pour filtrer celles qui ont >= 95% de données (2827 slots sur 2976 attendus)
    # On fait une première passe légère
    completeness = (
        lf.group_by("square_id")
        .agg(pl.count().alias("n_slots"))
        .filter(pl.col("n_slots") >= 2827)
        .collect()
    )
    eligible_cells = completeness["square_id"].to_list()
    print(f"Cellules éligibles (>= 95% complétude) : {len(eligible_cells)}/10000")
    
    del completeness
    gc.collect()

    print("Phase 1.2 : Extraction finale et sauvegarde (streaming)...")
    # Filtrage final et sink
    (
        lf.filter(pl.col("square_id").is_in(eligible_cells))
        .sort(["slot_30m", "square_id"])
        .sink_parquet(OUTPUT_PATH)
    )
    
    print(f"Ingestion terminée. Fichier sauvegardé : {OUTPUT_PATH}")
    print(f"Taille du fichier : {os.path.getsize(OUTPUT_PATH) / 1e6:.2f} Mo")

if __name__ == "__main__":
    run_ingestion_10k()
