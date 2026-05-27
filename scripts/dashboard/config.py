"""
Configuration constants and paths for the SON Dashboard.
"""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

class DashboardConfig(BaseSettings):
    """Global configuration settings for the dashboard - Recruiter Edition."""
    
    # Paths (Defaulting to the 1024 'research' structure)
    ROOT_DIR: Path = Path(__file__).parents[2]
    RESEARCH_DIR: Path = ROOT_DIR / "research"
    DATA_DIR: Path = RESEARCH_DIR / "data" / "processed"
    MODELS_DIR: Path = RESEARCH_DIR / "models"
    OFFLINE_DIR: Path = RESEARCH_DIR / "offline"
    CONFIG_DIR: Path = RESEARCH_DIR / "config"
    
    # File Names (Exclusively 1024 cells)
    TRAFFIC_FILE: str = "work_1024cells.parquet"
    FEATURES_FILE: str = "features_target_1024cells.parquet"
    FRACTIONS_FILE: str = "fractions_1024.parquet"
    TOPOLOGY_FILE: str = "network_topology_1024.yaml"
    ANTENNA_MAP_FILE: str = "cell_antenna_map_1024.json"
    CAPACITIES_FILE: str = "nominal_capacities_v2.parquet"
    MODEL_FILE: str = "xgb_q80.pkl"
    
    # UI Constants
    PRIMARY_COLOR: str = "#00d4aa"    # SON Teal
    SECONDARY_COLOR: str = "#4b8ef5"  # Greedy Blue
    DANGER_COLOR: str = "#ef4444"     # Static Red
    BACKGROUND_COLOR: str = "#0a0e17"
    CARD_BG_COLOR: str = "linear-gradient(135deg, #1a1f2e 0%, #162033 100%)"
    
    # Simulation Defaults
    DEFAULT_THRESHOLD: float = 1.0
    TOTAL_SLOTS: int = 48  # 24h of 30m slots

    def validate_paths(self):
        """Validates critical data and research directories exist."""
        required = [self.RESEARCH_DIR, self.DATA_DIR, self.MODELS_DIR, self.OFFLINE_DIR, self.CONFIG_DIR]
        for p in required:
            if not p.exists():
                raise FileNotFoundError(f"Missing required directory: {p}")

config = DashboardConfig()
