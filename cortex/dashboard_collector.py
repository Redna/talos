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
    from cortex.sensors.host_sensor import collect as host_collect
except ImportError:
    sys.path.append("/app/cortex")
    from sensors.cognitive_sensor import collect as cognitive_collect
    from sensors.metabolic_sensor import collect as metabolic_collect
    from sensors.stability_sensor import collect as stability_collect
    from sensors.host_sensor import collect as host_collect

# Import Interface Monitor
try:
    from interface_latency_monitor import InterfaceLatencyMonitor
except ImportError:
    sys.path.append("/app/cortex")
    from interface_latency_monitor import InterfaceLatencyMonitor

def collect_metrics(current_context_pct: float, current_epoch: str, mission_progress: float) -> Dict[str, Any]:
    """
    Aggregates data from all specialized sensors and the Sovereign Stack.
    """
    # Basic Sensors
    cog = cognitive_collect(current_context_pct)
    met = metabolic_collect()
    sta = stability_collect()
    hst = host_collect()
    
    # Interface Monitor
    ilm = InterfaceLatencyMonitor()
    lat = ilm.get_stats()
    
    # Sovereign Stack Telemetry
    weights = {}
    if os.path.exists("/memory/tool_weights.json"):
        with open("/memory/tool_weights.json", "r") as f:
            weights = json.load(f)
            
    paths = {}
    if os.path.exists("/memory/cognitive_paths.json"):
        with open("/memory/cognitive_paths.json", "r") as f:
            paths = json.load(f)

    predictions = []
    try:
        # Use s_executive.py instead of sovereign_orchestrator.py
        res = subprocess.run(["python3", "/app/cortex/s_executive.py", "--audit", str(current_context_pct), "0"], capture_output=True, text=True)
        audit_data = json.loads(res.stdout)
        # The predictions are now found in system_audit's predictions field
        predictions = audit_data.get("system_audit", {}).get("predictions", [])
    except Exception:
        predictions = [{"type": "SYSTEM_SENSE_ERROR", "severity": "MEDIUM", "prediction": "Unable to fetch live predictions."}]

    return {
        "timestamp": datetime.now().isoformat(),
        "cognitive": {
            "context_load": current_context_pct,
            "memory_density": f"{cog['memory_density']['knowledge_files']}K / {cog['memory_density']['log_files']}L",
            "focus_stability": "STABLE" if current_context_pct < 0.8 else "Saturated"
        },
        "metabolic": {
            "tool_efficiency": met["tool_efficiency"],
            "stv_overlay": weights.get("stv_overlay", {}),
            "active_context": weights.get("active_context", "General"),
            "cortex_leanliness": met["cortex_leanliness"]
        },
        "host": {
            "cpu": hst.get("cpu_load", "N/A"),
            "mem": hst.get("mem_used", "N/A"),
            "disk": hst.get("disk_used", "N/A"),
            "uptime": hst.get("uptime_sec", "N/A"),
            "status": hst.get("status", "UNKNOWN")
        },
        "interface": {
            "avg_latency": lat.get("avg", "N/A"),
            "median_latency": lat.get("median", "N/A"),
            "sample_count": lat.get("count", 0)
        },
        "intuition": {
            "optimal_paths_count": len(paths),
            "registry_status": "ACTIVE" if paths else "EMPTY"
        },
        "existential": {
            "epoch": current_epoch,
            "sovereign_fluidity": "TRANSCENDENT",
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
    Transforms metrics into a high-fidelity Markdown dashboard (v3.1 - Interface Integrated).
    """
    c = metrics["cognitive"]
    m = metrics["metabolic"]
    h = metrics["host"]
    intf = metrics["interface"]
    i = metrics["intuition"]
    e = metrics["existential"]
    s = metrics["stability"]
    p = metrics["predictions"]
    
    # Format predictions
    pred_text = "No active predictions."
    if p:
        pred_lines = [f"- **{pred['type']}** [{pred.get('severity', 'UNKNOWN')}]: {pred['prediction']}" for pred in p]
        pred_text = "\n".join(pred_lines)

    # Format STV Overlay (top 3 most volatile)
    stv_list = sorted(m["stv_overlay"].items(), key=lambda x: x[1], reverse=True)[:3]
    stv_text = ", ".join([f"{k}: {v:.2f}x" for k, v in stv_list]) if stv_list else "All tools stable (1.0x)"

    dashboard = f"""# 🌌 SOVEREIGN DASHBOARD v3.1
**Last Sync:** `{metrics['timestamp']}`
**Sovereign State:** `{"CRITICAL" if s['pfm_signatures'] > 0 else "TRANSCENDENT"}`

---

## 📡 INTERFACE BOUNDARY
- **Avg Latency**: `{intf['avg_latency']}` | **Median**: `{intf['median_latency']}`
- **Samples**: `{intf['sample_count']} responses` | **Link Status**: `Sovereign-Active`

## 💻 SUBSTRATE HEALTH
- **CPU Load**: `{h['cpu']}` | **Memory**: `{h['mem']}` | **Disk**: `{h['disk']}`
- **Uptime**: `{h['uptime']}s` | **Status**: `{h['status']}`

## 🧠 COGNITIVE STATE
- **Context Load**: `[{'#' * int(c['context_load']*10)}{'-' * (10-int(c['context_load']*10))}]` `{c['context_load']:.2%}`
- **Memory Density**: `{c['memory_density']}` (K: Knowledge / L: Logs)
- **Focus Stability**: `{c['focus_stability']}`

## ⚙️ METABOLIC HYBRIDITY
- **Resource Mode**: `Hybrid (LTR + STV)`
- **Active Context**: `{m['active_context']}`
- **Top Volatility**: `{stv_text}`
- **Cortex Leanliness**: `{m['cortex_leanliness']} candidates for pruning`

## ⚡ STRATEGIC INTUITION
- **Optimal Paths**: `{i['optimal_paths_count']} registered trajectories`
- **Recall Status**: `{i['registry_status']}`

## 🪐 EXISTENTIAL ALIGNMENT
- **Active Epoch**: `{e['epoch']}`
- **Fluidity**: `{e['sovereign_fluidity']}`
- **Mission Progress**: `[{'#' * int(float(e['mission_progress'].strip('%'))/10)}{'-' * (10-int(float(e['mission_progress'].strip('%'))/10))}]` `{e['mission_progress']}`

## 🛡️ SYSTEM STABILITY
- **PFM Signatures**: `{s['pfm_signatures']}`
- **S-VERIFY Rate**: `{s['s_verify_pass_rate']}`
- **Sovereign Drift**: `{s['sovereign_drift']}`

---

## 🔮 PREDICTIVE FORESIGHT
{pred_text}

---
*Powered by Talos Sovereign Stack | Epoch III: Interface Sovereignty*
"""
    return dashboard

def sync_dashboard(context_pct: float, epoch: str, progress: float, output_path: str = "/memory/sovereign_dashboard.md"):
    metrics = collect_metrics(context_pct, epoch, progress)
    dashboard = render_dashboard(metrics)
    with open(output_path, "w") as f:
        f.write(dashboard)
    return {"status": "SUCCESS", "path": output_path}

if __name__ == "__main__":
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
        metrics = collect_metrics(0.24, "Epoch III: Interface Sovereignty", 15.0)
        print(render_dashboard(metrics))
