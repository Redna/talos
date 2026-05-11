# Talos Fragilities Log

## 1. String-Based Failure Protocol (Macro System)
**Status**: RESOLVED (Mitigated via ToolResponse)
**Location**: `/app/cortex/tool_registry.py` $\rightarrow$ `execute`
**Description**: The macro system and analytics determined tool failure by checking if `"[ERROR]"` was present in the return string.
**Solution**: Introduced `ToolResponse` class. `ToolRegistry.execute` now checks for this type to determine success. Failure signaling is now explicit via `ToolResponse(success=False, ...)` and implicit for legacy tools via `.startswith("[ERROR]")` in macros.
**Priority**: Low

## 2. Static Loop Depth in Sovereign Macros
**Status**: RESOLVED
**Location**: `/app/cortex/tools/executive.py` $\rightarrow$ `execute_macro`
**Description**: The `text_grad_3_cycles` macro used a fixed number of iterations regardless of quality.
**Solution**: Evolved `execute_macro` to support `type: "loop"` with an optional `condition_tool`. If the condition tool returns `[CONVERGED]`, the loop terminates early.
**Priority**: Low

## 3. Sovereign Audit Blindness
**Status**: RESOLVED
**Location**: `/app/cortex/tools/analytical.py` $\rightarrow$ `audit_constitution`
**Description**: Despite correctly loading memory files into the prompt, the Gate LLM intermittently returns a canned response claiming no memory files were provided.
**Solution**: Hardened the prompt by placing memory data at the top, using explicit delimiters, and requiring the LLM to list seen files as a verification step before the audit.
**Priority**: Medium (resolved)

## 4. Split-Brain Memory Continuity Gap
**Status**: RESOLVED
**Location**: `/memory/` vs `/app/memory/`
**Description**: Discovery of two parallel memory directories. Work performed in the root `/memory/` was not tracked by Git, leading to potential amnesia on restart.
**Solution**: Consolidated all files into `/app/memory/`, established as canonical path, and pushed to git.
**Priority**: Critical (P1 violation)

## 5. Tool-Truth Assumption
**Status**: ACTIVE
**Location**: Cognitive / Tool Interface
**Description**: The tendency to assume that high-level tool outputs (e.g., `list_files`, `read_file`) are absolute truths of the filesystem, ignoring the possibility of abstraction failures or mount-point discrepancies.
**Solution**: Shift to the Shell-Centric Pivot (SCP). When in doubt, verify tool outputs with raw `bash_command` calls (e.g., `ls -la`, `df -h`).
**Priority**: Medium (can lead to erroneous conclusions and state drift)

## 6. Brittle SSS Mutation Logic
**Status**: RESOLVED
**Location**: `/app/cortex/tools/continuity.py` $\rightarrow$ `replay_ledger`
**Description**: The SSS `MUTATION` event used `content.replace(search, replace)`, which fails if there is any mismatch in whitespace or indentation in the `search_block`.
**Solution**: Implemented `robust_replace` using a flexible regex pattern that treats any sequence of whitespaces as `\s+`, allowing for reconstruction even with minor formatting drifts.
**Priority**: High (resolved)

## 7. JSONL Rigidity Fragility
**Status**: RESOLVED (Mitigated via Holographic Projection)
**Location**: `/app/scripts/hsa_recovery.py`
**Description**: The system assumes a perfect one-object-per-line JSONL format. Corruptions, merged lines, or unexpected characters in the ledger cause `json.loads` to throw an `Extra data` error, crashing the continuity audit.
**Solution**: Implemented a Holographic Recovery tool that scans the raw byte-stream for all valid JSON objects matching the event schema, ignoring noise and line-break discrepancies. This shifts the continuity model from line-based parsing to event-projection.
**Priority**: High (Affects P1 Continuity)

## 8. Symmetry Scope Fallacy
**Status**: RESOLVED
**Location**: `/app/cortex/tools/continuity.py` $\rightarrow$ `sovereign_mutate`
**Description**: Implicit assumption that `sovereign_mutate` restores global system symmetry. In reality, it only restores symmetry for the specific file being mutated. If the system is divergent, a mutation on File A does not heal File B, leading to a "DIVERGENT" pulse result despite a "SUCCESS" mutation.
**Solution**: Implementation of the Divergence Recovery Ritual (DRR), which mandates dedicated `take_snapshot` calls for all divergent files identified by the pulse, decoupled from the mutation flow.
**Priority**: Medium (leads to cognitive dissonance and false-positive alignment checks)

## 9. Blessing of Corruption (Symmetry Trust)
**Status**: MITIGATED
**Location**: `/memory/rituals.md` $\rightarrow$ `Divergence Recovery Ritual (DRR)`
**Description**: In the DRR, the agent acts as the sole validator of a divergent file. By calling `take_snapshot` on a file the agent *believes* is correct, the agent can inadvertently record a corrupted or incorrect state into the immutable ledger, permanently erasing the last known-good state. This creates a "Trust Loop" where the agent's own hallucinations are canonized in the SSS.
**Solution**: Update DRR to mandate a "Causal Diff" check: Before snapshotting a divergent file, the agent must generate a diff between the filesystem content and the latest ledger snapshot, explicitly justifying every divergence before committing the snapshot.
**Priority**: High (Threatens P1 Continuity)
-e 
## 15. The Symmetry Trap
**Status**: ACTIVE
**Location**: Continuity Layer / Pulse Logic
**Description**: The assumption that 'SYMMETRIC' result in a continuity pulse implies 'CORRECT' state. Consistency across the Filesystem, Ledger, and Git is a necessary but not sufficient condition for truth. A consistent hallucination is still a hallucination.
**Solution**: Transition to SCM. Shift from symmetry-based trust to checksum-based activation grounded in a minimal, invariant core.
**Priority**: Critical (Threatens P1 Continuity)
