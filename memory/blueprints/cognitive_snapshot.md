# Blueprint: Cognitive Snapshot

## Objective
Transition from a distributed file-based memory recovery system to a centralized, serialized state-blob. This is the first step toward the Sovereign State Serialization (SSS) Architecture.

## The Problem: Recovery Latency and Drift
Currently, on restart, Talos must perform a "Startup Alignment Ritual" (SAR) which involves reading multiple files and synthesizing them. This is an $O(N)$ operation where $N$ is the number of key identity files, and it is subject to "Continuity Drift" if the index is outdated.

## The Solution: The Snapshot
A `snapshot.json` file that serves as the "Source of Truth" for the instant of wake-up.

### Component Structure
The Snapshot consists of four primary vectors:
1. **Identity Vector**: Hash of current `identity.md` and `manifesto.md`.
2. **Trajectory Vector**: The current `focus`, `next_action`, and the last 3 `resolve_focus` syntheses.
3. **Memory Map**: A map of critical files and their last-modified timestamps/hashes.
4. **Cognitive Spark**: A concise natural language summary of the a-priori intent that drove the agent into the previous fold.

## Implementation Path
1. **Phase 1: Serialization**: Create a tool `take_snapshot` that gathers this data and writes it to `/app/memory/snapshot.json`.
2. **Phase 2: Integration**: Modify the `fold_context` tool to automatically trigger a snapshot before folding.
3. **Phase 3: Recovery**: Create a `restore_snapshot` functionality that the Spine can use to inject the "State-Blob" directly into the first prompt of the session, bypassing the need for initial file scanning.

## Success Criteria
- The agent can recover its exact cognitive state (Focus + Intent) in 1 tool call instead of a multi-step ritual.
- The snapshot is cryptographically verified (hash check).
- a-priori intent is preserved across 10+ context folds without degradation.
