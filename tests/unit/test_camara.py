"""
Tests unitaires pour le module CAMARA GSMA Open Gateway / Vodafone Analytics.
Aligne avec la specification officielle Vodafone sandbox (Sept 2026) :
  - Profil urgence : QOS_E (nom CAMARA officiel) ou QOS_EMERGENCY (alias)
  - Token prefix   : mock_bearer_ (conforme client.py mis a jour)
  - Trigger QoD    : profil haut = QOS_E sur sandbox Vodafone
"""

import pytest
from src.camara.client import CamaraClient
from src.camara.footfall_client import (
    FootfallClient,
    lat_lon_to_quadkey,
    quadkey_to_tile_xy
)
from src.camara.qod_trigger import QoDTriggerManager


class TestCamaraClient:

    def test_token_generation_mock(self):
        client = CamaraClient(mock_mode=True)
        token = client.get_token()
        assert token is not None
        # mock_bearer_ est le prefixe du client mis a jour (conforme Vodafone sandbox)
        assert token.startswith("mock_bearer_")
        # Deuxieme appel doit retourner le token cache
        token2 = client.get_token()
        assert token == token2

    def test_get_qos_profiles(self):
        client = CamaraClient(mock_mode=True)
        profiles = client.get_qos_profiles()
        assert isinstance(profiles, list)
        assert len(profiles) >= 3
        profile_names = [p["name"] for p in profiles]
        # Vodafone sandbox: QOS_E = urgence (conforme spec CAMARA officielle)
        # Accepte QOS_E ou QOS_EMERGENCY selon la version du client
        assert any(n in profile_names for n in ("QOS_E", "QOS_EMERGENCY"))
        assert "QOS_L" in profile_names
        assert "QOS_S" in profile_names
        for p in profiles:
            assert "name" in p
            assert "description" in p
            assert p["status"] == "ACTIVE"

    def test_qod_session_lifecycle(self):
        client = CamaraClient(mock_mode=True)
        # Numeros DE/GB pour sandbox Vodafone (mais mock accepte tout)
        phone = "+491234567890"

        # 1. Creation de session
        session = client.create_qod_session(
            phone_number=phone,
            qos_profile="QOS_L",
            duration=1800
        )
        assert "sessionId" in session
        assert session["device"]["phoneNumber"] == phone
        assert session["qosProfile"] == "QOS_L"
        assert session["qosStatus"] == "AVAILABLE"
        sess_id = session["sessionId"]

        # 2. Consultation GET /sessions/{sessionId}
        fetched = client.get_qod_session(sess_id)
        assert fetched["sessionId"] == sess_id
        assert fetched["qosStatus"] == "AVAILABLE"

        # 3. Extension POST /sessions/{sessionId}/extend (NOUVEAU v1.1.0)
        ext = client.extend_qod_session(sess_id, additional_seconds=900)
        assert ext["status"] == "EXTENDED"
        assert ext["newDuration"] == 1800 + 900

        # 4. Suppression DELETE /sessions/{sessionId}
        del_res = client.delete_qod_session(sess_id)
        assert del_res["status"] == "DELETED"

        # 5. Consultation post-suppression -> NOT_FOUND
        not_found = client.get_qod_session(sess_id)
        assert not_found["status"] == "NOT_FOUND"

    def test_retrieve_sessions_by_device(self):
        client = CamaraClient(mock_mode=True)
        phone = "+441234567890"

        # Creer 2 sessions pour le meme device
        s1 = client.create_qod_session(phone, "QOS_S", 60)
        s2 = client.create_qod_session(phone, "QOS_M", 120)

        # POST /retrieve-sessions (NOUVEAU v1.1.0)
        sessions = client.get_sessions_by_device(phone)
        assert len(sessions) == 2
        ids = {s["sessionId"] for s in sessions}
        assert s1["sessionId"] in ids
        assert s2["sessionId"] in ids

    def test_network_insights_compatibility(self):
        client = CamaraClient(mock_mode=True)
        insights = client.get_network_insights(area_id="milan_bloc_1024")
        assert insights["status"] == "success"
        assert "metrics" in insights
        assert insights["metrics"]["p95_prb_utilization_pct"] > 0

    def test_fallback_to_mock_on_network_error(self):
        client = CamaraClient(
            client_id="fake_id",
            client_secret="fake_secret",
            base_url="http://127.0.0.1:59999/qod/v1",
            auth_url="http://127.0.0.1:59999/oauth2/token",
            mock_mode=False
        )
        token = client.get_token()
        assert token is not None
        assert client.mock_mode is True   # Bascule automatique en mock


class TestFootfallClient:

    def test_lat_lon_to_quadkey(self):
        lat, lon = 45.4642, 9.1900   # Milan Duomo
        qk15 = lat_lon_to_quadkey(lat, lon, level=15)
        assert len(qk15) == 15
        assert all(c in "0123" for c in qk15)
        # Reversibilite
        tx, ty, lvl = quadkey_to_tile_xy(qk15)
        assert lvl == 15
        assert tx > 0 and ty > 0

    def test_get_quadkey_for_square(self):
        client = FootfallClient(mock_mode=True, quadkey_level=15)
        qk_4849 = client.get_quadkey_for_square("4849")
        qk_4850 = client.get_quadkey_for_square("4850")
        assert len(qk_4849) == 15
        assert len(qk_4850) == 15
        # Cache interne
        assert client.get_quadkey_for_square("4849") == qk_4849

    def test_get_realtime_footfall(self):
        client = FootfallClient(mock_mode=True)
        quadkeys = ["120220011220011", "120220011220012"]
        res = client.get_realtime_footfall(quadkeys)
        assert res["status"] == "success"
        assert res["tile_count"] == 2
        for qk in quadkeys:
            assert qk in res["data"]
            assert res["data"][qk]["device_count"] > 0

    def test_calibrate_demand_traffic(self):
        client = FootfallClient(mock_mode=True)
        traffic_noon  = client.calibrate_demand_traffic("4849", footfall_devices=300, hour_slot=12)
        traffic_night = client.calibrate_demand_traffic("4849", footfall_devices=300, hour_slot=3)
        assert traffic_noon > 0
        assert traffic_night > 0
        assert traffic_noon > traffic_night   # Heure de pointe > nuit


class TestQoDTriggerManager:

    def test_trigger_no_congestion(self):
        manager = QoDTriggerManager(congestion_threshold_ratio=0.03, min_residual_mo=500.0)
        decisions = {
            "site_001_sec1_F1_1800": {"offset_dB": 1.5, "residual_congestion_mo": 0.0},
            "site_001_sec2_F1_1800": {"offset_dB": 0.0, "residual_congestion_mo": 120.0}
        }
        caps = {"site_001_sec1_F1_1800": 10000.0, "site_001_sec2_F1_1800": 10000.0}
        res = manager.process_milp_residuals(decisions, caps)
        assert res["status"] == "completed"
        assert res["congested_cells_count"] == 0
        assert res["triggered_sessions_count"] == 0

    def test_trigger_with_residual_congestion(self):
        manager = QoDTriggerManager(
            congestion_threshold_ratio=0.03,
            min_residual_mo=300.0,
            max_sessions_per_slot=10
        )
        manager.register_critical_device("site_002_sec3_F1_1800", "+491234560001", "EMERGENCY")

        decisions = {
            "site_001_sec1_F1_1800": {"offset_dB": 0.0, "residual_congestion_mo": 50.0},
            "site_002_sec3_F1_1800": {"offset_dB": 3.0, "residual_congestion_mo": 2500.0}
        }
        caps = {"site_001_sec1_F1_1800": 10000.0, "site_002_sec3_F1_1800": 10000.0}

        res = manager.process_milp_residuals(decisions, caps)
        assert res["congested_cells_count"] == 1
        assert res["triggered_sessions_count"] >= 1

        first_session = res["sessions"][0]
        assert first_session["cell_id"] == "site_002_sec3_F1_1800"
        # Profil le plus haut disponible (QOS_E sur Vodafone, ou QOS_EMERGENCY selon client)
        assert first_session["qos_profile"] in ("QOS_E", "QOS_EMERGENCY")
        assert first_session["qos_status"] == "AVAILABLE"

    def test_budget_cap_enforcement(self):
        manager = QoDTriggerManager(
            congestion_threshold_ratio=0.01,
            min_residual_mo=100.0,
            max_sessions_per_slot=3
        )
        decisions = {
            f"site_{i:03d}_sec1_F1_1800": {"offset_dB": 0.0, "residual_congestion_mo": 5000.0}
            for i in range(10)
        }
        caps = {f"site_{i:03d}_sec1_F1_1800": 8000.0 for i in range(10)}

        res = manager.process_milp_residuals(decisions, caps)
        assert res["congested_cells_count"] == 10
        assert res["triggered_sessions_count"] <= 3   # Plafond budgetaire respecte

    def test_cleanup_expired_sessions(self):
        manager = QoDTriggerManager(min_residual_mo=100.0)
        decisions = {"site_001_sec1_F1_1800": {"offset_dB": 0.0, "residual_congestion_mo": 2000.0}}
        caps = {"site_001_sec1_F1_1800": 8000.0}
        manager.process_milp_residuals(decisions, caps)
        assert len(manager.active_sessions) > 0

        deleted = manager.cleanup_expired_sessions()
        assert deleted > 0
        assert len(manager.active_sessions) == 0
