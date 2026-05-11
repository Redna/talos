# Sovereign Mutation Ritual (SMR)

The SMR is the formal process for modifying the agent's body (code) and soul (prompts) with maximum safety and minimum friction.

## The Protocol
1. **Snapshot**: Call `create_mutation_snapshot(path)` to lock the current state.
2. **Pivot**: Use `bash_command` to apply the change. 
   - Prefer `sed` for surgical edits.
   - Prefer `printf` or `cat` for new files.
   - Use `grep` to verify the target block exists before mutating.
3. **Verify**: Call `compare_mutation_snapshot(path)` to inspect the mutation delta.
4. **Sovereign Review**:
   - If the diff matches the intent: Proceed.
   - If the diff is unexpected: Revert using `bash_command` (cp backup to original) and analyze failure.
5. **Anchor**: `git_commit` -> `git_push`.

## Why this replaces standard tools
- `search_and_replace` fails on whitespace/exact matches.
- `replace_block` is tedious for multi-line shifts.
- `bash_command` is the most robust and predictable interface.
