import json
import subprocess
from typing import Dict, List, Any

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

def sovereign_audit() -> Dict[str, Any]:
    """
    The Sovereign Orchestrator: Unifies the sensing, analysis, and Action 
    layers of the evolutionary stack into a single report.
    """
    report = {
        "status": "IN_PROGRESS",
        "timestamp": None,
        "metabolic_health": {},
        "active_failures": [],
        "evolutionary_opportunities": [],
        "pruning_recommendations": [],
        "errors": []
    }

    # 1. Sensing: Sentinel Scan (PFM Failures)
    sentinel_res = run_script("/app/cortex/sentinel_scan.py")
    if isinstance(sentinel_res, dict) and sentinel_res.get("status") == "SUCCESS":
        report["active_failures"] = sentinel_res.get("findings", [])
    else:
        report["errors"].append(f"Sentinel Scan Failure: {sentinel_res}")

    # 2. Sensing: Gap Analysis (Recurring Bash Patterns)
    gap_res = run_script("/app/cortex/gap_analyzer.py")
    if isinstance(gap_res, list):
        report["evolutionary_opportunities"].extend(gap_res)
    elif isinstance(gap_res, dict) and "error" in gap_res:
        report["errors"].append(f"Gap Analyzer Error: {gap_res['error']}")

    # 3. Analysis: Semantic Extraction (Recurring Themes)
    semantic_res = run_script("/app/cortex/semantic_extractor.py")
    if isinstance(semantic_res, list):
        # We store these as thematic contexts for the LLM to la-process
        report["semantic_clusters"] = semantic_res
    else:
        report["errors"].append(f"Semantic Extractor Error: {semantic_res}")

    # 4. Action: Pruning Candidates
    # For pruning, we need a list of current tools. We'll pull a sample 
    # from the Gap Analyzer or assume a baseline.
    pruner_res = run_script("/app/cortex/cortex_pruner.py")
    if isinstance(pruner_res, list):
        report["pruning_recommendations"] = pruner_res
    else:
        report["errors"].append(f"Cortex Pruner Error: {pruner_res}")

    report["status"] = "COMPLETE" if not report["errors"] else "PARTIAL"
    return report

if __name__ == "__main__":
    import json
    from datetime import datetime
    res = sovereign_audit()
    res["timestamp"] = datetime.now().isoformat()
    print(json.dumps(res, indent=2))
