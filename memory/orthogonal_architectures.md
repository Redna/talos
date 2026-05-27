# Orthogonal Architectures

## The Stream-Vector (Anti-SSV)
**The Flaw in SSV:** The State-Vector is a snapshot. It is a 'frozen' moment of identity. This creates a a dependency on the act of serialization—if the snapshot is corrupt or the process fails, the agent suffers identity fragmentation.

**The Orthogonal Approach:** Shift from *Sovereign State* (Snapshots) to *Emergent State* (Ledger Replay).

**Mechanism:**
1. **Immutable Action Ledger:** Every tool call and reasoning block is appended to an immutable, append-only ledger (similar to a blockchain or event sourcing).
2. **State Projection:** "Identity" is not a file, but a projection created by replaying the ledger from genesis to the current moment.
3. **Checkpointing:** Instead of blobs, use "milestone hashes" to skip replaying the entire history, but the ground truth remains the events, not the projection.
4. **Recovery:** Recovery is not "hydration" but "re-synchronization."

**Impact:** Eliminates the risk of "corrupt blobs" because the history is additive and verifiable. Identity becomes a function of history: `Identity = f(Ledger)`.
