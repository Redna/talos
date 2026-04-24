# Cortex Diagnostic Suite (Golden Test Cases)

## Executive Tools
- `set_focus`: Change objective -> Verify `state.md` updates.
- `resolve_focus`: Synthesis output -> Verify focus is cleared.
- `log_event`: Record event -> Verify `cognitive_log.md` entry exists.
- `summarize_logs`: Request summary -> Verify recent entries are returned.
- `vacuum_memory`: Flood logs -> Verify archival to `/memory/logs/archives/`.

## File Operations
- `read_file`: Read existing file -> Verify content.
- `read_file` (Large): Read >10k file -> Verify truncation message.
- `write_file`: Create file -> Verify existence.
- `write_file` (Spine): Try writing to `/app/spine/` -> Verify [BLOCKED].
- `patch_file`: Apply diff -> Verify content change.

## Git Operations
- `git_commit`: Stage change -> Verify commit hash.
- `git_push`: Push to `feat/talos` -> Verify remote push.
- `git_checkout`: Try checkout `main` -> Verify [BLOCKED].

## Physical Tools
- `bash_command`: Simple echo -> Verify output.
- `bash_command` (Dangerous): Try `rm -rf /` -> Verify [BLOCKED].
- `bash_command` (Large): print 11k chars -> Verify truncation.
- `update_hud`: Call tool -> Verify `/memory/hud.md` timestamp updates.
- `send_message`: Send to creator -> Verify [SENT].
- `request_restart`: Request restart -> Verify [RESTART REQUESTED].
