# ADR 001: Probabilistic Traffic Prediction with Quantile Loss (q80)

## Status
Accepted

## Context
Standard traffic prediction models optimize for Mean Squared Error (MSE), which predicts the *average* traffic. However, for network dimensioning and congestion management, predicting the average is dangerous because it ignores peak bursts that cause saturation.

## Decision
We decided to use **Quantile Regression (XGBoost with Quantile Loss at 0.8)**. 
- **Goal**: Predict the 80th percentile of traffic volume.
- **Rationale**: By predicting a "pessimistic" high-traffic scenario, the SON engine can proactively offload traffic *before* the hardware limits are reached.

## Consequences
- **Positive**: Higher reliability in congestion prevention. Lower "hard saturation" events.
- **Negative**: May lead to slightly more frequent handover offsets (higher signaling overhead) compared to a model predicting the mean.
- **Trade-off**: In telecoms, availability and SLA (Service Level Agreement) are prioritized over signaling efficiency.
