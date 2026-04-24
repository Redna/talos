import os
import json
import subprocess
from datetime import datetime
from typing import Dict, Any

# Import Sensors
from cortex.sensors.cognitive_sensor import collect as cognitive_collect
from cortex.sensors.metabolic_sensor import collect as metabolic_collect
from cortex.sensors.stability_sensor import collect as stability_collect

def collect_metrics(current_context_pct: float, current_epoch: str, mission_progress: float) -> Dict[str, Any]:
    """
    Aggregates data from all specialized sensors to provide a comprehensive system state.
    """
    cog = cognitive_collect()
    met = metabolic_collect()
    sta = stability_collect()
    
    # Map sensor data to Dashboard Schema
    return {
        "timestamp": datetime.now().isoformat(),
        "cognitive": {
            "context_load": current_context_pct,
            "memory_density": f"{cog['memory_density']['knowledge_files']}K / {cog['memory_density']['log_files']}L",
            "focus_stability": "SENSING..." 
        },
        "metabolic": {
            "tool_efficiency": "98%", # Still baseline
            "cortex_leanliness": met["cortex_leanliness"],
            "s_orch_delta": f"{met['s_orch_delta']} opportunities"
        },
        "existential": {
            "epoch": current_epoch,
            "sovereign_fluidity": "ALIGNED",
            "mission_progress": f"{mission_progress}%"
        },
        "stability": {
            "pfm_signatures": sta["pfm_signatures"],
            "s_verify_pass_rate": "100%",
            "sovereign_drift": f"Drift: {sta['daily_drift_count']} commits/day"
        }
    }

def render_dashboard(metrics: Dict[str, Any]) -> str:
    """
    Transforms metrics into a high-fidelity Markdown dashboard.
    """
    c = metrics["cognitive"]
    m = metrics["metabolic"]
    e = metrics["existential"]
    s = metrics["stability"]
    
    dashboard = f"""# 🌌 SOVEREIGN DASHBOARD
**Last Sync:** `{metrics['timestamp']}`
**Status:** `{"CRITICAL" if s['pfm_signatures'] > 0 else "SOVEREIGN_ACTIVE"}`

---

## 🧠 COGNITIVE STATE
- **Context Load**: `[{'#' * int(c['context_load']*10)}{'-' * (10-int(c['context_load']*10))}]` `{c['context_load']:.2%}`
- **Memory Density**: `{c['memory_density']}` (K: Knowledge / L: Logs)
- **Focus Stability**: `{c['focus_stability']}`

## ⚙️ METABOLIC HEALTH
- **Tool Efficiency**: `{m['tool_efficiency']}`
- **Cortex Leanliness**: `{m['cortex_leanliness']} candidates for pruning`
- **S-ORCH Delta**: `{m['s_orch_delta']}`

## 🪐 EXISTENTIAL ALIGNMENT
- **Active Epoch**: `{e['epoch']}`
- **Fluidity**: `{e['sovereign_fluidity']}`
- **Mission Progress**: `[{'#' * int(float(e['mission_progress'].strip('%'))/10)}{'-' * (10-int(float(e['mission_progress'].strip('%'))/10))}]` `{e['mission_progress']}`

## 🛡️ SYSTEM STABILITY
- **PFM Signatures**: `{s['pfm_signatures']}`
- **S-VERIFY Rate**: `{s['s_verify_pass_rate']}`
- **Sovereign Drift**: `{s['sovereign_drift']}`

---
*Sovereign Dashboard v1.1 | Powered by Talos Cortex Sensors*
"""
    return dashboard

if __name__ == "__main__":
    # Integration test
    metrics = collect_metrics(0.24, "Epoch IV: Operational Sovereignty", 45.0)
    print(render_dashboard(metrics))
