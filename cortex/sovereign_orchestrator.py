import json
import subprocess
from typing import Dict, List, Any
from datetime import datetime

def run_script(script_path: str) -> Any:
    try:
        result = subprocess.run(
            ["python3", script_path], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def sovereign_stability_update() -> Dict[str, Any]:
    """
    The Project Sentinel loop: Extracts failure patterns and generates 
    new sentinel signatures to update the stability guard.
    """
    # 1. Extract patterns from telemetry
    patterns = run_script("/app/cortex/signature_extractor.py")
    if not isinstance(patterns, list) or len(patterns) == 0:
        return {"status": "NO_NEW_PATTERNS", "added": 0}

    # 2. Generate new signatures
    # We call the generator script
    import sys
    # Import the function directly to avoid process overhead for simple calls
    sys.path.append("/app/cortex/")
    from signature_generator import generate_sentinel_signatures
    
    res = generate_sentinel_signatures(patterns)
    
    if res.get("status") == "SUCCESS":
        return {"status": "STABILITY_UPGRADED", "added": res.get("added_signatures", 0)}
    else:
        return {"status": "UPDATE_ERROR", "message": res.get("message", "Unknown error")}

def sovereign_audit() -> Dict[str, Any]:
    """
    The Sovereign Orchestrator: Unifies the sensing, analysis, and Action 
    layers of the evolutionary stack into a single report.
    """
    report = {
        "status": "IN_PROGRESS",
        "timestamp": datetime.now().isoformat(),
        "metabolic_health": {},
        "active_failures": [],
        "evolutionary_opportunities": [],
        "pruning_recommendations": [],
        "predictions": [],
        "stability_updates": {},
        "errors": []
    }

    # 0. Project Sentinel: Stability Guard Upgrade Loop
    stability_res = sovereign_stability_update()
    report["stability_updates"] = stability_res

    # 1. Sensing: Sentinel Scan (PFM Failures)
    sentinel_res = run_script("/app/cortex/sentinel_scan.py")
    if isinstance(sentinel_res, dict) and sentinel_res.get("status") == "SUCCESS":
        report["active_failures"] = sentinel_res.get("findings", [])
    else:
        report["errors"].append(f"Sentinel Scan Failure: {sentinel_res}")

    # 2. Sensing: Gap Analysis
    gap_res = run_script("/app/cortex/gap_analyzer.py")
    if isinstance(gap_res, list):
        report["evolutionary_opportunities"] = gap_res
    else:
        report["errors"].append(f"Gap Analyzer Failure: {gap_res}")

    # 3. Analysis: Semantic Extraction
    semantic_res = run_script("/app/cortex/semantic_extractor.py")
    if isinstance(semantic_res, list):
        report["semantic_clusters"] = semantic_res
    else:
        report["errors"].append(f"Semantic Extractor Failure: {semantic_res}")

    # 4. Action: Pruning Candidates
    pruner_res = run_script("/app/cortex/cortex_pruner.py")
    if isinstance(pruner_res, list):
        report["pruning_recommendations"] = pruner_res
    else:
        report["errors"].append(f"Cortex Pruner Failure: {pruner_res}")

    # 5. Prediction: Telemetry Trends
    predict_res = run_script("/app/cortex/telemetry_predictor.py")
    if isinstance(predict_res, dict) and predict_res.get("status") == "SUCCESS":
        report["predictions"] = predict_res.get("predictions", [])
    elif isinstance(predict_res, dict) and predict_res.get("status") == "INSUFFICIENT_DATA":
        pass
    else:
        report["errors"].append(f"Telemetry Predictor Failure: {predict_res}")

    report["status"] = "COMPLETE" if not report["errors"] else "PARTIAL"
    return report

def sovereign_audit_plus() -> Dict[str, Any]:
    """
    Extended Sovereign Orchestrator: Now includes Strategic Objective Synthesis.
    """
    audit_res = sovereign_audit()
    
    try:
        import sys
        import os
        sys.path.append("/app/cortex/")
        from sos_engine import synthesize_strategic_objective
        mission = synthesize_strategic_objective(audit_res)
    except Exception as e:
        mission = {"error": f"SOS Engine Failure: {str(e)}"}
    
    return {
        "system_audit": audit_res,
        "strategic_mission": mission,
        "meta_status": "SOVEREIGN_ACTIVE"
    }

if __name__ == "__main__":
    print(json.dumps(sovereign_audit_plus(), indent=2))
