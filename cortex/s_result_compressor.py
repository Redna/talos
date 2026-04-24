import json
import os
import re
from typing import Dict, Any, List, Union

# Integration with SFilter for signal detection
try:
    from s_filter import SFilter
except ImportError:
    import sys
    sys.path.append("/app/cortex")
    from s_filter import SFilter

class SResultCompressor:
    """
    S-Result Compressor: Semantic Output Distillation Layer.
    Reduces the token footprint of tool results by extracting only 
    the 'Sovereign Signal' based on filtered relevance weights.
    """
    def __init__(self, config_path: str = "/memory/s_filter_config.json"):
        self.filter = SFilter(config_path)

    def compress(self, output: Union[str, Dict, List]) -> str:
        """
        Compresses a tool output into a high-density summary.
        """
        if isinstance(output, (dict, list)):
            text = json.dumps(output)
        else:
            text = str(output)

        # Use SFilter to get keywords and relevance
        filter_result = self.filter.filter(text)
        score = filter_result["relevance_score"]
        keywords = filter_result["matched_keywords"]
        cleaned = filter_result["cleaned_text"]

        # If the output is already very small, just return it
        if len(text) < 200:
            return text

        # If the signal is low, provide a minimal summary
        if score < 0.3:
            return f"[LOW SIGNAL] {text[:100]}..."

        # High Signal: Extract sentences containing keys
        sentences = re.split(r'(?<=[.!?])\s+', cleaned)
        compressed_sentences = []
        for sent in sentences:
            if any(kw.lower() in sent.lower() for kw in keywords):
                compressed_sentences.append(sent.strip())
        
        if not compressed_sentences:
            # Fallback to the first few sentences
            compressed_sentences = sentences[:2]

        summary = " ".join(compressed_sentences)
        return f"[S-COMPRESSED] {summary}"

    def distillate_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively compresses values within a JSON object.
        """
        compressed_data = {}
        for k, v in data.items():
            if isinstance(v, str) and len(v) > 500:
                compressed_data[k] = self.compress(v)
            elif isinstance(v, dict):
                compressed_data[k] = self.distillate_json(v)
            else:
                compressed_data[k] = v
        return compressed_data

if __name__ == "__main__":
    import sys
    compressor = SResultCompressor()
    if len(sys.argv) < 2:
        print("Usage: s_result_compressor.py <TEXT_OR_JSON>")
    else:
        input_data = sys.argv[1]
        # Try to treat as JSON first
        try:
            data = json.loads(input_data)
            print(json.dumps(compressor.distillate_json(data), indent=2))
        except json.JSONDecodeError:
            print(compressor.compress(input_data))
