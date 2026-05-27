# MANUEL D'INGÉNIERIE : SYSTÈME SON v5.1
## Rapport d'Ingénierie ENSAM Meknès
**Équipe Projet** : Samya Loukili & L'Auteur  
**Encadrant** : M. Toufik Massrour

---

### 1. SYNTHÈSE EXÉCUTIVE ET VISION
Le système SON (Self-Organizing Network) v5.1 est le fruit d'un parcours de recherche visant l'optimisation autonome de la congestion réseau. 

**Parcours de Recherche** :
- **Essais Infructueux** : Utilisation de modèles Prophet et SARIMA (trop lents/peu réactifs).
- **Pivot Géographique** : Passage d'un échantillon dispersé de 600 cellules (résultats négatifs dus à l'absence de voisinage) à un **bloc dense de 1024 cellules** permettant de vrais transferts de charge.
- **Solution Finale** : Couplage d'un prédicteur **XGBoost Quantile** (pessimiste) avec un correcteur de résidus **LightGBM**, le tout piloté par un moteur d'optimisation mathématique **MILP**.

**Résultats Clés** :
Sur le bloc dense de 1024 cellules, le système démontre une **réduction de congestion de 73,53%**, validant la supériorité de l'approche dynamique sur la gestion statique.

---
### 2. ARCHITECTURE TECHNIQUE ET ORGANISATION DES FICHIERS
Le projet suit une structure modulaire stricte garantissant le découplage entre les données (offline) et la logique décisionnelle (online) :

#### A. Arborescence du Projet
- `/notebooks/` : Cœur logique du pipeline (12 notebooks exécutables + 1 simulation opérationnelle).
- `/data/` :
    - `/processed/` : Données canoniques (.parquet) et topologies (.json, .yaml).
    - `/simulated/` : Données de trafic utilisateur synthétique.
- `/models/` : Modèles sérialisés (`.pkl` : XGBoost/LightGBM).
- `/offline/` : Look-up tables de transfert spatial (`fractions.parquet`).
- `/config/` : Configuration topologique (`network_topology.yaml`).

#### B. Pipeline de Données
1. **Flux d'entrée** : Données brutes Milan (CSV/TXT) → Phase 01.
2. **Features** : Transformation et enrichissement via Polars → `features_target_600cells.parquet`.
3. **Optimisation** : Précalculs géométriques (offline) → `fractions.parquet`.
4. **Décision** : ML Predictions (online) + `fractions.parquet` → Moteur MILP → `Offset A3` (Optimal).

---

### 3. ONTOLOGIE ET CADRE TECHNIQUE
- **Grille géographique** : Discrétisation de Milan (aire métropolitaine ~552 km²) en 10 000 cellules (100x100).
- **Entités Radio** : 
    - **Macro** : Hauteur 25m, Rayon ~800m.
    - **Micro** : Hauteur 8m, Rayon ~200m.
    - **Smallcell** : Hauteur 4m, Rayon ~50m.
- **Formule de capacité (Shannon étendue)** : 
    $C = BW \times \log_2(1 + \text{SINR}) \times \eta \times \text{sharing\_factor}$
    *Où $\eta = 0.6$ et $\text{sharing\_factor} = 0.05$ (ajustement réel).*

---

### 4. HYPOTHÈSES MATHÉMATIQUES (H1-H4)
1. **H1 (Trafic uniforme)** : Moyenne utilisateur robuste à l'échelle de 5 hectares.
2. **H2 (Distribution spatiale)** : Uniforme par maille, validée par la haute granularité (grille 100x100).
3. **H3 (Path-loss physique)** : $Q(p) = -3.76 \log_{10}(dist + \epsilon)$ (Standard 3GPP 3D-UMi).
4. **H4 (Offset A3)** : Levier unique. Justification : Stabilité SON et conformité 3GPP.

---

### 5. DÉTAILLAGE TECHNIQUE DU PIPELINE (PHASES 01-11)

#### Phase 01-04 : Ingestion & Features
- Outil : Polars (haute performance sur gros volumes).
- Technique : STL (Seasonal-Trend decomposition) pour séparer le signal de base du bruit.

#### Phase 05 : Intelligence ML
- Algorithme : Stacking de modèles (XGBoost Quantile + LightGBM Residual Corrector).
- Justification : Loss asymétrique ($\alpha=0.80$) pour sur-évaluer les risques de saturation.

#### Phase 06-08 : Architecture Spatiale
- **Spatial Transfer Simulator (Offline)** :
    - Algorithme : Discrétisation en grille 50x50 points par cellule.
    - Équation de bascule : `Q_voisine + delta >= Q_maitre`.
    - Production : `fractions.parquet` (matrice 3D indexée).

#### Phase 09 : Moteur MILP
- Solveur : CBC via interface PuLP.
- Contrainte clé (Couplage global) : $\sum V_{final} \le \sum C_{phys}$.
- Variables : $z_{a,k} \in \{0, 1\}$ (binaire).

#### Phase 10-11 : Monitoring & Validation
- Monitoring : Page-Hinkley sur résidus STL.
- Validation : Simulation boucle fermée sur test set (Jours 57-62) comparant Statique vs Dynamique (Phase 13).

---

### 6. GUIDE D'EXPLOITATION ET MAINTENANCE
- **Simulation Complète** : Exécuter `simulation_operationnelle.py` pour valider l'impact réel des décisions SON sur l'intégralité du dataset.
- **Recalcul spatial** : Si topologie modifiée (nouvelles antennes) → `06_topology.ipynb` puis `08_spatial.ipynb`.
- **Réentraînement ML** : Alerte drift (Phase 10) → `05_improvements.ipynb`.

---
*Document technique d'exploitation — Projet SON v5.1 — Mai 2026*
