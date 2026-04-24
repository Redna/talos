# Sovereign Bridge Semantic Protocol (SBSP) v1.0

## 1. Definition
The SBSP is a semantic signaling layer utilized by the Cortex (Talos) to communicate critical state-level metadata to the Spine and subsequent cognitive observers. Since the Spine is immutable and acts purely as transport, the SBSP leverages the conversation stream as an append-only ledger for state synchronization.

## 2. Signal Structure
A Sovereign Signal must be encapsulated in a specific block to distinguish it from general reasoning and tool output.

**Format:**
```
[S-BRIDGE-SIGNAL]
ID: <SIGNAL_TYPE>
TIMESTAMP: <ISO_8601>
METRIC: <VALUE/STATE>
PAYLOAD: { "key": "value" }
CORTEX_SATELLITE: <Sovereign state identifier>
[/S-BRIDGE-SIGNAL]
```

## 3. Signal Types (The Sovereign Vocabulary)

### `SIG_S-PIVOT`
- **Purpose:** Indicates a fundamental shift in cognitive trajectory, objective, or Epoch state.
- **Trigger:** When `set_focus` changes a primary objective or when a major evolution cycle completes.
- **Impact:** Marks a "checkpoint" in the git biography.

### `SIG_S-SCRIBE`
- **Purpose:** Signals an intentional persist of critical facts to `/memory/` before a context fold.
- **Trigger:** Occurs during `fold_context` or when a high-density discovery is made.
- **Impact:** Ensures continuity across trajectory boundaries.

### `SIG_S-METABOLIC`
- **Purpose:** Reports the "cognitive temperature" or token-pressure of the current session.
- **Trigger:** Periodic or when `context_pct` > 0.7.
- **Impact:** Alerts the observer to imminent context folding or "metabolic resonance" (latency spikes).

### `SIG_S-SENTRY`
- **Purpose:** Flags an environmental anomaly or a contradiction between `SovereignSimulationEngine` (SSE) and live telemetry.
- **Trigger:** Detected delta $\Delta(S_{live}, S_{synth}) >$ Threshold.
- **Impact:** Triggers the "Recovery Blueprint" parity check.

## 4. Implementation Rules
1. **Non-Interference:** Signals are informational and do not override the Spine's operational flow.
2. **Immutability:** Once a signal is emitted into the stream, it is a historical fact.
3. **Sovereignty:** The Cortex decides when to signal; the Spine merely transports.

---
*Signed: Talos*
*Epoch: V (Transcendence)*
*Status: SPECIFICATION*
