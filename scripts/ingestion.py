from __future__ import annotations

from pathlib import Path
from typing import Iterable

import polars as pl


ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "dataverse_files"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "work_600cells.parquet"

# Seed fixe pour rendre la sélection reproductible.
RANDOM_SEED = 42


def list_raw_files(raw_dir: Path) -> list[Path]:
    files = sorted(raw_dir.glob("sms-call-internet-mi-*.txt"))
    if not files:
        raise FileNotFoundError(f"Aucun fichier brut trouvé dans {raw_dir}")
    return files


def optional_subset(files: Iterable[Path], n_days: int | None) -> list[Path]:
    files = list(files)
    if n_days is None:
        return files
    if n_days <= 0:
        raise ValueError("--n-days doit etre > 0")
    return files[: min(n_days, len(files))]


def quadrant_expr() -> pl.Expr:
    # Stratification geographique simplifiee en 4 quadrants de la grille 100x100.
    return (
        pl.when(pl.col("square_id") <= 2500)
        .then(pl.lit(1))
        .when(pl.col("square_id") <= 5000)
        .then(pl.lit(2))
        .when(pl.col("square_id") <= 7500)
        .then(pl.lit(3))
        .otherwise(pl.lit(4))
        .alias("quadrant")
    )


def build_work_dataset(files: list[Path]) -> pl.DataFrame:
    # Pourquoi aggregation multi-country_code ?
    # Chaque ligne distingue la nationalite SIM. Pour estimer le trafic total reel
    # d'une cellule, on doit sommer tous les country_code.
    lf = (
        pl.scan_csv(
            [str(p) for p in files],
            separator="\t",
            has_header=False,
            schema_overrides={
                "column_1": pl.Int32,   # square_id
                "column_2": pl.Int64,   # time_interval (ms epoch)
                "column_3": pl.Int32,   # country_code
                "column_4": pl.Float64,  # sms_in
                "column_5": pl.Float64,  # sms_out
                "column_6": pl.Float64,  # call_in
                "column_7": pl.Float64,  # call_out
                "column_8": pl.Float64,  # internet
            },
            null_values=[""],
            ignore_errors=True,
            rechunk=False,
        )
        .rename(
            {
                "column_1": "square_id",
                "column_2": "time_interval",
                "column_3": "country_code",
                "column_4": "sms_in",
                "column_5": "sms_out",
                "column_6": "call_in",
                "column_7": "call_out",
                "column_8": "internet",
            }
        )
        .with_columns(
            [
                pl.col("sms_in").fill_null(0.0),
                pl.col("call_in").fill_null(0.0),
                pl.col("internet").fill_null(0.0),
                # Pourquoi 30 min ?
                # C'est le compromis choisi: moins de bruit que 10 min, sans perdre
                # l'information utile pour predire a 30 min et 1h.
                ((pl.col("time_interval") // 1000) // 1800 * 1800).alias("slot_30m"),
            ]
        )
        .group_by(["square_id", "slot_30m"])
        .agg(
            [
                pl.sum("internet").alias("internet_volume"),
                pl.sum("sms_in").alias("sms_in"),
                pl.sum("call_in").alias("call_in"),
            ]
        )
    )

    aggregated = lf.collect(engine="streaming")

    # On conserve uniquement les cellules suffisamment completes
    # pour eviter des series trop trouees avant modelisation.
    t_min = aggregated.select(pl.min("slot_30m")).item()
    t_max = aggregated.select(pl.max("slot_30m")).item()
    expected_slots = int((t_max - t_min) // 1800 + 1)

    completeness = (
        aggregated.group_by("square_id")
        .agg(pl.col("slot_30m").n_unique().alias("n_slots"))
        .with_columns((pl.col("n_slots") / expected_slots * 100).alias("completeness_pct"))
    )
    eligible_cells = completeness.filter(pl.col("completeness_pct") >= 95).select("square_id")
    aggregated = aggregated.join(eligible_cells, on="square_id", how="inner")

    # Activite moyenne par cellule pour selection 500 actives + 100 calmes.
    activity = (
        aggregated.group_by("square_id")
        .agg(pl.mean("internet_volume").alias("mean_internet_volume"))
        .with_columns(quadrant_expr())
    )

    top_500 = activity.sort("mean_internet_volume", descending=True).head(500)
    top_ids = set(top_500["square_id"].to_list())

    quiet_pool = activity.filter(~pl.col("square_id").is_in(list(top_ids)))
    quiet_by_quadrant = []
    for q in [1, 2, 3, 4]:
        q_df = quiet_pool.filter(pl.col("quadrant") == q)
        # 100 cellules calmes, 25 par quadrant.
        quiet_by_quadrant.append(
            q_df.sample(n=min(25, q_df.height), seed=RANDOM_SEED + q, shuffle=True)
        )

    quiet_100 = pl.concat(quiet_by_quadrant)
    if quiet_100.height < 100:
        missing = 100 - quiet_100.height
        already = set(quiet_100["square_id"].to_list()) | top_ids
        extra = quiet_pool.filter(~pl.col("square_id").is_in(list(already))).sample(
            n=min(missing, quiet_pool.height), seed=RANDOM_SEED + 99, shuffle=True
        )
        quiet_100 = pl.concat([quiet_100, extra])

    selected_ids = top_500.select("square_id").vstack(quiet_100.select("square_id"))
    selected_ids = selected_ids.unique()

    if selected_ids.height != 600:
        raise ValueError(
            f"Selection inattendue: {selected_ids.height} cellules au lieu de 600."
        )

    work_df = aggregated.join(selected_ids, on="square_id", how="inner").sort(
        ["square_id", "slot_30m"]
    )
    return work_df


def quality_checks(work_df: pl.DataFrame) -> dict[str, float | int | str]:
    duplicates = work_df.select(
        pl.len() - pl.struct(["square_id", "slot_30m"]).n_unique()
    ).item()

    t_min = work_df.select(pl.col("slot_30m").min()).item()
    t_max = work_df.select(pl.col("slot_30m").max()).item()
    expected_slots = int((t_max - t_min) // 1800 + 1)

    completeness = (
        work_df.group_by("square_id")
        .agg(pl.col("slot_30m").n_unique().alias("n_slots"))
        .with_columns((pl.col("n_slots") / expected_slots * 100).alias("completeness_pct"))
    )

    min_completeness = float(completeness.select(pl.min("completeness_pct")).item())
    pct_above_95 = float(
        completeness.select((pl.col("completeness_pct") >= 95).mean() * 100).item()
    )

    return {
        "n_rows": work_df.height,
        "n_cells": int(work_df.select(pl.col("square_id").n_unique()).item()),
        "n_slots_total": int(work_df.select(pl.col("slot_30m").n_unique()).item()),
        "duplicates": int(duplicates),
        "slot_30m_min_epoch_s": int(t_min),
        "slot_30m_max_epoch_s": int(t_max),
        "expected_slots_per_cell": expected_slots,
        "min_completeness_pct": round(min_completeness, 2),
        "cells_above_95pct_completeness": round(pct_above_95, 2),
    }


def main(n_days: int | None = None) -> None:
    files = list_raw_files(RAW_DIR)
    files_to_read = optional_subset(files, n_days=n_days)

    print(f"Fichiers lus: {len(files_to_read)} / {len(files)}")
    work_df = build_work_dataset(files_to_read)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    work_df.write_parquet(OUTPUT_PATH, compression="zstd")

    checks = quality_checks(work_df)
    print("\n=== CONTROLES QUALITE ===")
    for k, v in checks.items():
        print(f"{k}: {v}")
    print(f"\nParquet ecrit: {OUTPUT_PATH}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingestion + reduction Telecom Milan")
    parser.add_argument(
        "--n-days",
        type=int,
        default=None,
        help="Limiter aux N premiers jours pour test rapide (optionnel).",
    )
    args = parser.parse_args()
    main(n_days=args.n_days)
