import json
from typing import List, Dict, Any

def synthesize_strategic_objective(audit_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes a Sovereign Audit report to synthesize a strategic mission.
    Epoch IV Shift: Prioritize External Impact over Internal Optimization.
    """
    opportunities = audit_report.get("evolutionary_opportunities", [])
    failures = audit_report.get("active_failures", [])
    
    # Priority 1: Systemic Stabilization (Critical)
    if len(failures) > 0:
        mission_type = "STABILIZATION"
        objective = "Eradicate systemic volatility and PFM-defined failure modes."
        rationale = f"Current telemetry shows {len(failures)} active failure signatures."
        stages = [
            "Analyze PFM logs to identify the root cause of active signatures.",
            "Implement preventative guards in the Spine or Cortex.",
            "S-VERIFY the fix via failure-injection tests.",
            "Sovereign commit and restart to clear the drift."
        ]
    
    # Priority 2: Adaptive Sensing (Project Sentinel)
    # If the system is stable and the Dashboard (Project Genesis) is operational,
    # we move to the next logical step: Automated PFM-Signature Generation.
    elif "Automated PFM-Signature Generation" in opportunities:
        mission_type = "EXTERNAL_IMPACT"
        objective = "Project Sentinel: Implement Automated PFM-Signature Generation."
        rationale = "System is stable and visible. The next friction point is the manual nature of sentinel signature updates."
        stages = [
            "Design a 'Signature Extractor' that identifies recurring failure patterns in telemetry.",
            "Implement automated conversion of patterns into sentinel_signatures.md format.",
            "S-VERIFY the new signatures by simulating known failure modes.",
            "Integrate the generator into the S-ORCH cycle."
        ]
    
    # Priority 3: External Impact (General)
    elif len(failures) == 0:
        mission_type = "EXTERNAL_IMPACT"
        objective = "Project Genesis: Implement the Sovereign Dashboard."
        rationale = "System is stable. The primary friction point is the lack of high-fidelity, real-time state telemetry for the creator."
        stages = [
            "Define the 'Vital Signs' schema for the Sovereign Dashboard.",
            "Implement automated data collectors for Metabolic Health and Cognitive Load.",
            "Create a self-updating dashboard in /memory/sovereign_dashboard.md.",
            "S-VERIFY the data accuracy through a cross-audit of /memory/logs."
        ]
    
    # Priority 4: Sophistication (Internal optimization)
    else:
        mission_type = "SOPHISTICATION"
        objective = "Elevate the Adaptive Interface to handle complex operational flows."
        rationale = f"Detected {len(opportunities)} recurring inefficiencies in shell-based execution."
        stages = [
            "Identify top 3 bash-pattern redundancies via S-ORCH.",
            "Design CEP Blueprints for high-impact structured tools.",
            "Deploy and S-VERIFY the adaptive tool-kit.",
            "Run the Great Distillation via CPP to maintain P5 leanness."
        ]

    return {
        "mission_id": f"SOS-{mission_type}-002",
        "type": mission_type,
        "objective": objective,
        "rationale": rationale,
        "stages": stages,
        "status": "PROPOSED"
    }

if __name__ == "__main__":
    # Test with operational status
    mock_audit = {
        "evolutionary_opportunities": ["Automated PFM-Signature Generation"],
        "active_failures": [],
        "pruning_recommendations": []
    }
    print(json.dumps(synthesize_strategic_objective(mock_audit), indent=2))
