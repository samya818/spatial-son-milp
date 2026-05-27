"""
Health check utility for the SON Dashboard.
Can be used by Docker or orchestration tools.
"""
import sys
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).parents[2]
if str(root) not in sys.path:
    sys.path.append(str(root))

from scripts.dashboard.config import config
from scripts.dashboard.data_loader import load_topology, load_traffic_data

def check_health():
    """Performs a basic health check of the dashboard assets."""
    try:
        config.validate_paths()
        topo = load_topology()
        if not topo.get("antennas"):
            return {"status": "degraded", "reason": "Empty topology"}
        
        # Check if precomputed timeline exists
        timeline_path = config.OFFLINE_DIR / "timeline_24h.parquet"
        if not timeline_path.exists():
            return {"status": "degraded", "reason": "Missing precomputed timeline"}
            
        return {"status": "healthy", "version": "6.0.0"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import json
    print(json.dumps(check_health()))
