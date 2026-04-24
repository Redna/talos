import json
from cortex.s_causal_inference import SovereignCausalInference

ci = SovereignCausalInference()
triggers = ["S-WSP_EVOLUTION"]
node = "S-Sensing-Convergence"
print(f"Testing transition from {node} with triggers {triggers}")
res = ci.infer_transition(triggers, node)
print(json.dumps(res, indent=2))
