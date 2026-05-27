import pytest
import polars as pl
from src.simulation.engine import SimulationEngine

@pytest.fixture
def mock_data():
    fractions = pl.DataFrame({
        "square_id": [1, 2],
        "master_id": ["A1", "A2"],
        "target_ant": ["A1", "A2"],
        "delta_level": [0, 0],
        "delta_dB": [0.0, 0.0],
        "fraction": [1.0, 1.0]
    })
    topology = {"antennas": {"A1": {"capacity_mo": 100}, "A2": {"capacity_mo": 100}}}
    slot_df = pl.DataFrame({
        "square_id": [1, 2],
        "internet_volume": [120.0, 80.0]
    })
    return fractions, topology, slot_df

def test_engine_static_baseline(mock_data):
    fractions, topology, slot_df = mock_data
    engine = SimulationEngine(fractions, topology)
    
    physical_caps = {"A1": 100.0, "A2": 100.0}
    trigger_thresholds = physical_caps.copy()
    
    res = engine.run_slot(slot_df, "static", 0, physical_caps, trigger_thresholds)
    
    assert res.status == "success"
    assert res.n_congested_baseline == 1
    assert res.unsatisfied_baseline == 20.0
    assert res.n_congested == 1
    assert res.unsatisfied == 20.0
    assert res.mass_error < 1e-6

def test_engine_greedy(mock_data):
    # Setup fractions for delta_level 1
    # For A1, delta_level 1: 50% stays (A1), 50% moves (A2)
    # For A2, delta_level 1: 100% stays (A2)
    fractions = pl.DataFrame({
        "square_id": [1, 1, 1, 2, 2],
        "master_id": ["A1", "A1", "A1", "A2", "A2"],
        "target_ant": ["A1", "A1", "A2", "A2", "A2"],
        "delta_level": [0, 1, 1, 0, 1],
        "delta_dB": [0.0, 3.0, 3.0, 0.0, 3.0],
        "fraction": [1.0, 0.5, 0.5, 1.0, 1.0]
    })
    topology = {"antennas": {"A1": {"capacity_mo": 100}, "A2": {"capacity_mo": 100}}}
    slot_df = pl.DataFrame({
        "square_id": [1, 2],
        "internet_volume": [120.0, 80.0]
    })
    
    engine = SimulationEngine(fractions, topology)
    physical_caps = {"A1": 100.0, "A2": 100.0}
    trigger_thresholds = {"A1": 110.0, "A2": 110.0}
    
    # A1 is at 120 > 110, so it should trigger delta_level 1
    # 50% of 120 (60) stays on A1, 50% (60) goes to A2.
    # A1 final = 60
    # A2 final = 80 + 60 = 140
    
    res = engine.run_slot(slot_df, "greedy", 1, physical_caps, trigger_thresholds)
    
    assert res.decisions == 1
    a1_res = res.antenna_results.filter(pl.col("ant_id")=="A1")
    a2_res = res.antenna_results.filter(pl.col("ant_id")=="A2")
    
    assert a1_res["final_volume"][0] == 60.0
    assert a2_res["final_volume"][0] == 140.0
    assert res.n_congested == 1 # Now A2 is congested
    assert res.unsatisfied == 40.0
