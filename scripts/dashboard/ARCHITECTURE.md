# SON Dashboard Architecture

## 🚀 Overview
This dashboard provides a real-time interface for monitoring and simulating the Self-Organizing Network (SON) optimization engine. It transitions from a static demonstration to a data-driven production tool using real Milan network traffic.

## 🏗️ Layers

### 1. Data Layer (`data_loader.py`)
- **Caching**: Uses `@st.cache_data` and `@st.cache_resource` for high performance.
- **Aggregators**: Joins cell-level traffic with antenna mappings.
- **ML Integration**: Loads XGBoost models and generates real-time predictions.
- **Validation**: Schema enforcement for critical Parquet files.

### 2. Logic Layer (`milp_connector.py`)
- **Simulation**: Implements spatial offloading logic using `fractions.parquet`.
- **Integrity**: Calculates mass conservation (C1), leakage (C2), and capacity compliance (C3).
- **Heuristics**: Provides fast approximations of MILP outcomes for UI responsiveness.

### 3. UI Layer (`pages/` & `components/`)
- **Modular Pages**: Each page (`overview`, `simulation`, etc.) is a standalone module.
- **Components**: Reusable Plotly wrappers and styled KPI cards.
- **State Management**: Uses `st.session_state` to persist simulation results across navigation.

## 🔄 Data Flow
1. **Bootstrap**: `app.py` initializes configuration and loads core data (Topology, Fractions).
2. **Predict**: `model_perf` triggers predictions if not cached.
3. **Simulate**: User selects a slot; `MILPConnector` computes offloading.
4. **Validate**: Integrity checks are performed on simulation outputs.
5. **Visualize**: Results are rendered via custom Plotly components.

## 🛠️ Tech Stack
- **Streamlit**: Web framework.
- **Polars**: Fast data processing.
- **Plotly**: Interactive visualizations.
- **XGBoost**: Predictive engine.
- **Pydantic**: Configuration management.
