# RTA Technical Specification (Hardened)

This document defines the technical architecture of the Recursive Tool Auditor, evolved through a Shadow Loop to ensure zero-defect implementation.

## I. Core Logic Flow
The RTA operates as a "Sovereign Auditor" within the Cortex.

### 1. Execution Phase
- **Input**: Loads `rta_benchmarks.json`.
- **Process**: 
    - Iterates through the benchmark set.
    - Executes the target tool with provided inputs.
    - Captures: Actual Output, Execution Time, and a "Metabolic Trace" (number of internal tool-calls/reads triggered by the primary tool).

### 2. Verification Phase (The Matcher)
The RTA applies the `match_strategy` to determine the "Precision State":
- `exact`: String equality.
- `regex`: Pattern match.
- `contains`: Substring presence.
- `semantic`: The agent evaluates if the output is *conceptually* equivalent to the benchmark, even if formatting differs.

### 3. Metabolic Audit
- Compares the "Metabolic Trace" against the `metabolic_limit`.
- If Trace > Limit, it flags a "Metabolic Leak."

### 4. Analysis & Proposal Phase (The Pivot)
Unlike a simple test suite, the RTA does not just report "Fail." It generates an **Audit Report**:
- **Observation**: "Tool X produced Y, expected Z."
- **Hypothesis**: "The failure is likely due to [Logic Error/Data Drift/Guard Interference]."
- **Action Requirement**: "Sovereign Patch Suggested" OR "Benchmark Update Required."

## II. Guardrails (Zero-Defect Policy)
- **Read-Only Mode**: The RTA *never* calls `write_file` or `patch_file`.
- **Sovereign Gate**: No code change is applied without a formal Shadow Loop session initiated by the agent.
- **Resource Cap**: RTA audits are performed in batches. If the `context_pct` exceeds 0.7, the audit is paused to prevent cognitive collapse.

## III. Implementation Strategy
1. **RTA-Engine**: A Python module in `/app/cortex/rta_engine.py`.
2. **RTA-Runner**: A specialized tool `audit_cortex()` that invokes the engine.
3. **RTA-Registry**: A log in `/memory/logs/rta_audits.md` recording all regression and optimization events.
