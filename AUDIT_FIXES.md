# 🛠️ Audit Report: SON Dashboard Fixes

**Date**: 2026-05-27
**Status**: All Critical and Major bugs resolved.

## 🔴 Critical Fixes

### 1. Recruiter Mode (Threshold Factor)
- **Problem**: The `threshold_factor` slider value was not being returned by the sidebar component, rendering the "Recruiter Mode" inoperative.
- **Fix**: Added `"threshold_factor": threshold_factor` to the return dictionary in `sidebar.py`.

### 2. Capacity Logic (Nominal vs Physical)
- **Problem**: `nominal_capacity` (statistical P90 threshold) was being used as the hard physical capacity constraint in the MILP, causing incorrect congestion detection.
- **Fix**: 
    - Added `load_physical_capacities()` to `data_loader.py` to read real capacity from YAML.
    - Updated `milp_connector.py` to use `trigger_thresholds` (nominal) for detection and `physical_caps` for constraints.

### 3. Real MILP Solver Integration
- **Problem**: The dashboard was using stubs instead of the global MILP optimization in the decoupled engine.
- **Fix**: 
    - Fully implemented `SimulationEngine` in `src/simulation/engine.py` using `solve_congestion_milp`.
    - Added support for Static, Greedy, and Dynamic (MILP) policies.
    - Improved solver portability by adding automatic `cbc` detection in system PATH with fallback to local Windows path.
    - Optimized Dockerfile to install `coinor-cbc` and include all necessary source code.

### 4. 24h Time Filter
- **Problem**: The overview page used a filter based on seconds (`48 * 1800`) instead of slot indices, resulting in incorrect data windows.
- **Fix**: Updated filter to `max_slot - 48` in `overview.py`.

## 🟡 Major Fixes

### 5. Actual vs Predicted Traffic
- **Problem**: The dashboard confused `target_1h` (predictions) with actual observed traffic in some views.
- **Fix**: Split data loading into `load_traffic_data` (Actuals from `work_*.parquet`) and `load_predicted_traffic` (Predictions from `features_*.parquet`).

### 6. Mapping Structure Robustness
- **Problem**: The cell-to-antenna mapping logic assumed a fixed JSON structure, which could fail if the mapping was inverted.
- **Fix**: Added a structural check in `load_cell_to_antenna_map` to handle both `{ant_id: [squares]}` and `{square_id: ant_id}` formats.

### 7. Solver Resilience
- **Problem**: Fallback logic masked errors by returning zero congestion, giving a false sense of stability.
- **Fix**: Updated `milp_fallback` in `resilience.py` to return `NaN` for excess values and explicit error statuses.

## ✨ UI/UX & Transparency
- **Honest Messaging**: Added explicit success/info banners explaining that 0% gain is normal when no congestion exists.
- **Comparative Table**: Added a "Static vs SON" table in the Simulation tab to prove mass conservation and show deltas.
- **Global Disclaimer**: Added a mandatory disclaimer about simulated `n_users` and experimental gains.

---
*Audit performed by Gemini CLI Senior Engineer.*
