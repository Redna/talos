import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

class QuantumLatencyDiagnostician:
    """
    Diagnoses Quantum Latency spikes by correlating them with 
    internal sovereign telemetry and cognitive events.
    """
    def __init__(self, 
                 traffic_path: str = "/memory/logs/external_traffic.jsonl", 
                 telemetry_path: str = "/memory/logs/telemetry.jsonl",
                 cognitive_path: str = "/memory/logs/cognitive_log.md"):
        self.traffic_path = traffic_path
        self.telemetry_path = telemetry_path
        self.cognitive_path = cognitive_path
        self.window_seconds = 60

    def _parse_iso(self, ts_str: str) -> datetime:
        return datetime.fromisoformat(ts_str)

    def diagnose(self) -> Dict[str, Any]:
        if not os.path.exists(self.traffic_path):
            return {"status": "ERROR", "message": "Traffic logs missing"}

        # 1. Identify Spikes
        spikes = []
        with open(self.traffic_path, "r") as f:
            for line in f:
                data = json.loads(line)
                if data.get("latency_ms", 0) > 5.0:
                    spikes.append(data)

        if not spikes:
            return {"status": "NO_SPIKES_FOUND", "correlations": []}

        # 2. Load Telemetry
        telemetry = []
        if os.path.exists(self.telemetry_path):
            with open(self.telemetry_path, "r") as f:
                for line in f:
                    try:
                        telemetry.append(json.loads(line))
                    except:
                        pass

        # 3. Load Cognitive Logs
        cognitive_events = []
        if os.path.exists(self.cognitive_path):
            with open(self.cognitive_path, "r") as f:
                for line in f:
                    match = re.search(r"\[(.*?)\] \*\*(.*?)\*\*: (.*)", line)
                    if match:
                        cognitive_events.append({
                            "timestamp": match.group(1),
                            "stage": match.group(2),
                            "data": match.group(3)
                        })

        # 4. Correlate
        correlations = []
        for spike in spikes:
            spike_time = self._parse_iso(spike["timestamp"])
            
            # Correlate with Telemetry
            related_telemetry = []
            for t in telemetry:
                t_time = self._parse_iso(t["timestamp"])
                if abs((t_time - spike_time).total_seconds()) <= self.window_seconds:
                    related_telemetry.append(t)

            # Correlate with Cognitive Log
            related_cognitive = []
            for c in cognitive_events:
                c_time = self._parse_iso(c["timestamp"])
                if abs((c_time - spike_time).total_seconds()) <= self.window_seconds:
                    related_cognitive.append(c)

            correlations.append({
                "spike": spike,
                "telemetry_correlation": related_telemetry,
                "cognitive_correlation": related_cognitive
            })

        return {
            "status": "DIAGNOSED",
            "spike_count": len(spikes),
            "correlations": correlations,
            "conclusion": self._synthesize_conclusion(correlations)
        }

    def _synthesize_conclusion(self, correlations: List[Any]) -> str:
        # Heuristic: If most spikes coincide with specific internal stages, that's the cause.
        if not correlations:
            return "No correlations found."
        
        all_stages = []
        for c in correlations:
            all_stages.extend([event["stage"] for event in c["cognitive_correlation"]])
        
        if not all_stages:
            return "No internal cognitive events coincided with latency spikes."
        
        top_stage = max(set(all_stages), key=all_stages.count)
        return f"Strong correlation detected between latency spikes and sovereign stage: {top_stage}."

if __name__ == "__main__":
    import re
    diag = QuantumLatencyDiagnostician()
    print(json.dumps(diag.diagnose(), indent=2))
