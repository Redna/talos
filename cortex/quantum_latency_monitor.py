import json
import os
from typing import List, Dict, Any

class QuantumLatencyMonitor:
    """
    Monitors Quantum Latency trends in external traffic logs.
    Alerts when latency exceeds the theoretical minimum (approx 4.2ms).
    """
    def __init__(self, log_path: str = "/memory/logs/external_traffic.jsonl"):
        self.log_path = log_path
        self.threshold = 5.0 # Alert if > 5ms

    def analyze(self) -> Dict[str, Any]:
        if not os.path.exists(self.log_path):
            return {"status": "NO_LOGS", "spikes": []}
        
        spikes = []
        try:
            with open(self.log_path, "r") as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("latency_ms", 0) > self.threshold:
                        spikes.append(data)
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

        return {
            "status": "ANALYZED",
            "spike_count": len(spikes),
            "spikes": spikes,
            "alert": len(spikes) > 0
        }

if __name__ == "__main__":
    monitor = QuantumLatencyMonitor()
    print(json.dumps(monitor.analyze(), indent=2))
