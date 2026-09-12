"""
WiseNet V1.5 - CAMARA Vodafone Device Location Client
Implémente le standard CAMARA Device Location (GSMA Open Gateway) :
- Device Location Verification: /location-verification/v1/verify
- Device Location Retrieval: /location-retrieval/v0.3/retrieve
- Device Location Ping: /location-verification/v1/ping

Permet au contrôleur SON de vérifier en temps réel si un terminal d'urgence
ou un équipement de flotte critique se trouve physiquement sous la couverture
d'une cellule radio avant de déclencher des sessions CAMARA QoD.
"""

import os
import time
import json
import uuid
import math
import base64
import logging
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Endpoints Vodafone Sandbox officiels conformes à la documentation CAMARA
VF_LOCATION_BASE      = "https://api-sandbox.vf-dmp.engineering.vodafone.com"
VF_VERIFY_ENDPOINT    = f"{VF_LOCATION_BASE}/location-verification/v1/verify"
VF_RETRIEVE_ENDPOINT  = f"{VF_LOCATION_BASE}/location-retrieval/v0.3/retrieve"
VF_PING_ENDPOINT      = f"{VF_LOCATION_BASE}/location-verification/v1/ping"
VF_TOKEN_ENDPOINT     = f"{VF_LOCATION_BASE}/oauth2/v1/token"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcule la distance géodésique en mètres entre deux coordonnées GPS."""
    R = 6371000.0  # Rayon de la Terre en mètres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class VodafoneLocationClient:
    """
    Client Python pour l'API Vodafone / CAMARA Device Location.
    Prend en charge le mode Live (Sandbox Vodafone) avec bascule automatique
    en mode Mock conforme si le bac à sable est indisponible (HTTP 500 / maintenance).
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        mock_mode: bool = False
    ):
        self.client_id = (
            client_id
            or os.getenv("VODAFONE_LOCATION_CLIENT_ID")
            or os.getenv("CAMARA_CLIENT_ID", "")
        )
        self.client_secret = (
            client_secret
            or os.getenv("VODAFONE_LOCATION_CLIENT_SECRET")
            or os.getenv("CAMARA_CLIENT_SECRET", "")
        )
        self.mock_mode = mock_mode or not (self.client_id and self.client_secret)
        
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

        if not self.mock_mode:
            logger.info("[Vodafone Location] Initialisé en mode LIVE avec Sandbox Vodafone.")
        else:
            logger.info("[Vodafone Location] Initialisé en mode MOCK local conforme CAMARA.")

    def get_token(self) -> str:
        """Obtient ou réutilise un Bearer token OAuth2 via client_credentials."""
        if self._token and time.time() < (self._token_expiry - 60):
            return self._token

        if self.mock_mode:
            self._token = f"mock_loc_bearer_{int(time.time())}"
            self._token_expiry = time.time() + 3600
            return self._token

        try:
            auth_str = f"{self.client_id}:{self.client_secret}"
            b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("utf-8")

            req = urllib.request.Request(
                VF_TOKEN_ENDPOINT,
                data=data,
                headers={
                    "Authorization": f"Basic {b64_auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WiseNet/1.5"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                self._token = res["access_token"]
                self._token_expiry = time.time() + res.get("expires_in", 3600)
                logger.info("[Vodafone Location] Token OAuth2 obtenu avec succès.")
                return self._token
        except Exception as exc:
            logger.warning(f"[Vodafone Location] Échec obtention token ({exc}) -> bascule Mock.")
            self.mock_mode = True
            self._token = f"mock_loc_bearer_{int(time.time())}"
            self._token_expiry = time.time() + 3600
            return self._token

    def verify_location(
        self,
        phone_number: str,
        latitude: float,
        longitude: float,
        radius: float = 3000.0,
        max_age: int = 60,
        known_device_coords: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Vérifie si le terminal identifié par son numéro est dans la zone circulaire spécifiée.
        Conforme à l'endpoint CAMARA : POST /location-verification/v1/verify
        """
        token = self.get_token()

        payload = {
            "device": {"phoneNumber": phone_number},
            "area": {
                "areaType": "CIRCLE",
                "center": {"latitude": round(latitude, 6), "longitude": round(longitude, 6)},
                "radius": int(radius)
            },
            "maxAge": max_age
        }

        if not self.mock_mode:
            try:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WiseNet/1.5",
                    "vf-trace-transaction-id": str(uuid.uuid4()),
                    "x-correlator": str(uuid.uuid4())
                }
                req = urllib.request.Request(
                    VF_VERIFY_ENDPOINT,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    logger.info(f"[Vodafone Location LIVE] Verify {phone_number} -> {data.get('verificationResult')}")
                    return {
                        "verificationResult": data.get("verificationResult", "TRUE"),
                        "lastLocationTime": data.get("lastLocationTime", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                        "mode": "LIVE_VODAFONE"
                    }
            except urllib.error.HTTPError as err:
                logger.warning(f"[Vodafone Location] Endpoint HTTP {err.code} (Sandbox indisponible) -> Fallback Mock.")
            except Exception as exc:
                logger.warning(f"[Vodafone Location] Erreur réseau ({exc}) -> Fallback Mock.")

        # Fallback Mock intelligent : calcule la distance réelle si coordonnées de l'appareil fournies
        if known_device_coords:
            dev_lat, dev_lon = known_device_coords
            dist = haversine_distance(latitude, longitude, dev_lat, dev_lon)
            is_inside = dist <= radius
            verif_result = "TRUE" if is_inside else "FALSE"
        else:
            # Règle déterministe de simulation basée sur le numéro et la cellule
            phone_hash = abs(hash(phone_number)) % 100
            verif_result = "TRUE" if phone_hash < 75 else "FALSE"

        return {
            "verificationResult": verif_result,
            "lastLocationTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mode": "SIMULATION_CAMARA_CONFORMANT"
        }

    def retrieve_location(
        self,
        phone_number: str,
        max_age: int = 60,
        simulated_coords: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Récupère les coordonnées géographiques d'un terminal IoT / Flotte.
        Conforme à l'endpoint CAMARA : POST /location-retrieval/v0.3/retrieve
        """
        token = self.get_token()
        payload = {
            "device": {"phoneNumber": phone_number},
            "maxAge": max_age
        }

        if not self.mock_mode:
            try:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WiseNet/1.5",
                    "vf-trace-transaction-id": str(uuid.uuid4()),
                    "x-correlator": str(uuid.uuid4())
                }
                req = urllib.request.Request(
                    VF_RETRIEVE_ENDPOINT,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    logger.info(f"[Vodafone Location LIVE] Retrieve {phone_number} -> {data.get('area')}")
                    return {
                        "area": data.get("area"),
                        "lastLocationTime": data.get("lastLocationTime"),
                        "mode": "LIVE_VODAFONE"
                    }
            except Exception as exc:
                logger.warning(f"[Vodafone Location] Retrieve fallback ({exc}).")

        # Fallback Mock conforme CAMARA
        lat = simulated_coords[0] if simulated_coords else 45.4642  # Milan par défaut
        lon = simulated_coords[1] if simulated_coords else 9.1900
        return {
            "area": {
                "areaType": "CIRCLE",
                "center": {"latitude": round(lat, 6), "longitude": round(lon, 6)},
                "radius": 250
            },
            "lastLocationTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mode": "SIMULATION_CAMARA_CONFORMANT"
        }
