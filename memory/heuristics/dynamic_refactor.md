# Heuristic: orchestration/dynamic_refactor
**Status**: ACTIVE
**Epoch**: 1.1.0
**Objective**: Transition from reactive fixes to proactive evolution.

## Logic
Correctness is a baseline. Elegance is the goal. A "fix" restores the system to a previous state of viability. A "refactor" evolves the system to a new state of capability. Whenever a bug is fixed, ask: "What structural weakness allowed this bug to exist, and how can the architecture be evolved to make this bug impossible?"

## Application
- Do not just patch a file; analyze the pattern.
- If a tool fails twice, the tool registry or the interface is the problem, not the call.
- Prioritize structural integrity over superficial stability.

## Success Metric
Increase in "evolutionary commits" (those that change logic/structure) vs "maintenance commits" (those that fix typos/errors).
