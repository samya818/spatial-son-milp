import pytest
import polars as pl
import numpy as np
# from src.spatial.transfer_matrix import TransferManager 
import json
from pathlib import Path

RESEARCH_DIR = Path.cwd() / "research"

def test_mass_conservation():
    """
    Vérifie que la somme des fractions de délestage pour chaque cellule est égale à 1.0.
    C'est la garantie physique que le trafic n'est ni créé ni détruit.
    """
    fractions_path = RESEARCH_DIR / "offline" / "fractions_1024.parquet"
    fractions_df = pl.read_parquet(fractions_path)
    
    # Groupement par master_id, square_id et delta_dB
    sums = (fractions_df.group_by(['master_id', 'square_id', 'delta_dB'])
            .agg(pl.col('fraction').sum().alias('total_fraction')))
    
    # Vérification avec une tolérance flottante
    assert all((sums['total_fraction'] - 1.0).abs() < 1e-9), "Mass conservation failed: fractions sum != 1.0"

def test_antenna_coverage_consistency():
    """
    Vérifie que toutes les cellules couvertes par une antenne maître 
    ont des entrées dans la matrice de transfert.
    """
    map_path = RESEARCH_DIR / "data" / "processed" / "cell_antenna_map_1024.json"
    with open(map_path, "r") as f:
        coverage = json.load(f)
    
    fractions_path = RESEARCH_DIR / "offline" / "fractions_1024.parquet"
    fractions_df = pl.read_parquet(fractions_path)
    unique_cells_in_matrix = set(fractions_df['square_id'].unique().to_list())
    
    all_cells_in_map = set()
    for cells in coverage.values():
        all_cells_in_map.update(cells)
        
    missing_cells = all_cells_in_map - unique_cells_in_matrix
    assert len(missing_cells) == 0, f"Missing cells in transfer matrix: {missing_cells}"
