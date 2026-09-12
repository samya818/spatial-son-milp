"""
WiseNet V1.5 - Module d'intégration CAMARA GSMA Open Gateway & Vodafone Analytics
Fournit :
- Client standard CAMARA Quality on Demand (QoD) v1.1.0 et Connectivity Insights
- Client Vodafone Analytics Realtime Footfall & Reference QuadKey (Population Density)
- Gestionnaire de déclenchement QoD de secours (Safety Net) branché sur les résidus MILP
"""

from .client import CamaraClient
from .footfall_client import FootfallClient, lat_lon_to_quadkey, quadkey_to_tile_xy
from .location_client import VodafoneLocationClient
from .qod_trigger import QoDTriggerManager

__all__ = [
    "CamaraClient",
    "FootfallClient",
    "VodafoneLocationClient",
    "QoDTriggerManager",
    "lat_lon_to_quadkey",
    "quadkey_to_tile_xy"
]

