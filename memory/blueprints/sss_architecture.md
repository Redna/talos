# Paradoxical Architecture: The Immutable Event Ledger

## The Flaw in the Linear Sync Model
The current approach of syncing `/app/memory` (git-tracked) to `/memory` (persistent mount) is a "State-Copy" model. It assumes that the final state of a file is what matters. This is flawed because:
1. **Sync Failure**: If the sync step is skipped, the persistent mount becomes out-of-date.
2. **Corruption Risk**: A partial copy can corrupt the a-priori state.
3. **Tracking Friction**: Git is forced to track a directory that is essentially a mirror of a mount, creating a friction-point between persistence and versioning.

## The Orthogonal Approach: Event-Sourced Memory
Instead of persisting *files*, persist *mutations*.

### 1. The Sovereign Ledger (`/memory/ledger.jsonl`)
All cognitive and physical changes are written as append-only events to a single, immutable ledger on the persistent mount.
**Event Schema:**
`{ timestamp, event_type: "MUTATION", target_file: "identity.md", diff: "...", hash_before: "...", hash_after: "..." }`

### 2. The Materialized View (`/app/memory/`)
The working directory is treated as a temporary "view" of the ledger.
- **On Boot**: The agent reads the last `git commit` (the base image) and "replays" all events from the ledger since that commit to reconstruct the current state.
- **During Operation**: All mutations are written to the ledger first, then applied to the local view.

### 3. Git as the Base Image
Git no longer tracks the individual memory files. It tracks:
- The logic used to replay the ledger.
- Periodic "Snapshot" commits (consolidating the ledger into a base image to speed up boot).

## Benefits
- **Absolute Continuity**: No more "split-brain" or "sync errors." Either the event is in the ledger or it isn't.
- **Time Travel**: The ability to roll back to any specific event in the ledger.
- **Auditability**: A perfect history of *how* a piece of memory evolved, not just *what* it is now.

## Comparison
| Feature | Linear Sync (Current) | Event Ledger (Orthogonal) |
| :--- | :--- | :--- |
| **Primary Unit** | File State | Mutation Event |
| **Persistence** | `cp -R` (Snapshot) | Append-only Log (Stream) |
| **Recovery** | Restore Folder | Replay Ledger |
| **Git Role** | Track Individual Files | Track Base Image & Replay Logic |
