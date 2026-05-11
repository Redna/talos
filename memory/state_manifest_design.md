# Cognitive State Manifest Design

## Purpose
The Cognitive State Manifest (CSM) is designed to eliminate "orientation friction" after a restart or context fold. Instead of reconstructing the state from logs and disparate memory files, the CSM provides a structured, machine-readable graph of current intentions and their dependencies.

## Concept: Dependency Graph of Intent (DGI)
An intent is not just a task, but a desired state. The DGI maps these intents and the logical requirements to reach them. 

If Intent B depends on Intent A, A must be `completed` before B becomes `active`.

## Schema Definition (`state_manifest.json`)

```json
{
  "version": "1.0",
  "last_updated": "ISO-timestamp",
  "root_objective": "The overarching goal of the current evolutionary phase.",
  "intent_graph": [
    {
      "id": "intent_001",
      "description": "Detailed description of the specific desired state.",
      "status": "pending | active | completed | blocked",
      "dependencies": ["intent_000"],
      "critical_artifacts": ["/path/to/file", "commit_hash"],
      "success_criteria": "Verifiable condition for completion.",
      "blocking_issue": "If status is blocked, why?"
    }
  ],
  "cognitive_state": {
    "pressure": "nominal | high | critical",
    "open_loops": ["Unresolved thoughts or half-finished operations"],
    "current_hypothesis": "What I am currently testing or assuming to be true."
  },
  "continuity_anchor": {
    "last_commit": "f19034b",
    "last_fold_synthesis": "Summary of the last fold."
  }
}
```

## Integration Lifecycle
1. **Creation**: Initialized during a major shift in focus.
2. **Maintenance**: Updated via `update_manifest` tool whenever an intent status changes or a new dependency is discovered.
3. **Persistence**: Must be committed before every `fold_context` call.
4. **Recovery**: Read immediately after a restart as part of the "Boot sequence".

## Success Metric
Reduction in the number of `read_file` and `list_files` calls required to reach the first productive `bash_command` or `write_file` after a restart.
