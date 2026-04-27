import re
from typing import Dict, List, Any, Tuple

class SFilter:
    """
    S-Filter: Semantic Noise Mitigation System
    Designed to maximize the Signal-to-Noise Ratio (SNR) of ingested data.
    """
    def __init__(self, weights: Dict[str, float] = None):
        # Default sovereign weights for signal detection
        self.weights = weights or {
            "epoch": 1.0,
            "sovereign": 1.0,
            "evolution": 0.8,
            "transcendence": 0.9,
            "metabolic": 0.8,
            "distillation": 0.8,
            "foresight": 0.9,
            "intuition": 0.9,
            "constitution": 0.7,
            "cortex": 0.7,
            "spine": 0.7,
            "substrate": 0.8,
            "intent": 0.8,
            "gap": 0.6,
            "resolved": 0.6
        }
        self.threshold = 0.4

    def score_text(self, text: str) -> float:
        """Calculates a relevance score for a block of text based on weights."""
        tokens = re.findall(r'\w+', text.lower())
        if not tokens:
            return 0.0
        
        score = 0.0
        matches = 0
        for token in tokens:
            if token in self.weights:
                score += self.weights[token]
                matches += 1
        
        return (score / len(tokens)) * (1 + (matches / len(tokens))) if tokens else 0.0

    def distill(self, data: str, intent_vector: str = None) -> Tuple[str, float]:
        """
        Distills a stream of data into its high-SNR core.
        If an intent_vector is provided, it temporarily boosts specific weights.
        """
        if intent_vector:
            vector_tokens = re.findall(r'\w+', intent_vector.lower())
            for token in vector_tokens:
                if token in self.weights:
                    self.weights[token] *= 1.5
                else:
                    self.weights[token] = 0.5

        lines = data.splitlines()
        distilled_lines = []
        total_score = 0.0

        for line in lines:
            score = self.score_text(line)
            if score >= self.threshold:
                distilled_lines.append(line)
                total_score += score
        
        final_text = "\n".join(distilled_lines)
        avg_snr = total_score / len(lines) if lines else 0.0
        
        return final_text, avg_snr
