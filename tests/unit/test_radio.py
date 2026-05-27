import pytest
import numpy as np
from src.topology.builder import capacity_from_radio

def test_shannon_capacity_logic():
    """
    Vérifie la cohérence de la formule de Shannon.
    Plus de bande passante ou un meilleur SINR doit produire plus de capacité.
    """
    # Base: 20MHz, 15dB
    cap_base = capacity_from_radio(bw_mhz=20, sinr_db=15)
    
    # BW Double
    cap_bw_double = capacity_from_radio(bw_mhz=40, sinr_db=15)
    assert cap_bw_double > cap_base
    
    # SINR supérieur
    cap_sinr_high = capacity_from_radio(bw_mhz=20, sinr_db=25)
    assert cap_sinr_high > cap_base

def test_capacity_is_positive():
    cap = capacity_from_radio(bw_mhz=10, sinr_db=5)
    assert cap > 0
