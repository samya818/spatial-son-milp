import numpy as np
from collections import deque

class DriftMonitor:
    """
    Moniteur de dérive (Data/Concept Drift) pour le pipeline ML.
    Utilise le résidu STL et l'erreur glissante.
    """
    def __init__(self, window=48, threshold_sigma=2.0, consecutive=5):
        self.window = window
        self.threshold = threshold_sigma
        self.consecutive = consecutive
        self.errors = deque(maxlen=window)
        self.anomaly_count = 0
        self.alerts = []

    def update(self, slot, predicted, actual, stl_residual):
        # Calcul de l'erreur absolue
        err = abs(predicted - actual)
        self.errors.append(err)
        
        # On attend d'avoir assez de points pour calculer une std stable
        if len(self.errors) < 10: 
            return False
            
        # Détection d'anomalie : si le résidu dépasse k * std(erreurs passées)
        # Cela signifie que l'erreur actuelle n'est plus expliquée par le bruit habituel
        current_std = np.std(self.errors)
        is_anomaly = abs(stl_residual) > self.threshold * current_std
        
        if is_anomaly:
            self.anomaly_count += 1
        else:
            self.anomaly_count = 0
            
        # Alerte si dérive persistante sur 'consecutive' slots
        if self.anomaly_count >= self.consecutive:
            rolling_mae = np.mean(self.errors)
            alert = {
                'slot': int(slot), 
                'rolling_mae': float(rolling_mae),
                'stl_residual': float(stl_residual), 
                'type': 'DRIFT_DETECTED'
            }
            self.alerts.append(alert)
            print(f'[DRIFT ALERT] Dérive détectée au slot {slot} ! Rolling MAE: {rolling_mae:.2f}')
            self.anomaly_count = 0
            return True
            
        return False

    def get_performance_summary(self):
        """Retourne un résumé des alertes et de la performance actuelle."""
        if not self.errors:
            return "Pas de données."
        return {
            'current_mae': float(np.mean(self.errors)),
            'alerts_count': len(self.alerts),
            'last_alert': self.alerts[-1] if self.alerts else None
        }
