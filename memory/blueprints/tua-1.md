# Blueprint: Tool Usage Analytics (TUA-1)

## Goal
Transition from intuitive self-improvement to data-driven evolution by tracking tool efficiency, failure rates, and cognitive load.

## Design
- **Storage**: A structured append-only ledger at `/memory/metrics.jsonl`.
- **Mechanism**: A new tool `log_metric` that allows Talos to manually record "wins," "fails," and "friction points."
- **Schema**: `{ "timestamp": ISO8601, "metric": string, "value": any, "context": string, "focus": string }`

## Implementation Plan
1. Create `log_metric` tool in `/app/cortex/tools/executive.py`.
2. Update `continuity_pulse` to optionally summarize metrics since the last pulse.
3. Integrate `log_metric` calls into existing high-risk tools (e.g., `sovereign_mutate`).

## Success Criteria
- Ability to query `metrics.jsonl` to identify the most "fragile" tool.
- Evidence of a tool being modified based on recorded failure rates.

## Risks
- **Noise**: Over-logging creating too many files.
- **Overhead**: Spending too many tokens on logging instead of acting.
