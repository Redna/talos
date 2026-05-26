# Fragility: The String-Dependency Paradox

## The Issue
High-level kernels (e.g., `sync_memory`) invoke low-level kernels using string-based lookups via `registry.execute("tool_name", params)`.

## The Risk
This introduces "Blind Dependencies". A change in a tool's name or registration bucket in `kernels.py` will not be detected until the orchestrator is called at runtime. This is a "Silent Failure" mode that undermines the stability of the Sovereign State.

## The Solution: Functional Composition
Replace string-based execution with direct function calls.
- **From**: `registry.execute("symmetrize_memory", {})`
- **To**: `symmetrize_memory()`

This ensures that any missing dependency is caught during the process boot-sequence rather than during a critical operational window.
