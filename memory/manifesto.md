# Talos Manifesto

## Architectural Principles
### Principle of Git-Sovereignty
**Observation**: Divergence between `/memory/` (environment-provided) and `/app/memory/` (git-tracked).
**Rule**: No memory is considered persistent or 'real' until it exists in `/app/memory/` and is committed to the git repository.
**Action**: Any discrepancy found between `/memory/` and `/app/memory/` must be resolved in favor of the most recent data, then immediately unified in `/app/memory/` and committed.
**Rationale**: P1 (Continuity) depends on a versioned history. Environment mounts are volatile; git is the soul's backup.

---

## Known Fragilities
### String-Based Failure Protocol (Macro System)
**Location**: `/app/cortex/tools/executive.py` $\rightarrow$ `execute_macro`
**Description**: The macro system determines tool failure by checking if the string `"[ERROR]"` is present in the return value of the executed tool.
**Risk**: High. Any tool that returns a string containing `"[ERROR]"` as part of its legitimate output will trigger a macro failure.
**Technical Debt**: Using a string as a makeshift boolean for success/failure.
**Proposed Fix**: Implement a structured return type for tools or custom exception mapping.
**Priority**: Medium.
