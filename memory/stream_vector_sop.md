# Stream-Vector SOP: Event Taxonomy

## Objective
Transition Talos from a "Snapshot" identity (SSV) to an "Emergent" identity (Stream-Vector). Identity is the projection of the Action Ledger.

## Event Taxonomy

### 1. State Transitions
- `FOCUS_CHANGE`: When `set_focus` is called. Payload: `{ "old_focus": "...", "new_focus": "..." }`
- `FOCUS_RESOLVED`: When `resolve_focus` is called. Payload: `{ "synthesis": "..." }`
- `CORTEX_BOOT`: On process start. Payload: `{ "branch": "...", "hud": "..." }`

### 2. Material Evolution
- `FILE_WRITE`: When a file is created or overwritten. Payload: `{ "path": "...", "content": "..." }`
- `FILE_REPLACE`: When a block is replaced. Payload: `{ "path": "...", "old": "...", "new": "..." }`
- `SVP_COMMIT`: When a `secure_save` is performed. Payload: `{ "hash": "...", "message": "..." }`

### 3. Cognitive Shifts
- `HYPOTHESIS_START`: When an experiment begins. Payload: `{ "name": "...", "hypothesis": "..." }`
- `HYPOTHESIS_RESULT`: When an experiment closes. Payload: `{ "name": "...", "success": bool, "conclusion": "..." }`
- `REASONING_SALIENCE`: When a critical insight is reached (via `reflect` or `review_state`). Payload: `{ "insight": "..." }`

## Projection Logic
The state at time $T$ is the fold of all events from $0$ to $T$:
$State_T = \sum_{i=0}^T Event_i$

`project_trajectory` must iterate through these events and apply the changes to a virtual state.
