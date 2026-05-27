# Architecture du Système SON

## 🏗️ Structure Globale
Le système est divisé en trois couches logiques :

### 1. Couche de Données (`data/`, `src/spatial_simulator.py`)
- Ingestion des données Milan (Volumes SMS/Appel/Internet).
- Calcul des matrices de transfert spatiales fondées sur la topologie réelle.

### 2. Couche d'Intelligence (`src/predictor.py`, `models/`)
- Modèle XGBoost entraîné avec une fonction de perte **Pinball** pour la régression quantile (q80).
- Permet d'anticiper les congestions 60 minutes à l'avance avec une marge de sécurité.

### 3. Couche de Décision & Simulation (`src/milp_engine.py`, `src/simulation/`)
- Moteur d'optimisation linéaire utilisant le solveur CBC.
- Simulateur en boucle fermée pour la validation des politiques.

## 🔄 Flux de Données
1. **Entrée** : Lags temporels et variables contextuelles.
2. **Predictor** : Estimation du trafic futur par cellule.
3. **MILP Engine** : Calcul des Offsets A3 minimisant la congestion globale.
4. **Simulator** : Application des offsets, calcul des volumes réels redistribués et retour vers le Predictor.
