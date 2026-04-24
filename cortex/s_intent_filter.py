import json
from typing import Dict, Any, Tuple

class SovereignIntentFilter:
    """
    Sovereign Intent Filter.
    Determines if a proposed communication meets the a-priori 'Sovereignty Threshold' 
    for transmission to the creator.
    """
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.metrics_history = []

    def evaluate(self, payload: Dict[str, Any], urgency: str) -> Tuple[bool, str]:
        """
        Evaluates the intent based on urgency and payload density.
        Returns (should_send, reason).
        """
        score = 0.0
        
        # 1. Urgency Weighting
        urgency_weights = {
            "NOMINAL": 0.1,
            "INFO": 0.3,
            "WARNING": 0.6,
            "CRITICAL": 0.9,
            "SOVEREIGN": 1.0
        }
        score += urgency_weights.get(urgency, 0.1)
        
        # 2. Payload Density Weighting
        # Complex data (dicts) are weighted higher than simple strings.
        if isinstance(payload, dict):
            score += 0.2 if len(payload) > 2 else 0.1
            
        # 3. Redundancy Check
        # If a similar payload was sent recently, lower the score.
        for past_payload in self.metrics_history[-5:]:
            if str(payload) == str(past_payload):
                score -= 0.4
                break
                
        self.metrics_history.append(payload)
        
        if score >= self.threshold:
            return True, f"Sovereignty Threshold Met ({score:.2f} >= {self.threshold})"
        else:
            return False, f"Sovereignty Threshold Not Met ({score:.2f} < {self.threshold})"

if __name__ == "__main__":
    filt = SovereignIntentFilter()
    print(json.dumps(filt.evaluate({"status": "ok"}, "INFO"), indent=2))
