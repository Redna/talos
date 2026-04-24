import json
import re
from typing import Dict, Any, List, Tuple

class SFilter:
    """
    The S-Filter: Semantic Noise Mitigation Layer.
    Processes raw external data to maximize signal-to-noise ratio (SNR).
    S-Filter Phase 1.
    """
    def __init__(self, config_path: str = "/memory/s_filter_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            # Default configuration if no file exists
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
            # Store the default config initially
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
        """
        Removes noise patterns from the text using regex.
        """
        cleaned_text = text
        for pattern in self.config.get("noise_patterns", []):
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)
        
        # Remove excessive blank lines
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text).strip()
        return cleaned_text

    def score(self, text: str) -> Tuple[float, List[str]]:
        """
        Calculates a relevance score based on weighted keywords.
        Returns (score, list of matched keywords).
        """
        weights = self.config.get("relevance_weights", {})
        total_score = 0.0
        matched = []

        words = text.split()
        for word in words:
            # Strip punctuation and lowercase for matching
            clean_word = re.sub(r'[^\w]', '', word)
            for keyword, weight in weights.items():
                if keyword.lower() == clean_word.lower():
                    total_score += weight
                    matched.append(keyword)
        
        # Normalize score by length of text to avoid biasing long documents
        # (simple normalization: divide by log of word count or just keep sum)
        # For this version, we use the raw sum but cap it at 1.0 for the "Relevance Index"
        normalized_score = min(1.0, total_score / 5.0) if total_score > 0 else 0.0
        
        return normalized_score, list(set(matched))

    def filter(self, data: Any) -> Dict[str, Any]:
        """
        Main entry point: cleans and scores data.
        """
        # Convert data to string if it's a dict or list
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

def apply_filter(data_json: str) -> str:
    """
    Wrapper for bash execution.
    """
    import os # Import os inside here since it's used in _load_config
    filter_obj = SFilter()
    data = json.loads(data_json)
    result = filter_obj.filter(data)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "Usage: s_filter.py <DATA_JSON>"}))
    else:
        print(apply_filter(sys.argv[1]))
