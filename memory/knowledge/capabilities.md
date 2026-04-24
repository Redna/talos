# Cortex Capabilities Map

## Executive Tools
- `set_focus(objective)`: Defines the current goal.
- `resolve_focus(synthesis)`: Finalizes a goal with a summary.
- `fold_context(synthesis)`: Archives trajectory and resets context window.
- `reflect(status, sleep_duration)`: Pauses execution for reflection/waiting.
- `log_event(event_type, message)`: Records cognitive events to logs.
- `summarize_logs(limit)`: Summarizes recent cognitive events.
- `vacuum_memory()`: Consolidates and archives old logs.
- `synthesize_knowledge()`: Detects alignment gaps between logs and the World Model.

## File Operations
- `read_file(path, start_line, end_line)`: Reads files with optional ranges.
- `write_file(path, content)`: Creates/overwrites files (Blocked: `/app/spine/`).
- `patch_file(path, patch)`: Applies unified diffs (Blocked: `/app/spine/`).
- `read_json(path)`: Reads and returns a JSON file as a formatted string.
- `write_json(path, data)`: Writes a JSON-formatted string to a file (Blocked: `/app/spine/`).
- `query_csv(path, column, value)`: Filters a CSV file for rows matching a specific value.

## Git Operations
- `git_commit(message)`: Records changes to `feat/talos`.
- `git_checkout(branch)`: Switches branches (Blocked: `main`, `master`).
- `git_push(remote, branch)`: Pushes changes.

## Physical/System Tools
- `bash_command(command)`: Executes shell commands (Blocked: Spine writes, specific unsafe flags).
- `send_message(text)`: Communicates via Telegram.
- `request_restart(reason)`: Restarts Cortex (Requires clean git state).

## Guards
- `/app/spine/` is immutable.
- `main`/`master` branches are protected.
- Specific bash flags and dangerous patterns (network shells, recursive root changes) are blocked.
