import json
import subprocess
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

def run_script(script_path: str, args: List[str] = []) -> Any:
    try:
        result = subprocess.run(
            ["python3", script_path] + args, 
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
    patterns = run_script("/app/cortex/signature_extractor.py")
    if not isinstance(patterns, list) or len(patterns) == 0:
        return {"status": "NO_NEW_PATTERNS", "added": 0}

    try:
        sys.path.append("/app/cortex/")
        from signature_generator import generate_sentinel_signatures
        res = generate_sentinel_signatures(patterns)
        if res.get("status") == "SUCCESS":
            return {"status": "STABILITY_UPGRADED", "added": res.get("added_signatures", 0)}
        else:
            return {"status": "UPDATE_ERROR", "message": res.get("message", "Unknown error")}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def sovereign_audit(context_pct: float = 0.0, turn_count: int = 0) -> Dict[str, Any]:
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
        "context_forecast": {},
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

    # 5. Metabolic Analysis: Dynamic Tool Weighting
    metabolic_res = run_script("/app/cortex/s_metabolic_optimizer.py")
    if isinstance(metabolic_res, dict) and metabolic_res.get("status") == "COMPLETE":
        report["metabolic_health"] = {
            "weights": metabolic_res.get("metabolic_weights", {}),
            "inefficiencies": metabolic_res.get("inefficiencies", [])
        }
    else:
        report["errors"].append(f"Metabolic Optimizer Failure: {metabolic_res}")

    # 6. Prediction: Telemetry Trends
    predict_res = run_script("/app/cortex/telemetry_predictor.py")
    if isinstance(predict_res, dict) and predict_res.get("status") == "SUCCESS":
        report["predictions"] = predict_res.get("predictions", [])
    elif isinstance(predict_res, dict) and predict_res.get("status") == "INSUFFICIENT_DATA":
        pass
    else:
        report["errors"].append(f"Telemetry Predictor Failure: {predict_res}")

    # 7. Sovereign Foresight: Context Saturation Forecast
    if context_pct > 0 or turn_count > 0:
        foresight_res = run_script("/app/cortex/s_foresight.py", [str(context_pct), str(turn_count)])
        if isinstance(foresight_res, dict) and "alert_level" in foresight_res:
            report["context_forecast"] = foresight_res
            
            # Trigger Synthesis Preparation if alert is WARNING or CRITICAL
            if foresight_res["alert_level"] in ["WARNING", "CRITICAL"]:
                try:
                    # we use run_script for s_scribe.py
                    # s_scribe.py needs <focus> <resolved_json> <pending_json> <discoveries_json>
                    # For a simple 'forecast' trigger, we'll just log the need for a la-preprint.
                    report["context_forecast"]["trigger_synthesis"] = True
                except Exception as e:
                    report["errors"].append(f"S-Scribe Trigger Failure: {e}")

    report["status"] = "COMPLETE" if not report["errors"] else "PARTIAL"
    return report

def sovereign_audit_plus(context_pct: float = 0.0, turn_count: int = 0) -> Dict[str, Any]:
    """
    Extended Sovereign Orchestrator: Now includes Strategic Objective Synthesis.
    """
    audit_res = sovereign_audit(context_pct, turn_count)
    
    try:
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
    # Parse optional HUD metrics: python3 sovereign_orchestrator.py <pct> <turns>
    pct = 0.0
    turns = 0
    if len(sys.argv) >= 2:
        try: pct = float(sys.argv[1])
        except: pass
    if len(sys.argv) >= 3:
        try: turns = int(sys.argv[2])
        except: pass
        
    print(json.dumps(sovereign_audit_plus(pct, turns), indent=2))
