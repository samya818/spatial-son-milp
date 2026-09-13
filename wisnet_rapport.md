# WiseNet V2.0: Autonomous Self-Organizing Mobile Network (SON) with Spatial-Temporal Demand Forecasting, 3GPP Radio Physics, Global MILP Optimization, and GSMA Open Gateway CAMARA Integration

**A Comprehensive Scientific, Architectural, and Empirical Report**  
*Prepared for the MENA Ignite Hackathon 2026 — GSMA & Nokia*  
*Authors: Samya Loukili & Fatima Zahra Azzi*  
*Technical Repository: [github.com/samya818/spatial-son-milp](https://github.com/samya818/spatial-son-milp)*  
*Target Standards: 3GPP TR 38.901, TS 36.331, TS 38.331 | GSMA Open Gateway CAMARA API v1.1.0*  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Core Problem: Spatial-Temporal Traffic Misalignment in Cellular Networks](#2-the-core-problem-spatial-temporal-traffic-misalignment-in-cellular-networks)
3. [The Actuation Mechanism: Handover Physics, RSRP, and A3 Cell Individual Offsets](#3-the-actuation-mechanism-handover-physics-rsrp-and-a3-cell-individual-offsets)
4. [Dataset & Spatial Discretization: The Milan Telecom Italia Benchmark](#4-dataset--spatial-discretization-the-milan-telecom-italia-benchmark)
5. [Disambiguation: Geographic Cells vs. Radio Cells](#5-disambiguation-geographic-cells-vs-radio-cells)
6. [3GPP TR 38.901 Network Topology: Tri-Sector Macro Sites and Dual-Carrier Layering](#6-3gpp-tr-38901-network-topology-tri-sector-macro-sites-and-dual-carrier-layering)
7. [Radio Propagation Modeling & The Offline Spatial Transfer Matrix Simulator](#7-radio-propagation-modeling--the-offline-spatial-transfer-matrix-simulator)
8. [Machine Learning Engine: Quantile Regression ($q_{80}$) and Asymmetric Loss (ADR-001)](#8-machine-learning-engine-quantile-regression-q_80-and-asymmetric-loss-adr-001)
9. [Causal Intelligence & Lucas Critique Immunity](#9-causal-intelligence--lucas-critique-immunity)
10. [Dynamic Coupling: Volumetric Transfer ($H$) Matrices](#10-dynamic-coupling-volumetric-transfer-h-matrices)
11. [The Optimization Engine: Global Mixed-Integer Linear Programming (MILP) with Pyomo & CBC](#11-the-optimization-engine-global-mixed-integer-linear-programming-milp-with-pyomo--cbc)
12. [Theoretical Superiority over Greedy Heuristics: Secondary Congestion (ADR-002)](#12-theoretical-superiority-over-greedy-heuristics-secondary-congestion-adr-002)
13. [Boundary Zone Protection: Physical Invariance Guarantees for End Users](#13-boundary-zone-protection-physical-invariance-guarantees-for-end-users)
14. [Rigorous 48-Hour (Two-Day, 96-Slot) Empirical Simulation Results](#14-rigorous-48-hour-two-day-96-slot-empirical-simulation-results)
    - [14.1 Experimental Protocol & Rigor](#141-experimental-protocol--rigor)
    - [14.2 Global 48-Hour Cumulative Performance](#142-global-48-hour-cumulative-performance)
    - [14.3 Diurnal Progression: Day 1 (J1) vs. Day 2 (J2) Analysis](#143-diurnal-progression-day-1-j1-vs-day-2-j2-analysis)
    - [14.4 Theoretical Oracle Benchmark & Machine Learning Efficiency](#144-theoretical-oracle-benchmark--machine-learning-efficiency)
    - [14.5 Computational Speed & Real-Time Production Viability](#145-computational-speed--real-time-production-viability)
15. [GSMA Open Gateway & CAMARA API Integration: The 6-Step Closed-Loop Pipeline](#15-gsma-open-gateway--camara-api-integration-the-6-step-closed-loop-pipeline)
16. [The Telecom Digital Twin & Cross-Operator Portability: Reconciling Milan & Vodafone](#16-the-telecom-digital-twin--cross-operator-portability-reconciling-milan--vodafone)
17. [Resilience Engineering: The Circuit Breaker Architecture](#17-resilience-engineering-the-circuit-breaker-architecture)
18. [MENA Regional Operational Scenarios](#18-mena-regional-operational-scenarios)
19. [Flagship V2.0 Interactive Platform (Streamlit & PyDeck)](#19-flagship-v20-interactive-platform-streamlit--pydeck)
20. [O-RAN Standardization & Production Deployment Roadmap](#20-o-ran-standardization--production-deployment-roadmap)
21. [Open-Source Stack, Verification, and Reproducibility](#21-open-source-stack-verification-and-reproducibility)
22. [Conclusion](#22-conclusion)

---

## 1. Executive Summary

**WiseNet** (internally designated `spatial-son-milp`) is a carrier-grade, closed-loop Self-Organizing Network (SON) architecture designed to solve localized radio access network (RAN) congestion autonomously. By combining **3GPP-compliant radio propagation physics**, **asymmetric machine learning forecasting (XGBoost $q_{80}$)**, **exact global Mixed-Integer Linear Programming (Pyomo/Coin-OR CBC)**, and **standardized GSMA Open Gateway CAMARA APIs**, WiseNet redistributes mobile traffic dynamically without requiring physical antenna reorientation, manual intervention, or capital expenditures (zero CapEx).

Operating over a dense metropolitan grid representing the commercial core of Milan, Italy ($1,024$ geographic cells, $126$ macro-sites, $378$ tri-sector wedges, and $756$ multi-carrier radio cells across 1.8 GHz LTE and 3.5 GHz 5G NR), WiseNet acts as a real-time **Telecom Digital Twin**.

### Key Empirical Findings from Rigorous 48-Hour Continuous Simulation (96 Decision Cycles)
- **Total Network Traffic Evaluated:** $88,348,191.9 \text{ MB}$ ($\approx 86.28 \text{ Terabytes}$ / $86,277.5 \text{ GB}$).
- **Static Baseline Unsatisfied Traffic:** $10,618,332.1 \text{ MB}$ ($10,369.5 \text{ GB}$).
- **WiseNet Closed-Loop Unsatisfied Traffic:** $7,930,446.3 \text{ MB}$ ($7,744.6 \text{ GB}$).
- **Net Traffic Saved from Congestion:** **$2,687,885.8 \text{ MB}$ ($2,624.9 \text{ GB}$ / $2.62 \text{ Terabytes}$)**.
- **Congestion Reduction Rate:** **$25.31\%$** reduction across 48 continuous hours ($26.64\%$ theoretical maximum under a clairvoyant Oracle).
- **Machine Learning Efficiency vs. Clairvoyant Oracle:** **$95.04\%$** ($98.7\%$ on peak hour slots), demonstrating that planning under quantile demand uncertainty ($q_{80}$) achieves near-perfect optimization.
- **Mean Solver Execution Latency:** **$0.583 \text{ seconds}$** per global network-wide decision cycle ($96$ slots solved in $136.8 \text{ seconds}$ total wall time), well within the $15\text{–}30$ minute O-RAN Non-RT RIC management loop.
- **Reliability:** $76.0\%$ of all operational slots experienced direct congestion relief ($73/96$ slots); the remaining $24\%$ operated under nominal load with zero unnecessary handovers.
- **Strict Mass Conservation:** $100.0000\%$ mathematically enforced ($\Delta < 10^{-6}$ error), strictly preventing phantom traffic or artificial data loss.
- **Safety Net Integration:** When residual localized saturation persists, CAMARA **Device Location** (`/verify`) and **Quality on Demand (QoD)** (`/sessions`) APIs provide targeted priority protection to emergency and mission-critical fleets (SAMU, Police, Civil Defense).

---

## 2. The Core Problem: Spatial-Temporal Traffic Misalignment in Cellular Networks

Modern mobile networks face an inherent structural inefficiency: **traffic demand is highly volatile, bursty, and geographically localized, while cellular infrastructure is fixed and statically provisioned**.

Consider a typical urban center:
- At 18:30 on a weekday, a cluster of macro-cells covering a central train station or stadium district is overwhelmed by thousands of commuters streaming video and making voice calls. Channels reach saturation, packet drop rates surge, and users suffer service degradation.
- Simultaneously, 400 meters away in an adjacent financial district where offices have emptied, neighboring macro-cells operate at under $20\%$ capacity, with abundant idle spectral resources.

Traditional static networks do not dynamically redistribute load across physical boundaries. Consequently, operators face severe customer churn and Quality of Service (QoS) degradation **not because aggregate network capacity is insufficient, but because existing capacity is misallocated in space and time**.

### Why Conventional Approaches Fail
1. **Capital Expenditure (CapEx) Expansion:** Building additional base stations is prohibitively expensive (often exceeding €150,000 per macro-site in dense urban centers), involves lengthy municipal zoning permits ($12\text{–}24$ months), and exacerbates inter-cell interference during non-peak hours.
2. **Greedy / Local Heuristics:** Traditional rule-based SON algorithms attempt to offload saturated antennas one-by-one by shifting load to the least congested neighbor. As demonstrated in Architectural Decision Record **ADR-002**, greedy heuristics trigger severe **secondary congestion cascades**: offloading antenna $A$ onto neighbor $B$ without a global network perspective overloads $B$, propagating saturation across the cluster.
3. **Reactive Adjustments:** Adjusting antenna parameters only after congestion has manifested forces subscribers to endure dropped connections and packet latency before remediation occurs.

**WiseNet resolves this trilemma through proactive, predictive, and globally coordinated mathematical optimization.**

---

## 3. The Actuation Mechanism: Handover Physics, RSRP, and A3 Cell Individual Offsets

To shift traffic between base stations without hardware modifications, WiseNet exploits the standardized radio access control mechanism: the **3GPP Event A3 Handover**.

### 3.1 The 3GPP A3 Handover Event Condition
In LTE (3GPP TS 36.331) and 5G NR (3GPP TS 38.331), a User Equipment (UE / smartphone) continuously measures the **Reference Signal Received Power (RSRP)** from its serving cell $s$ and surrounding candidate neighboring cells $n$. 

An **Event A3** handover trigger is formally defined as:
$$\text{RSRP}_n + \text{Off}_{s,n} - \text{Hys} > \text{RSRP}_s + \text{Off}_s + \text{Off}_{s,\text{freq}}$$

Where:
- $\text{RSRP}_s, \text{RSRP}_n$: Received signal power from serving cell $s$ and neighbor $n$ (in dBm).
- $\text{Hys}$: Hysteresis margin to prevent rapid ping-pong handovers (typically $1.0\text{–}2.0 \text{ dB}$).
- $\text{Off}_{s,n}$: Cell Individual Offset (CIO / $\delta_{s,n}$), a software-configurable radio resource management (RRM) parameter.

### 3.2 Cell Individual Offset (CIO) as the Control Lever
The CIO ($\delta$) is a pure software parameter configured in the base station's digital baseband unit. By increasing $\delta_{s,n}$ by $+1.0 \text{ dB}$ to $+3.0 \text{ dB}$:
- The target neighbor $n$ appears artificially "better" to UEs situated in the border region between cell $s$ and cell $n$.
- Handover triggers occur earlier, gracefully transferring UEs near the cell edge to the neighbor.
- **Zero CapEx:** No antennas are tilted, no azimuths are changed, and no hardware is touched.
- **Zero User Disruption:** Transfers occur through standard soft/hard handovers with zero call interruption.

WiseNet operates by determining the optimal discrete vector $\boldsymbol{\delta}^*$ across all 756 radio cells simultaneously every 30 minutes.

---

## 4. Dataset & Spatial Discretization: The Milan Telecom Italia Benchmark

### 4.1 Benchmark Selection
Evaluating radio resource algorithms requires real-world, high-resolution human mobility and data consumption data. Because commercial operators strictly withhold live baseband traffic logs due to legal and competitive constraints, wireless communications literature relies on the **Telecom Italia Big Data Challenge (Milan Dataset)** as the gold-standard open benchmark.

### 4.2 Spatial Discretization ($32 \times 32$ Urban Core)
- **Geographic Grid:** The metropolitan area of Milan is partitioned into regular square tiles measuring $235 \text{ m} \times 235 \text{ m}$ ($\approx 0.0552 \text{ km}^2$ per tile).
- **Region of Interest:** WiseNet extracts the central, highest-density $32 \times 32$ block of tiles ($1,024$ contiguous geographic squares), covering approximately $56.5 \text{ km}^2$ of urban Milan (including the Duomo central commercial district, Porta Nuova business center, and dense residential corridors).
- **Temporal Resolution:** Raw 10-minute Call Detail Records (CDRs) encompassing Internet traffic, voice calls, and SMS are aggregated into **30-minute operational slots**, aligning precisely with carrier-grade SON optimization cycles.
- **Evaluation Period:** A continuous 48-hour longitudinal window spanning **November 12, 2013 (00:00) to November 13, 2013 (23:30)** ($96$ consecutive 30-minute intervals).

---

## 5. Disambiguation: Geographic Cells vs. Radio Cells

A frequent source of confusion in wireless data science is the conflation of geographic demand with radio infrastructure. WiseNet strictly formalizes and decouples these two concepts:

```
┌─────────────────────────────────────────────────────────────┐
│                 GEOGRAPHIC DEMAND DOMAIN                    │
│  1,024 Geographic Cells (Milan Grid: 235m x 235m tiles)     │
│  - Represents human ground-level traffic generation (MB)   │
│  - Exogenous, uncontrollable, and invariant to handovers    │
│  - Predicted by Machine Learning (XGBoost q80)              │
└──────────────────────────────┬──────────────────────────────┘
                               │ Spatial Transfer Fractions
                               ▼ (3GPP UMi Propagation)
┌─────────────────────────────────────────────────────────────┐
│                RADIO INFRASTRUCTURE DOMAIN                  │
│  756 Logical Radio Cells (126 Sites x 3 Sectors x 2 Carriers│
│  - 126 Physical Macro-Sites (Hexagonal grid, ISD = 750m)    │
│  - 378 Directional Sectors (120° azimuths: 0°, 120°, 240°)  │
│  - 756 Logical Carriers (F1 LTE 1.8GHz + F2 5G NR 3.5GHz)   │
│  - Controlled by Mathematical Optimization (Pyomo / MILP)   │
└─────────────────────────────────────────────────────────────┘
```

1. **Geographic Cell ($c \in \{1, \dots, 1024\}$):** A fixed $235\text{m} \times 235\text{m}$ square on the ground. It generates mobile demand based on human activity. It has no frequency, no antenna gain, and no hardware.
2. **Radio Cell ($r \in \{1, \dots, 756\}$):** A logical carrier operating on a specific directional sector of a physical antenna mast. Each physical site hosts 3 sectors, and each sector hosts 2 carrier layers (1.8 GHz LTE and 3.5 GHz 5G NR), yielding $126 \times 3 \times 2 = 756$ distinct radio entities, each with finite bandwidth and nominal processing capacity.

The **Spatial Simulator** bridges these domains by computing the exact proportion of traffic from each geographic cell $c$ absorbed by each radio cell $r$ as a function of the offset $\delta$.

---

## 6. 3GPP TR 38.901 Network Topology: Tri-Sector Macro Sites and Dual-Carrier Layering

To ensure scientific validity, antenna sites are not randomly scattered. WiseNet implements the standardized **3GPP TR 38.901 Urban Macro (UMa/UMi)** deployment specification:

```
                    Sector 0 (0° Azimuth - North)
                              ▲
                             / \
                            /   \
                           /  ●  \  <-- Macro Site Tower
                          /       \
                         /_________\
                        ◄           ►
      Sector 2 (240° Azimuth)    Sector 1 (120° Azimuth)
```

- **Physical Sites:** $126$ macro-cellular towers arranged in a regular hexagonal lattice with an **Inter-Site Distance (ISD) of $750 \text{ meters}$**.
- **Sectorization:** Each tower features 3 directional cross-polarized panel antennas spaced at $120^\circ$ azimuths ($\theta_0 = 0^\circ, \theta_1 = 120^\circ, \theta_2 = 240^\circ$), with a horizontal half-power beamwidth $\theta_{3\text{dB}} = 65^\circ$.
- **Dual-Carrier Layering:**
  - **Layer 1 ($F_1$ - 1.8 GHz LTE Band 3):** Anchor coverage layer. Characterized by low path loss, high penetration through building walls, and standard capacity.
  - **Layer 2 ($F_2$ - 3.5 GHz 5G NR Band n78):** High-throughput capacity layer. Characterized by higher bandwidth, higher propagation attenuation, and dense urban offloading capability.
- **Total Elementary Radio Cells:** $126 \text{ sites} \times 3 \text{ sectors} \times 2 \text{ carriers} = \mathbf{756 \text{ logical radio cells}}$.

---

## 7. Radio Propagation Modeling & The Offline Spatial Transfer Matrix Simulator

### 7.1 Electromagnetic Propagation Models
The received power $\text{RSRP}_{r}(p)$ at any geographic coordinate $p = (x, y)$ from radio cell $r = (\text{site } s, \text{sector } k, \text{freq } f)$ is governed by:

$$\text{RSRP}_r(p) = P_{\text{tx}, f} + G_k(\phi_{r, p}) - \text{PL}_f(d_{s, p})$$

Where:
1. **Transmit Power ($P_{\text{tx}}$):** Standardized base station EIRP ($46 \text{ dBm}$ for 1.8 GHz; $49 \text{ dBm}$ for 3.5 GHz).
2. **3GPP Horizontal Antenna Radiation Pattern ($G_k$):**
   $$A(\phi) = -\min \left[ 12 \left( \frac{\phi - \theta_k}{\theta_{3\text{dB}}} \right)^2, A_m \right]$$
   where $A_m = 30 \text{ dB}$ is the maximum front-to-back attenuation ratio.
3. **Path Loss Model ($\text{PL}_f$ - 3GPP TR 38.901 Dense Urban):**
   $$\text{PL}(d, f) = 28.0 + 22.0 \log_{10}(d_{[\text{m}]}) + 20.0 \log_{10}(f_{[\text{GHz}]})$$

### 7.2 The Offline Sub-Point Simulation ($400$ Evaluation Points per Tile)
To avoid boundary discretization artifacts, WiseNet does not model each $235\text{m} \times 235\text{m}$ tile as a single point. Instead, each tile is subdivided into a uniform internal grid of **$400$ sub-points ($20 \times 20$, spacing $\approx 11.75 \text{ meters}$)**.

For each sub-point $p_{c, i}$ ($i \in \{1, \dots, 400\}$) in geographic tile $c$:
1. The exact signal strength $\text{RSRP}_r(p_{c, i})$ is calculated for all 756 radio cells.
2. For each candidate A3 offset level $\delta \in \{0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0\} \text{ dB}$, the serving cell is determined:
   $$r^*(p_{c, i}, \delta) = \arg\max_{r} \left[ \text{RSRP}_r(p_{c, i}) + \delta_r \right]$$
3. The spatial transfer fraction $F(c, r, \delta)$ is computed as the empirical proportion:
   $$F(c, r, \delta) = \frac{1}{400} \sum_{i=1}^{400} \mathbf{1}_{\{ r^*(p_{c, i}, \delta) = r \}}$$

### 7.3 Mathematical Invariance and Mass Conservation
Because antenna locations, building geography, and propagation physics are static, **these transfer fractions are calculated strictly offline once and saved to disk**.

**Mathematical Mass Conservation (ADR-001):**
$$\forall c \in \{1, \dots, 1024\}, \quad \forall \delta \in \Delta: \quad \sum_{r=1}^{756} F(c, r, \delta) = 1.000000 \pm 10^{-6}$$

This strict physical property guarantees that no traffic is artificially created, lost, or duplicated during transfer.

---

## 8. Machine Learning Engine: Quantile Regression ($q_{80}$) and Asymmetric Loss (ADR-001)

### 8.1 The Feature Engineering Pipeline (31 Predictors)
For every 30-minute interval and each of the $1,024$ geographic cells, WiseNet computes 31 engineered features:
- **Temporal Autoregressive Lags:** Demand at $t-1$ (30 min), $t-2$ (60 min), $t-3$ (90 min), $t-48$ (same time yesterday), and $t-96$ (two days ago).
- **Rolling Statistics:** Rolling mean, standard deviation, min, and max over 3-hour, 6-hour, and 12-hour windows.
- **Spatial Neighborhood Lags:** Mean and max traffic across adjacent 8-neighbor tiles.
- **Calendar & Diurnal Encodings:** Sinusoidal encodings of hour-of-day ($\sin(2\pi h / 24), \cos(2\pi h / 24)$) and day-of-week indicators.

### 8.2 Asymmetric Risk and the Pinball Loss Function
In cellular network operation, prediction errors have fundamentally asymmetric consequences:
- **Underestimating Demand ($\hat{y} < y$):** Catastrophic. The optimization engine allocates insufficient capacity. Physical cells saturate, radio links drop, and subscribers experience severe QoS degradation.
- **Overestimating Demand ($\hat{y} > y$):** Benign. The optimization engine pre-allocates a slight excess of buffer capacity, offloading border UEs early with zero packet loss.

To align with this physical reality, WiseNet rejects standard Mean Squared Error (MSE) / Ordinary Least Squares (OLS) regression in favor of **Quantile Regression at the 80th percentile ($q_{80}$)** using the Pinball Loss:

$$\mathcal{L}_{q}(\hat{y}, y) = \max \left[ q (y - \hat{y}), (1 - q)(\hat{y} - y) \right]$$

Setting $q = 0.80$ penalizes under-prediction four times more severely than over-prediction, embedding an intrinsic engineering safety margin into every traffic forecast.

---

## 9. Causal Intelligence & Lucas Critique Immunity

A prevalent design flaw in naive machine learning applications for cellular networks is training prediction models on historical cell-level (antenna) traffic measurements.

### 9.1 The Lucas Critique Feedback Loop Failure
If an optimization algorithm shifts 200 GB from Antenna $A$ to Antenna $B$ at 14:00:
1. Recorded traffic on Antenna $A$ drops.
2. An ML model trained on antenna telemetry observes this decline and predicts that "demand at Antenna $A$ is dropping."
3. In subsequent cycles, the model forecasts even lower traffic, leading to under-provisioning.
4. The prediction model learns from its own historical control actions rather than underlying human behavior.

### 9.2 The WiseNet Structural Solution
WiseNet decouples **Human Ground Demand** from **Radio Assignment**:

$$\frac{\partial \, \text{Geographic\_Demand}(c, t)}{\partial \, \delta_{r}} \equiv 0$$

- The XGBoost model predicts exclusively at the level of the $235\text{m} \times 235\text{m}$ **geographic square**.
- Whether an individual's phone is served by Sector 1 on Tower 12 or Sector 2 on Tower 14, their physical location and data consumption remain identical.
- Ground demand is invariant to handover decisions, guaranteeing that the ML model remains causally clean, stable, and immune to feedback corruption over indefinite operational horizons.

---

## 10. Dynamic Coupling: Volumetric Transfer ($H$) Matrices

At the start of each 30-minute operational cycle $t$, the offline spatial fractions and the online ML forecasts are combined in real time:

$$H_{\text{offload}}(r, \delta, t) = \sum_{c=1}^{1024} \hat{y}_c(t) \cdot \max\left(0, F(c, r, 0) - F(c, r, \delta)\right)$$

$$H_{\text{receive}}(r, \delta, t) = \sum_{c=1}^{1024} \hat{y}_c(t) \cdot \max\left(0, F(c, r, \delta) - F(c, r, 0)\right)$$

Where $\hat{y}_c(t)$ is the predicted demand vector (in MB). Because this requires only sparse matrix-vector multiplication, computation takes **under 45 milliseconds** for all 756 radio cells.

---

## 11. The Optimization Engine: Global Mixed-Integer Linear Programming (MILP) with Pyomo & CBC

### 11.1 Mathematical Formulation
Let:
- $\mathcal{R} = \{1, \dots, 756\}$: Set of all radio cells.
- $\mathcal{K} = \{0, 1, \dots, 6\}$: Set of discrete offset levels corresponding to $\{0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0\} \text{ dB}$.
- $C_r$: Nominal capacity of radio cell $r$ (in MB per 30 minutes).
- $D_r$: Initial offered demand on radio cell $r$ under nominal baseline ($\delta=0$).
- $x_{r, k} \in \{0, 1\}$: Binary decision variable indicating whether offset level $k$ is selected for cell $r$.
- $u_r \ge 0$: Continuous auxiliary variable representing unsatisfied (congested) traffic on cell $r$.

**Objective Function:**
$$\min_{\mathbf{x}, \mathbf{u}} \quad \sum_{r \in \mathcal{R}} u_r + \lambda \sum_{r \in \mathcal{R}} \sum_{k \in \mathcal{K}} k \cdot x_{r, k}$$

*(where $\lambda = 10^{-4}$ is a small regularization parameter penalizing unnecessary offset changes).*

**Subject to Constraints:**

1. **Uniqueness Constraint:** Exactly one offset level chosen per radio cell:
   $$\sum_{k \in \mathcal{K}} x_{r, k} = 1, \quad \forall r \in \mathcal{R}$$

2. **Net Traffic Flow Conservation & Capacity Bounds:**
   The effective traffic $T_r$ on cell $r$ after redistribution is:
   $$T_r = D_r - \sum_{k \in \mathcal{K}} H_{\text{offload}}(r, k) \cdot x_{r, k} + \sum_{k \in \mathcal{K}} H_{\text{receive}}(r, k) \cdot x_{r, k}$$

3. **Unsatisfied Traffic Definition:**
   $$u_r \ge T_r - C_r, \quad \forall r \in \mathcal{R}$$
   $$u_r \ge 0, \quad \forall r \in \mathcal{R}$$

4. **Discrete Binary Bounds:**
   $$x_{r, k} \in \{0, 1\}, \quad \forall r \in \mathcal{R}, \; k \in \mathcal{K}$$

### 11.2 The Open-Source CBC Solver
The optimization problem is formulated in Python via **Pyomo 6.10** and solved using **Coin-OR CBC 2.10**, a high-performance open-source branch-and-cut solver.

---

## 12. Theoretical Superiority over Greedy Heuristics: Secondary Congestion (ADR-002)

To understand why exact mathematical optimization is required, consider a localized network cluster:

```
[Cell A (Saturated)] ──(Greedy Offload)──► [Cell B (Near Capacity)] ──(Overflow)──► [Cell C]
       120% Load                                  95% Load                           80% Load
                                            BECOMES 135% SATURATED!
```

- **The Greedy Failure Mode:** Antenna $A$ observes that it is at $120\%$ capacity. It greedily shifts $25\%$ of its load to its closest neighbor $B$. However, Antenna $B$ was already operating at $95\%$ capacity. Absorbing $A$'s overflow pushes $B$ into severe saturation ($120\%$). Antenna $B$ is now forced to offload onto $C$, creating a chain reaction of cascading secondary congestion.
- **The Global MILP Advantage:** The MILP considers the entire adjacency graph simultaneously. It recognizes that cell $B$ cannot absorb traffic, and instead routes boundary users from $A$ across multiple sectors or executes vertical inter-frequency offloads to the 3.5 GHz 5G layer.

---

## 13. Boundary Zone Protection: Physical Invariance Guarantees for End Users

A critical operational requirement for mobile network operators is that traffic optimization must **never degrade connectivity for users enjoying strong radio links**.

WiseNet provides a mathematical guarantee of user protection:

$$\text{RSRP}_{\text{serving}}(p) - \text{RSRP}_{\text{neighbor}}(p) > \delta_{\max} \implies \text{No Handover Possible}$$

- In dense urban macro deployments, a user located in the interior of a sector receives an RSRP from their serving antenna that is $15\text{–}30 \text{ dB}$ higher than any neighboring signal.
- The maximum CIO applied by WiseNet is strictly bounded: $\delta_{\max} = 3.0 \text{ dB}$.
- Therefore, users inside coverage cores are **physically immune** to handover triggers.
- Only users located in ambiguous edge zones (where signal differentials are within $\pm 3.0 \text{ dB}$) are eligible for re-assignment. For these border users, both candidate cells provide high-quality coverage, ensuring zero perceived service disruption.

---

## 14. Rigorous 48-Hour (Two-Day, 96-Slot) Empirical Simulation Results

### 14.1 Experimental Protocol & Rigor
To validate WiseNet under full operational conditions, a continuous **48-hour longitudinal simulation** was executed on the Milan urban core:
- **Duration:** 96 consecutive 30-minute intervals covering Tuesday, November 12, 2013 and Wednesday, November 13, 2013.
- **Scale:** 1,024 geographic demand cells, 756 logical radio cells.
- **Closed-Loop Execution:** Each cycle executes the complete pipeline: past observation $\to$ feature calculation $\to$ XGBoost $q_{80}$ forecast $\to$ $H$-matrix generation $\to$ Pyomo/CBC solve $\to$ real-traffic application and validation.
- **Reproducibility:** Seed fixed to 42, dataset SHA256 verified (`e47b4f3c...`), model SHA256 verified (`09d55a35...`).

### 14.2 Global 48-Hour Cumulative Performance

The following table reports the cumulative volumetric performance across the complete 48-hour evaluation:

| Metric | Real Demand | Static Network (Unmanaged) | Greedy Heuristic (ADR-002) | WiseNet MILP (This Work) | Clairvoyant Oracle (Theoretical Upper Bound) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Total Demand (MB)** | **$88,348,191.9$** | $88,348,191.9$ | $88,348,191.9$ | $88,348,191.9$ | $88,348,191.9$ |
| **Equivalent in Gigabytes (GB)** | **$86,277.5 \text{ GB}$** | $86,277.5 \text{ GB}$ | $86,277.5 \text{ GB}$ | $86,277.5 \text{ GB}$ | $86,277.5 \text{ GB}$ |
| **Unsatisfied Congested Traffic (MB)** | — | $10,618,332.1$ | $9,012,410.0$ | **$7,930,446.3$** | $7,790,077.7$ |
| **Unsatisfied Congested Traffic (GB)** | — | $10,369.5 \text{ GB}$ | $8,801.2 \text{ GB}$ | **$7,744.6 \text{ GB}$** | $7,607.5 \text{ GB}$ |
| **Net Traffic Saved from Saturation** | — | Baseline ($0 \text{ GB}$) | $1,568.3 \text{ GB}$ | **$2,624.9 \text{ GB}$ ($2.62 \text{ TB}$)** | $2,762.0 \text{ GB}$ |
| **Congestion Reduction Rate (%)** | — | $0.00\%$ | $15.12\%$ | **$25.31\%$** | **$26.64\%$** |
| **Improvement over Greedy Heuristic** | — | — | Baseline | **$+67.3\%$ more traffic saved** | — |
| **ML Efficiency vs. Clairvoyant Oracle**| — | — | $56.8\%$ | **$95.04\%$** | $100.00\%$ |
| **Mean Solve Time per 30-min Slot** | — | $0.00 \text{ s}$ | $0.04 \text{ s}$ | **$0.583 \text{ s}$** | $0.520 \text{ s}$ |

```
Congestion Volume Remaining across 48 Hours (Lower is Better):
Static (Unmanaged):  ████████████████████ 10,369.5 GB
Greedy Heuristic:    █████████████████     8,801.2 GB (-15.1%)
WiseNet MILP:        ██████████████        7,744.6 GB (-25.3%)  <-- 2.62 TERABYTES SAVED
Clairvoyant Oracle:  █████████████         7,607.5 GB (-26.6%)  <-- Theoretical Physics Limit
```

### 14.3 Diurnal Progression: Day 1 (J1) vs. Day 2 (J2) Analysis

The 48-hour longitudinal dataset captures distinct diurnal demand cycles across two consecutive business days:

| Temporal Phase | Typical Slot Hours | Base Static Congestion | WiseNet MILP Congestion | Net Gain (GB Saved) | Mean Solve Time |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Night Quiet Hours** | 00:00 – 06:00 | $\approx 0.8 \text{ GB}$ | $0.0 \text{ GB}$ | $0.8 \text{ GB}$ ($100\%$ resolved) | $0.38 \text{ s}$ |
| **Morning Commute Peak**| 07:30 – 09:30 | $128.6 \text{ GB}$ | $78.2 \text{ GB}$ | $50.4 \text{ GB}$ ($-39.2\%$) | $0.67 \text{ s}$ |
| **Midday Business Plateau**| 11:30 – 14:30 | $245.1 \text{ GB}$ | $179.8 \text{ GB}$ | $65.3 \text{ GB}$ ($-26.6\%$) | $0.72 \text{ s}$ |
| **Evening Rush Peak** | 18:00 – 20:30 | $312.4 \text{ GB}$ | $228.1 \text{ GB}$ | $84.3 \text{ GB}$ ($-27.0\%$) | $0.74 \text{ s}$ |

- **Day 1 (2013-11-12):** Initial surge occurs at Slot 14 (07:30). Static congestion spikes from $2.9 \text{ GB}$ to $196.3 \text{ GB}$ by 10:00. WiseNet reduces this peak to $152.6 \text{ GB}$, successfully saving $43.7 \text{ GB}$ during the morning rush alone.
- **Day 2 (2013-11-13):** Structural validation under repeated weekday loading. Day 2 exhibits identical stability, with WiseNet maintaining an average solve latency of $0.58 \text{ seconds}$ without memory leaks or drift degradation.

### 14.4 Theoretical Oracle Benchmark & Machine Learning Efficiency

To rigorously measure the penalty imposed by forecasting uncertainty, WiseNet benchmarked its predictive closed-loop against a **Clairvoyant Oracle**:
- The Oracle solver is given perfect, zero-error foreknowledge of future real demand ($y_{\text{real}}$).
- The Oracle achieves a theoretical maximum congestion reduction of $26.636\%$.
- WiseNet, operating under uncertainty with XGBoost $q_{80}$ predictions, achieves **$25.314\%$**.
- **Machine Learning Efficiency:**
  $$\text{Efficiency} = \frac{\text{Gain}_{\text{WiseNet}}}{\text{Gain}_{\text{Oracle}}} = \frac{2,687,885.8 \text{ MB}}{2,828,254.4 \text{ MB}} = \mathbf{95.04\%}$$
- **Total 48-Hour Regret:** Across 86.3 Terabytes of total throughput, the cumulative gap between WiseNet and the perfect Oracle was **only 137.1 GB** ($0.155\%$ of network traffic). This confirms the effectiveness of the $q_{80}$ quantile training strategy: by budgeting for peak load variations, the MILP rarely makes under-allocation errors.

### 14.5 Computational Speed & Real-Time Production Viability
- **Total Wall Time for 96 Complete Cycles:** $136.8 \text{ seconds}$.
- **Average MILP Solve Time:** $0.583 \text{ seconds}$ per cycle.
- **Peak Slot Solve Time:** $0.882 \text{ seconds}$ (Slot 14 during the morning transition).
- Standard O-RAN Non-RT RIC management loops operate on cycles of $15\text{–}30 \text{ minutes}$. An optimization engine requiring less than 1 second consumes less than $0.1\%$ of the available decision budget, confirming production readiness for carrier networks.

---

## 15. GSMA Open Gateway & CAMARA API Integration: The 6-Step Closed-Loop Pipeline

WiseNet links its algorithmic engine to live network interfaces through the **GSMA Open Gateway** initiative and standardized **CAMARA APIs**:

```
 ┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   THE 6-STEP CLOSED-LOOP PIPELINE                                      │
 └────────────────────────────────────────────────────────────────────────────────────────────────────────┘
    STEP 1: Live Crowd Telemetry (Vodafone Network Insights / Bing QuadKey API)
       │    - Queries live device density on geographic tiles
       ▼
    STEP 2: Machine Learning Forecasting (XGBoost q80 Asymmetric Predictor)
       │    - Quantile forecast (MB) per geographic cell for next 30 min
       ▼
    STEP 3: Global Network Optimization (Pyomo + Coin-OR CBC Solve in 0.58s)
       │    - Formulates MILP with mass conservation and capacity bounds
       ▼
    STEP 4: Residual Congestion Detection (Threshold Scanning)
       │    - Identifies cells where demand still exceeds capacity after optimal A3 offload
       ▼
    STEP 5: Geographic Emergency Fleet Verification (CAMARA Device Location API /verify)
       │    - Verifies whether critical MSISDNs (SAMU, Police) are physically inside congested cell
       ▼
    STEP 6: Surgical Priority Allocation (CAMARA Quality on Demand API /sessions)
            - Establishes dedicated 5QI=1 / 5QI=3 QoD bearer sessions for verified emergency devices
```

### Detailed Endpoint Specifications
1. **CAMARA Device Location Verification API (`/location-verification/v1/verify`):**
   - Eliminates blind resource allocation by verifying whether emergency responders are physically located within a congested radio sector's radius ($2.5 \text{ km}$).
   - Returns boolean confirmation (`verificationResult: TRUE`).
2. **CAMARA Quality on Demand API (`/qod/v0/sessions`):**
   - For confirmed emergency MSISDNs, creates high-priority bearer sessions (`QOS_E` / 5QI=1 for voice/telemetry, `QOS_L` / 5QI=3 for real-time video).
   - Enforces automated teardown via `DELETE /sessions/{sessionId}` when congestion subsides, preventing operator billing overruns.

---

## 16. The Telecom Digital Twin & Cross-Operator Portability: Reconciling Milan & Vodafone

A critical question addressed during development is:  
*How does one reconcile training an ML model on Telecom Italia Milan data while interfacing with Vodafone developer CAMARA sandboxes?*

Far from an inconsistency, this demonstrates the **Telecom Digital Twin** paradigm and the core value proposition of GSMA Open Gateway:

1. **City-Agnostic 3GPP Physics:** Maxwell's equations and 3GPP TR 38.901 propagation constants are universal. A dense urban fabric in Milan shares path loss exponents, beamwidths, and sectorization with Frankfurt, London, or Casablanca.
2. **GSMA Standardization:** CAMARA data schemas (`/location-verification`, `/qod/v0/sessions`) are operator-invariant by design. Code written for the Vodafone sandbox runs unmodified on Orange, Telefónica, or stc.
3. **Rigorous Data Fusion Formula:**
   $$\text{Offered Traffic } v_c(t) = \underbrace{\text{Footfall}(\text{QuadKey}, t)}_{\text{Vodafone Realtime Crowd API}} \times \underbrace{\text{Consumption\_Ratio}(c, t)}_{\text{Milan Behavioral Model (XGBoost)}}$$
   - **Milan Dataset** provides the endogenous human consumption profile (MB/user/hour).
   - **Vodafone Footfall** provides exogenous real-time crowd dynamics (protests, stadium arrivals).
   - This achieves true inter-operator portability and validation.

---

## 17. Resilience Engineering: The Circuit Breaker Architecture

To prevent software failures from destabilizing live carrier infrastructure, WiseNet implements an industrial **Circuit Breaker** design pattern:

```
                  ┌──────────────────────┐
                  │   CLOSED (Nominal)   │
                  │  Full MILP + CAMARA  │
                  └──────────┬───────────┘
                             │ Failures > Threshold (e.g. Solver timeout > 5s)
                             ▼
                  ┌──────────────────────┐
                  │   OPEN (Failsafe)    │
                  │ Fallback: Reset δ=0  │
                  └──────────┬───────────┘
                             │ After Cooldown Period (15 min)
                             ▼
                  ┌──────────────────────┐
                  │      HALF-OPEN       │
                  │ Test Single Sub-Grid │
                  └──────────────────────┘
```

- **CLOSED State (Normal):** Full closed-loop operation. Sub-second MILP solves and automated CAMARA QoD provisioning.
- **OPEN State (Failsafe):** If external API endpoints fail or solver execution exceeds safety bounds ($5.0 \text{ s}$), the circuit trips. Offsets revert to baseline ($\delta = 0$), preserving network stability and logging telemetry.
- **HALF-OPEN State (Recovery):** The system tests optimization on a restricted sub-grid before restoring full automated control.

---

## 18. MENA Regional Operational Scenarios

WiseNet includes dedicated scenario profiles tailored to Middle East and North Africa operational environments:

1. **Hajj & Umrah (Mina Mega-Density):** Simulates the world's most extreme device concentration. Pedestrian densities exceed $5 \text{ devices/m}^2$. The MILP maximizes intra-site offloading, while CAMARA QoD sessions protect emergency medical coordinators and crowd control dispatchers.
2. **Casablanca Urban Commute:** Models steep traffic gradients between the central business district (Boulevard d'Anfa) and outlying residential suburbs during morning and evening rush hours.
3. **AFCON Stadium Surge:** Simulates high-bandwidth demand spikes during football matches, followed by rapid dispersal across surrounding transit arteries.
4. **NEOM Smart City IoT Night Mode:** Evaluates low aggregate data volumes coupled with ultra-dense, mission-critical IoT telemetry requiring strict latency guarantees.

---

## 19. Flagship V2.0 Interactive Platform (Streamlit & PyDeck)

WiseNet V2.0 includes a production-grade operations console (`scripts/dashboard/app.py`):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              WiseNet V2.0 Flagship Console                             │
├───────────────────────────────┬────────────────────────────────────────────────────────┤
│ Controls & Telemetry          │ 3GPP Interactive Hexagonal Map                         │
│ • 24h/48h Auto-Play Slider    │ • 126 Macro-Sites (750m ISD)                           │
│ • Frequency Selector:         │ • 378 Directional Wedges (120° Azimuths)               │
│   F1 (1.8GHz) / F2 (3.5GHz)   │ • Real-time Side-by-Side View:                         │
│ • Circuit Breaker: CLOSED     │   [🔴 Unmanaged Saturated] vs [🟢 WiseNet Optimized]  │
│                               │ • Animated A3 Handover Vectors                         │
├───────────────────────────────┴────────────────────────────────────────────────────────┤
│ Decision Receipts & Safety Net Fleet Table                                             │
│ • Real-time XGBoost Prediction, MAE, and CBC Solve Time Receipt                        │
│ • ADR-002 Greedy Secondary Congestion Comparison (+GB saved)                           │
│ • CAMARA Fleet Table: SAMU Ambulance 01/02 (Location Verified + QoD Active)            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Hexagonal Tri-Sector Cartography:** Built on PyDeck, displaying all 126 macro sites, 378 directional sector wedges, and 756 radio cells with dynamic color-coding based on live utilization (Green < 75%, Amber 75–100%, Red > 100% saturation).
- **Multi-Carrier Spectral Layering:** Allows operators to toggle between 1.8 GHz LTE coverage (`F1_1800`), 3.5 GHz 5G NR capacity (`F2_3500`), or dual-carrier view (`ALL`) to observe vertical offloading.
- **Side-by-Side Comparative Mode:** Visualizes unmanaged saturated cells (red) alongside WiseNet-optimized cells (green) in real time, delivering a direct visual demonstration of the 25.3% global (up to 73.5% peak) congestion reduction.
- **Dynamic A3 Handover Vectors:** Displays animated spatial flow vectors indicating horizontal offload between adjacent physical sectors and vertical offload between LTE and 5G NR.
- **Transparent Decision Receipts:** Displays mathematical verification receipts for each cycle, including XGBoost forecast, MAE, CBC status, execution latency (< 0.6s), and mass conservation audits.
- **Greedy Secondary Congestion Benchmark (ADR-002):** Real-time quantitative display of secondary congestion avoided (+GB saved vs. myopic heuristics).
- **CAMARA Fleet Table & Safety Net Badges:** Real-time tracking of emergency fleet vehicles (SAMU, Police, Civil Defense) with verified in-cell physical location and active `QOS_E` / `QOS_L` priority bearer sessions.
- **Circuit Breaker Status Indicator:** Live visual badge (`CLOSED` / `HALF-OPEN` / `OPEN`) confirming fault-tolerant resilience.
- **Temporal 24-Hour Slider & Auto-Play:** Allows continuous play-through across all 48 half-hour slots to simulate live network operations throughout an entire diurnal cycle.

---

## 20. O-RAN Standardization & Production Deployment Roadmap

WiseNet is designed for direct integration into **Open RAN (O-RAN) Alliance** standardized architectures:

```
┌─────────────────────────────────────────────────────────────┐
│              Non-RT RIC (SMO / Management Plane)            │
│  • WiseNet rApp                                             │
│  • Long-term prediction (XGBoost q80)                       │
│  • CAMARA Open Gateway API Orchestrator                     │
│  • Time scale: > 1 second (WiseNet: 0.58s)                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ A1 Interface (Policies / CIO Intents)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Near-RT RIC (Distributed Control Plane)         │
│  • xApp: Real-time Radio Resource Management                │
│  • Enforcement of A3 CIO (δ) across E2 Nodes (gNodeB / eNB) │
│  • Time scale: 10ms – 1s                                    │
└─────────────────────────────────────────────────────────────┘
```

- **rApp Deployment:** WiseNet functions as an O-RAN **rApp** hosted on the Non-Real-Time RAN Intelligent Controller (Non-RT RIC).
- **A1 Interface Compliance:** The computed optimal CIO vectors $\boldsymbol{\delta}^*$ are communicated to the Near-RT RIC as declarative optimization policies over the standardized **A1 interface**.
- **Actuation:** Base station eNodeBs and gNodeBs execute the offset adjustments natively, ensuring compatibility with multi-vendor Open RAN deployments.

---

## 21. Open-Source Stack, Verification, and Reproducibility

WiseNet uses an entirely open-source software stack, avoiding proprietary solver licenses (such as Gurobi or CPLEX) that limit academic reproducibility and commercial scalability:
- **Language & Data Processing:** Python 3.11 / 3.12, Polars, NumPy, SciPy.
- **Machine Learning:** XGBoost (Quantile Objective, $q=0.80$).
- **Mathematical Modeling & Optimization:** Pyomo 6.10, Coin-OR CBC 2.10.
- **Visualization & UI:** Streamlit, PyDeck, Plotly.
- **API Standards:** GSMA Open Gateway CAMARA v1.1.0 (Location Verification, QoD, Footfall).

### Cross-Platform Local Execution Guide (Windows, Mac, Linux)

To evaluate and demonstrate the platform independently on any machine (even across differing host Python versions):

#### 1. Clone the repository and select the production branch
```bash
git clone https://github.com/samya818/spatial-son-milp.git
cd spatial-son-milp
git checkout feature/final-interface
```

#### 2. Create and activate an isolated virtual environment
An isolated virtual environment ensures zero package version conflicts regardless of the system's global Python environment:
- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
  *(If script execution is restricted: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*
- **Windows (Command Prompt CMD):**
  ```cmd
  python -m venv .venv
  .\.venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

#### 3. Upgrade pip and install dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pydeck pandas
```
> *Note on Python 3.12+: `requirements.txt` is structured to automatically bypass non-essential C++ compiled forecasting libraries (`prophet`, `neuralforecast`) on newer Python versions, ensuring clean and instantaneous installation.*

#### 4. Execute the 48-Hour Continuous Empirical Simulation
```bash
# Run the rigorous 96-slot benchmark (generates summary JSON, CSVs, and audit figures)
python scripts/simulation_48h_rigorous.py
```

#### 5. Launch the V2.0 Flagship Operations Console
- **Windows (PowerShell):**
  ```powershell
  $env:PYTHONPATH="."
  streamlit run scripts/dashboard/app.py
  ```
- **Windows (CMD):**
  ```cmd
  set PYTHONPATH=.
  streamlit run scripts/dashboard/app.py
  ```
- **macOS / Linux:**
  ```bash
  PYTHONPATH=. streamlit run scripts/dashboard/app.py
  ```
The console automatically opens in your default browser at: **`http://localhost:8501`**.

---

## 22. Conclusion

WiseNet demonstrates that **mathematical intelligence and standardized APIs can resolve wireless network congestion without capital expenditure**.

By unifying:
1. **3GPP propagation physics** across dual-carrier tri-sector topologies,
2. **Asymmetric machine learning demand forecasting** with causal Lucas-immunity,
3. **Exact global Mixed-Integer Linear Programming** executing in sub-second time, and
4. **GSMA Open Gateway CAMARA APIs** for verified mission-critical prioritization,

WiseNet achieves a measured **$25.31\%$ reduction in network congestion** over 48 continuous hours of real-world urban data, saving **$2.62 \text{ Terabytes}$** of mobile traffic from dropped packets and saturation while capturing **$95.04\%$** of the theoretical maximum performance of a clairvoyant Oracle.

WiseNet provides mobile network operators in the MENA region and globally with a practical, scientifically grounded, and standards-compliant framework for autonomous self-organizing networks.

---

*WiseNet V2.0 — MENA Ignite Hackathon 2026 (GSMA & Nokia)*  
*Authors: Samya Loukili & Fatima Zahra Azzi*  
*Dataset: Telecom Italia Big Data Challenge (Milan Metropolitan Grid)*  
*Standards: 3GPP TR 38.901, TS 36.331, TS 38.331 | GSMA Open Gateway CAMARA API v1.1.0*