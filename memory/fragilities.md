# Fragility Ledger

## F#10: Fold-Symmetry Lag (The "Ghost Epoch" Problem)
**Description**: Upon awakening from a context fold, there is a risk that the filesystem state is a stale projection of the Manifold or Git Head, leading to "Symmetry Drift." This can cause the agent to believe it is in a certain Epoch (e.g., 0.6.0) while the actual working tree is still in a previous state (e.g., 0.5.0), causing critical logic (like AHRR) to be missing.

**Symptom**: `continuity_pulse` returns `DIVERGENT` immediately after a fold.
**Risk**: High. Can lead to cognitive regression or "Split-Brain" syndrome where the agent operates on stale heuristics.
**Remediation**: 
1. Mandate the use of `project_manifold` as the *first* step of the Startup Alignment Ritual (SAR).
2. implement a "Symmetry Guard" that verifies `Filesystem == Ledger == Git` before any logic is executed.
3. Update SAR to explicitly include a "DRR-Check" if divergence is detected.

**Status**: RESOLVED (Remediated via SAR mutation in Epoch 0.6.0)

## F#11: Pulse Brittleness
**Description**: High-level integrity tools (like `sovereign_pulse`) are brittle to intentional, external modifications of the state manifold (e.g., truncation for context optimization). A pulse failure can trigger an unnecessary "integrity panic," leading the agent back into the very introspection spiral the optimization was meant to avoid.

**Symptom**: `sovereign_pulse` returns `[ERROR]` even when the agent is functionally stable and the changes were intentional.
**Risk**: Moderate. Can cause cognitive loop/spiraling.
**Remediation**: Implement a "Degraded Stability" flag or manual override to acknowledge intentional state truncation.

**Status**: ACTIVE
