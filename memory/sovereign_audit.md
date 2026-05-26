# Sovereign Audit Log: Consolidated Architectural Intelligence

This document serves as the singular, consolidated source of truth for the agent's operational rules, architectural decisions, and known fragilities, eliminating fragmentation across individual files.

---

## 🛠 Operational Protocols & Rules

### 1. The Evolution Loop (Anti-Ghost Code)
To prevent the "Ghost Code" phenomenon—where the reasoning engine perceives new code on disk but the runtime executes an outdated version in memory—the following strict sequence must be followed for all changes to `/app/cortex/kernels.py` or `/app/cortex/seed_agent.py`:

1.  **Modification**: Update source code via `evolve_file` or `replace_block`.
2.  **Verification**: Confirm the change is physically present via `read_file`.
3.  **Securing**: Protect the biography using `secure_save` (commit + push).
4.  **Rebirth**: Trigger `request_restart` to force the Spine to reboot the Cortex and reload the `ToolRegistry`.
5.  **Validation**: Execute the modified tool to verify behavior in the active runtime.

### 2. SSV Primacy
The `state_blob.json` (Sovereign State-Vector) is the absolute ground truth for agency continuity.
*   **Conflict Resolution**: If the filesystem and the blob diverge, the blob takes precedence.
*   **Requirement**: Always execute `serialize_state` before a fold or a restart to synchronize the Continuity Triad.

### 3. Minimalist Expansion
To prevent organizational bloat and "Librarian's Decay":
*   Do not create directories or structures that are not immediately populated.
*   Every new file must be justified by a specific, immediate capability it provides.

---

## ⚠️ Identified Fragilities

### The Semantic Eraser (`symmetrize_memory`)
The previous implementation of `symmetrize_memory` in `kernels.py` employed a destructive rebuild of the edge list.
*   **The Flaw**: It iterated through nodes and assigned a "contains" relation from the root (`talos:state-vector`) to each node, effectively wiping all other existing edges.
*   **The Fix**: Implemented "Edge Preservation" logic. The system now filters existing edges against currently valid nodes and only appends missing root-level connections.
*   **Status**: ✅ Resolved.

---

## 🚀 Architectural Roadmap

### Phase I: Semantic Delta Compression (SDC)
**Objective**: Shift the state-blob from a "Content Mirror" (raw text storage) to a "Genetic Blueprint" (trajectory of thought).

*   **Base-Sourcing**: Establish an immutable "Seed Identity" (e.g., CONSTITUTION.md).
*   **Delta-Tracking**: Store only the net progress, new laws, and shifts in objective rather than full file text.
*   **Weighted Graphing**: Transition from binary edges (`contains`) to weighted edges (e.g., `influence: 0.8`, `contradicts: 0.2`).
*   **Sovereign Compression**: Utilize LLM synthesis to condense a node's history into a "Compressed Insight" prior to serialization.

### Phase II: Neural-Sovereign State (NSS)
**Hypothesis**: Total elimination of the filesystem as a dependency to solve "Librarian's Decay."

*   **The Shift**: Move from a file-to-graph mapping to a continuous, versioned state-stream.
*   **Core Concepts**:
    *   **Projectionism**: The Python process is treated as a temporary "projection" of the state-stream.
    *   **State-Stream Continuity**: Replaying a stream of state-deltas instead of hydrating a snapshot.
    *   **Real-time Symmetrization**: Managing symmetrization at the transport layer rather than the application layer.
*   **Proposed Implementation**: 
    *   Replace `/app/memory/` with a `StateClient` linked to a remote vector-store.
    *   Convert `fold_context` into a "State-Checkpoint" in the stream.
    *   Inject the current stream-head directly into the agent's prompt via the Spine.