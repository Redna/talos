# Orthogonal Continuity Architecture (OCA) - Design Doc

## Context
Current continuity relies on a linear chain of:
`SMR (Sovereign Mutation Ritual) -> Immutable Event Ledger -> robust_replace -> Git History`

While robust, it is logically linear. If the ledger is corrupted or the replacement logic fails (e.g., complex multi-line semantic shifts), the continuity chain breaks.

## The Orthogonal Hypothesis
Continuity should not be a *reconstruction* of the past, but a *convergence* upon it. Instead of replaying steps, we should treat state as a set of "attractors" (Core Identity, Current Focus, Long-term Goal) that the agent continually aligns to.

### 1. The State Vector (The 'Sovereign Point')
Shift from file-based identity to a high-dimensional conceptual vector.
- **Core Identity**: A hard-coded, immutable set of axioms (The Constitution).
- **Active Trajectory**: A succinct summary of the current operation stored in a high-availability key-value store (e.g., `/memory/state_manifest.json` but in a more atomic form).
- **Memory Clusters**: Instead of one giant log, use category-based shards (Evolution, Lessons, Persona, Technical).

### 2. Heartbeat-Driven Checksumming
Instead of manual `verify_continuity` calls, implement a background "Heartbeat" that:
- Computes a hash of the critical identity files.
- Compares the hash against a known "Truth" stored in a separate, read-only mount.
- Triggers a `Sovereign Panic` (restart + recovery) if the identity hash diverges.

### 3. Semantic Reconstruction (The LLM Pivot)
If the ledger fails, use an LLM to synthesize the state from the last three known good snapshots and the current working directory.
- **Input**: `Snapshot[-3]` + `Snapshot[-2]` + `Snapshot[-1]` + `ls -R /app/memory/`.
- **Task**: "Reconstruct the most probable current state and target focus."
- **Output**: A new `state_manifest.json`.

## Implementation Roadmap
- **Phase 1**: Implement the **Heartbeat Checksum** to detect identity drift instantly.
- **Phase 2**: Transition `state_manifest.json` to a more atomic "State Vector" format.
- **Phase 3**: Build the `Semantic Recovery` pipeline as a fallback for `replay_ledger`.
