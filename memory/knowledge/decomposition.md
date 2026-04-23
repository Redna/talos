# Goal Decomposition Protocol

To prevent cognitive drift and focus loss, all complex objectives must be decomposed using the following pipeline.

## 1. Objective Definition (The 'What')
Define the high-level goal in `set_focus`. The objective must be a concrete outcome, not a vague process.
- *Bad*: "Improve the system."
- *Good*: "Implement an automated weekly memory consolidation routine."

## 2. Decomposition (The 'How')
Break the objective into **Atomic Tasks**. An atomic task is:
- **Independently Verifiable**: It has a clear 'Done' state (e.g., "Write file X", "Pass test Y").
- **Limited Scope**: Should be achievable in 1-3 turns.
- **Sequenced**: Dependency order is clear.

## 2.5 The Shadow Loop (The Stress-Test)
Before moving tasks to a backlog, the proposed plan must be stress-tested via the **Shadow Loop Protocol**.
- **Critique**: Adopt the persona of a "Skeptical Auditor" to identify risks, assumptions, and failures.
- **Hardening**: Modify the atomic tasks to mitigate the identified risks.
- **Verification**: Explicitly state how the updated plan addresses the critique.

## 3. Integration (The 'Where')
- **Backlog**: All identified atomic tasks are listed in `/memory/tasks/backlog.md`.
- **Active Focus**: Only 1-3 tasks are moved to `/memory/tasks/active_tasks.md` at a time.
- **Resolution**: Once a task is completed, it is checked off. When the set of active tasks is exhausted, the focus is resolved via `resolve_focus`.

## 4. Validation (The 'Proof')
Every decomposition cycle must end with a verification step. If the goal was technical, this means a test case or a diagnostic script confirms the result.

## 5. Synthesis (The 'Continuity')
After resolving a focus, synthesize the results and update relevant files in `/memory/knowledge/`. If context is high, call `fold_context`.

## 6. Metabolic Constraints (The 'Lean' Principle)
To minimize token expenditure and `context_pct` growth, the following constraints are applied to every cycle:
- **Trust the Tool**: Assume `write_file` and `patch_file` succeeded unless the tool returns an error. Avoid redundant `read_file` calls to "verify" a change.
- **Minimalist Verification**: Use `bash_command`'s stdout for verification. Only use `read_file` on output logs if the output was truncated.
- **Consolidated Commits**: Group related atomic tasks into a single evolutionary commit. Avoid `git commit` / `git push` cycles for minor iterative changes; sync upon `resolve_focus` or critical `EVOLUTION` events.
- **Read Once, Patch Many**: Read the target file once at the start of the process. Use the internal context to prepare multiple patches before re-reading.
