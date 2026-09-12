# 🌐 WiseNet
### Autonomous Predictive Self-Organizing Network (SON) Optimization
*(Technical repository name: `spatial-son-milp` | Version: **v1.5**)*  
**Design & Development of Version 1.5: [Samya Loukili](https://github.com/samya818) & Fatima Zahra Azzi**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![3GPP TR 38.901](https://img.shields.io/badge/3GPP-TR%2038.901%20Compliant-purple.svg)](https://www.3gpp.org/specifications-technologies)
[![Pyomo](https://img.shields.io/badge/Pyomo-MILP%20Engine-green)](http://www.pyomo.org/)
[![Coin-OR CBC](https://img.shields.io/badge/Solver-Coin--OR%20CBC%20(Open%20Source)-informational)](https://github.com/coin-or/Cbc)
[![XGBoost](https://img.shields.io/badge/XGBoost-Quantile%20q80-orange)](https://xgboost.readthedocs.io/)
[![CAMARA Ready](https://img.shields.io/badge/GSMA-CAMARA%20Open%20Gateway-blueviolet)](https://camaraproject.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Interactive%20App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **A mobile cellular network that anticipates its own congestion and reorganizes autonomously.**  
> A complete autonomous pipeline (SON — *Self-Organizing Network*) combining predictive Machine Learning, 3GPP tri-sector & multi-carrier radio propagation, and exact global mathematical optimization (MILP) solved in less than one second.  
> *Version 1.5 designed, developed, and evaluated jointly by Samya Loukili and Fatima Zahra Azzi.*

---

> ### 🧭 Looking to understand the entire architecture from A to Z?
> For reviewers, engineers, and researchers seeking a comprehensive walkthrough—from intuitive analogies to radio propagation equations and engineering trade-offs—consult our central interactive document:  
> 👉 **[📘 Open the Full Explanatory Report — WiseNet from A to Z (`docs/Rapport_WiseNet_Projet_Explique.html`)](docs/Rapport_WiseNet_Projet_Explique.html)**  
> *(Complete guide, zero unnecessary jargon, optimized for screen reading and direct PDF export).*  
> 👉 **[🔬 Open the English Scientific Report (`docs/WiseNet_V1_5_Scientific_Report.html`)](docs/WiseNet_V1_5_Scientific_Report.html)**

---

> [!NOTE]
> ### ⏪ Looking for Version 1.0 as it was originally built?
> You can access the entire **original v1.0 repository intact**, with its initial source code and original README:
> - 🌿 **[👉 Browse the v1.0 Repository & Original README on GitHub (`v1-stable` Branch)](https://github.com/samya818/spatial-son-milp/tree/v1-stable)**
> - 🏷️ **[Official Release Tag v1.0 (`v1.0-validated`)](https://github.com/samya818/spatial-son-milp/tree/v1.0-validated)**
> - 📄 **[Read the archived copy of README v1.0 in this branch (`docs/README_v1.md`)](docs/README_v1.md)**
> - 🇫🇷 **[Lire la version française de ce README (`docs/README_fr.md`)](docs/README_fr.md)**
> - 💻 **Via command line:** `git checkout v1-stable` *(or `git clone -b v1-stable https://github.com/samya818/spatial-son-milp.git`)*

---

### 📌 Quick Navigation: Versions & Resources

| Resource | What you will find | Direct Link |
| :--- | :--- | :--- |
| **WiseNet v1.5 (Current)** | 3GPP multi-sector architecture, dual-carrier $(s, f)$, 24h closed loop, CAMARA & Vodafone APIs | **This document (README.md)** |
| **Jury Defense Guide & FAQ (FR)** | Clear justification of Milan data, Vodafone Sandbox APIs, and Device Location | [🎓 `docs/GUIDE_JURY_CAMARA_ET_DONNEES.md`](docs/GUIDE_JURY_CAMARA_ET_DONNEES.md) |
| **Version 1.0 (Original Repo & README)** | Direct access to frozen v1.0 repository with original README | [🌿 **Access v1.0 on GitHub**](https://github.com/samya818/spatial-son-milp/tree/v1-stable) |
| **Complete Reference Guide (FR)** | In-depth pedagogical explanation from A to Z (philosophy, physics, telecom) | [📘 `docs/Rapport_WiseNet_Projet_Explique.html`](docs/Rapport_WiseNet_Projet_Explique.html) |
| **Scientific Report (EN)** | Verified benchmarks, formal mathematical formulations & protocol | [🔬 `docs/WiseNet_V1_5_Scientific_Report.html`](docs/WiseNet_V1_5_Scientific_Report.html) |
| **README v1.0 (Archived Copy)** | Original v1.0 documentation preserved in `docs/` | [📄 `docs/README_v1.md`](docs/README_v1.md) |
| **French README (Copie FR)** | Version originale française de cette documentation | [🇫🇷 `docs/README_fr.md`](docs/README_fr.md) |
| **Release v1.0-validated** | Official release tag on GitHub | [🏷️ Tag `v1.0-validated`](https://github.com/samya818/spatial-son-milp/releases/tag/v1.0-validated) |

---

## 📑 Table of Contents
1. [🌟 The Telecom Challenge: Why WiseNet Exists](#-the-telecom-challenge-why-wisenet-exists)
2. [🧭 The Design Journey: Why Most Prediction-to-Action Systems Fail in the Real World](#-the-design-journey-why-most-prediction-to-action-systems-fail-in-the-real-world)
   - [The Trap We Had to Avoid](#the-trap-we-had-to-avoid)
   - [The Insight That Changed Everything](#the-insight-that-changed-everything)
   - [What This Means in Practice](#what-this-means-in-practice)
   - [🛡️ Formal Proof: Why WiseNet Escapes the Lucas Critique](#%EF%B8%8F-formal-proof-why-wisenet-escapes-the-lucas-critique)
   - [Direct Verification in Code](#direct-verification-in-code)
   - [The Honest Limit](#the-honest-limit)
3. [💡 The WiseNet Philosophy: Pragmatic Engineering](#-the-wisenet-philosophy-pragmatic-engineering)
4. [📖 The Story of V1.5: Why This Version and Not a V2?](#-the-story-of-v15-why-this-version-and-not-a-v2)
5. [🚀 Everything Built in WiseNet V1.5 (And Why)](#-everything-built-in-wisenet-v15-and-why)
   - [Building Block 1: 3GPP Tri-Sector Hexagonal Topology](#building-block-1-3gpp-tri-sector-hexagonal-topology)
   - [Building Block 2: Dual-Carrier Spectrum & the $(s, f)$ Logical Unit](#building-block-2-dual-carrier-spectrum--the-s-f-logical-unit)
   - [Building Block 3: Micro-Grid Spatial Simulation & Directional RSRP](#building-block-3-micro-grid-spatial-simulation--directional-rsrp)
   - [Building Block 4: Dual Offloading (Horizontal vs. Vertical)](#building-block-4-dual-offloading-horizontal-vs-vertical)
   - [Building Block 5: The Offline / Online Architectural Decoupling](#building-block-5-the-offline--online-architectural-decoupling)
   - [Building Block 6: Exact MILP Decision Engine (< 0.8s)](#building-block-6-exact-milp-decision-engine--08s)
   - [Building Block 7: 24-Hour Closed-Loop Predictive Simulation & $q_{80}$ Quantile ML](#building-block-7-24-hour-closed-loop-predictive-simulation--q_80-quantile-ml)
   - [Building Block 8: Industrial GSMA Open Gateway & Vodafone APIs](#building-block-8-industrial-gsma-open-gateway--vodafone-apis)
6. [📐 End-to-End Pipeline Architecture Diagram](#-end-to-end-pipeline-architecture-diagram)
7. [📊 Scientific Evidence: Measured Results on Milan Real-World Data](#-scientific-evidence-measured-results-on-milan-real-world-data)
8. [🛡️ Why End Users Never Suffer Degradation](#%EF%B8%8F-why-end-users-never-suffer-degradation)
9. [⚡ Quick Start & Reproduction Commands](#-quick-start--reproduction-commands)
10. [🗂️ Detailed Repository Structure](#%EF%B8%8F-detailed-repository-structure)
11. [👥 Credits & Acknowledgments](#-credits--acknowledgments)

---

## 🌟 The Telecom Challenge: Why WiseNet Exists

Picture a Friday evening downtown: thousands of people leave offices, gather in restaurants, or attend a stadium concert. Their mobile phones overwhelm the local cell tower. Calls drop, video streams freeze.  
Yet, **only 300 meters away**, in a quiet office district, another tower sits with **70% idle, unused capacity**.

```
THE TYPICAL PROBLEM (WASTE & CONGESTION):
+-----------------------------------+             +-----------------------------------+
|      Tower A (City Center)        |             |    Tower B (Office District)      |
|    Load: 130% [SATURATED]         |             |      Load: 30% [UNDERUTILIZED]    |
|   >>> Dropped calls, zero speed   |             |   >>> Wasted spectral bandwidth   |
+-----------------------------------+             +-----------------------------------+
```

### The Magic Lever: Handover and the A3 Event Offset
In standardized mobile cellular networks (4G LTE and 5G NR), a smartphone decides when to hand over to a neighboring cell (*Handover*) according to the 3GPP standard condition (Event A3):

$$\text{RSRP}_{\text{neighbor}} + \delta > \text{RSRP}_{\text{current}}$$

* **RSRP** (*Reference Signal Received Power*) measures raw radio signal power received by the mobile phone (in dBm).
* **Offset $\delta$** is a software margin dynamically adjustable remotely by the operator (in dB).

If the operator increases this offset $\delta$ on Tower A in favor of Tower B, **smartphones in the boundary zone automatically switch to Tower B**, without dropping calls and **without spending a single dollar on new physical infrastructure**.

### The Challenge: Why Humans Cannot Solve This Manually
An urban network comprises hundreds of interconnected cells. If Tower A offloads onto Tower B, Tower B may in turn become congested and need to offload onto Tower C. This creates a **complex domino effect**.  
**WiseNet** solves this puzzle autonomously: it **predicts** future congestion, **simulates** signal physics, and **computes the optimal mathematical combination of all offsets across the entire network simultaneously**, in less than one second.

---

## 🧭 The Design Journey: Why Most Prediction-to-Action Systems Fail in the Real World

When we started building WiseNet, we faced a question that breaks most ML-for-control projects:

> *You train a model to predict the future. Then you act on that prediction. But the moment you act, you change the very world the model was trained on. Does the prediction still mean anything?*

This is not a bug in the code. It is a structural trap. Across finance, economics, and network engineering, teams have watched their beautifully accurate models collapse the instant they went from "observing" to "steering." The model learned patterns from a world where nobody was steering. Once steering begins, the patterns change. The model, blind to its own influence, drifts into nonsense.

We knew that if WiseNet fell into this trap, it would not matter how elegant our optimizer was, or how clean our data was. The system would work beautifully on historical benchmarks and then quietly fail in production.

### The Trap We Had to Avoid

The naive way to build a SON optimizer is to predict *traffic per antenna*, then use those predictions to decide which antenna should offload to which neighbor. This feels intuitive. But it hides a fatal loop:

1. Your model learns: *"Antenna A usually carries this much traffic at 2 PM."*  
2. Then your policy says: *"Antenna A is overloaded — push users to Antenna B."*  
3. Next hour, Antenna A's traffic drops. Not because demand dropped, but because *you* moved it.  
4. The model looks at the new numbers and thinks: *"Demand on Antenna A is falling. I should predict less next time."*  
5. But demand never fell. You only hid it behind a handover. The model is now learning from its own shadow.

In control theory and macroeconomics, this is the **Lucas Critique (1976)**: a model trained under passive observation loses validity the moment it becomes an active policy participant. In modern machine learning, it is called **Performative Prediction**: the predictor performs an action that reshapes the distribution it is trying to predict.

We refused to accept that this was inevitable.

### The Insight That Changed Everything

We stopped and asked: ***What if the thing we predict is not the thing we control?***

In a mobile cellular network, users do not choose which antenna serves them. They choose to open an app, stream a video, send a message. That decision — how much data they consume — happens in a physical place: a 235-meter square on the Milan grid. It is an organic human behavior. It does not change just because the network quietly hands them off from one tower to another.

So we redesigned the architecture around a simple but strict causal separation:

* **Predict the ground, not the tower.**  
  Our model predicts demand per geographic cell (`square_id`) — the actual human activity on the ground. This demand exists independently of network policy. A handover does not move the person, and it does not change how much data they want.
* **Control the assignment, not the demand.**  
  The optimizer decides how to distribute that fixed, predicted demand across antennas using physical signal models. It moves the *connection*, never the *behavior*.

Because the predicted quantity (ground demand) is causally untouched by the controlled quantity (antenna offsets), the model's training distribution remains valid even after deployment. The world the model learned from — organic human traffic patterns — is the same world it continues to predict into. The policy redistributes what is already there; it does not alter what is coming.

### What This Means in Practice

In our closed-loop validation, the model sees lag features, rolling averages, and seasonal patterns drawn from historical demand per geographic cell. These features describe human rhythms: morning commutes, lunch spikes, evening streaming. They are unaffected by whether yesterday's optimizer shifted load from sector 3 to sector 7.

If we had instead trained on traffic *per antenna*, those same lags would be poisoned. A spike at 2 PM might be a real demand surge, or it might be a residual from an aggressive offset at 1:30 PM. The model could not tell the difference. The signal would be corrupted by the system's own past decisions.

By keeping the prediction layer anchored to geography and the control layer anchored to radio assignment, we created a one-way street: predictions flow forward, decisions flow sideways. They never loop back to contaminate the source.

---

### 🛡️ Formal Proof: Why WiseNet Escapes the Lucas Critique

Formally, this causal separation is reflected in both the code and the mathematics of the system:

| Layer | What it does | Level of Analysis | Causal Regime |
| :--- | :--- | :--- | :--- |
| **ML Prediction** (`src/ml/predictor.py`) | XGBoost Quantile $q_{80}$ predicts traffic demand per `square_id` | **Geographic cell** ($235\text{ m} \times 235\text{ m}$) | **Exogenous:** human demand in a physical square does not depend on the antenna serving it |
| **Spatial Model** (`src/spatial/simulator_v1_5.py`) | Fraction matrices $H$ computed by 3GPP physics (distance, azimuth, frequency) | Grid point $\to$ Antenna | **Mechanical:** deterministic radio propagation law, not statistical |
| **MILP Optimization** (`src/optimization/milp_engine_v1_5.py`) | Chooses offsets $\delta$ to minimize residual congestion $\sum e_{s,f}$ | **Radio cell $(s, f)$** (Antenna / Sector / Carrier) | **Endogenous:** the action modifies only radio assignment, never raw demand |

#### The Mathematical Proof of Non-Contamination
If $v_c$ is predicted demand for geographic cell $c$, and $M(\delta)$ is the physical redistribution matrix induced by offset $\delta$, the volume arriving at each antenna is:

$$V_{\text{antenna}} = M(\delta) \cdot v_{\text{cell}}$$

And the fundamental derivative that guarantees absolute system stability is:

$$\frac{\partial v_{\text{cell}}}{\partial \delta} = 0$$

Ground demand is **causally invariant under policy intervention**. The offset only alters the radio routing of this demand. The ML model, trained on historical trajectories where no offloading took place ($\delta = 0$), remains **100% valid under active intervention**. It continues to predict genuine organic demand, which the MILP then mechanically reassigns.

### Direct Verification in Code
In [`src/simulation/closed_loop_v1_5.py`](src/simulation/closed_loop_v1_5.py), the closed loop executes strictly:
1. **Reading**: Read telemetry indexed by geographic coordinate (`square_id`).
2. **Prediction**: `preds_t_plus_1 = model.predict(X_geo)` $\to$ future ground demand estimation.
3. **Optimization**: MILP over tensor $H$ (product of physical fractions $F$ and predicted demand $v$).
4. **Action**: Apply optimal offsets to sectors.

At no point is the ML model trained or fed with traffic counters measured at the tower post-handover. Historical features (lags, rolling averages, seasonality) strictly operate on ground geographic demand, which is completely impervious to offset decisions.

### The Honest Limit
This protection holds **if and only if** model input remains **organic demand per geographic zone**, rather than an internal radio counter aggregated at the base station after handovers have been applied.

In real-world operator deployments (via CAMARA `Network Insights` or `Vodafone Analytics Footfall`), telemetry ingested must represent a proxy of **ground demand** (such as geographic QuadKey footfall or initial cell of coverage), not post-handover load counters. Re-injecting post-optimization antenna counters into model training would re-introduce endogeneity, making the Lucas critique fully applicable.

> 💎 **In Summary:**  
> *"We did not build a better predictor. We built a system where prediction and control occupy different causal lanes."*  
> *(WiseNet survives the Lucas critique not through mathematical tricks, but because its architecture causally decouples human behavior from radio engineering).*

---

## 💡 The WiseNet Philosophy: Pragmatic Engineering

WiseNet is guided by a pragmatic engineering philosophy for AI applied to telecommunications:

* **1. Sub-Second Real-Time Agility (< 1s) vs Theoretical Inertia:**  
  A cellular network does not wait. If an algorithm takes 20 minutes to solve, the crowd has already dispersed and subscribers have already experienced dropped calls. WiseNet optimizes 756 cells in **0.74 seconds**.
* **2. Open-Source Democratization vs Proprietary Licensing:**  
  No commercial $10,000/license solvers (Gurobi/CPLEX) are required to run the project. WiseNet runs 100% on auditable, open-source building blocks: Python, Pyomo, and **Coin-OR CBC**.
* **3. Predictive Caution ($q_{80}$) vs Naive Averaging:**  
  In cellular networks, underestimating a traffic surge causes catastrophic call drops. Slightly overestimating has no negative operational consequence. WiseNet therefore dimensions its decisions on the reasonable worst case (80th percentile quantile).
* **4. Fundamental Offline / Online Decoupling:**  
  Never recompute online what does not change. Urban geometry and radio link budgets are computed once offline, dedicating all online computing power to sub-second decision making.
* **5. Concrete Industrial Connection (GSMA Open Gateway & CAMARA):**  
  An isolated mathematical model has limited value to an operator. WiseNet natively integrates **GSMA Open Gateway / CAMARA APIs** to be production-ready on modern Open RAN architectures (O-RAN Non-RT RIC).

*(To dive deeper into this conceptual journey, read the [WiseNet Explanatory Report](docs/Rapport_WiseNet_Projet_Explique.html)).*

---

## 📖 The Story of V1.5: Why This Version and Not a V2?

Following V1 (which validated the concept with a 73.53% congestion reduction on a simplified isotropic model), a crucial engineering decision arose: **What should we build next?**

### The Pitfall of an "Overly Theoretical V2"
An ultra-theoretical "V2" plan was initially considered:
- Modeling instantaneous micro-interferences between all individual handsets.
- Recomputing network physical matrices on every cycle (15 to 25 minutes of continuous calculation).
- Deploying heavy proprietary commercial solvers.
- Solving a non-linear problem with 12,600 variables.

### The Pragmatic Choice: Why V1.5 is a Superior Design
In the context of technology competitions (notably the **GSMA + Nokia MENA Ignite Hackathon 2026**), this theoretical V2 plan had fatal flaws:
1. **Unacceptable demo latency:** In front of a technical jury or CTO, a live demo lasts minutes. A system requiring 20 minutes per cycle is unusable.
2. **Artificial licensing barriers:** Relying on private paid licenses breaks open-source accessibility.
3. **Misalignment with operator priorities:** Operators prioritize standardized interoperability (GSMA CAMARA APIs) over academic non-linear interference equations.

> 🎯 **The WiseNet V1.5 Choice:**  
> *"Keep what works brilliantly (sub-second execution, MILP linear formulation, free Coin-OR CBC solver, closed-loop pipeline), upgrade the radio model to full 3GPP industrial standards, and connect the system to real operator APIs."*

---

## 🚀 Everything Built in WiseNet V1.5 (And Why)

Here is the detailed breakdown of the major innovations delivered in Version 1.5:

---

### Building Block 1: 3GPP Tri-Sector Hexagonal Topology
*Source file: [`src/topology/builder_v1_5.py`](src/topology/builder_v1_5.py)*

* **In V1:** Antennas were placed randomly and emitted uniform circular coverage (isotropic antenna). In reality, no urban antenna radiates isotropically.
* **What We Built in V1.5:** We deployed a **deterministic 3GPP TR 38.901 hexagonal grid** across the $56.55\text{ km}^2$ area of the City of Milan (1,024 real-world cells):
  * **126 physical macro sites** spaced with strict inter-site distance ($\text{ISD} = 750\text{ meters}$).
  * Each site is split into **3 directional $120^\circ$ sectors** oriented at $0^\circ$ (North), $120^\circ$ (South-East), and $240^\circ$ (South-West), like 3 pizza slices covering the plane.
* **Why this choice?** It faithfully reproduces the real physical geometry of networks deployed by tier-1 operators such as Telecom Italia (TIM) in dense urban environments.

---

### Building Block 2: Dual-Carrier Spectrum & the $(s, f)$ Logical Unit
*Source file: [`src/topology/builder_v1_5.py`](src/topology/builder_v1_5.py)*

* **The Reality:** A telecom cell tower does not operate on a single magic frequency; it stacks multiple spectral layers.
* **What We Built in V1.5:** We incorporated official spectrum licenses from TIM Italy:
  1. **Carrier $F_1$ (LTE Band 3 - 1.8 GHz FDD, 20 MHz):** Anchor layer with long-range propagation and deep wall penetration; nominal capacity of **$6,600.8\text{ MB} / 30\text{ min}$**.
  2. **Carrier $F_2$ (5G NR n78 - 3.5 GHz TDD, 80 MHz):** High-capacity ultra-broadband layer; massive capacity of **$32,580.2\text{ MB} / 30\text{ min}$**.
* **The Elementary $(s, f)$ Unit:**  
  Each physical site comprises $3\text{ sectors} \times 2\text{ carriers} = \mathbf{6\text{ distinct logical radio cells}}$.  
  Across the 126 sites of Milan, this produces **756 independent radio cells $(s, f)$**.
* **Why this choice?** Saturation never hits an entire tower uniformly: it strikes, for example, the 3.5 GHz band on the North sector during an event. Optimizing per $(s, f)$ pair provides surgical control.

---

### Building Block 3: Micro-Grid Spatial Simulation & Directional RSRP
*Source file: [`src/spatial/simulator_v1_5.py`](src/spatial/simulator_v1_5.py)*

* **The Milan Dataset Limitation:** The Milan dataset aggregates traffic on $235\text{ m} \times 235\text{ m}$ squares. Treating each square as a single point discards boundary effects where handovers actually happen.
* **What We Built in V1.5:**
  1. **Micro-discretization:** Each $235\text{m}$ square is discretized into a fine grid of **$20 \times 20 = 400\text{ sub-pixels}$** ($11.75\text{ m} \times 11.75\text{ m}$ each).
  2. **3GPP-Compliant RSRP Computation:** For every sub-pixel, received power is computed according to the standard formula:
     $$\text{RSRP} = P_{\text{tx}} - \text{PathLoss}(d, f) + G(\Delta\theta)$$
     where $G(\Delta\theta) = -\min[12 \cdot (\Delta\theta / 65^\circ)^2, 30\text{ dB}]$ is directional antenna gain based on the angular offset from the sector boresight.
* **Why this choice?** A user aligned with sector boresight receives full power, while a user at the same distance but off-axis suffers 15 to 30 dB attenuation. Incorporating azimuth $\Delta\theta$ ensures realistic handover behavior.

---

### Building Block 4: Dual Offloading (Horizontal vs. Vertical)
*Source files: [`src/spatial/simulator_v1_5.py`](src/spatial/simulator_v1_5.py) & [`src/optimization/milp_engine_v1_5.py`](src/optimization/milp_engine_v1_5.py)*

Reasoning at the $(s, f)$ level unlocks two-dimensional optimization capabilities:

```
                        ┌──────────────────────────────────────────────┐
                        │      VERTICAL OFFLOADING (INTER-BAND)        │
                        │ Shift 3.5 GHz -> 1.8 GHz on the SAME SITE    │
                        └──────────────────────┬───────────────────────┘
                                               │
                                               ▼
+------------------------------------+                   +------------------------------------+
|         SITE 1 - SECTOR 0          |                   |         SITE 2 - SECTOR 2          |
| Carrier F2 (3.5 GHz) [Saturated]   |                   |                                    |
|              ▲                     |   HORIZONTAL      |                                    |
|  (Vertical)  │                     |   OFFLOADING      |                                    |
|              ▼                     | (Inter-Sector)    |                                    |
| Carrier F1 (1.8 GHz) [Capacity]    | ════════════════► | Carrier F1 (1.8 GHz) [Available]   |
+------------------------------------+                   +------------------------------------+
```

1. **Horizontal Offloading (Spatial):** Users on geographic sector boundaries shift to adjacent sectors (on the same site or a neighboring site).
2. **Vertical Offloading (Frequency Layer):** If 5G (3.5 GHz) is saturated while 4G (1.8 GHz) on the **same physical sector** has headroom, users shift carriers **without changing towers**.

---

### Building Block 5: The Offline / Online Architectural Decoupling
*Source file: [`src/spatial/simulator_v1_5.py`](src/spatial/simulator_v1_5.py)*

* **Why is radio simulation traditionally slow?** Evaluating propagation across 409,600 sub-pixels for 756 cells across 7 offset levels requires tens of millions of trigonometric operations.
* **The Architectural Breakthrough:**  
  Building positions and antenna towers do not move every 30 minutes!  
  We precompute transfer fractions **once offline** and store normalized mass tensors (`fractions_v1_5.parquet`).
* **Online Mode (Real-Time):**  
  Every 30-minute slot, the engine simply multiplies these precomputed fractions by predicted traffic demand to instantiate transfer matrices $H$. This online operation takes **less than 0.05 seconds**!

---

### Building Block 6: Exact MILP Decision Engine (< 0.8s)
*Source file: [`src/optimization/milp_engine_v1_5.py`](src/optimization/milp_engine_v1_5.py)*

* **Pyomo + Coin-OR CBC:**  
  Pyomo models the system as a Mixed-Integer Linear Program, solved by open-source **CBC** with no proprietary licenses.
* **Why MILP Beats Greedy Heuristics:**  
  Greedy heuristics act selfishly antenna by antenna: *"I am overloaded, so I dump everything onto my right neighbor."* But if that neighbor is also nearing saturation, greedy moves trigger cascading network failure.  
  In contrast, the MILP considers **all 756 cells simultaneously in a single global matrix**, finding the true global optimum.
* **Measured Execution Time:** **$0.74\text{ seconds}$** to solve 5,292 binary variables under strict mass conservation.

---

### Building Block 7: 24-Hour Closed-Loop Predictive Simulation & $q_{80}$ Quantile ML
*Source file: [`src/simulation/closed_loop_v1_5.py`](src/simulation/closed_loop_v1_5.py)*

* **In reality, the future is uncertain:** Deciding at time $t$ for interval $t+1$ requires reliable demand forecasting.
* **XGBoost Quantile $q_{80}$:**  
  Forecasting an average is hazardous in cellular networks: underestimating peak traffic crashes the cell. We train XGBoost on the **80th percentile quantile**, an intentionally conservative engineering design: *"prepare the network for the reasonable worst case"*.
* **24-Hour Continuous Evaluation:**  
  Simulated across 48 consecutive 30-minute slots on real Milan traffic (**43.57 Terabytes total traffic**). Decisions are made purely on ML forecasts and evaluated against ground truth.
* **Result:** Captures **98.7% of the performance of a clairvoyant theoretical Oracle** (an ideal model with perfect future knowledge).

---

### Building Block 8: Industrial GSMA Open Gateway & Vodafone APIs
*Source files: [`src/camara/client.py`](src/camara/client.py), [`src/camara/footfall_client.py`](src/camara/footfall_client.py), [`src/camara/location_client.py`](src/camara/location_client.py), [`src/camara/qod_trigger.py`](src/camara/qod_trigger.py)*

To seamlessly integrate with global telecommunications standards (**GSMA Open Gateway** / **O-RAN Non-RT RIC**):
1. **Vodafone Analytics Realtime Footfall & Reference QuadKey:** Ingests live, exogenous human density per geographic QuadKey tile (~1 km²), providing genuine ground-truth demand immune to historical handover bias (Lucas-immune).
2. **CAMARA Device Location Verification & Retrieval (`/location-verification/v1/verify` & `/location-retrieval/v0.3/retrieve`):** Replaces artificial/random mock identifiers by validating physical presence of mission-critical IoT devices (ambulances, police patrols, autonomous shuttles) under congested cells before allocating radio resources.
3. **CAMARA Quality on Demand (QoD v1.1.0):** Acts as a **surgical safety net**. If residual saturation persists after global MILP optimization, WiseNet triggers priority QoD sessions (`QOS_E` / `QOS_L` profiles, 5QI=1/3) to guarantee bandwidth for verified critical devices.
4. **Universal Client Architecture:** Supports OAuth2 `client_credentials` authentication directly against the Vodafone Developer Sandbox, with seamless failover to high-fidelity conformant local mocks when sandbox backends are unavailable.


---

## 📐 End-to-End Pipeline Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 1. OFFLINE PHASE                                        │
│                         Computed once during network setup                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
      ┌──────────────────────────────────────┴──────────────────────────────────────┐
      ▼                                                                             ▼
[3GPP Hexagonal Topology]                                                [Milan 1024 Grid]
126 sites x 3 sectors x 2 carriers                                       400 micro-pixels per square
= 756 logical radio cells (s, f)                                         Spatial resolution: 11.75 m
      │                                                                             │
      └──────────────────────────────────────┬──────────────────────────────────────┘
                                             ▼
                           [3GPP Directional RSRP Simulation]
                          P_tx - PL(d,f) + G(Δθ) across 400 pts
                                             │
                                             ▼
                     [Precomputed Fraction Transfer Tensors H]
                     Conserved offloaded/received fraction matrices
                     (Persisted in fractions_v1_5.parquet)

═══════════════════════════════════════════════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  2. ONLINE PHASE                                        │
│                      Executed in a closed loop every 30 minutes                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
             [Vodafone Analytics Realtime Footfall / CAMARA Network Insights]
             Exogenous geographic human density per QuadKey (Lucas-immune)
                                             │
                                             ▼
                           [XGBoost Quantile q80 Demand Predictor]
                          Prudent forecast of future ground demand at t+1
                                             │
                                             ▼
                         [Dynamic Traffic Volume Instantiation]
                          Traffic Tensor = Offline Fractions x Forecast Demand
                                             │
                                             ▼
                        [Exact MILP Decision Engine (Pyomo + CBC)]
                        Global exact optimization across 756 cells
                        Solving time: 0.74 seconds (< 1s)
                                             │
                                             ▼
                       [Application of Handover Offsets (0 to 3 dB)]
                      Horizontal Offloading (spatial) + Vertical (carrier)
                                             │
                                             ▼
                    [CAMARA Device Location Verification]
                    Validate presence of critical fleet under cell
                                             │
                                             ▼
                    [Field Validation & CAMARA QoD Safety Net Trigger]
                    Evaluate residual congestion + provision emergency QoD sessions
                                             │
                                             ▼
                            [Next Cycle (Continuous Closed Loop)]
```

---

## 📊 Scientific Evidence: Measured Results on Milan Real-World Data

All benchmarks are fully reproducible using repository scripts and run on the real **Telecom Italia Big Data Challenge** dataset (`work_1024cells.parquet`).

### 1. At Peak Congestion (30-min Slot — $1.38\text{ TB}$ Traffic)
*Run command: `python -m src.benchmark.benchmark_v1_5`*

| Strategy Tested | Congested / Lost Traffic | GB Equivalent | Gain vs. Static Network | Compute Time |
| :--- | :---: | :---: | :---: | :---: |
| **Static Network (Fixed)** ($\delta = 0\text{ dB}$) | 314,331.7 MB | 306.96 GB | Baseline (0.0 %) | 0.00 s |
| **Greedy Heuristic** (Local, cell-by-cell) | 269,055.3 MB | 262.75 GB | 14.40 % | 0.01 s |
| **WiseNet V1.5 MILP** (Global Exact Optimization) | **260,686.1 MB** | **254.58 GB** | **17.07 %** | **0.74 s** |

*Key finding: MILP saves an additional **+8,369.2 MB (+8.37 GB)** of data compared to the greedy baseline in a single 30-minute interval.*

---

### 2. Full 24-Hour Evaluation (48 Consecutive Slots — $43.57\text{ TB}$ Traffic)
*Run command: `python -m src.benchmark.benchmark_24h_v1_5`*

| Operational Strategy | 24h Cumulative Congestion (GB) | Congestion Reduction | Average Time per Cycle |
| :--- | :---: | :---: | :---: |
| **Static Network** (Unmanaged) | 5,072.57 GB (~5.07 TB) | Baseline | — |
| **Greedy Heuristic** (Local) | 3,852.84 GB | 24.05 % | 0.012 s |
| **WiseNet V1.5 MILP** (Multi-Carrier) | **3,670.99 GB** | **27.63 %** | **0.576 s** |

---

### 3. Predictive Closed Loop (Real ML Uncertainty over 24h)
*Run command: `python -m src.simulation.closed_loop_v1_5`*

In this realistic test, the optimizer receives no future knowledge and optimizes strictly on forecasts produced by the $q_{80}$ XGBoost model:

```
RELATIVE EFFICIENCY COMPARED TO PERFECT CLAIRVOYANT ORACLE (100%):
Theoretical Perfect Oracle  [████████████████████████████████████████] 100.0% (Theoretical Ceiling)
WiseNet Predictive MILP    [███████████████████████████████████████ ]  98.7% (Near-perfect capture!)
Greedy Heuristic           [██──────────────────────────────────────]  86.0% (Lost opportunities)
```

* **+123.56 GB of additional delivered data** over 24 hours compared to the predictive heuristic.
* **Strict mass conservation** verified mathematically to within $10^{-6}$: zero megabytes are artificially created or destroyed.

---

## 🛡️ Why End Users Never Suffer Degradation

A common concern with offloading algorithms is: *"If a user consumes heavy data near the cell center, will the system force a handover and degrade their connection?"*

WiseNet provides **strict physical guarantees** ensuring this never happens:
1. **Radio quality is purely physical:** RSRP depends on distance and antenna radiation pattern, not tower traffic load. The system cannot artificially claim a weak signal is strong.
2. **Cell centers are physically shielded:** A phone near its serving tower receives a very strong signal (e.g. $-75\text{ dBm}$), while neighboring towers arrive at $-105\text{ dBm}$. A maximum offset of $3\text{ dB}$ will never overcome a $30\text{ dB}$ physical gap. These users **never switch**.
3. **Only boundary users transition:** Only users located where signals from both cells are nearly equal (gap $< 3\text{ dB}$) participate in handovers. For them, switching is transparent and quality-preserving.

*(For detailed derivations, see Section 1.9 of the [Explanatory Report](docs/Rapport_WiseNet_Projet_Explique.html)).*

---

## ⚡ Quick Start & Reproduction Commands

### 1. Two-Minute Installation

```bash
# Clone the repository
git clone https://github.com/samya818/spatial-son-milp.git
cd spatial-son-milp

# Create a Python virtual environment
python -m venv .venv

# Activate the environment:
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# Upgrade pip & install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Environment Variables (Optional Vodafone Sandbox Credentials)

```bash
cp .env.example .env
# Edit .env with your credentials if testing live Vodafone sandbox APIs
```

### 3. Run Automated Tests

```bash
pytest tests -v
# Expected: 23 passed
```

### 4. Reproduce V1.5 Benchmarks

```bash
# Run peak congestion benchmark (0.74s solve time)
python -m src.benchmark.benchmark_v1_5

# Run full 24-hour evaluation (48 slots)
python -m src.benchmark.benchmark_24h_v1_5

# Run closed-loop predictive simulation (ML + MILP)
python -m src.simulation.closed_loop_v1_5

# Run CAMARA 6-step end-to-end demo pipeline
python scripts/demo_camara_pipeline.py
```

### 5. Launch Interactive Dashboard

```bash
streamlit run scripts/dashboard/app.py
```
Open your browser at `http://localhost:8501`.

---

## 🗂️ Detailed Repository Structure

```text
spatial-son-milp/
├── docs/                                   # DOCUMENTATION & TECHNICAL REPORTS
│   ├── Rapport_WiseNet_Projet_Explique.html # 📘 CENTRAL GUIDE: Comprehensive Explanatory Report (HTML)
│   ├── WiseNet_V1_5_Scientific_Report.html # 🔬 Full V1.5 Scientific Report (HTML)
│   ├── WiseNet_V1_5_Scientific_Report.md   # 📝 Markdown version of scientific report
│   ├── README_v1.md                        # 📄 Archived original v1.0 README
│   └── README_fr.md                        # 🇫🇷 French version of this README
│
├── src/                                    # PRODUCTION SOURCE CODE
│   ├── topology/
│   │   ├── builder.py                      # Isotropic v1.0 topology
│   │   └── builder_v1_5.py                 # ⭐ 3GPP TR 38.901 Hexagonal Tri-Sector Topology (TIM 1.8/3.5GHz)
│   ├── spatial/
│   │   ├── simulator.py                    # Spatial simulator v1.0
│   │   └── simulator_v1_5.py               # ⭐ 3GPP Micro-grid Simulator (400 pts/sq, directional RSRP, tensor H)
│   ├── optimization/
│   │   ├── milp_engine.py                  # MILP solver v1.0
│   │   ├── milp_engine_v1_5.py             # ⭐ MILP Decision Engine v1.5 (Pyomo, (s,f) units, Coin-OR CBC)
│   │   └── greedy_engine_v1_5.py           # Conservative greedy baseline heuristic
│   ├── simulation/
│   │   ├── closed_loop_sim.py              # Closed-loop v1.0
│   │   └── closed_loop_v1_5.py             # ⭐ 24-hour Predictive Closed Loop v1.5 (XGBoost q80 + MILP)
│   ├── benchmark/
│   │   ├── benchmark_v1_5.py               # 30-min peak benchmark script
│   │   └── benchmark_24h_v1_5.py           # 24-hour continuous benchmark script
│   └── camara/
│       ├── client.py                       # ⭐ CAMARA QoD v1.1.0 Client (OAuth2, Sessions lifecycle)
│       ├── footfall_client.py              # ⭐ Vodafone Analytics Realtime Footfall & Reference QuadKey Client
│       └── qod_trigger.py                  # ⭐ Post-MILP Emergency QoD Safety Net Trigger
│
├── research/
│   ├── notebooks_v1_5/
│   │   ├── pipeline_v1_5.ipynb             # 📓 Reproducible research notebook v1.5
│   │   └── camara_api_integration.ipynb    # 📓 CAMARA & Vodafone API integration walkthrough
│   └── notebooks/                          # Initial exploratory notebooks (v1.0)
│
├── scripts/
│   ├── dashboard/                          # Interactive Streamlit application
│   ├── demo_camara_pipeline.py             # 6-step CAMARA & Vodafone end-to-end demo script
│   └── check_camara_sandbox.py             # Connectivity & token validation for Vodafone sandbox
├── tests/                                  # Unit & integration tests (23 test cases)
│   ├── unit/                               # Radio, transfer, engine, and CAMARA unit tests
│   └── integration/                        # End-to-end closed-loop pipeline tests
├── check_environment.py                    # Environment pre-flight & solver availability checker
└── requirements.txt                        # Core runtime dependencies
```

---

## 👥 Credits & Acknowledgments

### Version 1.5 (3GPP Architecture, $(s, f)$ Formulation, Dual Offloading, CAMARA & 24h Loop)
* **Samya Loukili & Fatima Zahra Azzi** — **Design, research, modeling, and development of Version 1.5**:
  * Conception of the 3GPP tri-sector hexagonal topology and TIM dual-carrier spectrum ($F_1/F_2$).
  * Mathematical formulation of the MILP per elementary radio cell $(s, f)$ and Coin-OR CBC resolution.
  * Physical modeling of directional 3GPP RSRP and micro-grid spatial simulation ($400\text{ pts/square}$).
  * Algorithms for dual horizontal and vertical offloading with strict mass conservation.
  * 24-hour predictive closed-loop pipeline with Quantile $q_{80}$ ML and industrial GSMA Open Gateway / Vodafone API integration.
  * Authorship of scientific reports, experimental benchmarks, and engineering documentation.

### Historical Track: Version 1.0 (Preliminary Exploratory Isotropic Phase)
* Developed initially as a team project by **Samya Loukili** and ** fatima zahra azzi**,

### Standardized References
* **3GPP TR 38.901**: *Channel model for frequencies from 0.5 to 100 GHz (Urban Macro specifications).*
* **3GPP TS 36.331 / TS 38.331**: *Radio Resource Control (RRC) — Event A3 Handover offset parameters.*
* **GSMA Open Gateway & CAMARA Project**: *Quality on Demand (QoD v1.1.0) & Network Insights APIs Specifications.*
* **Vodafone Developer Platform**: *Vodafone Analytics Realtime Footfall & Reference QuadKey APIs.*
* **Telecom Italia Big Data Challenge**: *Open telecommunications density grid of the City of Milan.*
