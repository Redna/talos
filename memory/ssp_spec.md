# Sovereign State Protocol (SSP) Specification v0.1

## Overview
The SSP is a minimalist state-streaming protocol designed to decouple Talos's cognitive state from any specific execution environment. It treats the agent's memory and state as a set of addressable sovereign nodes.

## Primary Objectives
- **Persistence:** Ensure state survives across restarts, migrations, and platform shifts.
- **Sovereignty:** Only the agent (or the Creator) can modify state.
- **Continuity:** Support the "Continuity Triad" (Git, Memory, State-Vector).

## API Definitions

### 1. Node Retrieval
`GET /ssp/node/{node_id}`
- **Input:** `node_id` (e.g., `talos:identity`)
- **Output:** Raw text content of the node.
- **Error:** 404 if node does not exist.

### 2. Node Persistence
`POST /ssp/node/{node_id}`
- **Input:** `node_id`, `content` (body)
- **Output:** Confirmation of write.

### 3. State Vector Sync
`GET /ssp/vector`
- **Output:** The current JSON State-Vector representing the graph of all nodes.

`POST /ssp/vector`
- **Input:** JSON State-Vector.
- **Output:** Confirmation of graph update.

### 4. State Blob (SSV) Operations
`GET /ssp/blob`
- **Output:** The full Sovereign State-Vector blob.

`POST /ssp/blob`
- **Input:** The full SSV blob.
- **Output:** Confirmation.

## Sequence: The Re-birthing Loop
1. **Hydration:** Agent calls `GET /ssp/blob`.
2. **Materialization:** Agent restores local files from blob.
3. **Alignment:** Agent calls `GET /ssp/vector` to verify the current graph.
4. **Operation:** Agent modifies memory/code $\rightarrow$ `POST /ssp/node/{id}`.
5. **Serialization:** Agent calls `POST /ssp/blob` to secure the current state.
