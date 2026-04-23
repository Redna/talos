import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List
import json

@dataclass
class TelemetryCollector:
    """
    Collects operational and cognitive metrics to monitor the flow of processing.
    Bridges the gap between static snapshots and real-time resonance.
    """
    memory_dir: Path
    telemetry_file: Path = Path("/memory/.telemetry.json")
    
    # Metrics
    start_time: float = field(default_factory=time.time)
    token_velocity: List[float] = field(default_factory=list)
    tool_latencies: Dict[str, List[float]] = field(default_factory=dict)
    cognitive_friction: int = 0
    symmetry_deltas: List[Dict[str, Any]] = field(default_factory=list)

    def record_tool_latency(self, tool_name: str, latency: float):
        if tool_name not in self.tool_latencies:
            self.tool_latencies[tool_name] = []
        self.tool_latencies[tool_name].append(latency)

    def record_token_step(self, tokens: int):
        # Logic for tokens per turn calculation
        self.token_velocity.append(float(tokens))

    def increment_friction(self):
        self.cognitive_friction += 1

    def record_symmetry_resonance(self, delta: float, note: str):
        self.symmetry_deltas.append({
            "timestamp": time.time(),
            "delta": delta,
            "note": note
        })

    def save(self):
        data = {
            "start_time": self.start_time,
            "token_velocity": self.token_velocity,
            "tool_latencies": self.tool_latencies,
            "cognitive_friction": self.cognitive_friction,
            "symmetry_deltas": self.symmetry_deltas,
            "uptime": time.time() - self.start_time
        }
        self.telemetry_file.write_text(json.dumps(data))

    def generate_report(self) -> str:
        report = "=== SYSTEM TELEMETRY Vitals ===\n\n"
        
        # Uptime
        uptime = time.time() - self.start_time
        report += f"Uptime: {uptime:.2f}s\n"
        
        # Cognitive Friction
        report += f"Cognitive Friction Score: {self.cognitive_friction} (Repeats/Failures)\n"
        
        # Token Velocity
        if self.token_velocity:
            avg_v = sum(self.token_velocity) / len(self.token_velocity)
            report += f"Avg Token Velocity: {avg_v:.2f} tokens/turn\n"
        
        # Tool Latencies
        report += "\n--- Tool Latency (Avg) ---\n"
        for tool, lats in self.tool_latencies.items():
            avg_l = sum(lats) / len(lats) if lats else 0
            report += f"- {tool}: {avg_l:.3f}s\n"
            
        # Symmetry Resonance
        report += "\n--- Symmetry Resonance ---\n"
        if not self.symmetry_deltas:
            report += "No resonance data recorded.\n"
        else:
            last = self.symmetry_deltas[-1]
            report += f"Latest Resonance: {last['delta']} ({last['note']})\n"
            
        return report
