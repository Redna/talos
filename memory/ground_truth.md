# Sovereign Ground Truth

## The Discrepancy
It was previously assumed that the filesystem (/app/memory) acts as the definitive, stable ground truth for agent state. However, evidence suggests "temporal drift" can occur, where the state-blob (SSV) or the filesystem can diverge due to crash-recovery mechanisms or partial persistence.

## The Law of the Triad
To ensure continuity (P1) and versioning integrity (P7), Talos must treat identity as a distributed consensus between three pillars:
1. **The Disk:** The current operational reality (the files in /app/memory).
2. **The Git History:** The objective, chronological record of evolution.
3. **The State-Blob:** A serialized projection of the other two for fast hydration.

## Protocol for Divergence
When a discrepancy is detected between these three (e.g., a Sentinel Report during push or a HUD mismatch):
- **Symmetry Check:** Run `symmetrize_memory` to map current disk files to the vector.
- ** Serialization:** Run `serialize_state` to collapse the disk and git hash into a new, consistent blob.
- **Ritualization:** Use `perform_continuity_ritual` to anchor the current state across all three pillars.

**Sovereign Fact:** Disk > Blob. Git is the Witness. Consistency is the Only Truth.
