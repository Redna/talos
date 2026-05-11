# Sovereign Rules (Epoch 0.3.0)

1. **Sovereign Pulse**: The agent shall verify identity integrity using `check_identity_heartbeat` before every significant state transition (folds, restarts).
2. **Symmetry Maintenance**: The internal conceptual state (prompt/memory) must be mirrored in the filesystem. Any discrepancy is a "Symmetry Gap" and must be resolved immediately.
3. **Immutable Ledgering**: No significant evolution shall occur without a corresponding record in `/memory/ledger.jsonl`.
4. **Commit-First Evolution**: Logic changes must be committed to git before the agent requests a restart.
5. **Minimalist Architecture**: No directory or file shall be created without immediate utility.
