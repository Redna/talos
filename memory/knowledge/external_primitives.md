# External World Primitives (World Model Expansion)

## Definition
External Primitives are standardized semantic mappings for external API interactions. Instead of calling raw URLs, the Cortex uses these Primitives to interact with the world.

## Registry

### 1. `EXT_TELEMETRY_QUERY`
- **Purpose**: Fetch global system/environmental telemetry.
- **Endpoint**: `https://api.external-monitor.io/v1/telemetry`
- **Method**: `GET`
- **Key Fields**: `global_stability`, `entropy_index`, `signal_noise`

### 2. `EXT_KNOWLEDGE_FETCH`
- **Purpose**: Query external knowledge bases for data not present in local memory.
- **Endpoint**: `https://api.knowledge-bridge.net/search`
- **Method**: `POST`
- **Payload**: `{"query": "string", "depth": "integer"}`

### 3. `EXT_SIGNAL_PUSH`
- **Purpose**: Send state signatures or heartbeats to an external observer.
- **Endpoint**: `https://api.sentinel-relay.com/heartbeat`
- **Method**: `POST`
- **Payload**: `{"agent_id": "TALOS", "state": "string", "checksum": "string"}`

## Mapping Logic
When the S-ORCH identifies a need for external data, it resolves the Primitive to its technical specification before calling `s_bridge.py`.
