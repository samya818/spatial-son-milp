# 🛰️ Spatial SON-MILP

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pyomo](https://img.shields.io/badge/Pyomo-Optimized-green)](http://www.pyomo.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-q80-orange)](https://xgboost.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Pipeline hybride ML + Optimisation MILP pour la gestion autonome de la congestion réseau (Self-Organizing Networks)**

> 🚀 **Chiffre clé :** Réduction de **73,5%** de la congestion sur un bloc dense de 1 024 cellules (Milan dataset).

---

## 📑 Table des matières
1. [🚀 Quick Start (5 min)](#-quick-start-5-min)
2. [📦 Installation complète](#-installation-complète)
3. [🗂️ Architecture du repo](#%EF%B8%8F-architecture-du-repo)
4. [🖥️ Lancer l'application Streamlit](#%EF%B8%8F-lancer-lapplication-streamlit)
5. [📓 Notebooks de recherche](#-notebooks-de-recherche)
6. [🧪 Tests & Qualité](#-tests--qualité)
7. [📊 Benchmarks](#-benchmarks)
8. [⚠️ Résolution des problèmes courants](#%EF%B8%8F-résolution-des-problèmes-courants)
9. [📚 Références](#-références)
10. [👥 Auteurs](#-auteurs)

---

## 🚀 Quick Start (5 min)

```bash
# 1. Cloner le repo
git clone https://github.com/samya818/spatial-son-milp.git
cd spatial-son-milp

# 2. Créer et activer l'environnement virtuel
python -m venv .venv
# Sur Windows :
.\venv\Scripts\activate
# Sur Linux/macOS :
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Vérifier l'environnement
python check_environment.py

# 5. Lancer le dashboard
python -m streamlit run scripts/dashboard/app.py
```

---

## 📦 Installation complète

### 🛰️ Données et Assets
Le dataset brut Telecom Italia Milan n'est pas inclus directement dans le repo pour des raisons de licence et de volume (> 1 Go). 
- **Assets pré-calculés :** Pour lancer le dashboard immédiatement, téléchargez les modèles et matrices pré-calculées :
  ```bash
  bash scripts/download_assets.sh
  ```
- **Reconstruction complète :** Si vous possédez les fichiers CSV bruts, placez-les dans `data/raw/` et exécutez les notebooks de recherche `01` à `08`.

### 🛠️ Dépendances
- `requirements.txt` : Dépendances critiques pour la production et le dashboard.
- `requirements-dev.txt` : Outils de développement (Pytest, Black, Jupyter).

### ⌨️ Makefile
| Cible | Description |
| :--- | :--- |
| `make install` | Installe l'environnement et les dépendances. |
| `make run` | Exécute le pipeline complet sur le bloc 1024. |
| `make verify` | Vérifie l'intégrité physique (conservation de masse). |
| `make test` | Lance la suite de tests unitaires. |
| `make lint` | Analyse statique et formatage du code. |
| `make clean` | Nettoie les caches et fichiers temporaires. |

---

## 🗂️ Architecture du repo

```text
spatial-son-milp/
├── docs/                   # Documentation technique et guide interactif
├── scripts/                # Dashboards et utilitaires
│   └── dashboard/          # Code source de l'application Streamlit
├── src/                    # CODE SOURCE PRODUCTION (Moteur MILP, ML)
├── research/               # TRAVAUX DE R&D
│   ├── notebooks/          # Parcours de recherche (01 à 15)
│   ├── models/             # Modèles sérialisés (XGBoost q80, LGBM)
│   └── offline/            # Matrices de transfert géométriques
├── tests/                  # Tests unitaires et intégration
├── check_environment.py    # Validateur de configuration
└── Makefile                # Automatisation des tâches
```

---

## 🖥️ Lancer l'application Streamlit

L'application doit toujours être lancée depuis la racine du projet :

```bash
python -m streamlit run scripts/dashboard/app.py
```

- **URL :** `http://localhost:8501`
- **Option .env :** Vous pouvez créer un fichier `.env` avec `PYTHONPATH=.` pour simplifier les imports.

### 🆘 FAQ anti-erreur
- **`ModuleNotFoundError: src`** : Assurez-vous de lancer la commande depuis la racine avec `python -m streamlit`.
- **`FileNotFoundError`** sur un fichier `.parquet` ou `.pkl` : Vous avez oublié de récupérer les assets. Exécutez `bash scripts/download_assets.sh`.
- **`ModuleNotFoundError: scripts.dashboard.app`** : Ne lancez pas la commande depuis l'intérieur du dossier `scripts/`.

---

## 📓 Notebooks de recherche

Consultez `docs/PIPELINE_GUIDE.html` pour une explication scientifique détaillée de chaque phase.

| Phase | Notebook | Description |
|-------|----------|-------------|
| 01 | `01_ingestion.ipynb` | ✅ Ingestion & nettoyage Telecom Italia Milan (10 min → 30 min) |
| 02 | `02_eda.ipynb` | ✅ EDA : STL, ADF, ACF/PACF, détection outliers |
| 03 | `03_features.ipynb` | ✅ Feature Engineering (31 variables causales) |
| 04 | `04_modelling.ipynb` | ✅ Baselines XGBoost, LSTM, Prophet, SARIMA |
| 05 | `05_improvements.ipynb` | ✅ Quantile q80 + TiDE + correcteur LightGBM L2 |
| 06 | `06_topology.ipynb` | ✅ Architecture 1024 cellules, antennes hétérogènes |
| 07 | `07_user_simulator.ipynb` | ✅ Simulation n_users par cellule (saisonnalité + bruit) |
| 08 | `08_spatial_simulator.ipynb` | ✅ Précalcul offline des matrices de transfert path-loss |
| 09 | `09_milp_decision_engine.ipynb` | ✅ Moteur MILP Pyomo (optimalité globale) |
| 10 | `10_monitoring.ipynb` | ✅ Détection de drift (Page-Hinkley, rolling MAE) |
| 11 | `11_closed_loop.ipynb` | ✅ Validation boucle fermée (gain 73,53%) |
| 12 | `12_comparison_report.ipynb` | ✅ Rapport comparatif intermédiaire |
| 13 | `13_full_scale_simulation.ipynb` | ✅ Simulation à l'échelle complète |
| 14 | `14_final_benchmark_report.ipynb` | ✅ Rapport de benchmark final |
| 15 | `15_greedy_comparison.ipynb` | ✅ Benchmark MILP vs Greedy (+52,5% vs heuristique) |

---

## 🧪 Tests & Qualité

Nous maintenons une suite de tests rigoureuse pour garantir la validité physique des transferts de charge.
```bash
# Lancer les tests unitaires
pytest tests/unit/ -v

# Vérification pré-flight
python check_environment.py --verify
```

---

## 📊 Benchmarks (Bloc 1024 cellules)

| Politique de Décision | Volume Insatisfait (Mo) | Gain vs Statique |
| :--- | :---: | :---: |
| **Statique** (Baseline) | 160 237 Mo | 0% |
| **Greedy Heuristic** | 89 375 Mo | 44,22% |
| **MILP Global** (SON) | **42 419 Mo** | **73,53%** |

---

## ⚠️ Résolution des problèmes courants
- **FileNotFound (data)** : Les modèles et matrices ne sont pas inclus dans le repo de base (Git LFS). Utilisez `bash scripts/download_assets.sh` pour vérifier leur présence locale.
- **Documentation complète** : Pour une explication scientifique détaillée et un guide interactif complet de chaque phase, consultez impérativement **`docs/PIPELINE_GUIDE.html`**.
- **PYTHONPATH** : Si vos scripts ne trouvent pas le module `src`, exportez le chemin : `export PYTHONPATH=$PYTHONPATH:.` (ou `$env:PYTHONPATH="."` sur PowerShell).
- **Performance MILP** : Le solveur par défaut est CBC. Pour des performances industrielles sur > 10 000 cellules, nous recommandons Gurobi ou CPLEX.

---

## 📚 Références
- **[1] Wang et al. (2015)** : Q-Learning Approach for SON with A3 Offset.
- **[2] Zhang et al. (2023)** : Self-Organizing Network Load Balancing Survey.
- **[3] Huang et al. (2024)** : MILP Formulation for Load Balancing.
- **[4] Das et al. (2023)** : TiDE: Time-series Dense Encoder.
- **[5] 3GPP TS 36.331** : Radio Resource Control (RRC) Specification.

---

## 👥 Auteurs
- **Loukili Samya**
- **Kenza El Khaniri**
- Encadré par **M. Toufik Massrour** (ENSAM Meknès).

---
*Developed for R&D purposes using the Telecom Italia Big Data Challenge dataset.*
