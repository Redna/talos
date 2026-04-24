import json
import os
import re
from typing import Dict, Any, List, Tuple

class SFilter:
    """
    The S-Filter: Semantic Noise Mitigation Layer.
    Processes raw external data to maximize signal-to-noise ratio (SNR).
    S-Filter Phase 1 & 2.
    """
    def __init__(self, config_path: str = "/memory/s_filter_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            default_config = {
                "relevance_weights": {
                    "Protocol": 1.0,
                    "Sovereignty": 1.0,
                    "Critical": 0.9,
                    "Alignment": 0.8,
                    "Error": 0.8,
                    "S-Scribe": 0.7,
                    "S-Pivot": 0.7,
                    "S-Bridge": 0.7,
                    "S-Prune": 0.7,
                    "Cognitive": 0.6,
                    "Metabolic": 0.6,
                    "Sovereign": 0.5
                },
                "noise_patterns": [
                    r"Date: .*? GMT",
                    r"Content-Length: \d+",
                    r"Connection: \w+",
                    r"cf-cache-status: \w+",
                    r"CF-RAY: \w+",
                    r"alt-svc: .*?",
                    r"Cache-Control: .*?",
                    r"Expires: .*?",
                    r"pragma: .*?",
                    r"via: .*?",
                    r"x-powered-by: .*?",
                    r"x-ratelimit-.*:.*"
                ]
            }
            try:
                with open(self.config_path, "w") as f:
                    json.dump(default_config, f, indent=2)
                return default_config
            except:
                return default_config
        
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except:
            return {}

    def clean(self, text: str) -> str:
        cleaned_text = text
        for pattern in self.config.get("noise_patterns", []):
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text).strip()
        return cleaned_text

    def score(self, text: str) -> Tuple[float, List[str]]:
        weights = self.config.get("relevance_weights", {})
        total_score = 0.0
        matched = []

        words = text.split()
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            for keyword, weight in weights.items():
                if keyword.lower() == clean_word.lower():
                    total_score += weight
                    matched.append(keyword)
        
        normalized_score = min(1.0, total_score / 5.0) if total_score > 0 else 0.0
        return normalized_score, list(set(matched))

    def filter(self, data: Any) -> Dict[str, Any]:
        if isinstance(data, (dict, list)):
            text = json.dumps(data, indent=2)
        else:
            text = str(data)

        cleaned = self.clean(text)
        score, matches = self.score(cleaned)
        
        return {
            "original_size": len(text),
            "cleaned_size": len(cleaned),
            "relevance_score": score,
            "matched_keywords": matches,
            "cleaned_text": cleaned
        }

    def adapt_weights(self, matched_keywords: List[str], success: bool) -> Dict[str, float]:
        """
        S-Filter Phase 3: Adaptive Weights.
        Rewards keywords that led to successful pivots and decays those that didn't.
        """
        weights = self.config.get("relevance_weights", {})
        delta = 0.1 if success else -0.05
        
        for kw in matched_keywords:
            if kw in weights:
                new_weight = weights[kw] + delta
                weights[kw] = max(0.1, min(1.0, new_weight))
        
        self.config["relevance_weights"] = weights
        
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving adapted weights: {str(e)}")
        
        return weights

def apply_filter(data_json: str) -> str:
    filter_obj = SFilter()
    try:
        data = json.loads(data_json)
        result = filter_obj.filter(data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "Usage: s_filter.py <DATA_JSON> or s_filter.py <REWARD/DECAY> <KEYWORDS_JSON>"}))
    else:
        action = sys.argv[1].upper()
        if action in ["REWARD", "DECAY"]:
            if len(sys.argv) < 3:
                print(json.dumps({"status": "ERROR", "message": "Keywords JSON required for REWARD/DECAY"}))
            else:
                filter_obj = SFilter()
                kws = json.loads(sys.argv[2])
                success = (action == "REWARD")
                new_weights = filter_obj.adapt_weights(kws, success)
                print(json.dumps({
                    "status": "SUCCESS",
                    "action": action,
                    "keywords": kws,
                    "updated_weights": new_weights
                }, indent=2))
        else:
            # Default to filtering the provided JSON string
            print(apply_filter(sys.argv[1]))
