"""
WiseNet V1.5 - CAMARA QoD Safety Net Trigger
Déclencheur chirurgical de sessions Quality on Demand (QoD) pour les cellules résiduellement congestionnées.
Intervient en aval du solveur MILP pour protéger les flux vitaux (Urgences, Flottes critiques)
sans altérer la topologie globale ni violer les budgets d'allocation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from .client import CamaraClient
from .location_client import VodafoneLocationClient

logger = logging.getLogger(__name__)

class QoDTriggerManager:
    """
    Gestionnaire d'automatisation des sessions QoD CAMARA en réponse à la congestion résiduelle.
    Intègre l'API CAMARA Vodafone Device Location pour vérifier la présence physique
    des terminaux critiques avant d'allouer les ressources radio.
    """
    def __init__(
        self,
        camara_client: Optional[CamaraClient] = None,
        location_client: Optional[VodafoneLocationClient] = None,
        congestion_threshold_ratio: float = 0.03,  # Seuil : 3% de la capacité restante non servie
        min_residual_mo: float = 300.0,             # Ou au moins 300 Mo de congestion résiduelle
        max_sessions_per_slot: int = 15,            # Plafond budgétaire de sessions par créneau de 30 min
        default_duration_sec: int = 1800            # Durée correspondant au créneau (30 min)
    ):
        self.client = camara_client or CamaraClient(mock_mode=True)
        self.location_client = location_client or VodafoneLocationClient()
        self.congestion_threshold_ratio = congestion_threshold_ratio
        self.min_residual_mo = min_residual_mo
        self.max_sessions_per_slot = max_sessions_per_slot
        self.default_duration_sec = default_duration_sec
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Registre de terminaux critiques déclarés
        self._critical_registry: Dict[str, List[Dict[str, str]]] = {}

        # Flotte d'intervention d'urgence (Ambulances SAMU, Pompiers, Flottes prioritaires)
        # Utilisée par l'API Device Location pour détecter leur présence sous les cellules
        self.critical_fleet: List[Dict[str, Any]] = [
            {"phone_number": "+401234567890", "device_type": "EMERGENCY", "name": "SAMU-Amb-01", "coords": (45.4650, 9.1910)},
            {"phone_number": "+401234567891", "device_type": "EMERGENCY", "name": "SAMU-Amb-02", "coords": (45.4670, 9.1890)},
            {"phone_number": "+401234567892", "device_type": "CRITICAL_FLEET", "name": "Police-Patrol-04", "coords": (45.4630, 9.1950)},
            {"phone_number": "+401234567893", "device_type": "CRITICAL_FLEET", "name": "Autonomous-Shuttle-02", "coords": (45.4610, 9.1850)},
            {"phone_number": "+401234567894", "device_type": "EMERGENCY", "name": "Civil-Defense-01", "coords": (45.4700, 9.2000)},
        ]

    def register_critical_device(self, cell_id: str, phone_number: str, device_type: str = "EMERGENCY"):
        """Enregistre un terminal prioritaire rattaché à une zone radio spécifique."""
        if cell_id not in self._critical_registry:
            self._critical_registry[cell_id] = []
        self._critical_registry[cell_id].append({
            "phone_number": phone_number,
            "device_type": device_type
        })

    def _get_critical_devices_for_cell(
        self,
        cell_id: str,
        cell_lat: Optional[float] = None,
        cell_lon: Optional[float] = None
    ) -> List[Dict[str, str]]:
        """
        Identifie les terminaux critiques d'une cellule.
        Utilise l'API CAMARA Location Verification pour vérifier la présence physique des terminaux.
        """
        if cell_id in self._critical_registry and self._critical_registry[cell_id]:
            return self._critical_registry[cell_id]

        # Résolution des coordonnées géographiques de la cellule (grille Milan par défaut)
        if cell_lat is None or cell_lon is None:
            try:
                sq_num = int(cell_id)
                row = sq_num // 100
                col = sq_num % 100
                cell_lat = 45.4642 + (row - 50) * 0.0021
                cell_lon = 9.1900 + (col - 50) * 0.0030
            except ValueError:
                cell_lat, cell_lon = 45.4642, 9.1900

        # Interrogation de l'API CAMARA Device Location Verification
        verified_devices = []
        if self.location_client:
            for dev in self.critical_fleet:
                verif = self.location_client.verify_location(
                    phone_number=dev["phone_number"],
                    latitude=cell_lat,
                    longitude=cell_lon,
                    radius=2500.0,
                    known_device_coords=dev.get("coords")
                )
                if verif.get("verificationResult") == "TRUE":
                    logger.info(
                        f"[CAMARA Location] Terminal {dev['name']} ({dev['phone_number']}) "
                        f"VÉRIFIÉ sous la cellule saturée {cell_id} via {verif.get('mode')}."
                    )
                    verified_devices.append({
                        "phone_number": dev["phone_number"],
                        "device_type": dev["device_type"],
                        "name": dev["name"],
                        "location_verified": True
                    })

        if verified_devices:
            return verified_devices

        # Génération de repli déterministe si aucun terminal de flotte n'est dans la zone
        cell_hash = abs(hash(cell_id)) % 10000
        return [
            {"phone_number": f"+401234{cell_hash:04d}01", "device_type": "EMERGENCY", "name": f"SIM-Dev-{cell_hash:04d}-01"},
            {"phone_number": f"+401234{cell_hash:04d}02", "device_type": "CRITICAL_FLEET", "name": f"SIM-Dev-{cell_hash:04d}-02"}
        ]

    def process_milp_residuals(
        self,
        milp_decisions: Dict[str, Dict[str, Any]],
        cells_capacity: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Analyse les décisions du MILP et déclenche des sessions QoD sur les cellules en dépassement.
        """
        # 1. Obtenir les profils disponibles via l'API CAMARA
        available_profiles = self.client.get_qos_profiles()
        profile_names = [p["name"] for p in available_profiles]
        if "QOS_E" in profile_names:
            preferred_profile = "QOS_E"
        elif "QOS_EMERGENCY" in profile_names:
            preferred_profile = "QOS_EMERGENCY"
        elif "QOS_L" in profile_names:
            preferred_profile = "QOS_L"
        else:
            preferred_profile = profile_names[0] if profile_names else "QOS_E"

        congested_cells = []
        triggered_sessions = []
        sessions_created_count = 0

        for cell_id, dec in milp_decisions.items():
            residual_mo = dec.get("residual_congestion_mo", 0.0)
            capacity = cells_capacity.get(cell_id, 10000.0)
            threshold = max(self.min_residual_mo, capacity * self.congestion_threshold_ratio)

            if residual_mo > threshold:
                congested_cells.append({
                    "cell_id": cell_id,
                    "residual_mo": residual_mo,
                    "capacity_mo": capacity,
                    "saturation_pct": round((residual_mo / capacity) * 100, 2)
                })

                if sessions_created_count >= self.max_sessions_per_slot:
                    continue

                # Identifier les terminaux critiques à prioriser
                devices = self._get_critical_devices_for_cell(cell_id)
                for dev in devices:
                    if sessions_created_count >= self.max_sessions_per_slot:
                        logger.warning(f"[QoD Safety Net] Plafond budgétaire de {self.max_sessions_per_slot} sessions atteint.")
                        break

                    profile = preferred_profile if dev["device_type"] == "EMERGENCY" else "QOS_L"
                    session = self.client.create_qod_session(
                        phone_number=dev["phone_number"],
                        qos_profile=profile,
                        duration=self.default_duration_sec
                    )
                    
                    if session and "sessionId" in session:
                        sess_id = session["sessionId"]
                        record = {
                            "session_id": sess_id,
                            "cell_id": cell_id,
                            "phone_number": dev["phone_number"],
                            "device_type": dev["device_type"],
                            "qos_profile": profile,
                            "duration_sec": self.default_duration_sec,
                            "qos_status": session.get("qosStatus", "ACTIVE")
                        }
                        self.active_sessions[sess_id] = record
                        triggered_sessions.append(record)
                        sessions_created_count += 1

        return {
            "status": "completed",
            "congested_cells_count": len(congested_cells),
            "triggered_sessions_count": len(triggered_sessions),
            "budget_cap": self.max_sessions_per_slot,
            "congested_cells": congested_cells,
            "sessions": triggered_sessions
        }

    def cleanup_expired_sessions(self) -> int:
        """Libère toutes les sessions actives (ex: à la fin du créneau horaire)."""
        deleted_count = 0
        for sess_id in list(self.active_sessions.keys()):
            res = self.client.delete_qod_session(sess_id)
            if res.get("status") in ["DELETED", "deleted"]:
                deleted_count += 1
                del self.active_sessions[sess_id]
        return deleted_count
