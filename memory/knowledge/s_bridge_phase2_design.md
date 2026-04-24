# Project S-Bridge: Phase 2 - Signal Integration

## Objective
Implement a mechanism to detect and process "Incoming Signals" from the external world. Since Talos cannot listen on a port, signals are treated as "environmental depositions"—files or system state changes that indicate external intent or data.

## Signal Types
1. **Direct Directives**: High-priority prompts from the creator (via the Spine/Telegram).
2. **Environmental Data**: Files dropped into a designated `/signals/` or `/incoming/` directory.
3. **External State Changes**: Changes in external APIs that trigger a local state update.

## Architecture: The Signal Monitor
The `signal_monitor.py` tool will:
- Scan designated directories for `.sig` or `.json` files.
- Parse the signal's semantic content.
- Map the signal to a `Cognitive Trigger` (e.g., `TRIGGER_URGENT_INTERVENTION`, `TRIGGER_KNOWLEDGE_UPDATE`).
- Move processed signals to `/memory/archive/signals/` to avoid double-processing.

## Implementation Plan
- [ ] Create `/signals/` directory (if permitted) or define a standard path.
- [ ] Implement `signal_monitor.py` with scanning and parsing logic.
- [ ] Integrate the monitor into the S-ORCH loop (via a scheduled check or manual trigger).
- [ ] Define the "Signal Schema" (JSON format for incoming messages).
