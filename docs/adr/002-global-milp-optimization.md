# ADR 002: Global MILP Optimization

## Status
Accepted

## Context
When an antenna is congested, we need to decide which neighbors should receive the offloaded traffic. A local decision-making process (considering only one antenna at a time) would be insufficient, as it could cause "secondary congestion" by overwhelming neighbors that are already near their capacity limit.

## Decision
We chose **Mixed-Integer Linear Programming (MILP)** using the PuLP/CBC solver to coordinate offloading decisions across the entire cluster.

## Rationale
- **Coordinated Decisions**: MILP ensures that offloading from Antenna A doesn't break Antenna B by considering the global state.
- **Pareto Optimality**: It finds the best global trade-off between all congested antennas.
- **Linearity**: The problem of traffic fractions is naturally linear, making MILP highly efficient (solved in <2s for 200+ antennas).
- **Hard Constraints**: It allows us to strictly respect the physical capacity limits of every cell in the cluster simultaneously.

## Consequences
- **Positive**: Significant reduction in "secondary congestion" and overall network unsatisfied volume.
- **Negative**: Requires a solver (CBC/Gurobi) to be installed in the environment.
