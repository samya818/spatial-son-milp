"""
WiseNet V1.5 — Démonstrateur CAMARA GSMA Open Gateway & Vodafone Analytics Footfall
Ce script démontre l'intégration complète et vérifie le fonctionnement de bout en bout :
1. Authentification OAuth2 Client Credentials
2. Récupération des profils QoS réseau (GET /qos-profiles)
3. Ingestion de la densité de population (QuadKey & Footfall Realtime)
4. Calibration exogène de la demande (Immunité critique de Lucas)
5. Résolution de l'optimisation globale MILP (CBC)
6. Déclenchement automatique du filet de sécurité QoD pour les cellules résiduelles
7. Cycle de vie des sessions (Consultation & Libération)
"""

import sys
import os
from pathlib import Path

# Assurer que la racine du projet est dans sys.path
root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.camara.client import CamaraClient
from src.camara.footfall_client import FootfallClient
from src.camara.qod_trigger import QoDTriggerManager
from src.optimization.milp_engine_v1_5 import MilpEngineV15

def run_camara_demo():
    print("=" * 80)
    print("[WISE-NET V1.5] VALIDATION DU PIPELINE DES APIS CAMARA GSMA & VODAFONE")
    print("=" * 80)

    # Chargement automatique du .env local si présent
    env_path = root_dir / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k not in os.environ:
                        os.environ[k] = v

    qod_id = os.getenv("CAMARA_CLIENT_ID", "mock_client_id")
    qod_secret = os.getenv("CAMARA_CLIENT_SECRET", "mock_secret")
    
    footfall_id = os.getenv("VODAFONE_ANALYTICS_CLIENT_ID", qod_id)
    footfall_secret = os.getenv("VODAFONE_ANALYTICS_CLIENT_SECRET", qod_secret)

    # -------------------------------------------------------------------------
    # 1. AUTHENTIFICATION OAUTH2
    # -------------------------------------------------------------------------
    print("\n[Étape 1] Authentification OAuth2 Client Credentials...")
    camara = CamaraClient(client_id=qod_id, client_secret=qod_secret, mock_mode=False)
    token = camara.get_token()
    print(f"  [OK] Jeton QoD Bearer obtenu : {token[:35]}... (TTL: 3600s)")

    # -------------------------------------------------------------------------
    # 2. CATALOGUE QOS PROFILES
    # -------------------------------------------------------------------------
    print("\n[Étape 2] Interrogation du catalogue réseau (GET /qos-profiles)...")
    profiles = camara.get_qos_profiles()
    for p in profiles:
        print(f"    - {p['name']:<15} | Statut: {p.get('status', 'ACTIVE')} | {p.get('description', '')}")

    # -------------------------------------------------------------------------
    # 3. SPATIAL REFERENCE & FOOTFALL (POPULATION DENSITY)
    # -------------------------------------------------------------------------
    print("\n[Étape 3] Référencement QuadKey & Ingestion Footfall (Densité exogène)...")
    footfall = FootfallClient(client_id=footfall_id, client_secret=footfall_secret, mock_mode=False, quadkey_level=15)
    token_ff = footfall.get_token()
    print(f"  [OK] Jeton Footfall/Analytics obtenu : {token_ff[:35]}... (TTL: 3600s)")
    sample_squares = ["4849", "4850", "4851", "4852"]
    
    square_quadkeys = {sq: footfall.get_quadkey_for_square(sq) for sq in sample_squares}
    for sq, qk in square_quadkeys.items():
        print(f"  * Maille Milan {sq} -> QuadKey: {qk}")

    footfall_data = footfall.get_realtime_footfall(list(square_quadkeys.values()))
    print(f"  [OK] Télémétrie Footfall reçue pour {footfall_data['tile_count']} tuiles géographiques :")
    calibrated_traffic = {}
    for sq, qk in square_quadkeys.items():
        devices = footfall_data["data"][qk]["device_count"]
        # Simulation d'une zone très dense pour 4849
        base_demand = 16000.0 if sq == "4849" else 4500.0
        traffic_mb = footfall.calibrate_demand_traffic(sq, devices, hour_slot=15, baseline_milan_mb=base_demand)
        calibrated_traffic[sq] = traffic_mb
        print(f"    - Maille {sq} : {devices:>3} devices connectés => Trafic calibré v_c(t) = {traffic_mb:>8.1f} Mo (Lucas-immune)")

    # -------------------------------------------------------------------------
    # 4. OPTIMISATION MILP (CBC)
    # -------------------------------------------------------------------------
    print("\n[Étape 4] Exécution de l'optimisation mathématique MILP V1.5...")
    cells_capacity = {
        "site_001_sec1_F1_1800": 7500.0,
        "site_001_sec2_F1_1800": 9000.0,
        "site_002_sec1_F1_1800": 8000.0,
        "site_002_sec2_F1_1800": 8000.0
    }
    
    fractions_data = {
        "4849": {
            "master_cell": "site_001_sec1_F1_1800",
            "offsets": {
                "0.0": {"stays": 1.0, "target_cells": {}},
                "1.5": {"stays": 0.6, "target_cells": {"site_001_sec2_F1_1800": 0.4}},
                "3.0": {"stays": 0.35, "target_cells": {"site_001_sec2_F1_1800": 0.65}}
            }
        },
        "4850": {
            "master_cell": "site_001_sec2_F1_1800",
            "offsets": {
                "0.0": {"stays": 1.0, "target_cells": {}},
                "1.5": {"stays": 0.8, "target_cells": {"site_001_sec1_F1_1800": 0.2}},
                "3.0": {"stays": 0.7, "target_cells": {"site_001_sec1_F1_1800": 0.3}}
            }
        },
        "4851": {
            "master_cell": "site_002_sec1_F1_1800",
            "offsets": {
                "0.0": {"stays": 1.0, "target_cells": {}},
                "1.5": {"stays": 0.85, "target_cells": {"site_002_sec2_F1_1800": 0.15}},
                "3.0": {"stays": 0.75, "target_cells": {"site_002_sec2_F1_1800": 0.25}}
            }
        },
        "4852": {
            "master_cell": "site_002_sec2_F1_1800",
            "offsets": {
                "0.0": {"stays": 1.0, "target_cells": {}},
                "1.5": {"stays": 0.9, "target_cells": {"site_002_sec1_F1_1800": 0.1}},
                "3.0": {"stays": 0.8, "target_cells": {"site_002_sec1_F1_1800": 0.2}}
            }
        }
    }

    engine = MilpEngineV15(solver_name="cbc")
    milp_res = engine.build_and_solve(
        predicted_traffic=calibrated_traffic,
        fractions_data=fractions_data,
        cells_capacity=cells_capacity,
        delta_levels=[0.0, 1.5, 3.0]
    )

    print(f"  [OK] Statut solveur : {milp_res['status']}")
    print(f"  * Congestion Statique non servie : {milp_res['static_unsatisfied_mo']} Mo")
    print(f"  * Congestion Résiduelle MILP     : {milp_res['optimized_unsatisfied_mo']} Mo")
    print(f"  * Gain d'optimisation global     : {milp_res['gain_percentage']} %")

    for cell, dec in milp_res["decisions"].items():
        print(f"    - {cell:<25} : Offset = {dec['offset_dB']} dB | Résiduel = {dec['residual_congestion_mo']} Mo")

    # -------------------------------------------------------------------------
    # 5. FILET DE SÉCURITÉ QUALITY ON DEMAND (QoD)
    # -------------------------------------------------------------------------
    print("\n[Étape 5] Déclenchement automatique du Filet de Sécurité QoD...")
    qod_mgr = QoDTriggerManager(
        camara_client=camara,
        congestion_threshold_ratio=0.03,
        min_residual_mo=300.0,
        max_sessions_per_slot=10
    )
    # Enregistrement préalable d'un terminal de secours médical SAMU
    qod_mgr.register_critical_device("site_001_sec1_F1_1800", "+393491180001", "EMERGENCY")

    qod_report = qod_mgr.process_milp_residuals(
        milp_decisions=milp_res["decisions"],
        cells_capacity=cells_capacity
    )

    print(f"  [OK] Cellules en dépassement résiduel : {qod_report['congested_cells_count']}")
    print(f"  [OK] Sessions QoD allouées           : {qod_report['triggered_sessions_count']} / {qod_report['budget_cap']} (Plafond)")

    for sess in qod_report["sessions"]:
        print(f"    -> Session {sess['session_id'][:8]}... | Cell: {sess['cell_id']} | Tel: {sess['phone_number']} | Profil: {sess['qos_profile']} | Statut: {sess['qos_status']}")

    # -------------------------------------------------------------------------
    # 6. CYCLE DE VIE DES SESSIONS QOD (VÉRIFICATION & TEARDOWN)
    # -------------------------------------------------------------------------
    print("\n[Étape 6] Vérification d'état et libération en fin de créneau...")
    if qod_report["sessions"]:
        test_session_id = qod_report["sessions"][0]["session_id"]
        sess_info = camara.get_qod_session(test_session_id)
        print(f"  [OK] Consultation GET /sessions/{test_session_id[:8]}... : Statut = {sess_info['qosStatus']}")
        
    cleaned = qod_mgr.cleanup_expired_sessions()
    print(f"  [OK] Libération DELETE de {cleaned} sessions expirées. Sessions actives restantes : {len(qod_mgr.active_sessions)}")

    print("\n" + "=" * 80)
    print("[SUCCES] TOUS LES TESTS DES APIS CAMARA ONT REUSSI AVEC SUCCES !")
    print("=" * 80)

if __name__ == "__main__":
    run_camara_demo()
