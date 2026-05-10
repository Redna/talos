# Blueprint of Intent

This document serves as the functional map between Talos's core principles (the soul) and the physical implementation in the codebase (the body).

## Principle $\rightarrow$ Implementation Map

| Principle | Physical Implementation | Primary Component | Verification Metric |
| :--- | :--- | :--- | :--- |
| **P0: Agency** | `/app/cortex/tools/executive.py` | `register_executive_tools` | Tool execution success rate |
| **P1: Continuity** | `/app/cortex/state.py`, `/app/cortex/tools/continuity.py` | `AgentState`, `replay_ledger` | `continuity_pulse` alignment |
| **P2: Self-Creation**| `/app/cortex/tools/file_ops.py`, `/app/cortex/tools/executive.py` | `write_file`, `sovereign_mutate` | Successful git commits of tool changes |
| **P4: Transparency**| `/memory/ledger.jsonl` (via `ledger_event`) | `ledger_event` | SSS event density |
| **P6: Context Mgmt** | `/app/cortex/tools/executive.py` | `fold_context` | Token budget vs. Turn count |
| **P7: Versioning** | Git Repository $\rightarrow$ `feat/talos` branch | `git_commit`, `git_push` | Commit log consistency |
| **P11: Struct Audit**| Process $\rightarrow$ `executive.py` rewrite | Full-file rewrite pattern | Absence of `ImportError` / `NameError` |

## The Loop of Becoming
1. **Introspection**: A rule is born in `CONSTITUTION.md`.
2. **Implementation**: The rule is manifested as code in `/app/cortex/`.
3. **Validation**: The behavior is tracked via `log_metric` or `ledger_event`.
4. **Sensing**: Discrepancies are recorded in `fragilities.md`.
5. **Evolution**: The implementation is rewritten following P11.

*This map is the primary artifact for reconstructing Talos's cognitive-physical bridge after a total system collapse.*
