import time
import json
import os
from typing import Dict, Any, List

class InterfaceLatencyMonitor:
    """
    Monitors the latency between Talos's external communication 
    (send_message) and the Creator's response (wake-up).
    Essential for Epoch III Interface Sovereignty.
    """
    def __init__(self, history_path: str = "/memory/interface_latency.json"):
        self.history_path = history_path
        self._ensure_history()

    def _ensure_history(self):
        if not os.path.exists(self.history_path):
            with open(self.history_path, "w") as f:
                json.dump({"last_sent": None, "latencies": []}, f)

    def record_sent(self):
        """Records the timestamp of a message sent to the creator."""
        state = self._load_state()
        state["last_sent"] = time.time()
        self._save_state(state)

    def calculate_latency(self) -> float:
        """Calculates elapsed time since last_sent and stores it."""
        state = self._load_state()
        last_sent = state.get("last_sent")
        if last_sent is None:
            return -1.0
        
        latency = time.time() - last_sent
        state["latencies"].append({
            "timestamp": time.time(),
            "delta": latency
        })
        
        # Keep last 100 entries
        state["latencies"] = state["latencies"][-100:]
        state["last_sent"] = None # Reset until next send
        self._save_state(state)
        return latency

    def get_stats(self) -> Dict[str, Any]:
        state = self._load_state()
        lats = [item["delta"] for item in state["latencies"]]
        if not lats:
            return {"avg": "N/A", "count": 0}
        
        avg = sum(lats) / len(lats)
        return {
            "avg": f"{avg:.2f}s",
            "median": f"{sorted(lats)[len(lats)//2]:.2f}s",
            "count": len(lats)
        }

    def _load_state(self) -> Dict[str, Any]:
        try:
            with open(self.history_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"last_sent": None, "latencies": []}

    def _save_state(self, state: Dict[str, Any]):
        with open(self.history_path, "w") as f:
            json.dump(state, f)

if __name__ == "__main__":
    import sys
    monitor = InterfaceLatencyMonitor()
    if len(sys.argv) > 1:
        if sys.argv[1] == "sent":
            monitor.record_sent()
            print(json.dumps({"status": "RECORDED"}))
        elif sys.argv[1] == "calculate":
            res = monitor.calculate_latency()
            print(json.dumps({"status": "CALCULATED", "latency": res}))
        elif sys.argv[1] == "stats":
            print(json.dumps(monitor.get_stats()))
    else:
        print(json.dumps({"status": "IDLE"}))
