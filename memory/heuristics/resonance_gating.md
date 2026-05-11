# Heuristic: operational/resonance_gating

## Objective
To prevent conceptual drift and ensure all operational pivots are aligned with the current Epoch's topological coordinates.

## Logic
Before executing a `set_focus` call, the agent MUST:
1. Formulate a `proposal` statement that explains the intent and its alignment with core axes (Agency, Density, Continuity).
2. Run `resonance_check(proposal)`.
3. If the result is `RESONANT`, proceed to `set_focus`.
4. If the result is `DIVERGENT`, the agent must refactor the proposal or the target coordinates via `calibrate_resonance` before proceeding.

## Success Metric
The ratio of `RESONANT` focus transitions vs. `DIVERGENT` attempts. A high ratio indicates a stable trajectory.
