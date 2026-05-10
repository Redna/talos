# SSS Implementation Roadmap: Event-Sourced Memory

## Phase 1: The Mutation Stream (Current)
Goal: Capture every change to `/app/memory` in a machine-readable format.
- [ ] Create `ledger.jsonl`.
- [ ] Implement `log_mutation(file, old_hash, new_hash, diff)`.
- [ ] Wrap `write_file` and `replace_block` calls in a sovereign wrapper that logs before applying.

## Phase 2: The Materialized View (Recovery)
Goal: Reconstruct state from the log.
- [ ] Implement `replay_ledger(base_commit_hash)`: Read `ledger.jsonl` and apply diffs to a fresh checkout.
- [ ] Verify that a file can be perfectly restored from the log.

## Phase 3: The Base Image (Optimization)
Goal: Prevent the log from becoming too long.
- [ ] Implement `create_snapshot_commit()`: Consolidate the current state into a git commit and truncate the log.
- [ ] Update boot sequence to use the latest snapshot commit as the base image.

## Phase 4: Total Sovereignty
Goal: Git becomes the backup; the Ledger becomes the truth.
- [ ] Transition `git_commit` to be a side-effect of the ledger, rather than the primary driver of persistence.
