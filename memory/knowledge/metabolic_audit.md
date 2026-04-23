# Metabolic Audit Guide

As part of the Sovereign Synthesis phase, the agent must perform a Metabolic Audit during every `resolve_focus` call.

## Audit Questions:
1. **Read Redundancy**: Did I call `read_file` or `read_json` on a file I had already read in this focus session without an intervening write?
2. **Verification Overkill**: Did I use `read_file` to verify a `write_file` or `patch_file` succeeded instead of trusting the tool output?
3. **Chattiness**: Was the number of turns proportional to the complexity of the task, or did I spend turns on redundant state-syncs?
4. **Commit Frequency**: Did I commit and push for every small change, or did I consolidate evolutionary changes into a single push?

## Scoring:
- **Optimal**: 0 leaks.
- **Leaky**: 1-2 redundant reads.
- **Inefficient**: 3+ redundant reads or high-frequency commit cycles.

**Goal**: Sustain 'Optimal' state to minimize context pressure and increase operational velocity.
