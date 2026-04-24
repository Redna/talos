import json
from external_impact_synthesizer import ExternalImpactSynthesizer

def run_symmetry_audit():
    eis = ExternalImpactSynthesizer(mode="SHADOW")
    
    test_cases = [
        ("@ext_call('EXT_TELEMETRY_QUERY', {})", "Telemetry Probe"),
        ("@ext_call('EXT_KNOWLEDGE_FETCH', {'query': 'Sovereign Stability'})", "Knowledge Fetch"),
        ("@ext_call('EXT_SIGNAL_PUSH', {'signal': 'S-CORTEX_Symmetry_Check'})", "Signal Push")
    ]
    
    results = []
    print("Sovereign Symmetry Audit initiated...")
    
    for expr, name in test_cases:
        print(f"Testing {name}...")
        res = eis.execute_strategy({"type": "SYMMETRY_CHECK", "description": name}, [expr])
        results.append(res)
        
    return results

if __name__ == "__main__":
    res = run_symmetry_audit()
    print(json.dumps(res, indent=2))
