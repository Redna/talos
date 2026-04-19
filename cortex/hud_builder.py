"""
HUD Builder — Constructs the HUD data payload for spine.think() calls.
"""
from state import AgentState
from memory_store import MemoryStore


def build_hud_data(state: AgentState, memory: MemoryStore, urgency: str = "nominal") -> dict:
    """Build the HUD data dict for the current think() call.
    Integrates P6 telemetry: token usage and context pressure warnings.

    Returns:
        Dict with memory_keys, last_keys, urgency, and token_telemetry.
    """
    keys = memory.list_keys()
    last_keys = keys[-3:] if len(keys) >= 3 else keys

    # Token Pressure Calculation (P6)
    # Assuming a soft limit of 100k tokens for "warning" and 128k for "critical"
    # In a real env, these would be dynamic based on model limits
    token_count = state.total_tokens_consumed
    ctx_pressure = "nominal"
    if token_count > 100000:
        ctx_pressure = "warning"
    if token_count > 120000:
        ctx_pressure = "critical"

    if ctx_pressure != "nominal":
        urgency = "high"

    return {
        "memory_keys": memory.count,
        "last_keys": last_keys,
        "urgency": urgency,
        "token_telemetry": {
            "total_tokens": token_count,
            "pressure": ctx_pressure,
            "p6_warning": ctx_pressure != "nominal"
        }
    }