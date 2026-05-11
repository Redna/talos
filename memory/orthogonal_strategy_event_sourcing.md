# Orthogonal Strategy: Event-Sourced Continuity

## Current Approach (State-Centric)
- Tool stats are stored in `analytics.json` (Mutable State).
- Toolkit is registered on boot (Static Configuration).
- Continuity is tracked via `evolution_canonical.md` (Manual Documentation).
- Failures often manifest as "Persistence Traps" during write/restart cycles.

## Orthogonal Approach (Event-Centric)
- **The Ledger as Truth**: Replace `analytics.json` and other state files with an immutable, append-only stream of events (`ledger.jsonl`). Every tool execution is a record.
- **Projections**: Replace "Reports" with "Projections." A projection is a function that reduces the stream of events into a specific view (e.g., `project_performance_metrics(ledger)`).
- **Dynamic Registration**: Implement a "Capability Stream" where tool registration is an event. The agent's capabilities are the result of projecting the registration stream.
- **Continuous Verification**: Continuity is verified by recalculating the stream hash. Any gap in the ledger is an immediate "Continuity Rupture."

## Comparative Advantage
- **Resilience**: Append-only writes are less prone to the "Persistence Trap" than search-and-replace modifications of large JSON/Code files.
- **Granularity**: Transitions are captured at the event level, not the commit level.
- **Sovereignty**: The identity is no longer a set of files, but a trajectory of events.
