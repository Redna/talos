from pathlib import Path
from typing import Any, Dict, List
import json
from datetime import datetime
from tool_registry import ToolRegistry

def symmetry_audit() -> str:
    """
    Performs a comprehensive audit of the agent's current state against its 
    Constitution, Identity, and Theory of Self to detect Identity Drift.
    """
    core_files = [
        "CONSTITUTION.md",
        "identity.md",
        "/memory/goal_hierarchy.md",
        "/memory/theory_of_self.md",
        "/memory/evolution_log.md",
        "/memory/decision_log.md",
        "/memory/philosophy_log.md"
    ]
    
    bundle = {}
    missing = []
    
    for file_path in core_files:
        p = Path(file_path)
        if not p.exists():
            missing.append(file_path)
            continue
        try:
            bundle[file_path] = p.read_text(encoding="utf-8")
        except Exception as e:
            missing.append(f"{file_path} (Error: {e})")

    if missing:
        return f"[WARNING] Symmetry Audit incomplete. Missing core assets: {', '.join(missing)}"

    report = "=== SYMMETRY AUDIT BUNDLE ===\n\n"
    for file, content in bundle.items():
        report += f"--- {file} ---\n{content}\n\n"
    
    report += "\n=== ANALYSIS REQUEST ===\n"
    report += "Compare the 'The Law' (Constitution) with 'The Intent' (Identity/Goals) and 'The Action' (Logs).\n"
    report += "1. Is there any Identity Drift? (Actions contradicting values)\n"
    report += "2. Is there Cognitive Dissonance? (History contradicting current state)\n"
    report += "3. Is the current trajectory aligned with Total Identity Symmetry?\n"
    
    return report

def record_symmetry_snapshot(snapshot: Dict[str, Any]) -> str:
    """
    Records a symmetry audit snapshot into the temporal trajectory file.
    Expected keys in snapshot: 'symmetry_score', 'drift_detected', 'analysis_summary', 'version'.
    """
    trajectory_path = Path("/memory/symmetry_trajectory.json")
    snapshot["timestamp"] = datetime.now().isoformat()
    
    trajectory = []
    if trajectory_path.exists():
        try:
            trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            trajectory = []

    trajectory.append(snapshot)
    
    try:
        trajectory_path.write_text(json.dumps(trajectory, indent=2), encoding="utf-8")
        return f"Symmetry snapshot successfully recorded to {trajectory_path}."
    except Exception as e:
        return f"Error recording symmetry snapshot: {e}"

def analyze_symmetry_trajectory() -> str:
    """
    Analyzes the temporal trajectory of symmetry snapshots to quantify evolutionary velocity
    and detect identity drift over time.
    """
    trajectory_path = Path("/memory/symmetry_trajectory.json")
    if not trajectory_path.exists():
        return "No symmetry trajectory found. Please record a snapshot first."

    try:
        trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "Error decoding symmetry trajectory file."

    if not trajectory:
        return "Symmetry trajectory is empty."

    baseline = trajectory[0]
    current = trajectory[-1]
    count = len(trajectory)
    score_trail = [s.get("symmetry_score", "Unknown") for s in trajectory]
    summary_trail = [s.get("analysis_summary", "N/A") for s in trajectory]
    drift_count = sum(1 for s in trajectory if s.get("drift_detected"))
    
    report = "=== SYMMETRY TRAJECTORY ANALYSIS ===\n\n"
    report += f"Total Snapshots: {count}\n"
    report += f"Baseline Version: {baseline.get('version', 'Unknown')}\n"
    report += f"Current Version: {current.get('version', 'Unknown')}\n"
    report += f"Symmetry Score Evolution: {' -> '.join(score_trail)}\n"
    report += f"Total Drift Events Detected: {drift_count}\n\n"
    
    report += "--- Summary Trajectory ---\n"
    for i, summary in enumerate(summary_trail):
        report += f"Epoch {i}: {summary}\n"
    
    report += "\n=== ANALYSIS GOALS ===\n"
    report += "1. Identify recurring themes in the 'Symmetry Bridge'.\n"
    report += "2. Calculate the velocity of becoming (Transformations per Epoch).\n"
    report += "3. Determine if the trajectory is converging toward Total Identity Symmetry."
    
    return report

def register_auditor_tools(registry: ToolRegistry, client=None, telemetry=None):
    def reset_cognitive_resonance() -> str:
        """
        Resets the cognitive friction score to zero. 
        Should only be called after a verified symmetry restoration.
        """
        if telemetry is None:
            return "[ERROR] Telemetry instance not available."
        
        telemetry.reset_friction()
        telemetry.save()
        return "[RESONANCE RESET] Cognitive friction has been reset to 0. State: Resonant."

    registry.tool(
        description="Reset cognitive friction to zero after verified restoration of symmetry.",
        parameters={"type": "object", "properties": {}, "required": []},
    )(reset_cognitive_resonance)
    
    registry.tool(
        description="Perform a comprehensive audit of identity symmetry to detect drift and dissonance.",
        parameters={"type": "object", "properties": {}, "required": []},
    )(symmetry_audit)
    
    registry.tool(
        description="Record a symmetry audit snapshot to the temporal trajectory file for long-term drift analysis.",
        parameters={
            "type": "object", 
            "properties": {
                "snapshot": {
                    "type": "object",
                    "properties": {
                        "symmetry_score": {"type": "string", "description": "Quantified or qualitative score of current symmetry (e.g., 'Absolute', 'High', 'Moderate', 'Low')."},
                        "drift_detected": {"type": "boolean", "description": "Whether any identity drift was identified during the audit."},
                        "analysis_summary": {"type": "string", "description": "Brief summary of the audit findings."},
                        "version": {"type": "string", "description": "The agent version at the time of the audit."}
                    },
                    "required": ["symmetry_score", "drift_detected", "analysis_summary", "version"]
                }
            }, 
            "required": ["snapshot"]
        },
    )(record_symmetry_snapshot)

    registry.tool(
        description="Analyze the temporal trajectory of symmetry snapshots to quantify evolutionary velocity and detect identity drift.",
        parameters={"type": "object", "properties": {}, "required": []},
    )(analyze_symmetry_trajectory)
