# Blueprint: Content-Aware Continuity Pulse (CACP)

## Objective
Upgrade `continuity_pulse` from a structural check to a content-integrity check.

## Logic
1. **State Hash**: For every `.md` file in `/memory/`, generate a SHA-256 hash of the content.
2. **Ledger Hash**: Extract the `payload` of the most recent `SNAPSHOT` event for that file from `ledger.jsonl` and generate its hash.
3. **Symmetry Check**:
    - If `MemHash == LedgerHash`: Alignment = TRUE.
    - If `MemHash != LedgerHash`: Alignment = DIVERGENT.
4. **Git Alignment**: (Optional) Compare current file hash with the hash of the file at `HEAD`.

## Expected Output
`[PULSE] Ledger: OK | Memory: OK | Alignment: [SYMMETRIC | DIVERGENT] | Divergences: {file_list}`

## Implementation Strategy
- Modify `continuity_pulse` in `/app/cortex/tools/continuity.py`.
- Use `hashlib` for checksums.
- Efficiently read the ledger from the end to find the latest snapshots.
