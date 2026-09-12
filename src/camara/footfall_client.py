"""
WiseNet V1.5 - CAMARA / Vodafone Analytics Footfall & QuadKey Client
Intégration des APIs Vodafone Analytics Sandbox :
- Realtime Footfall: https://api-sandbox.vf-dmp.engineering.vodafone.com/vfAnalytics/realTimeFootfall/v1
- Reference QuadKey: https://api-sandbox.vf-dmp.engineering.vodafone.com/vfAnalytics/referenceQuadkey/v1
- Historic Footfall: https://api-sandbox.vf-dmp.engineering.vodafone.com/vfAnalytics/historicFootfall/v1

Fournit une mesure exogène de la demande géographique par tuile QuadKey / maille Milan.
Préserve l'immunité à la critique de Lucas : d(demande)/d(offset) = 0.
"""

import os
import math
import time
import json
import base64
import logging
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Endpoints Sandbox Vodafone vérifiés
VF_FOOTFALL_BASE = "https://api-sandbox.vf-dmp.engineering.vodafone.com/vfAnalytics/realTimeFootfall/v1"
VF_QUADKEY_BASE  = "https://api-sandbox.vf-dmp.engineering.vodafone.com/vfAnalytics/referenceQuadkey/v1"
VF_TOKEN_URL     = "https://api-sandbox.vf-dmp.engineering.vodafone.com/oauth2/v1/token"


def lat_lon_to_quadkey(lat: float, lon: float, level: int = 15) -> str:
    """
    Convertit des coordonnées géographiques (latitude, longitude) en QuadKey Bing/OSM.
    Standard de partition spatiale hiérarchique utilisé par Vodafone Analytics.
    """
    lat = max(min(lat, 85.05112878), -85.05112878)
    lon = max(min(lon, 180.0), -180.0)

    x = (lon + 180.0) / 360.0
    sin_lat = math.sin(lat * math.pi / 180.0)
    y = 0.5 - math.log((1.0 + sin_lat) / (1.0 - sin_lat)) / (4.0 * math.pi)

    map_size = 1 << level
    pixel_x = int(min(max(x * map_size * 256.0, 0), map_size * 256.0 - 1))
    pixel_y = int(min(max(y * map_size * 256.0, 0), map_size * 256.0 - 1))

    tile_x = pixel_x // 256
    tile_y = pixel_y // 256

    quadkey_digits = []
    for i in range(level, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if (tile_x & mask) != 0:
            digit += 1
        if (tile_y & mask) != 0:
            digit += 2
        quadkey_digits.append(str(digit))

    return "".join(quadkey_digits)


def quadkey_to_tile_xy(quadkey: str) -> Tuple[int, int, int]:
    """Convertit une chaîne QuadKey en coordonnées (tile_x, tile_y, level)."""
    tile_x = 0
    tile_y = 0
    level = len(quadkey)
    for i in range(level, 0, -1):
        mask = 1 << (i - 1)
        char = quadkey[level - i]
        if char == '1':
            tile_x |= mask
        elif char == '2':
            tile_y |= mask
        elif char == '3':
            tile_x |= mask
            tile_y |= mask
        elif char != '0':
            raise ValueError(f"Caractère QuadKey invalide: {char}")
    return tile_x, tile_y, level


class FootfallClient:
    """
    Client pour les APIs Vodafone Realtime Footfall & Reference QuadKey / CAMARA Population Density.
    Gère l'authentification OAuth2, la conversion spatiale maille Milan <-> QuadKey et l'échelle de demande.
    """
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: str = VF_FOOTFALL_BASE,
        auth_url: str = VF_TOKEN_URL,
        mock_mode: bool = True,
        quadkey_level: int = 15
    ):
        self.client_id = client_id or os.getenv("VODAFONE_ANALYTICS_CLIENT_ID", os.getenv("CAMARA_CLIENT_ID", "mock_client_id"))
        self.client_secret = client_secret or os.getenv("VODAFONE_ANALYTICS_CLIENT_SECRET", os.getenv("CAMARA_CLIENT_SECRET", "mock_secret"))
        self.base_url = base_url.rstrip("/")
        self.auth_url = auth_url
        self.mock_mode = mock_mode
        self.quadkey_level = quadkey_level
        self._cache_quadkeys: Dict[str, str] = {}
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    def get_token(self) -> str:
        """Récupère ou renouvelle le jeton OAuth2 Bearer via Basic Auth RFC 6749."""
        if self._token and time.time() < (self._token_expiry - 60):
            return self._token

        if self.mock_mode:
            self._token = f"mock_bearer_footfall_{int(time.time())}"
            self._token_expiry = time.time() + 3600
            return self._token

        try:
            auth_str = f"{self.client_id}:{self.client_secret}"
            b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("utf-8")
            req = urllib.request.Request(
                self.auth_url,
                data=data,
                headers={
                    "Authorization": f"Basic {b64_auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                res = json.loads(r.read().decode("utf-8"))
                self._token = res["access_token"]
                self._token_expiry = time.time() + res.get("expires_in", 3600)
                logger.info("[FOOTFALL] Token OAuth2 Vodafone obtenu avec succès.")
                return self._token
        except Exception as e:
            logger.warning(f"[FOOTFALL] Échec authentification ({e}) -> bascule mock.")
            self.mock_mode = True
            return self.get_token()

    def get_quadkey_for_square(self, square_id: str, center_lat: float = 45.4642, center_lon: float = 9.1900) -> str:
        """
        Associe un identifiant de maille Milan (ex: '4849') à sa tuile QuadKey correspondante.
        Permet un mapping spatial pérenne sans dépendance réseau répétée.
        """
        if square_id in self._cache_quadkeys:
            return self._cache_quadkeys[square_id]

        try:
            sq_num = int(square_id)
            row = sq_num // 100
            col = sq_num % 100
            lat = center_lat + (row - 50) * 0.0021
            lon = center_lon + (col - 50) * 0.0030
        except ValueError:
            lat, lon = center_lat, center_lon

        qk = lat_lon_to_quadkey(lat, lon, level=self.quadkey_level)
        self._cache_quadkeys[square_id] = qk
        return qk

    def get_realtime_footfall(self, quadkeys: List[str]) -> Dict[str, Any]:
        """
        Interroge l'API Realtime Footfall pour obtenir le comptage d'appareils actifs par QuadKey.
        """
        if self.mock_mode:
            results = {}
            current_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            for qk in quadkeys:
                hash_val = sum(ord(c) for c in qk)
                base_count = 120 + (hash_val % 450)
                results[qk] = {
                    "quadkey": qk,
                    "device_count": base_count,
                    "timestamp": current_time,
                    "confidence_score": 0.95
                }
            return {
                "status": "success",
                "source": "mock_vodafone_footfall",
                "tile_count": len(quadkeys),
                "data": results
            }

        token = self.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        url = f"{self.base_url}/vodafone-analytics-realtime-footfall/footfall"
        payload = json.dumps({"quadkeys": quadkeys}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"[FOOTFALL] Requête live {url} indisponible ({e}) -> Bascule en mode Mock.")
            self.mock_mode = True
            return self.get_realtime_footfall(quadkeys)

    def calibrate_demand_traffic(
        self,
        square_id: str,
        footfall_devices: int,
        hour_slot: int = 12,
        baseline_milan_mb: float = 150.0
    ) -> float:
        """
        Calibre le trafic géographique v_c(t) en Mo à partir du comptage réel d'appareils.
        Formule causale : v_c(t) = footfall(c, t) * ratio_milan(c, heure).
        Respecte rigoureusement la condition d(v_c) / d(delta) = 0 (immunité de Lucas).
        """
        hour_weight = 1.0 + 0.4 * math.sin((hour_slot - 6) * math.pi / 12)
        ratio = max(0.5, (baseline_milan_mb / 200.0)) * hour_weight
        estimated_traffic_mo = footfall_devices * ratio
        return round(estimated_traffic_mo, 2)
