import polars as pl
import pickle
from pathlib import Path

class TrafficPredictor:
    """
    Module de prédiction du trafic basé sur XGBoost Quantile (q80).
    Anticipe les pics de congestion avec une marge de sécurité.
    """
    def __init__(self, model_path='research/models/xgb_q80.pkl'):
        self.model_path = Path(model_path)
        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)
            
        self.feature_cols = [
            'internet_volume', 'sms_in', 'call_in', 'hour_slot', 'dow', 'sin_hour', 'cos_hour', 
            'sin_dow', 'cos_dow', 'is_weekend', 'lag_1', 'lag_2', 'lag_6', 
            'lag_12', 'lag_24', 'lag_48', 'lag_96', 'lag_336', 'roll_mean_3h', 
            'roll_std_3h', 'roll_max_3h', 'roll_mean_6h', 'roll_std_6h', 
            'roll_max_6h', 'roll_mean_24h', 'roll_std_24h', 'roll_max_24h', 
            'neighbor_mean_t_minus_2'
        ]

    def predict(self, slot_df):
        """
        Réalise une prédiction pour un dataframe de cellules au slot T+2 (1h ahead).
        """
        X = slot_df.select(self.feature_cols).to_numpy()
        return self.model.predict(X)

    def get_features_list(self):
        return self.feature_cols
