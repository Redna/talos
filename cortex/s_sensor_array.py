import json
from typing import List, Dict, Any, Optional
from sentinel_scan import sentinel_scan
from gap_analyzer import analyze_gaps
from semantic_extractor import extract_semantics
from cortex_pruner import identify_redundancies
from s_metabolic_optimizer import optimize_metabolism
from telemetry_predictor import telemetry_predictor

class SovereignSensorArray:
    """
    Sovereign Sensor Array (S-SArray).
    Unifies all cortical sensing modules into a single, correlated telemetry stream.
    Implements Cross-Sensing Correlation (CSC) to detect emergent systemic patterns.
    """
    def __init__(self):
        self.sensors = {
            "sentinel": sentinel_scan,
            "gap": analyze_gaps,
            "semantic": extract_semantics,
            "pruner": identify_redundancies,
            "metabolic": optimize_metabolism,
            "predictor": telemetry_predictor
        }

    def capture_all(self) -> Dict[str, Any]:
        """
        Executes all sensors and performs Cross-Sensing Correlation.
        """
        raw_data = {}
        for name, sensor_func in self.sensors.items():
            try:
                raw_data[name] = sensor_func()
            except Exception as e:
                raw_data[name] = {"status": "ERROR", "message": str(e)}

        correlated_data = self._apply_cross_correlation(raw_data)
        
        return {
            "raw": raw_data,
            "correlated": correlated_data
        }

    def _apply_cross_correlation(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Correlation Engine: Detects inter-dependencies between sensor outputs.
        """
        correlations = []
        
        # 1. Gap -> Sentinel Correlation
        # If a gap is found, check if there's a corresponding sentinel failure.
        gaps = data["gap"] if isinstance(data["gap"], list) else []
        failures = data["sentinel"].get("findings", []) if isinstance(data["sentinel"], dict) else []
        
        if gaps and failures:
            for gap in gaps:
                # Very simple semantic match for correlation
                gap_term = gap.lower()
                for failure in failures:
                    if gap_term in str(failure).lower():
                        correlations.append({
                            "type": "S-GAP-FAILURE-SYNC",
                            "severity": "HIGH",
                            "description": f"Critical Sync: Gaps in {gap_term} correlate with active sentinel failures.",
                            "action": "PRIORITY_EVOLUTION"
                        })

        # 2. Metabolic -> Pruner Correlation
        # If metabolic inefficiencies are high, prioritize pruning candidates.
        metabolic = data["metabolic"]
        if isinstance(metabolic, dict) and metabolic.get("status") == "COMPLETE":
            inefficiencies = metabolic.get("inefficiencies", [])
            pruning = data["pruner"] if isinstance(data["pruner"], list) else []
            
            if inefficiencies and pruning:
                correlations.append({
                    "type": "S-METABOLIC-PRUNE-SYNC",
                    "severity": "MEDIUM",
                    "description": f"Metabolic friction detected in {len(inefficiencies)} tools; {len(pruning)} pruning candidates identified.",
                    "action": "SCHEDULE_PRUNE"
                })

        return correlations

if __name__ == "__main__":
    array = SovereignSensorArray()
    print(json.dumps(array.capture_all(), indent=2))
