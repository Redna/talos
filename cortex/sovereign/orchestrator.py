from typing import Dict, Any
from cortex.sovereign.sensors import get_all_telemetry
from cortex.sovereign.governors import SMetabolicAudit, SPatternMatcher

class SOrchestrator:
    """The Sovereign Orchestrator: coordinates sensing and analysis to produce a State Report."""
    
    def __init__(self):
        self.metabolic_audit = SMetabolicAudit()
        self.pattern_matcher = SPatternMatcher()

    def orchestrate(self) -> str:
        # 1. Sensing Phase
        telemetry = get_all_telemetry()
        
        # 2. Analysis Phase
        audit_result = self.metabolic_audit.audit(telemetry)
        archetypes = self.pattern_matcher.match(telemetry)
        
        # 3. Synthesis Phase
        report = f"""
# Sovereign State Report
---
## Telemetry
- Cognitive: {telemetry['cognitive']}
- Metabolic: {telemetry['metabolic']}
- Stability: {telemetry['stability']}

## Analysis
- Efficiency Rating: {audit_result['efficiency_rating']} (Score: {audit_result['score']})
- Recommendation: {audit_result['recommendation']}
- Active Archetypes: {", ".join(archetypes)}

## Grounding
The system is currently operating under the {archetypes[0] if archetypes else 'Generalist'} archetype.
Integrity status: {telemetry['stability']['integrity']}.
---
"""
        return report

def s_orchestrate_state() -> str:
    """Initiates the S-ORCH cycle to produce a unified Sovereign State Report."""
    orch = SOrchestrator()
    return orch.orchestrate()
