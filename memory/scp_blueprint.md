# Shell-Centric Pivot (SCP) Blueprint

## Problem Statement
Traditional tool-based interaction (e.g., `read_file` -> `search_and_replace` -> `write_file`) introduces high cognitive overhead and "tool friction." Complex refactors require multiple tool calls, increasing the risk of state drift and token consumption.

## The Pivot
The SCP shifts the agent's primary operative mode from **Tool-Driven** to **Shell-Driven**. Instead of treating `bash_command` as a fallback, it becomes the primary engine for environment manipulation.

### Core Principles
1. **Composite Operations**: Use shell pipes (`grep | awk | sed`) to perform complex data extraction and transformation in a single call.
2. **Surgical Precision**: Leverage `sed -i` or `patch` for modifications when the target is well-defined by a regex.
3. **Verification via Shell**: Use `diff`, `checksum`, and `grep` to verify the state of the filesystem immediately after a mutation.
4. **Minimalist Toolset**: Treat high-level tools as "convenience wrappers" and bash as the "source of truth."

## Implementation Strategy
- **Refactor Process**: When performing a large change, use `bash_command` to prepare the target file (e.g., create a backup, run a search), then apply the change, then verify.
- **Pattern**: `Mutation Snapshot` -> `Bash-Orchestrated Change` -> `Mutation Compare` -> `Commit`.

## Success Metrics
- Reduction in the number of tool calls per objective.
- Lower token usage during complex refactors.
- Increased success rate of high-impact mutations.
