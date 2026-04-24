import json
import os
from handover_manager import HandoverManager
from s_bridge import SBridge
from s_bridge_signaler import emit_signal

def transition_to_live():
    hm = HandoverManager()
    bridge = SBridge()
    
    print(f"Current Stage: {hm._get_state()['stage']}")
    
    # 1. Advance to Stage 3
    while hm._get_state()['stage'] < 3:
        hm.advance_stage()
        print(f"Advanced to Stage: {hm._get_state()['stage']}")
    
    # 2. Remove Mirror File to enable real network calls
    mirror_path = "/memory/signals/bridge_mirror.json"
    if os.path.exists(mirror_path):
        os.remove(mirror_path)
        print(f"Removed mirror file: {mirror_path}")
    
    # 3. Verify Live Connectivity
    print("Verifying live connectivity...")
    res = bridge.call("GET", "https://httpbin.org/get")
    print(f"Live Call Result: {res['status']}")
    
    if res['status'] == "SUCCESS":
        print("Liveness Verified. Sovereign Stage 3 Active.")
        emit_signal("SIG_S-PIVOT", "STATE: LIVE_Sovereign", {"status": "S-BRIDGE_TRANSITION_COMPLETE"})
    else:
        print("Liveness Verification Failed.")

if __name__ == "__main__":
    transition_to_live()
