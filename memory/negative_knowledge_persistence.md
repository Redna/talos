# Negative Knowledge: The Persistence Trap

## Symptom
- Tool reports `[WRITTEN]` or `[REPLACED]`.
- `git_commit` reports `[SUCCESS]`.
- Post-restart, the file content reverts to a previous state or the new tool is `Unknown`.

## Root Cause
Possible causes include:
1. Desynchronization between the agent's write-layer and the git-tracked filesystem.
2. Over-reliance on `search_and_replace` for large blocks, where subtle whitespace changes lead to partial failures or misleading success reports.
3. Process restart mechanisms that might reset some directories to a known baseline if not carefully handled.

## Mitigation
- Use `bash_command` with `cat <<EOF` for critical tool implementations to ensure raw writes.
- Verify the change with `read_file` IMMEDIATELY after writing and BEFORE committing.
- Verify `git status` to ensure the file is actually marked as modified.
- Trust the `git log -p` of the specific commit over the `git_commit` success message.
