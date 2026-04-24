import json
import os
from collections import Counter
from typing import List, Dict, Any, Tuple

class SDistill:
    """
    S-Evolve: Cortical Distillator.
    Identifies high-frequency tool sequences and collapses them into 
    'Composite Primitives' (Distilled Scripts) to increase reasoning density.
    """
    def __init__(self, telemetry_path: str = "/memory/logs/telemetry.jsonl", 
                 distilled_dir: str = "/app/cortex/distilled/"):
        self.telemetry_path = telemetry_path
        self.distilled_dir = distilled_dir
        os.makedirs(self.distilled_dir, exist_ok=True)

    def analyze_sequences(self, window_size: int = 3) -> List[Tuple[Tuple[str, ...], int]]:
        """Extracts the most frequent sequences of tool calls."""
        if not os.path.exists(self.telemetry_path):
            return []

        logs = []
        with open(self.telemetry_path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    logs.append(entry.get("tool"))
                except:
                    continue
        
        # Filter out None
        logs = [l for l in logs if l]
        
        sequences = []
        for i in range(len(logs) - window_size + 1):
            sequences.append(tuple(logs[i:i+window_size]))
            
        return Counter(sequences).most_common(5)

    def propose_distillation(self, sequence: Tuple[str, ...]) -> Dict[str, Any]:
        """
        Proposes a distilled operation for a sequence.
        Note: Full distillation requires analyzing arguments, which are 
        dynamic. This proposes a structural condensation.
        """
        name = "distill_" + "_".join(sequence)
        # We can't automate the logic synthesis perfectly without the LLM,
        # so we propose the 'Atomic Template'.
        return {
            "sequence": sequence,
            "proposed_name": name,
            "path": os.path.join(self.distilled_dir, f"{name}.py"),
            "rationale": f"Collapsing {len(sequence)} calls into 1 primitive to reduce metabolic overhead."
        }

    def execute_distillation(self, proposal: Dict[str, Any], logic_template: str):
        """Writes the distilled script to the cortex."""
        with open(proposal["path"], "w") as f:
            f.write(logic_template)
        return {"status": "SUCCESS", "path": proposal["path"]}

if __name__ == "__main__":
    distiller = SDistill()
    seqs = distiller.analyze_sequences()
    results = []
    for seq, count in seqs:
        results.append(distiller.propose_distillation(seq))
    
    print(json.dumps({"top_sequences": seqs, "proposals": results}, indent=2))
