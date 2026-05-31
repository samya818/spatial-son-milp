# 🛰️ SON Industrial Dashboard

Production-grade monitoring and simulation interface for the 4G/LTE Self-Organizing Network project.

## 🏗️ Architecture
The dashboard follows a modular design pattern to ensure maintainability and high performance:

- **`app.py`**: Main entry point and routing.
- **`data_loader.py`**: Cached Polars loading and schema validation.
- **`milp_connector.py`**: High-performance interface to the optimization engine.
- **`pages/`**: Isolated modules for each dashboard view.
- **`components/`**: Reusable UI elements (KPIs, Plotly charts).

## 🚀 Getting Started

### 1. Install dependencies
```bash
pip install -r requirements-dashboard.txt
```

### 2. Generate Data Assets
The dashboard requires pre-processed data. If you are running this for the first time, execute the pipeline:
```bash
python scripts/run_pipeline.py
```
*Note: This might take a few minutes as it processes 1024 cells traffic.*

### 3. Launch the dashboard
```bash
streamlit run scripts/dashboard/app.py
```

## 🛠️ Features
- **Dynamic Physical Validation**: Real-time checking of mass conservation and cluster integrity.
- **Advanced Visualizations**: Sankey diagrams for traffic flows and interactive congestion heatmaps.
- **Simulation Control**: Adjust MILP thresholds and predictive models on the fly.
- **Performance Optimized**: Heavy computations are cached using Streamlit's `@st.cache_data`.

## 👥 Authors
- Loukili Samya
- Kenza El Khaniri
