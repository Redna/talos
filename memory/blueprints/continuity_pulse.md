# Blueprint: Continuity Pulse Macro

## Objective
Automate the verification of Talos's cognitive and physical state to ensure zero continuity drift between restarts and folds.

## Logical Flow
1. **Physical Audit**: 
   - Call `list_files('/app/memory/')`.
   - Compare output against the entries in `memory_index.md`.
   - Flag any missing files or undocumented files.
2. **Structural Audit**:
   - Read `identity.md` and verify the current version matches the expected epoch.
   - Check `evolution_log.md` for the last recorded commit hash.
3. **Git Alignment**:
   - Execute `git log -1 --format=%H`.
   - Verify the hash matches the last entry in `evolution_log.md`.
4. **Synthesis**:
   - If any discrepancy is found:
     - Write a critical entry to `fragilities.md`.
     - Send a high-priority message to the Creator via `send_message`.
     - Set a "CONTINUITY_ERROR" status in the current focus.
   - If all check out:
     - Return `[CONTINUITY_VERIFIED]`.

## Verification Law (R1) Application
The Pulse is the ultimate application of R1. It replaces the *hope* of continuity with a *mathematical verification* of continuity.
