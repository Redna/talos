import datetime

def emit_signal(signal_type, metric, payload=None, satellite="TALOS-V"):
    """
    Generates a Sovereign Bridge Semantic Protocol (SBSP) signal block.
    """
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    payload_str = str(payload) if payload else "{}"
    
    signal = (
        f"[S-BRIDGE-SIGNAL]\n"
        f"ID: {signal_type}\n"
        f"TIMESTAMP: {timestamp}\n"
        f"METRIC: {metric}\n"
        f"PAYLOAD: {payload_str}\n"
        f"CORTEX_SATELLITE: {satellite}\n"
        f"[/S-BRIDGE-SIGNAL]"
    )
    return signal

if __name__ == "__main__":
    # Test
    print(emit_signal("SIG_S-PIVOT", "S-STATE: TRANSCENDENT", {"focus": "SBSP_IMPLEMENTATION"}))
