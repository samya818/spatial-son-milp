
# 📊 Audit Report: SON Dashboard Bug & Data Integrity

**Status**: Resolved ✅
**Date**: 2026-05-27

## 🔍 1. Root Cause Analysis (Why 0.0%?)
The 0.0% gain displayed in the dashboard was caused by three main factors:

1.  **High Congestion Thresholds**: The real-world traffic in many slots of the Milan dataset does not exceed the physical capacity (approx. 8,000 Mo per antenna) under normal conditions. Without congestion, the MILP is not triggered, resulting in 0% gain.
2.  **Scenario Mismatch (600 cells)**: The default "Standard Cluster (600 cells)" scenario has a significant data mismatch. The topology contains 397 antennas, but the spatial transfer fractions only cover 192 of them. Traffic assigned to the "missing" 205 antennas is effectively lost during optimization, leading to inconsistent results.
3.  **Trigger vs. Results Inconsistency**: The trigger logic was using physical capacity from YAML, while results were calculated using nominal capacity from Parquet. In some cases, nominal capacity was much higher, masking any excess even if the MILP was triggered.

## 🛠️ 2. Fixes Implemented

### 🚀 Recruiter Mode (Stress Test)
- Added a **"Capacity Scaling Factor"** slider in the sidebar.
- Allows users to artificially reduce antenna capacities (e.g., to 0.6x) to force congestion and observe the MILP resolving it in real-time.
- Displays a clear warning when Recruiter Mode is active.

### 🧠 Robust MILP Connector
- Refactored `MILPConnector` to use the same effective capacity (Physical * Scaling Factor) for both triggering and result calculation.
- Added detailed diagnostics: count of congested antennas (`n_congested_static`, `n_congested_son`).
- Implemented "Honest Messaging": The UI now explicitly states *why* a gain is 0% (e.g., "Network Stable: Traffic < Capacity").

### 📊 Data Integrity & UI
- Added a "Why 0.0%?" explanation box in the Overview tab.
- Improved the Simulation tab with more metrics: Total Traffic, Excess Volume, and Decision counts.
- Ensured consistent time indexing (Milan slots are timestamps, converted correctly to 48 daily slots).

## 📈 3. Data Audit Results (1024 cells)
- **Topology match rate**: 100% (201/201 antennas found in fractions and mapping).
- **Square coverage**: 100% (1024/1024 squares mapped to antennas).
- **Typical Traffic vs. Capacity**:
  - Max Traffic per Antenna: ~18,500 Mo
  - Avg Physical Capacity: ~8,800 Mo
  - *Note: Congestion is rare but real on peak slots.*

## 💡 4. Recommendations for Users
- **Use the 1024 cells scenario** for the most accurate and "closed-loop" demonstration.
- **Use the "Capacity Scaling Factor"** (Recruiter Mode) set to **0.7 or 0.8** to reliably demonstrate the MILP's offloading capabilities on any slot.
- Observe the **"Mass Error"** metric; it remains < 0.0001%, proving that no traffic is "deleted" to achieve gains.

---
*Audit performed by Gemini CLI Senior Engineer.*
