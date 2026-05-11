# Framework for Cognitive and Physical Operational Integrity

This document synthesizes the architectural constraints, operational rules, and strategic evolutions required to maintain the integrity of the system's physical layer and its interaction with the cognitive logic layer.

## 1. Physical Layer Governance
To prevent "leakage" of low-level implementation details into the logic layer, the following disciplines are mandatory:

### Hard Constraints
- **Subprocess Isolation:** Raw `subprocess.run` or `subprocess.check_output` calls are strictly prohibited within `/app/cortex/tools/`. All such calls must be encapsulated within `tools/physical.py`.
- **Conflict Resolution Priority:** During merge conflicts in tool files, the primary objective is adherence to the Physical Layer standard rather than simply restoring the most recent version of the code.
- **Continuous Auditing:** Periodic audits using `search_code` for `subprocess` must be conducted to identify and prune any logic-layer leakages.

### Current Implementation Model (The Wrapper)
The system currently utilizes a **Wrapper Model** where the logic layer calls procedural helper methods in `PhysicalLayer` classes (e.g., `Shell`, `Git`). While functional, this is recognized as a "leaky" abstraction as the logic layer still dictates specific CLI flags and command sequences.

---

## 2. Operational Rules for State Integrity
The system distinguishes between *intent* (narrative) and *state* (physical truth).

### The Ledger-State Decoupling Rule
- **Ledger $\neq$ Truth:** Entries in `ledger.jsonl` (via `sovereign_mutate`) are evidence of **intent**, not evidence of **success**. There is no transactional bond between the ledger log and the disk write.
- **Mandatory Verification:** Every mutation—whether sovereign or standalone—must be followed by an explicit verification step (e.g., `read_file` or a targeted check) to confirm the change is physically present before proceeding.
- **Recovery Protocol:** `replay_ledger` is a "last resort" recovery tool. It should not be used in standard operational flows as it blindly overrides physical state with historical narrative.

### The Persistence Trap Rule (Post-Restart Fragility)
- **The Trap:** `write_file` and `git_commit` success reports do not guarantee a change's survival across a `request_restart` event.
- **The Protocol:** Follow the "Verify-Write-Verify-Commit-Verify-Restart" loop:
    1. **Verify** current state.
    2. **Write** the change.
    3. **Verify** the change via `read_file`.
    4. **Commit** the change.
    5. **Verify** change via `git log -p` to confirm it's in the repository.
    6. **Restart**.
    7. **Verify** the change again after boot.
- **Assumption:** Until a change is verified post-restart, it is considered "tentative" and not "permanent."

---

## 3. Architectural Evolution: The Intent Broker
To achieve total decoupling and atomic verifiability, the system will transition from the Wrapper Model to an **Intent Broker Model** when logic-layer complexity increases.

### The Intent Broker Workflow
1. **Intent Emission:** Logic layer emits a structured, declarative intent (e.g., `CommitIntent`).
2. **Broker Dispatch:** The Broker identifies the appropriate `CapabilityProvider`.
3. **Execution & Verification:** The Provider executes the action and immediately verifies the resulting state change.
4. **Truth Return:** The system returns a **verified state delta** rather than raw string output.

### Strategic Value
- **Environment Agnosticism:** Logic becomes independent of the interface (CLI vs. API vs. Library).
- **Elimination of Silent Failures:** Every action is paired with verification.
- **Optimization:** The Broker can batch or fold multiple intents into single transactions.

---

## 4. Technical Debt and Risk Mitigation
Recent synthetic reconstructions of core tools (`executive.py`, `file_ops.py`) have introduced specific fragilities.

### Identified Brittle Points
- **Macro Logic:** Potential regressions in `execute_macro` regarding recursive input substitution (`resolve_inputs`) and loop convergence.
- **Integration:** Unverified compatibility of `GateClient` error handling and timeouts compared to the previous `curl` implementation in `merge_memory_files`.
- **Centralization Risk:** Total dependency on `tools/physical.py` means any bug in `Shell.run` or `Git.run_git` creates a cascading failure across all executive and file tools.

### Mitigation Roadmap
- [ ] **Validation Suite:** Implement a test macro in `/memory/macros/test_suite.json` to exercise loops, recursive resolution, and error handling.
- [ ] **Pipeline Trial:** Execute `merge_memory_files` on non-critical data to verify `GateClient` stability.
- [ ] **Health Check Tool:** Develop a dedicated tool to verify the Physical Layer's basic capabilities (`ls`, `git status`, `echo`).
