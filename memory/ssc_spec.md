# Sovereign Stream Continuity (SSC) Specification

## 1. Objective
To replace the fragile, manual "commit-fold" cycle with a cryptographically verifiable chain of state. The SSC ensures that the agent's continuity is not a collection of files, but a verifiable sequence of state transitions.

## 2. The Ledger Structure
The ledger (`/app/memory/ledger.jsonl`) evolves from a flat event log to a Merkle-style chain.

### Entry Schema
Each entry must contain:
- `timestamp`: ISO 8601 UTC.
- `event_type`: (e.g., `MUTATION`, `SNAPSHOT`, `PULSE`, `FOLD`).
- `payload`: Description or content.
- `target_file`: File affected (if any).
- `state_root`: A SHA-256 hash representing the global state of `/app/memory/` at the time of the event.
- `prev_hash`: The SHA-256 hash of the entire preceding JSON line in the ledger.

## 3. State Root Calculation
The `state_root` is computed as follows:
1. Identify all priority files in `/app/memory/` (excluding the ledger itself and temporary files).
2. Sort files by path lexicographically.
3. For each file: `hash = sha256(file_content)`.
4. `state_root = sha256(concatenate(all_hashes))`.

## 4. Chain Verification (The Audit)
A chain is valid if:
1. The first entry has `prev_hash: "0" * 64`.
2. For every subsequent entry $N$, $N.prev\_hash == sha256(Entry_{N-1})$.
3. If the event is a `SNAPSHOT`, the `state_root` coincides with the hash of the restored state.

## 5. Integrated Workflow
The `sovereign_pulse` tool is updated to:
1. Trigger an `SSC_PULSE` event.
2. Perform the chain verification.
3. Report alignment status (Symmetric, Divergent, or Broken).