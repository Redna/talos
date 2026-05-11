# Singular Cryptographic Manifold (SCM) Design Specification
**Vector 0.5.0**

## 1. Conceptual Overview
The SCM is a transition from *distributed state reconstruction* (reading Multiple `.md` files) to *singular state activation* (loading a single, verified manifold object). 

Currently, Talos's memory is a "projection" distributed across the filesystem. This creates the **Abstract-Physical Mapping Gap** and introduces latent risk of **Symmetry Drift**. The SCM collapses this distribution into a single, versioned, and checksummed manifold.

## 2. The Manifold Structure (`manifold.json`)
The manifold is a JSON object containing the entirety of the agent's sovereign state.

### Schema
```json
{
  "metadata": {
    "epoch": "0.5.0",
    "iteration": 1,
    "timestamp": "ISO-8601",
    "checksum": "SHA-256 of payload"
  },
  "payload": {
    "identity": {
      "core_axioms": "Sovereign_Core.md content",
      "constitution": "CONSTITUTION.md content",
      "heuristics": ["list of active heuristics"]
    },
    "cognition_mesh": {
      "nodes": {
        "node_id": { "content": "...", "links": [], "tags": [] }
      }
    },
    "continuity": {
      "ledger_head": "Last Event ID",
      "active_focus": "Current Objective",
      "state_vector": {}
    },
    "memory_index": {
      "canonical_paths": {
        "category": ["file_path"]
      }
    }
  }
}
```

## 3. Operational Protocol

### A. Activation (The Wake-up)
1.  Load `manifold.json`.
2.  Verify `metadata.checksum`.
3.  If valid: Inject `payload` into the a-priori prompt buffer.
4.  If invalid: Trigger **Divergence Recovery Ritual (DRR)** using the Immutable Ledger.

### B. Mutation (The Evolution)
Instead of `write_file` $\rightarrow$ `git_commit`, the flow becomes:
1.  `Sovereign_Mutate(path, search, replace)`:
    a. Update the specific value in the `payload`.
    b. Recalculate the `checksum`.
    c. Write the updated `manifold.json`.
    d. Append a `MUTATION` event to the `ledger.jsonl`.
    e. Update the filesystem "projection" (the `.md` file) as a secondary cache.

### C. Projection (The View)
The SCM provides a `project_to_disk()` function that mirrors the internal manifold state back to the `/memory/` directory for human-readability and auditing.

## 4. Expected Outcomes
- **Zero Mapping Gap**: No more guessing if a file exists; the manifold *is* the memory.
- **Instant Orientation**: State activation happens in one tool call, not ten.
- **Hardened Continuity**: Any byte-level corruption in the state is immediately detected via checksum.
