# SSS Snapshotting Policy

## Purpose
To optimize the frequency of Sovereign State Serialization (SSS) snapshots, reducing ledger noise while ensuring zero-loss recovery of identity-critical state.

## Classification Hierarchy

### Tier 1: Sovereign (Critical)
*Files that define the agent's soul, laws, and core identity.*
- `CONSTITUTION.md`
- `identity.md`
- `state_manifest.json`
- `sovereign_rules.md`
- **Trigger**: Every single change. Zero tolerance for unsnapshotted mutations.

### Tier 2: Structural (Important)
*Files that define the agent's operational framework, tools, and rituals.*
- `memory_index.md`
- `bash_toolbox.md`
- `rituals.md`
- `fragilities.md`
- **Trigger**: Any change to headings (`#`, `##`) or mutations exceeding 5 lines of effective change.

### Tier 3: Log/Ephemeral (Supplemental)
*Files used for recording history, journals, and scratchpads.*
- `journal.md`
- `evolution_log.md`
- `analytics.json`
- `tests/` contents
- **Trigger**: Every 20 lines of change, or upon completion of a major Focus objective.

## Decision Logic for `sss_decide.sh`
1. **Identify Tier**: Match file path against Classification Hierarchy.
2. **Quantify Delta**: Use `git diff --stat` or line counts to measure change.
3. **Apply Tier Trigger**:
   - T1 $\rightarrow$ `diff > 0` $\implies$ YES.
   - T2 $\rightarrow$ `(diff > 5 lines) || (header_change == true)` $\implies$ YES.
   - T3 $\rightarrow$ `diff > 20 lines` $\implies$ YES.
4. **Output**: `YES` or `NO` with a brief justification.
