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

def sentinel_synthesis_loop() -> Dict:
    """
    Orchestrates the Sentinel Scan and the Semantic Extractor to 
    bridge the gap between immediate failure and long-term evolution.
    """
    # 1. Sentinel Scan: What just happened?
    sentinel_res = run_script("/app/cortex/sentinel_scan.py")
    
    if isinstance(sentinel_res, dict) and sentinel_res.get("status") == "ERROR":
        return sentinel_res

    findings = sentinel_res.get("findings", []) if isinstance(sentinel_res, dict) else []
    if not findings:
        return {
            "status": "NOMINAL",
            "message": "No immediate failure signatures detected. System is stable."
        }

    # 2. Semantic Extraction: Is this part of a broader pattern?
    semantic_res = run_script("/app/cortex/semantic_extractor.py")
    
    # semantic_extractor returns a LIST of clusters, not a DICT with status
    if isinstance(semantic_res, dict) and semantic_res.get("status") == "ERROR":
        return {
            "status": "PARTIAL",
            "sentinel_findings": findings,
            "extractor_error": semantic_res.get("message")
        }

    # 3. Synthesis: Cross-reference findings with semantic clusters
    synthesis = []
    for finding in findings:
        mode = finding.get("mode", "")
        directive = finding.get("directive", "")
        
        related_clusters = []
        if isinstance(semantic_res, list):
            related_clusters = [
                c for c in semantic_res 
                if isinstance(c, dict) and any(word in c.get('phrase', '').lower() for word in mode.lower().split())
            ]
        
        synthesis.append({
            "trigger_mode": mode,
            "immediate_directive": directive,
            "semantic_context": related_clusters,
            "proposal": "Consider whether this failure warrants a new CPR primitive to permanently anchor the correct behavior."
        })

    return {
        "status": "CRITICAL",
        "synthesis": synthesis,
        "summary": f"Detected {len(findings)} failure(s) with accompanying semantic analysis."
    }

if __name__ == "__main__":
    print(json.dumps(sentinel_synthesis_loop(), indent=2))
