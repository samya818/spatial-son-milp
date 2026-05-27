# 🛰️ Spatial SON-MILP

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pyomo](https://img.shields.io/badge/Pyomo-Optimized-green)](http://www.pyomo.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-q80-orange)](https://xgboost.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> ℹ️ **Note:** For the full scientific documentation (in French), see **`docs/PIPELINE_GUIDE.html`**.

**Hybrid ML + MILP Optimization Pipeline for autonomous network congestion management (Self-Organizing Networks)**

> 🚀 **Proof of Concept:** In our simulation model, which is based on the documented H1-H4 hypotheses, we observe a **73.53%** reduction in unsatisfied volume. This proof of concept validates the hybrid ML+MILP approach and paves the way for validation on realistic network simulators (ns-3) and, eventually, field deployment.

---

## 📑 Table of Contents
1. [🚀 Quick Start (5 min)](#-quick-start-5-min)
2. [📦 Full Installation](#-full-installation)
3. [🗂️ Repository Architecture](#%EF%B8%8F-repository-architecture)
4. [🖥️ Launching the Streamlit Application](#%EF%B8%8F-launching-the-streamlit-application)
5. [📓 Research Notebooks](#-research-notebooks)
6. [🧪 Tests & Quality](#-tests--quality)
7. [📊 Benchmarks](#-benchmarks)
8. [⚠️ Troubleshooting](#%EF%B8%8F-troubleshooting)
9. [📚 References](#-references)
10. [👥 Authors](#-authors)

---

## 🚀 Quick Start (5 min)

```bash
# 1. Clone the repo
git clone https://github.com/samya818/spatial-son-milp.git
cd spatial-son-milp

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify environment
python check_environment.py

# 5. Launch the dashboard
python -m streamlit run scripts/dashboard/app.py
```

---

## 📦 Full Installation

### 🛰️ Data and Assets
The raw Telecom Italia Milan dataset is not included directly in the repo due to licensing and volume (> 1 GB).
- **Pre-computed Assets:** To launch the dashboard immediately, verify the pre-computed models and matrices:
  ```bash
  bash scripts/download_assets.sh
  ```
- **Full Reconstruction:** If you have the raw CSV files, place them in `data/raw/` and run research notebooks `01` to `08`.

### 🛠️ Dependencies
- `requirements.txt`: Critical dependencies for production and the dashboard.
- `requirements-dev.txt`: Development tools (Pytest, Black, Jupyter).

### ⌨️ Makefile
| Target | Description |
| :--- | :--- |
| `make install` | Installs the environment and dependencies. |
| `make run` | Runs the full pipeline on the 1024 block. |
| `make verify` | Verifies physical integrity (mass conservation). |
| `make test` | Runs the unit test suite. |
| `make lint` | Static analysis and code formatting. |
| `make clean` | Cleans caches and temporary files. |

---

## 🗂️ Repository Architecture

```text
spatial-son-milp/
├── docs/                   # Technical documentation and interactive guide
├── scripts/                # Dashboards and utilities
│   └── dashboard/          # Streamlit application source code
├── src/                    # PRODUCTION SOURCE CODE (MILP Engine, ML)
├── research/               # R&D WORK
│   ├── notebooks/          # Research path (01 to 15)
│   ├── models/             # Serialized models (XGBoost q80, LGBM)
│   └── offline/            # Geometric transfer matrices
├── tests/                  # Unit and integration tests
├── check_environment.py    # Configuration validator
└── Makefile                # Task automation
```

---

## 🖥️ Launching the Streamlit Application

The application must always be launched from the project root:

```bash
python -m streamlit run scripts/dashboard/app.py
```

- **URL:** `http://localhost:8501`
- **.env Option:** You can create a `.env` file with `PYTHONPATH=.` to simplify imports.

### 🆘 Troubleshooting FAQ
- **`ModuleNotFoundError: src`**: Ensure you launch the command from the root using `python -m streamlit`.
- **`FileNotFoundError`** on a `.parquet` or `.pkl` file: You may be missing assets. Run `bash scripts/download_assets.sh`.
- **`ModuleNotFoundError: scripts.dashboard.app`**: Do not launch the command from inside the `scripts/` folder.

---

## 📓 Research Notebooks

Consult the interactive scientific documentation for a detailed explanation of each phase:
- 🇬🇧 **[English Interactive Guide](https://rawcdn.githack.com/samya818/spatial-son-milp/main/docs/PIPELINE_GUIDE_EN.html)**
- 🇫🇷 **[Guide Interactif en Français](https://rawcdn.githack.com/samya818/spatial-son-milp/main/docs/PIPELINE_GUIDE_FR.html)**

| Phase | Notebook | Description |
|-------|----------|-------------|
| 01 | `01_ingestion.ipynb` | ✅ Ingestion & cleaning Telecom Italia Milan (10 min → 30 min) |
| 02 | `02_eda.ipynb` | ✅ EDA: STL, ADF, ACF/PACF, outlier detection |
| 03 | `03_features.ipynb` | ✅ Feature Engineering (31 causal variables) |
| 04 | `04_modelling.ipynb` | ✅ Baselines: XGBoost, LSTM, Prophet, SARIMA |
| 05 | `05_improvements.ipynb` | ✅ Quantile q80 + TiDE + LightGBM L2 corrector |
| 06 | `06_topology.ipynb` | ✅ 1024-cell architecture, heterogeneous antennas |
| 07 | `07_user_simulator.ipynb` | ✅ User per cell simulation (seasonality + noise) |
| 08 | `08_spatial_simulator.ipynb` | ✅ Offline pre-computation of path-loss transfer matrices |
| 09 | `09_milp_decision_engine.ipynb` | ✅ Pyomo MILP Engine (global optimality) |
| 10 | `10_monitoring.ipynb` | ✅ Drift detection (Page-Hinkley, rolling MAE) |
| 11 | `11_closed_loop.ipynb` | ✅ Closed-loop validation (73.53% gain) |
| 12 | `12_comparison_report.ipynb` | ✅ Intermediate comparative report |
| 13 | `13_full_scale_simulation.ipynb` | ✅ Full-scale simulation |
| 14 | `14_final_benchmark_report.ipynb` | ✅ Final benchmark report |
| 15 | `15_greedy_comparison.ipynb` | ✅ MILP vs Greedy benchmark (+52.5% vs heuristic) |

---

## 🧪 Tests & Quality

We maintain a rigorous test suite to ensure the physical validity of load transfers.
```bash
# Run unit tests
pytest tests/unit/ -v

# Pre-flight verification
python check_environment.py --verify
```

---

## 📊 Benchmarks (1024-cell Block)

| Decision Policy | Unsatisfied Volume (MB) | Gain vs Static |
| :--- | :---: | :---: |
| **Static** (Baseline) | 160,237 MB | 0% |
| **Greedy Heuristic** | 89,375 MB | 44.22% |
| **Global MILP** (SON) | **42,419 MB** | **73.53%** |

---

## ⚠️ Troubleshooting
- **FileNotFound (data)**: Models and matrices are not included in the base repo (Git LFS). Use `bash scripts/download_assets.sh` to verify their local presence.
- **Full Documentation**: For a detailed scientific explanation and a complete interactive guide for each phase, it is imperative to consult **`docs/PIPELINE_GUIDE.html`**.
- **PYTHONPATH**: If your scripts cannot find the `src` module, export the path: `export PYTHONPATH=$PYTHONPATH:.` (or `$env:PYTHONPATH="."` on PowerShell).
- **MILP Performance**: The default solver is CBC. For industrial performance on > 10,000 cells, we recommend Gurobi or CPLEX.

---

## 📚 References
- **[1] Wang et al. (2015)**: Q-Learning Approach for SON with A3 Offset.
- **[2] Zhang et al. (2023)**: Self-Organizing Network Load Balancing Survey.
- **[3] Huang et al. (2024)**: MILP Formulation for Load Balancing.
- **[4] Das et al. (2023)**: TiDE: Time-series Dense Encoder.
- **[5] 3GPP TS 36.331**: Radio Resource Control (RRC) Specification.

---

## 👥 Authors
- **Loukili Samya**
- **Kenza El Khaniri**
- Supervised by **Mr. Toufik Massrour** (ENSAM Meknès).

---
*Developed for R&D purposes using the Telecom Italia Big Data Challenge dataset.*
