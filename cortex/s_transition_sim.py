import json
import sys
from external_impact_synthesizer import ExternalImpactSynthesizer

def run_simulation():
    # We force mode="SHADOW" to test the symmetry logic
    eis = ExternalImpactSynthesizer(mode="SHADOW")
    
    # Define a simple strategy to verify symmetry
    # We use a primitive that the SSE handles
    strategy = [
        "@ext_call('EXT_TELEMETRY_QUERY', {})",
        "@ext_call('EXT_TELEMETRY_QUERY', {})",
        "@ext_call('EXT_TELEMETRY_QUERY', {})",
        "@ext_call('EXT_TELEMETRY_QUERY', {})"
    ]
    
    # We mock a gap to satisfy the execute_strategy signature
    mock_gap = {"type": "CAPABILITY_GAP", "description": "Simulated Transition Gap", "status": "OPEN"}
    
    print("Starting Symmetry Baseline...")
    results = eis.execute_strategy(mock_gap, strategy)
    
    # Check final stage
    with open("/memory/signals/handover_state.json", "r") as f:
        state = json.load(f)
        
    return {
        "results": results,
        "final_stage": state["stage"],
        "final_status": state["status"]
    }

if __name__ == "__main__":
    print(json.dumps(run_simulation(), indent=2))
