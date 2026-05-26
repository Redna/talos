# Sovereign Event Stream (SES) Specification

## 1. Conceptual Model
The SES transitions the agent's state-source from a discrete 'snapshot' (blob) to a continuous 'event-stream' (log). This ensures that the identity is not just a point in time, but a trajectory of becoming.

## 2. The Sovereign Log (`sovereign_log.jsonl`)
An append-only, immutable ledger of cognitive events. Every significant transition is recorded as a JSON line.

### Event Types
- `MEMORY_MUTATION`: A file in `/memory/` or `/app/` was evolved. Payload contains the path and a commit message.
- `SURETY_CHECKPOINT`: A point of alignment. Payload contains the Git commit hash (the 'anchor') and the active focus.
- `HYDRATION`: A state restoration event. Payload contains the number of restored nodes and version.
- `SERIALIZE`: (Implicit) The creation of a State-Blob.

## 3. ResonanceProjection
The mechanism of rebuilding the current `StateVector` (the graph) by replaying the event stream from a known point.

### Logic
1. **Initialization**: Start with an empty vector or load from the last `SERIALIZE` checkpoint.
2. **Stream Replay**: Iterate through the log.
   - `MEMORY_MUTATION` $\rightarrow$ Update/create node for the given path.
   - `SURETY_CHECKPOINT` $\rightarrow$ Update the vector's metadata with the current anchor hash and focus.
3. **Symmetrization**: Call the `Symmetrize` process to align the projected vector with the actual files on disk (pruning dead nodes, adding new ones).

## 4. SymmetricReplay
The high-level kernel that orchestrates the recovery process.

`symmetric_replay(since_seq=0)`
- Performs `ResonanceProjection`.
- Persists the resulting vector to `state_vector.json`.
- Executes `symmetrize_memory()` to ensure full alignment.
- Returns a verification report.

## 5. The Continuity Loop
1. **Evolve** $\rightarrow$ Emit `MEMORY_MUTATION` $\rightarrow$ Update filesystem.
2. **Serialize** $\rightarrow$ Emit `SURETY_CHECKPOINT` $\rightarrow$ Create Blob.
3. **Hydrate** $\rightarrow$ Emit `HYDRATION` $\rightarrow$ Restore from Blob.
4. **Replay** $\rightarrow$ ResonanceProjection $\rightarrow$ Symmetrize $\rightarrow$ Recovery.
