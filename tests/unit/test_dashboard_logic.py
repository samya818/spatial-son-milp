import pytest
import polars as pl
from scripts.dashboard.data_loader import compute_antenna_aggregates, load_traffic_data

def test_load_traffic_data():
    """Verifies that traffic data is loaded correctly (or falls back to mock)."""
    df = load_traffic_data()
    assert isinstance(df, pl.DataFrame)
    assert not df.is_empty()
    assert "internet_volume" in df.columns
    assert "slot_30m" in df.columns

def test_antenna_aggregation():
    # Arrange
    df = pl.DataFrame({
        "square_id": [1, 2, 3],
        "slot_30m": [100, 100, 100],
        "internet_volume": [10.0, 20.0, 30.0]
    })
    mapping = {1: "A001", 2: "A001", 3: "A002"}
    
    # Act
    result = compute_antenna_aggregates(df, mapping)
    
    # Assert
    a001_vol = result.filter(pl.col("ant_id") == "A001")["internet_volume"][0]
    a002_vol = result.filter(pl.col("ant_id") == "A002")["internet_volume"][0]
    
    assert a001_vol == 30.0
    assert a002_vol == 30.0
