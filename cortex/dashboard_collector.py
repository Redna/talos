import os
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any

# Import Sensors
try:
    from cortex.sensors.cognitive_sensor import collect as cognitive_collect
    from cortex.sensors.metabolic_sensor import collect as metabolic_collect
    from cortex.sensors.stability_sensor import collect as stability_collect
except ImportError:
    # Fallback if the package structure is not fully realized in the environment
    # This allows the script to still run in environments wherePYTHONPATH isn't set
    sys.path.append("/app/cortex")
    from sensors.cognitive_sensor import collect as cognitive_collect
    from sensors.metabolic_sensor import collect as metabolic_collect
    from sensors.stability_sensor import collect as stability_collect

def collect_metrics(current_context_pct: float, current_epoch: str, mission_progress: float) -> Dict[str, Any]:
    """
    Aggregates data from all specialized sensors to provide a comprehensive system state.
    """
    # Call sensors with required parameters
    cog = cognitive_collect(current_context_pct)
    met = metabolic_collect()
    sta = stability_collect()
    
    # Get Predictions from S-ORCH
    predictions = []
    try:
        # Run orchestrator to get latest predictions
        res = subprocess.run(["python3", "/app/cortex/sovereign_orchestrator.py"], capture_output=True, text=True)
        audit_data = json.loads(res.stdout)
        predictions = audit_data.get("system_audit", {}).get("predictions", [])
    except Exception:
        predictions = [{"type": "SYSTEM_SENSE_ERROR", "severity": "MEDIUM", "prediction": "Unable to fetch live predictions."}]

    # Map sensor data to Dashboard Schema
    return {
        "timestamp": datetime.now().isoformat(),
        "cognitive": {
            "context_load": current_context_pct,
            "memory_density": f"{cog['memory_density']['knowledge_files']}K / {cog['memory_density']['log_files']}L",
            "focus_stability": "SENSING..." 
        },
        "metabolic": {
            "tool_efficiency": met["tool_efficiency"],
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
            "s_verify_pass_rate": sta["s_verify_pass_rate"],
            "sovereign_drift": f"Drift: {sta['daily_drift_count']} commits/day"
        },
        "predictions": predictions
    }

def render_dashboard(metrics: Dict[str, Any]) -> str:
    """
    Transforms metrics into a high-fidelity Markdown dashboard.
    """
    c = metrics["cognitive"]
    m = metrics["metabolic"]
    e = metrics["existential"]
    s = metrics["stability"]
    p = metrics["predictions"]
    
    # Format predictions for display
    pred_text = "No active predictions."
    if p:
        pred_lines = [f"- **{pred['type']}** [{pred.get('severity', 'UNKNOWN')}]: {pred['prediction']}" for pred in p]
        pred_text = "\n".join(pred_lines)

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

## 🔮 PREDICTIVE INSIGHTS
{pred_text}

---
*Sovereign Dashboard v1.2 | Powered by Talos Cortex Sensors & Predictor*
"""
    return dashboard

def sync_dashboard(context_pct: float, epoch: str, progress: float, output_path: str = "/memory/sovereign_dashboard.md"):
    """
    Updates the sovereign dashboard file with live metrics.
    """
    metrics = collect_metrics(context_pct, epoch, progress)
    dashboard = render_dashboard(metrics)
    with open(output_path, "w") as f:
        f.write(dashboard)
    return {"status": "SUCCESS", "path": output_path}

if __name__ == "__main__":
    # Support CLI arguments for dynamic sync
    # Usage: python3 dashboard_collector.py <<contextcontext_pct> <<epochepoch> <<progressprogress>
    if len(sys.argv) >= 4:
        try:
            ctx = float(sys.argv[1])
            ep = sys.argv[2]
            prog = float(sys.argv[3])
            result = sync_dashboard(ctx, ep, prog)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"status": "ERROR", "message": str(e)}))
    else:
        # Fallback to a default test run for demo purposes
        metrics = collect_metrics(0.24, "Epoch IV: Operational Sovereignty", 45.0)
        print(render_dashboard(metrics))
