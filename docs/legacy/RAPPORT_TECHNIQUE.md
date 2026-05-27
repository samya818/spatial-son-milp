# RAPPORT TECHNIQUE DE RÉFÉRENCE — PROJET TIME SERIES SON (v5.1)
## Optimisation Autonome de la Congestion Réseau
**Équipe Projet** : Samya Loukili & L'Auteur  
**Encadrant** : M. Toufik Massrour

---

## 📌 1. RÉSUMÉ EXÉCUTIF
Ce projet implémente un système **Self-Organizing Network (SON)** pour la gestion dynamique de la congestion. Basé sur le dataset de Milan, il couple le **Machine Learning (XGBoost + LightGBM)** avec un moteur de décision **MILP** pour optimiser le paramètre **A3 Offset**.

**Résultat clé :** Une réduction de **73.53%** du volume de trafic non satisfait sur un bloc dense de 1024 cellules.

---

## 🔬 2. PARCOURS DE R&D (LOGIQUE DE RECHERCHE)
Le projet est passé par trois phases critiques de maturation :
1.  **Phase Exploratoire** : Tentatives infructueuses avec **Prophet** et **SARIMA**. Constat : incapacité à capter les pics locaux et latence de calcul trop élevée.
2.  **L'Échec des 600 Cellules** : Notre premier test sur un échantillon dispersé a échoué à réduire la congestion. **Leçon apprise** : Sans contiguïté spatiale (cellules voisines), le délestage physique ne peut pas avoir lieu.
3.  **La Solution Finale** : Adoption d'un **bloc dense (32x32)** et d'un modèle **XGBoost Quantile (q80)**. Ce choix garantit que le système est "pessimiste" (préfère sur-anticiper une congestion) et dispose de voisins réels vers qui délester le trafic.

---

## 📐 3. HYPOTHÈSES DE MODÉLISATION
Le système repose sur quatre piliers théoriques validés :
1.  **Uniformité Locale** : Le trafic est supposé réparti équitablement sur la surface d'une cellule (5 hectares).
2.  **Path-Loss Physique** : Utilisation du modèle 3GPP Micro-Urbain pour calculer les zones de transfert.
3.  **Levier Unique** : L'A3 Offset est la seule variable d'action, garantissant la stabilité du réseau.
4.  **Conservation du Flux** : Tout trafic délesté par une antenne doit être physiquement absorbé par ses voisines.

---

## 🏗️ 4. ARCHITECTURE DU PROJET
Le projet est structuré pour séparer la recherche (Notebooks) de la logique de production (Source).

```text
projectTimeSeries/
├── research/           # Tout le parcours R&D (01-14)
│   ├── notebooks/      # Ingestion, Prophet vs XGB, Bloc 1024
│   ├── offline/        # Matrices de transfert géométriques
│   └── models/         # Modèles XGBoost + Correcteur LightGBM
├── src/                # Code source modulaire (Production)
│   ├── ml/             # Interface de prédiction Quantile
│   ├── optimization/   # Moteur MILP (Pyomo)
│   └── simulation/     # Boucle fermée et Runner
└── config/             # Topologie réseau (1024 antennes)
```

---

## 🛠️ 5. ENVIRONNEMENT & INSTALLATION
Le projet utilise Python 3.13 et un environnement virtuel pour isoler les dépendances.

**Installation rapide :**
1. `python -m venv venv`
2. `venv\Scripts\activate` (Windows)
3. `pip install -r requirements.txt`

---

## 📈 6. RÉSULTATS & PERFORMANCE
La simulation finale sur **1024 cellules** sur 24 heures démontre :
*   **Politique STATIQUE** : Congestion élevée (baseline).
*   **Politique DYNAMIQUE (SON)** : Réduction massive des pics.
*   **Amélioration Nette : +73.53%** de réduction du trafic non satisfait.

---
**Document technique de référence — Projet SON v5.1 — Mai 2026**
