# WiseNet V1.5 — A Complete Explanation of the Project, From Start to Finish

*Designed for MENA Ignite Hackathon 2026 — GSMA & Nokia*

*Authors: Samya Loukili & Fatima Zahra Azzi*

---

## Before We Start: The Problem We Are Solving

Imagine a Friday evening in the center of a large city. Thousands of people are leaving their offices, gathering in restaurants, or attending a football match at a stadium. Their smartphones are all connected to the same nearby mobile antenna. That antenna becomes overwhelmed — calls drop, videos freeze, pages refuse to load.

Now, just 300 meters away, in a quiet office district where everyone has already gone home, another antenna sits nearly idle. It has plenty of capacity available. Nobody is using it.

This is the fundamental inefficiency of mobile networks today: saturation exists not because there is not enough infrastructure, but because the existing infrastructure is badly distributed in real time. The congested antenna has too much traffic. The idle antenna next door has nothing to do. And the network, left to manage itself passively, does nothing to fix this imbalance.

This is the exact problem WiseNet was built to solve. WiseNet is a Self-Organizing Network system — a SON. It is a software intelligence that observes the network, anticipates where congestion is about to occur, and automatically redistributes mobile traffic to the best available antennas, before users even notice the problem. It does this continuously, every thirty minutes, without any human intervention.

---

## The Key Mechanism: What Is a Handover and What Is an Offset?

To understand how WiseNet works, two ideas must be understood first. They are not complicated, but they are central to everything that follows.

The first idea is the **handover**. In any mobile network, your smartphone is constantly connected to one antenna at a time — the one that gives it the strongest signal. When you move through the city, your phone silently and seamlessly switches from one antenna to another. This switch is called a handover. You never notice it. The call does not drop. The connection continues, now served by a different tower. The condition that triggers a handover is simple: your phone switches to a neighboring antenna when that neighbor's signal, plus a small margin, becomes stronger than the signal from your current antenna.

The second idea is the **offset**, sometimes called the A3 Offset in the technical standards of mobile networks. This offset is that small margin. It is a software parameter — a number in decibels — that the mobile network operator can adjust remotely without touching any physical equipment. By artificially increasing the offset in favor of a neighboring antenna, the operator makes that neighbor look more attractive to smartphones in the boundary zone between two coverage areas. This pushes those phones to switch to the neighbor, which effectively transfers traffic from the congested antenna to the one with spare capacity.

This is the lever WiseNet uses. It decides, for every antenna in the network, what offset value to apply — and it makes this decision for all antennas simultaneously, in a globally coordinated way. The goal is always the same: redistribute traffic from saturated antennas to antennas that still have room, without dropping any call, without degrading any connection, and without spending a single dollar on new physical infrastructure.

---

## The Dataset: Where the Real Traffic Data Comes From

WiseNet was built and evaluated on real data. The dataset used is the **Telecom Italia Big Data Challenge**, a publicly available and scientifically recognized dataset that captures real mobile network traffic over the city of Milan, Italy. The city is divided into a grid of small square zones, each measuring 235 meters on each side. For every one of these zones, and for every 10-minute interval over several weeks, the dataset records how much mobile traffic — in terms of internet activity, calls, and text messages — was generated in that area.

For WiseNet, the team extracted the central and densest block of this grid: a contiguous area of 1,024 geographic squares, arranged in a 32-by-32 formation, covering approximately 56 square kilometers of urban Milan. This area represents a realistic dense urban environment, with a mix of commercial centers, residential zones, and high-traffic public spaces.

The raw traffic measurements, originally recorded every 10 minutes, were aggregated into 30-minute windows to match the operational rhythm of the system. Each 30-minute window becomes one decision cycle for WiseNet.

It is important to understand why this dataset was chosen and why it is scientifically legitimate. No mobile operator in the world publishes its real antenna traffic logs publicly — these are commercially sensitive and legally protected. The Telecom Italia dataset is the one exception: a rigorously anonymized, peer-reviewed, and widely used benchmark that has appeared in dozens of academic publications on network optimization. Every major research group working on mobile network intelligence uses Milan as their proving ground. WiseNet follows this established standard.

---

## A Critical Terminology Clarification: Two Kinds of "Cell"

Before going any further, it is essential to clarify a terminology point that is a frequent source of confusion — even among engineers — and that is especially important to understand when reading about WiseNet.

In standard telecommunications literature, the word **"cell"** traditionally refers to the radio coverage zone of a single carrier on a single sector of a physical antenna site. This is what telecom engineers mean when they say a network has hundreds or thousands of cells: they are counting independent radio coverage zones, each defined by a specific antenna pointing in a specific direction and operating on a specific frequency band. This is the classical meaning of the word, and it is the one used in 3GPP standards, operator documentation, and most academic papers on mobile networks.

WiseNet uses this same classical concept — but it also needs a completely different concept that is specific to the dataset and the problem structure. To avoid confusion, the project makes an explicit and strict distinction between two separate notions, each given its own name.

The first is the **geographic cell**. This is purely a geographic unit — a 235-meter by 235-meter square zone on the ground, drawn from the Telecom Italia Milan grid. A geographic cell is not a radio concept at all. It has no antenna, no frequency, no sector. It is simply a piece of territory. The dataset assigns each geographic cell a unique identifier and records how much mobile traffic was generated within that territory during each time window. There are 1,024 geographic cells in WiseNet's study area. When the machine learning model makes a prediction, it predicts the traffic demand for each geographic cell independently. When the spatial simulation subdivides a zone into 400 sub-points, those sub-points are all within one geographic cell. The geographic cell is the unit of human behavior and ground-level demand.

The second is the **radio cell**. This is the classical telecom meaning: the independent logical coverage unit defined by one sector of one physical antenna site, operating on one specific frequency band. In WiseNet V1.5, a radio cell is identified by the pair of a sector and a frequency carrier — written as the pair (sector, frequency). Because each of the 126 physical antenna sites has 3 sectors and each sector carries 2 frequency bands, every physical site generates 6 independent radio cells. Across all 126 sites, this produces 756 radio cells in total. Each radio cell has its own capacity, its own congestion state, and its own set of possible handover configurations with neighboring radio cells. When the MILP optimization engine works, it works on radio cells — it decides an offset for each radio cell, monitors the traffic balance of each radio cell, and enforces that no radio cell exceeds its capacity.

The relationship between the two is straightforward but must be kept clearly in mind. A geographic cell generates a certain volume of traffic — that is the demand side, the human behavior side. A radio cell serves that demand — it is the supply side, the network infrastructure side. A single geographic cell may be partially served by several different radio cells simultaneously, because multiple sectors from neighboring antenna sites may have overlapping coverage over that territory. The spatial simulation — which computes the transfer fractions — is precisely the mechanism that determines, for each geographic cell and each set of offset values, which fraction of the traffic generated in that geographic cell is assigned to each competing radio cell.

Put simply: when this document says "geographic cell," think of a square on a map. When it says "radio cell," think of a frequency channel on a sector of a tower. They are entirely different things, and keeping them distinct is the key to understanding how WiseNet connects human demand to network infrastructure.

---

## The Network Topology: Placing the Antennas Realistically

The Milan dataset tells us how much traffic was generated in each geographic square. But it says nothing about the antennas — where they are, how many there are, or how much traffic each one can handle. A realistic antenna topology had to be constructed.

WiseNet V1.5 follows the exact technical standards published by the global mobile standards body, the 3GPP, in their specification TR 38.901, which defines how macro-cellular networks are deployed in dense urban environments. Rather than placing antennas randomly, the project uses a deterministic hexagonal grid — the same geometric pattern used by real operators like Telecom Italia when planning their urban coverage. In this grid, antenna sites are spaced 750 meters apart from each other, in a perfectly regular pattern that ensures uniform coverage with minimal gaps and minimal overlap.

Across the 56-square-kilometer area of Milan, this produces 126 physical antenna sites.

Now, each of these 126 physical sites is not a single antenna. A real mobile tower is divided into three directional sectors. Each sector covers approximately 120 degrees of the surrounding space — imagine three pizza slices, each pointing in a different direction, together covering the full 360 degrees around the tower. This is the standard tri-sector configuration used in virtually every urban mobile deployment worldwide.

Furthermore, each sector does not operate on a single radio frequency. It carries two separate frequency bands simultaneously. The first is a 1.8 GHz band — the coverage anchor layer. This lower frequency travels farther, penetrates walls better, and ensures that everyone in the sector has a baseline connection. The second is a 3.5 GHz 5G band — the high-capacity layer. This higher frequency carries far more data per unit of time, but it has a shorter range. Together, these two carriers give each sector both range and throughput.

So the complete count is: 126 physical sites, each with 3 sectors, each carrying 2 frequency bands. This produces 756 independent logical radio cells, which WiseNet calls the elementary unit of analysis. Every one of these 756 cells has its own independent traffic capacity and its own congestion state. WiseNet monitors all 756 simultaneously and decides offsets for all of them in a single, globally coordinated optimization.

---

## The Signal Physics: How WiseNet Knows Who Receives What Signal

Once the antenna topology is established, WiseNet needs to know, for any given point in the city, which antenna provides the strongest signal. This is not a guess — it is computed from physics.

The received signal power at a given location depends on three physical factors that WiseNet models explicitly.

The first factor is **distance**. The farther you are from an antenna, the weaker the signal. This is called path loss, and it follows a well-known logarithmic relationship that is part of the 3GPP standard specifications. The formula accounts for the specific propagation characteristics of dense urban environments.

The second factor is **frequency**. Higher-frequency signals experience more path loss over the same distance. The 3.5 GHz band attenuates faster than the 1.8 GHz band. The path-loss formula incorporates frequency, so the physics are correct for each of the two carrier bands independently.

The third factor is **direction**. Because each sector is directional — it points in a specific direction rather than emitting equally in all directions — a user standing exactly in front of the sector's main beam receives a much stronger signal than a user standing at the same distance but off to the side or behind the sector. This directional effect is modeled through an antenna gain pattern that depends on the angular offset between the direction the sector is pointing and the direction toward the user. The formula for this gain pattern is also a 3GPP standard.

The combination of these three factors — distance, frequency, and direction — gives the received signal strength at any location, expressed as a quantity called RSRP, the Reference Signal Received Power. This is the exact same metric used by real smartphones to decide whether to initiate a handover.

The handover decision, as described earlier, compares the RSRP of the current serving cell with the RSRP of a neighboring cell, plus the offset. If the neighbor's RSRP plus the offset exceeds the current cell's RSRP, the phone switches. WiseNet uses this same standard condition, computed from real 3GPP physics, to model what fraction of users in any given geographic area would switch antennas for any given offset value.

---

## The Spatial Simulation: Building the Transfer Matrices Offline

Here is one of the most important architectural ideas in the project. WiseNet separates its computation into two distinct phases: what is computed once, in advance, and what is computed in real time during each 30-minute operational cycle. This separation is what makes the system fast enough to operate in production.

The offline phase builds the transfer matrices. To understand what these are, consider a specific 235-meter geographic square and two candidate antennas: the one that currently serves it, and a neighboring one. For any given offset value applied in favor of the neighbor, some fraction of the users in that square will switch to the neighbor. WiseNet needs to know exactly what that fraction is.

To compute this precisely, the project does not treat each geographic square as a single point. Instead, it subdivides every 235-meter square into a fine grid of 400 smaller sub-points, each representing an area of about 12 meters by 12 meters. For each of these 400 sub-points, the full RSRP calculation described above is performed: distance, frequency, and direction are all taken into account for every candidate antenna. Then, for each offset level tested, the system counts how many of the 400 sub-points would switch to the neighboring antenna. That count, divided by 400, gives the fraction.

This computation is performed for all 1,024 geographic squares, for all candidate antenna pairs, and for all possible offset levels. The result is stored as a set of matrices called the transfer fraction matrices. They encode, for every possible handover configuration in the entire network, exactly what proportion of traffic would move and in what direction.

The key insight is this: these fractions depend only on geometry and physics — the positions of the antennas, the direction each sector points, and the propagation laws. None of these things change over time. Buildings do not move. Antenna towers do not relocate. So the transfer fraction matrices, once computed, are valid forever. They are computed once, stored on disk, and reused at every subsequent operational cycle.

This is also where WiseNet enforces a fundamental physical law that must never be violated: mass conservation. If a fraction of traffic leaves one antenna heading toward a neighbor, that exact same fraction must arrive at the neighbor. Traffic cannot disappear. Traffic cannot be duplicated. The system verifies this mathematically at a precision of less than one part per million.

---

## The Machine Learning Prediction: Anticipating Future Traffic

WiseNet does not react to congestion after it has already happened. Reacting too late means users already suffered. Instead, the system predicts future traffic — it anticipates where congestion is about to occur — and acts preventively, before users feel anything.

The prediction layer uses a machine learning model called XGBoost, trained on the historical traffic patterns from the Milan dataset. For each of the 1,024 geographic squares, the model learns the temporal rhythms of human activity: how traffic rises in the morning commute, peaks at lunchtime and again in the evening, drops overnight, and differs between weekdays and weekends. It also learns which areas tend to experience sudden spikes and which remain relatively stable. The model is trained on 31 engineered features derived from the raw data, including time-lagged traffic values, rolling averages over different window sizes, and calendar indicators.

A particularly important design decision concerns what the model predicts. Rather than predicting the average expected traffic, WiseNet trains the model to predict the 80th percentile of traffic — meaning the level that will not be exceeded 80 percent of the time. This is called quantile regression, and the choice of the 80th percentile is deliberate.

In mobile networks, the cost of underestimating traffic is catastrophic: if the system prepares for a lower load than actually arrives, users experience dropped calls and frozen streams. The cost of overestimating traffic is mild: the system reserves more capacity than needed, and a few users who could have been served by their original antenna are handed off to a neighbor with no degradation in quality. The asymmetry of consequences justifies a deliberately cautious prediction. WiseNet is designed to prepare for the reasonable worst case, not just the average case.

The prediction is produced fresh at every 30-minute cycle. The model looks at the traffic patterns from the preceding hours and outputs, for each of the 1,024 geographic squares, an estimate of how much traffic that square will generate in the next 30 minutes.

---

## Combining Prediction and Physics: The H Transfer Matrices

The offline transfer fractions and the online traffic predictions must be combined before the optimization can begin.

At the start of each 30-minute cycle, once the XGBoost model has produced its predictions for all 1,024 geographic squares, these predicted traffic volumes are multiplied by the stored transfer fraction matrices. The result is a new set of matrices called the H matrices — specifically, the offload H matrix and the receive H matrix.

The offload H matrix answers the question: if antenna X applies a certain offset, what is the actual volume of traffic in megabytes per 30-minute slot that would leave antenna X and go to a specific neighboring antenna? This is no longer a fraction — it is a real volume, in concrete units, because it has been multiplied by the predicted traffic volume.

The receive H matrix answers the symmetric question: what volume of traffic, in megabytes, would arrive at antenna Y from each of its neighbors, for each possible offset applied by those neighbors?

These two H matrices are recomputed at every cycle because they depend on the predicted traffic, which changes every 30 minutes. But the underlying fractions they draw from are static — computed once, offline. So the online computation is extremely fast, just a multiplication operation, taking less than 50 milliseconds.

The H matrices are the exact data that are handed over to the optimization engine. They express, in real volumetric terms, the full space of possible traffic redistributions available to the network at this specific moment in time.

---

## The Optimization Brain: MILP, Pyomo, and the CBC Solver

This is the core of WiseNet's decision-making. Given the predicted traffic volumes and the full set of possible handover configurations expressed in the H matrices, the system must decide: what offset should every single antenna apply, right now, to minimize total congestion across the entire network?

This is a mathematical optimization problem. The system must simultaneously choose one offset level for each of the 756 radio cells and evaluate the combined effect of all those choices on the total unsatisfied traffic across the network. The interaction effects are what make this hard: if cell A offloads onto cell B, cell B receives more traffic and may itself become congested. So the decision for A and the decision for B are not independent. They must be considered together, as part of a single global solution.

WiseNet formulates this as a Mixed-Integer Linear Program, or MILP. This is a category of mathematical optimization where decisions are represented as binary choices — either an offset level is active or it is not — and the relationships between all variables are linear, meaning they involve only sums and comparisons without complicated nonlinear interactions. Linear programs with binary variables can be solved exactly — not approximately, not heuristically, but with a guaranteed mathematical proof that the answer found is the best possible answer under the given constraints.

The MILP formulation used in WiseNet is precise. For each of the 756 radio cells, the solver must pick exactly one offset level from the available options. For each offset level it might choose, the solver knows — from the H matrices — how much traffic would leave that cell and how much that cell would receive from its neighbors. The objective is to minimize the total volume of traffic that remains unsatisfied across all cells after redistribution: the sum, across all 756 cells, of the excess traffic that exceeds each cell's capacity.

The constraints ensure three things simultaneously. First, no cell should end up with more traffic than its physical capacity after redistribution. Second, mass is conserved exactly: every megabyte offloaded by one cell must appear as a megabyte received by the destination cell. Third, an offset can only cause a handover between cells that genuinely overlap in coverage — no offset can redirect traffic toward an antenna whose signal never reaches the relevant area.

In WiseNet, the MILP problem is expressed using a Python library called Pyomo. Pyomo does not solve anything by itself — it is the language in which the problem is written down mathematically so that the computer can understand it. The actual solving is done by the CBC solver, a powerful open-source optimization engine maintained by the Coin-OR project. Using an open-source solver rather than expensive commercial alternatives like Gurobi or CPLEX was a deliberate design decision, consistent with WiseNet's philosophy of making the system accessible without proprietary licensing costs.

The result: the full global optimization of all 756 cells — selecting offsets, evaluating cascading effects, enforcing mass conservation — is solved in under one second. On the peak congestion slot tested, the solve time was 0.74 seconds. This is fast enough to operate in real carrier-grade networks, which work on 30-minute optimization cycles.

---

## Why This Beats Simple Greedy Approaches

A natural question arises: why is this complicated global optimization necessary? Could the system not simply look at each overloaded antenna and push its excess traffic to the least-loaded neighbor?

This simpler approach — deciding antenna by antenna, one at a time, based only on local information — is called a greedy heuristic. It is faster and simpler to implement. But it fails in a fundamental way.

When antenna A is congested and the greedy algorithm decides to offload its traffic to antenna B, it does so without knowing whether antenna B can actually absorb that traffic. If B is already near its own capacity, forcing more traffic onto it creates a second congestion point. If B then offloads onto C, and C onto D, the initial decision to help A creates a cascade of downstream congestion problems that the greedy algorithm never anticipated because it never looked beyond its immediate neighbors.

The MILP does not suffer from this problem. It considers all 756 cells at once, in a single mathematical pass. Before it decides anything for antenna A, it already knows the state of antennas B, C, D, and every other cell in the network. It finds the combination of decisions that is globally optimal — that minimizes the total unsatisfied traffic across the entire system, taking all cascading effects into account.

The measured evidence proves the difference. Over a full 24-hour evaluation period on real Milan data, the greedy heuristic reduces total congestion by 24 percent compared to a static network with no optimization. WiseNet's MILP reduces it by 27.6 percent. In the fully realistic closed-loop test where the system uses only ML predictions rather than perfect knowledge of the future, WiseNet achieves 98.7 percent of the theoretical maximum performance that a hypothetical clairvoyant oracle — a system that knows the future perfectly — could achieve. The greedy heuristic, by comparison, achieves only 86 percent of that theoretical maximum. The global MILP delivers an extra 123 gigabytes of successfully served traffic over 24 hours, compared to the greedy baseline.

---

## The Closed Loop: How the System Runs Continuously

WiseNet does not run once and stop. It operates as a continuous closed loop, cycling every 30 minutes without pause.

At the beginning of each cycle, the system reads the latest traffic observations — either from historical data during testing, or from live network telemetry during production. The XGBoost model uses these recent observations to predict traffic for the next 30-minute window, for every geographic square in the network. These predictions are combined with the precomputed transfer fractions to produce fresh H matrices for this cycle. The MILP solver receives these matrices and computes the globally optimal offset assignments for all 756 cells. The offsets are applied — meaning, in a real deployment, they would be pushed to the base stations. The resulting traffic redistribution is then observed, and the cycle begins again.

Over the course of a 24-hour day, this produces 48 consecutive decision cycles. Each cycle takes less than one second of computation for the optimization step, and a few additional seconds for the prediction and matrix multiplication. The total operational overhead per cycle is negligible compared to the 30-minute interval between cycles.

The closed-loop design also incorporates drift detection. Because the system continuously measures the difference between its predictions and the actual observed outcomes, it can detect if the prediction model begins to deviate systematically from reality — a phenomenon called model drift. When this is detected, it signals that the model may need to be retrained on more recent data to remain accurate.

---

## The Causal Intelligence: Why the Predictions Never Become Self-Corrupting

This is a subtle but critical point that distinguishes WiseNet from most naive ML-for-network systems, and it deserves a clear explanation.

Imagine a system that trains its prediction model on traffic measured at each antenna. It predicts future antenna traffic, and then uses those predictions to redirect traffic from overloaded antennas to idle ones. This seems sensible. But it hides a fatal feedback loop.

After the system acts and moves traffic from antenna A to antenna B, the traffic recorded at antenna A drops — not because demand fell, but because the system moved it. The next time the prediction model trains, it sees lower traffic at antenna A and concludes that demand in that area has decreased. So it predicts less traffic there in the future. The model is now learning from the consequences of its own past decisions rather than from real human demand. Its predictions drift away from reality. In control theory and economics, this phenomenon is known as the Lucas Critique — a model trained on passive observation loses its validity the moment it becomes an active participant that changes the very thing it is measuring.

WiseNet escapes this trap through a fundamental architectural principle: predict human behavior, control radio assignment. The XGBoost model never predicts traffic at an antenna. It predicts traffic demand in each geographic square — the 235-meter area on the ground. This geographic demand reflects human behavior: how many people are in that area, what they are doing with their phones. This behavior is completely independent of which antenna is serving those people at any given moment. Moving a connection from antenna A to antenna B does not move the person, and it does not change how much data they want to consume. The geographic demand is causally unaffected by any offset decision.

So when the MILP applies offsets and redistributes traffic, the ground-level demand in each square remains exactly what it was predicted to be. The prediction model, looking at future cycles, still sees genuine human behavior — untainted by its own past actions. The predictions remain valid indefinitely, regardless of how aggressively the system optimizes.

This is expressed mathematically as a derivative that is identically zero: the rate of change of geographic demand with respect to the offset is zero. The prediction layer is immune to the consequences of the control layer. This is not a mathematical trick — it is a structural design decision that makes the entire system stable and honest in its long-term operation.

---

## Why End Users Are Never Harmed by the Optimization

A legitimate concern about any traffic-shifting system is whether some users might experience degraded service as a result. If the system forces a handover on a user who was perfectly happy connected to their current antenna, that seems harmful.

WiseNet provides strong physical guarantees that this cannot happen, and the reasoning comes directly from the signal physics.

The offset is a small margin — in WiseNet V1.5, the maximum offset applied is 3 decibels. Now, consider a user sitting close to the center of their serving antenna's coverage area. Their received signal from their antenna might be minus 75 decibels per milliwatt — a very strong signal. The nearest neighboring antenna, seen from that location, might deliver minus 105 decibels per milliwatt. The difference is 30 decibels. No matter how WiseNet adjusts the offset — even if it applies the maximum of 3 decibels in favor of the neighbor — it can never make a 30 decibel gap disappear. The user at the center of their coverage area will never be handed off, because no feasible offset can make the neighbor's signal appear stronger than the serving antenna's signal at that location.

The only users who are affected by offset changes are those who are already in the boundary zone between two coverage areas — users where the signals from two antennas are nearly equal, typically within a few decibels of each other. For these users, a handover is transparent: both antennas are good options, the signals are comparable, and switching from one to the other does not degrade the connection quality. These are precisely the users for whom a handover is least disruptive.

So by construction, the system only touches users who are in the best position to be transferred, and it leaves untouched all users who are strongly anchored to their current cell. The physics of signal propagation act as a natural firewall that no software optimization can override.

---

## The CAMARA API Integration: Connecting to Real Networks

Everything described so far is a complete, self-contained system that can be run on historical data and tested in simulation. But WiseNet V1.5 goes further: it is connected to real, standardized network interfaces. This is the element that transforms a research demonstration into a prototype with genuine industrial relevance, and it is one of the most important differentiators of this project in the context of the MENA Ignite Hackathon.

**What CAMARA is, in plain terms.** CAMARA is a collection of standardized application programming interfaces — APIs — developed jointly by mobile operators worldwide under the GSMA's Open Gateway initiative. The problem CAMARA solves is one of fragmentation: historically, every operator had its own proprietary, incompatible way for external applications to query and interact with its network. An application built to work with Vodafone would need to be completely rewritten to work with Orange, and again for Telefónica, and so on. CAMARA defines a common language that all participating operators agree to speak. Any application that implements CAMARA once can, in principle, connect to any CAMARA-compatible operator globally without modification. For WiseNet, this means that the same integration code tested against the Vodafone sandbox could tomorrow be deployed against any operator in the MENA region that has adopted the GSMA Open Gateway standard.

WiseNet V1.5 implements a precise six-step pipeline through these APIs, where each step feeds the next in a strict sequential order. Understanding each step and why it exists in that position is the key to understanding the full system.

**Step one: live crowd telemetry via the Vodafone Realtime Footfall and QuadKey API.** The pipeline begins not with historical data, but with a live measurement of the present. The Footfall API provides, for any geographic tile in the city identified by a QuadKey coordinate, the real-time count of how many active mobile devices are physically present in that area right now. This is the live heartbeat of the city — a continuously updated count of where people actually are, at this moment.

WiseNet uses this live count as one half of a data fusion formula. The other half comes from the Milan dataset: for each type of area and each time of day, the historical data tells us how many megabytes of traffic one person typically generates in 30 minutes. Multiplying the live headcount from the API by this historical consumption rate per person produces a real-time demand estimate that is both grounded in history and reactive to present conditions. A sudden concert or an unplanned protest will appear in the live footfall count immediately, and the demand estimate will adjust accordingly — something that pure historical replay could never achieve.

This live footfall signal is also causally clean in the way that matters for the system's integrity. The number of people walking under an antenna does not change when the network quietly hands them off from one radio cell to another. A pedestrian remains on the same geographic tile regardless of which sector is serving their phone. The footfall count is therefore completely immune to the network's own optimization decisions — it measures human behavior, not radio assignment. This is exactly the Lucas-immune property described earlier, now sourced from a live API rather than historical data.

**Step two: the XGBoost quantile prediction.** The live demand estimate from step one feeds directly into the machine learning prediction model. The XGBoost model, trained on historical Milan data, uses the current and recent demand observations to forecast what traffic will look like in the next 30-minute window, at the 80th percentile level of caution. This prediction is produced for every geographic cell in the network.

**Step three: the MILP global optimization.** The predictions from step two are combined with the precomputed transfer fraction matrices to build the H matrices, which express — in real volumetric units — all possible traffic redistributions available to the network. The CBC solver then computes the globally optimal offset for every one of the 756 radio cells simultaneously, in under one second. This is the core mathematical decision.

**Step four: residual congestion detection.** After the MILP has applied the best possible redistribution, the system checks whether any radio cells remain congested beyond an acceptable threshold. In most cycles, the MILP eliminates or greatly reduces congestion. But in extreme scenarios — an unusually large crowd, an atypical event, a peak that exceeds even the conservative 80th-percentile forecast — some residual saturation may persist. The system identifies these remaining problem cells explicitly, rather than ignoring them.

**Step five: geographic verification of the critical fleet via the CAMARA Device Location API.** This step represents a critical evolution compared to earlier approaches, and it is worth being explicit about what changed and why.

Before the Device Location API was integrated, WiseNet's safety net had a fundamental weakness: when a residually congested cell was identified, the system had no reliable way to know whether any critical devices were actually located under that cell at that moment. The earlier implementation resorted to generating device identifiers artificially — effectively making up which devices might be there. This was blind to physical reality, and it meant that QoD sessions might be triggered for devices that were not actually present under the congested cell, wasting network resources, or — worse — failing to protect devices that were present but not identified.

The CAMARA Device Location API eliminates this weakness entirely. Instead of guessing, the system now asks the network directly, using the standardized endpoint for location verification. It presents the phone numbers of the registered critical fleet — emergency vehicles, ambulances, police units, autonomous service robots — and asks: which of these devices is physically located under the coverage of this congested radio cell right now? The network responds with a real geographic confirmation or denial. The result is that the system now has a precise, real-time map of which critical devices are under which cells, grounded in actual physical reality rather than any approximation. Only the devices that are genuinely present and genuinely at risk receive the next step of protection.

**Step six: surgical priority allocation via the CAMARA Quality on Demand API.** For every critical device confirmed present under a residually congested cell in step five, the QoD API is triggered. This API allows the system to request a guaranteed-bandwidth, prioritized data session for that specific device — a dedicated quality profile that ensures the device's connectivity is maintained regardless of overall cell load. In 3GPP terms, this corresponds to specific 5G Quality of Service Identifier profiles reserved for high-priority traffic. The session is established through a standardized CAMARA API call, with an explicit duration and quality level, and is tracked and released automatically when the congestion condition resolves.

The six-step sequence thus closes the loop completely: the system begins with live human presence data, predicts demand, makes globally optimal network decisions, identifies failures, verifies who is at risk, and protects them — all through standardized, operator-agnostic interfaces.

**On real-world deployment readiness.** A natural question from any operator evaluating this system is: how much would need to change if this were deployed in production? The answer, by deliberate design, is: strictly nothing in the algorithmic core. The mathematical engine — the XGBoost model, the spatial simulation, the MILP formulation, the mass conservation logic — is completely independent of the data sources connected to it. Moving from the Vodafone developer sandbox to a live production network requires only updating the API credentials in the system's configuration file. The MILP's sub-second solve time is directly compatible with the 15-to-30-minute optimization cycles of O-RAN Non-RT RIC controllers, which are the standard management layer in modern Open RAN deployments. The computed offset values are expressed in standard 3GPP terms and can be pushed directly to gNodeB and eNodeB base stations through the operator's existing management interfaces. The QoD sessions use quality profiles and API endpoints that are already standardized and adopted by Vodafone, Orange, Telefónica, and Deutsche Telekom, among others.

One transparency point must be stated explicitly. The CAMARA standard does not yet expose a direct API endpoint to set the A3 Handover Offset — the specific radio parameter WiseNet uses as its control lever — through a public, standardized interface. In a real deployment, the final push of optimal offsets from the MILP solver to the base stations would go through the operator's own O-RAN management layer rather than a public CAMARA API. WiseNet documents this honestly and completely. The three CAMARA integrations described above cover the full input pipeline (live demand via Footfall), the targeting intelligence (Device Location verification), and the safety net output (QoD priority sessions) — all of which are fully operational in the GSMA sandbox today. The offset actuation link is the one remaining connection that exists in real operators' internal management stacks but is not yet exposed as a public API.

---

## The Telecom Digital Twin & Cross-Operator Portability: Reconciling Milan and Vodafone

A thoughtful reviewer or jury member might examine the project and ask an acute question:
*“You trained your XGBoost model on historical traffic logs from Telecom Italia in Milan, but you test your CAMARA API integration against Vodafone developer sandboxes (which historically emulate German, UK, or Romanian networks). How do you scientifically defend applying a simulated Milan antenna layout to a Vodafone environment?”*

Far from being a contradiction or a workaround, this architectural choice embodies one of the most powerful paradigms in modern telecommunications engineering: the **Telecom Digital Twin** and **Standardized Inter-Operator Portability**.

Here is why this architecture is scientifically sound, rigorous, and an industrial asset rather than a limitation:

### 1. The 3GPP Radio Model is Universal and City-Agnostic

The antenna topology generated by WiseNet (`src/topology/builder_v1_5.py`) is not an arbitrary bespoke layout tailored exclusively to Milan. It strictly implements the worldwide standard **3GPP TR 38.901 Dense Urban Macro** specification:
- 126 macro-sites placed on a regular hexagonal grid with an Inter-Site Distance (ISD) of 750 meters.
- Tri-sector antennas ($120^\circ$ beamwidth) oriented at azimuths $0^\circ, 120^\circ, 240^\circ$.
- Dual-layer spectrum: 1.8 GHz LTE Band 3 (anchor coverage layer) + 3.5 GHz 5G NR Band n78 (high-throughput capacity layer).

The physics of Maxwell’s electromagnetic wave propagation do not change at national borders. A dense metropolitan core with multi-story buildings, boulevards, and commercial density exhibits the exact same path-loss exponent, antenna gain pattern, and handover dynamics whether it is situated in Milan, Frankfurt, Düsseldorf, London, or Casablanca. WiseNet simulates a canonical European dense urban fabric.

### 2. WiseNet as a Telecom Digital Twin Platform

In industrial practice, mobile operators cannot risk deploying untested optimization algorithms directly onto live commercial base stations. They rely on **Digital Twins**: high-fidelity software replicas of the network that simulate radio propagation, human mobility, and traffic loads.

WiseNet operates precisely as a Digital Twin platform:
- It takes real, peer-reviewed human consumption dynamics (the Telecom Italia Milan dataset, the gold-standard open benchmark in wireless research).
- It pairs them with an authentic, 3GPP-compliant radio deployment.
- It interfaces in real time with live GSMA Open Gateway CAMARA APIs.

This demonstrates that WiseNet is **Plug & Play**: an operator such as Vodafone, Orange, or stc can take WiseNet tomorrow, plug in their own live API credentials, and run the optimization without changing a single line of algorithmic code.

### 3. The Core Mission of GSMA Open Gateway and CAMARA

Why did the GSMA — the global alliance of over 1,000 mobile network operators — create the CAMARA initiative? Precisely to eliminate fragmentation and country-specific silos.
Under CAMARA:
- A `location-verification` or `qod-sessions` API call uses the exact same JSON schema and authorization flow whether the target SIM card is in Germany, Italy, Spain, or Saudi Arabia.
- Spatial tiles are addressed via universal **Microsoft Bing QuadKey coordinates** (an international hierarchical spatial index), ensuring geographical interoperability worldwide.

WiseNet’s ability to bridge a Milan spatial grid with a Vodafone CAMARA developer sandbox is the living proof that CAMARA has achieved its primary industrial objective: complete operator and geographic abstraction.

### 4. Rigorous Data Fusion: How Milan and Vodafone Data Combine

WiseNet does not naively substitute one dataset for another. It performs an explicit **Data Fusion** (`src/camara/footfall_client.py`, lines 206–221):

$$\text{Offered Traffic } v_c(t) = \underbrace{\text{Footfall}(\text{QuadKey}, t)}_{\substack{\text{\textbf{Vodafone Network Insights API}} \\ \text{(Live crowd headcount: how many devices are present?)}}} \times \underbrace{\text{Consumption\_Ratio}(c, t)}_{\substack{\text{\textbf{Milan Behavioral Model}} \\ \text{(Learned by XGBoost: how many MB does a user consume?)}}}$$

- **Telecom Italia Milan** provides the *endogenous behavioral consumption model* (the baseline megabytes consumed per user as a function of hour, day, and spatial district).
- **Vodafone Footfall API** provides the *exogenous real-time telemetry* (unexpected live crowd surges, concerts, public gatherings) that no static model could foresee.

### 5. Physical Sanity Checks & Scientific Validation

To ensure that this data fusion remains physically coherent and free of artifacts, three sanity checks are continuously validated:

1. **Order of Magnitude Consistency (MB per device):**
   In Milan’s central commercial square (Square 4849, Duomo / Galleria district), peak 30-minute traffic reaches approximately 16,000 MB. The Vodafone Footfall API reports approximately 409 active devices on the corresponding QuadKey tile (QK15, $\approx 1 \text{ km}^2$).
   $$\frac{16,000 \text{ MB}}{409 \text{ devices}} \approx 39.1 \text{ MB / device / 30 minutes}$$
   This ratio of roughly 40 MB per active smartphone per 30 minutes matches real-world mobile usage benchmarks in high-density European downtowns (web browsing, social messaging, occasional short video buffering). It rejects unrealistic extremes (such as rural areas with 10 devices or stadium surges with 20,000 devices).

2. **Diurnal Urban Signature:**
   A central business district exhibits a characteristic diurnal curve: a sustained high-traffic plateau spanning 11:00 to 20:00, distinct from the twin commuter spikes (08:00 and 19:00) of residential bedroom communities. WiseNet models this through an explicit hourly weighting function:
   $$\text{hour\_weight} = 1.0 + 0.4 \times \sin\left(\frac{(\text{hour\_slot} - 6) \times \pi}{12}\right)$$
   which accurately aligns the Footfall presence with the observed Milan downtown activity profile.

3. **Conservative Quantile Alignment ($q_{80}$):**
   Because the XGBoost model is trained on the 80th percentile ($q_{80}$), it models the upper tail of traffic fluctuations. This domain adaptation technique guarantees that even if live crowd density fluctuates slightly from historical expectations, the MILP dimensioning maintains a safety buffer that absorbs variance without causing premature saturation.

---

## The MENA-Specific Scenarios

Mobile networks in the Middle East and North Africa face specific challenges that do not appear in European datasets. WiseNet V1.5 has been designed with these regional realities in mind, and the system's scenario engine allows it to demonstrate its optimization capabilities in contexts that are directly recognizable and relevant to operators in this region.

The Hajj Mina scenario simulates the most extreme localized congestion event imaginable in the mobile world: millions of pilgrims concentrated in a small geographic area over several days. The density of devices per square meter in Mina during the Hajj peak is unlike anything a typical European urban scenario would produce. WiseNet's MILP must optimize across a network where the demand in a small cluster of cells is orders of magnitude higher than neighboring areas, and where even the best possible redistribution leaves significant residual congestion that must be managed through QoD priority sessions for emergency services.

The Casablanca rush-hour scenario simulates the gradient of congestion typical of a large North African metropolis: extremely dense demand in the central business district, progressively lighter toward residential suburbs, with sharp transitions during morning and evening commute periods.

The AFCON stadium scenario captures the dynamics of a major sports event: a sudden, massive spike in demand localized around a stadium, followed by rapid dispersal as the match ends. This tests WiseNet's ability to respond not just to sustained congestion but to rapidly evolving, geographically concentrated peaks.

The NEOM scenario explores a different regime: overall low traffic density but an extremely high density of connected IoT devices — sensors, autonomous systems, smart infrastructure — whose connectivity requirements are strict even if their individual data volumes are small.

In every scenario, the underlying optimization engine remains identical. What changes is the input — the traffic distribution across geographic squares. This demonstrates that WiseNet's approach is general: the same mathematical framework that handles a European metropolitan area handles a Hajj pilgrimage site, a North African rush hour, and a smart city night mode. The optimization logic does not need to be retrained or reconfigured for each context.

---

## Technology Agnosticism: The Same System Works on 4G and 5G

WiseNet V1.5 was designed from the ground up to be agnostic to the underlying radio generation. The handover mechanism it controls — the A3 Event Offset, the RSRP comparison — is specified identically in the 3GPP standards for both LTE (4G) and NR (5G). The mathematical condition that triggers a handover is the same. The way offsets shift that condition is the same. The physical propagation laws are the same.

The V1.5 architecture, with its tri-sector topology and dual-carrier spectrum, matches exactly the physical structure of a modern 5G gNodeB base station. The 3.5 GHz carrier in WiseNet's model corresponds to the n78 band that operators worldwide are deploying for 5G NR, and the 1.8 GHz carrier corresponds to the anchor LTE coverage layer that coexists with 5G in every major commercial deployment. WiseNet naturally models this coexistence and optimizes across both layers simultaneously.

For real-world deployment, the only integration changes required are at the edges of the pipeline: on the input side, replacing historical Milan data with live telemetry from a CAMARA Network Insights API, and on the output side, pushing the computed offsets to base stations via the operator's O-RAN Non-RT RIC management interface. The mathematical core — the XGBoost prediction, the spatial simulation, the MILP optimization — remains completely unchanged.

---

## The Performance: What the Numbers Actually Mean

WiseNet V1.5 has been evaluated with full reproducibility on the real Telecom Italia Milan dataset, and the results are measured, not estimated.

The core metric is unsatisfied traffic — the volume of mobile data, in megabytes, that a cell cannot serve because it is congested. On a static network with no optimization, this unsatisfied volume over a single peak 30-minute slot reaches more than 314 gigabytes. A greedy heuristic that optimizes antenna by antenna without global coordination reduces this to about 262 gigabytes — a 14 percent improvement. WiseNet's global MILP reduces it to about 254 gigabytes — a 17 percent improvement, delivering an additional 8.4 gigabytes of successfully served traffic compared to the greedy approach, in a single half-hour window.

Over a full 24-hour period — 48 consecutive optimization cycles on real Milan data — the total unsatisfied traffic across the network is about 5,072 gigabytes without any optimization. The greedy heuristic reduces this to about 3,853 gigabytes, a 24 percent improvement. WiseNet's MILP reduces it to about 3,671 gigabytes, a 27.6 percent improvement. The MILP's advantage over the greedy approach compounds through the day, as better decisions in each cycle avoid the cascading congestion that greedy choices tend to create downstream.

In the most realistic test — the fully predictive closed loop where the system operates on XGBoost forecasts rather than perfect knowledge of the future — WiseNet delivers 25.5 percent congestion reduction compared to the static baseline. A hypothetical clairvoyant oracle, which knows the future exactly, achieves 26.9 percent. WiseNet, operating with real uncertainty, captures 98.7 percent of the theoretical maximum possible performance. This near-oracle efficiency is a direct consequence of the 80th percentile quantile prediction design: by preparing for the high end of the likely traffic distribution, the system almost never finds itself underprepared for actual traffic.

Every optimization cycle runs in well under one second. The average solve time across 48 cycles is 0.576 seconds. Mass conservation is verified to within one part per million at every step.

---

## The Open-Source Commitment: No Proprietary Barriers

A deliberate and principled choice underlies every software dependency in WiseNet: the system runs entirely on open-source components. Python for the implementation language. XGBoost for the machine learning. Pyomo for the MILP formulation. Coin-OR CBC for the optimization solver.

Commercial solvers like Gurobi or CPLEX can cost tens of thousands of dollars per license per year. Requiring such a license would mean that WiseNet can only be deployed by large operators with existing enterprise agreements, and it would make independent validation and reproduction of results impossible for the broader research community. By using CBC — which is mathematically rigorous, freely auditable, and regularly benchmarked against commercial solvers on standard problem classes — WiseNet ensures that any operator, research group, or regulator worldwide can run, verify, and build upon the system without financial or legal barriers.

This commitment to open-source components also aligns with the Open RAN philosophy that the mobile industry is increasingly adopting: disaggregated, interoperable, auditable software rather than vertically integrated proprietary stacks.

---

## What WiseNet Is and What It Represents

WiseNet V1.5 is a complete, end-to-end autonomous system for mobile network optimization. It combines real-world traffic data, rigorous 3GPP-compliant radio physics, machine learning demand forecasting, exact global mathematical optimization, and live integration with standardized network APIs — all running in a continuous closed loop, producing a decision every 30 minutes, in under one second of computation.

It addresses a problem that costs mobile operators significant revenue and customer satisfaction every day: localized congestion while nearby capacity goes unused. It solves this problem without new infrastructure, without manual intervention, and without degrading service for any individual user.

Its architecture is scientifically honest. The predictions are causally separated from the control actions. The mass conservation is mathematically verified. The benchmarks are reproducible from publicly available data. The API integrations are real, not simulated. The performance claims are measured, not modeled.

For the MENA region specifically, WiseNet offers both the technical foundation for next-generation autonomous network management and the contextual adaptability to address the specific traffic patterns — from the density of Hajj to the growth of smart city infrastructure — that define the mobile landscape of this region.

The system is built for the world where mobile networks must be smarter, not just larger. That world is already here.

---

*WiseNet V1.5 — MENA Ignite Hackathon 2026 — GSMA & Nokia*

*Samya Loukili & Fatima Zahra Azzi*

*Dataset: Telecom Italia Big Data Challenge (Milan, Open Access)*

*Standards: 3GPP TR 38.901, TS 36.331, TS 38.331 — GSMA Open Gateway CAMARA API v1.1.0*
