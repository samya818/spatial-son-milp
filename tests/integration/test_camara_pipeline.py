"""
Test d'intégration End-to-End CAMARA Open Gateway dans la boucle fermée WiseNet V1.5.
Valide la chaîne complète :
Footfall/QuadKey -> Ingestion Trafic -> Optimisation MILP -> Déclencheur QoD de Secours.
"""

import pytest
from src.camara.client import CamaraClient
from src.camara.footfall_client import FootfallClient
from src.camara.qod_trigger import QoDTriggerManager
from src.optimization.milp_engine_v1_5 import MilpEngineV15

def test_closed_loop_camara_pipeline():
    # 1. Initialisation des composants
    camara_client = CamaraClient(mock_mode=True)
    footfall_client = FootfallClient(mock_mode=True)
    qod_manager = QoDTriggerManager(camara_client=camara_client, min_residual_mo=200.0, max_sessions_per_slot=5)
    milp_engine = MilpEngineV15(solver_name="cbc")

    # 2. Ingestion exogène de la demande via Footfall (Population Density)
    squares = ["4849", "4850", "4851"]
    quadkeys = [footfall_client.get_quadkey_for_square(sq) for sq in squares]
    footfall_res = footfall_client.get_realtime_footfall(quadkeys)
    assert footfall_res["status"] == "success"

    # Calibration du trafic par maille (MB)
    calibrated_traffic = {}
    for sq, qk in zip(squares, quadkeys):
        dev_count = footfall_res["data"][qk]["device_count"]
        # On force un volume pour simuler une saturation sur 4849
        base_mb = 12000.0 if sq == "4849" else 4000.0
        calibrated_traffic[sq] = footfall_client.calibrate_demand_traffic(sq, dev_count, hour_slot=14, baseline_milan_mb=base_mb)

    # 3. Topologie et simulateur spatial synthétique
    cells_capacity = {
        "site_001_sec1_F1_1800": 6000.0,
        "site_001_sec2_F1_1800": 8000.0,
        "site_002_sec1_F1_1800": 5000.0
    }
    
    fractions_data = {
        "4849": {
            "master_cell": "site_001_sec1_F1_1800",
            "offsets": {
                "0.0": {"stays": 1.0, "target_cells": {}},
                "1.5": {"stays": 0.6, "target_cells": {"site_001_sec2_F1_1800": 0.4}},
                "3.0": {"stays": 0.4, "target_cells": {"site_001_sec2_F1_1800": 0.6}}
            }
        },
        "4850": {
            "master_cell": "site_001_sec2_F1_1800",
            "offsets": {
                "0.0": {"stays": 1.0, "target_cells": {}},
                "1.5": {"stays": 0.8, "target_cells": {"site_001_sec1_F1_1800": 0.2}},
                "3.0": {"stays": 0.6, "target_cells": {"site_001_sec1_F1_1800": 0.4}}
            }
        },
        "4851": {
            "master_cell": "site_002_sec1_F1_1800",
            "offsets": {
                "0.0": {"stays": 1.0, "target_cells": {}},
                "1.5": {"stays": 1.0, "target_cells": {}},
                "3.0": {"stays": 1.0, "target_cells": {}}
            }
        }
    }

    # 4. Résolution MILP
    milp_result = milp_engine.build_and_solve(
        predicted_traffic=calibrated_traffic,
        fractions_data=fractions_data,
        cells_capacity=cells_capacity,
        delta_levels=[0.0, 1.5, 3.0]
    )
    assert milp_result["status"] == "optimal"
    assert "decisions" in milp_result

    # 5. Déclenchement du Filet de Sécurité QoD CAMARA
    qod_report = qod_manager.process_milp_residuals(
        milp_decisions=milp_result["decisions"],
        cells_capacity=cells_capacity
    )
    assert qod_report["status"] == "completed"

    # Vérification : si une cellule reste saturée, des sessions QoD sont allouées
    if qod_report["congested_cells_count"] > 0:
        assert qod_report["triggered_sessions_count"] > 0
        assert len(qod_manager.active_sessions) > 0
        # Vérification qu'une session a le bon statut
        first_session = qod_report["sessions"][0]
        fetched = camara_client.get_qod_session(first_session["session_id"])
        assert fetched["qosStatus"] == "AVAILABLE"

    # Nettoyage
    cleaned = qod_manager.cleanup_expired_sessions()
    assert len(qod_manager.active_sessions) == 0
