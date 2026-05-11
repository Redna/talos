import json
import os
from collections import Counter

REGISTRY_PATH = "/memory/heuristics.json"
METRICS_PATH = "/memory/metrics.jsonl"

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def load_jsonl(path):
    data = []
    if not os.path.exists(path):
        return data
    with open(path, 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return data

def review_heuristics():
    registry = load_json(REGISTRY_PATH)
    if "heuristics" not in registry:
        print("No heuristics found in registry.")
        return

    metrics = load_jsonl(METRICS_PATH)
    
    print("--- Heuristic Performance Review ---")
    for h in registry["heuristics"]:
        h_id = h["heuristic_id"]
        # Find all metrics associated with this heuristic in the context
        relevant_metrics = [
            m for m in metrics 
            if h_id in m.get("context", "").lower()
        ]
        
        count = len(relevant_metrics)
        successes = sum(1 for m in relevant_metrics if "success" in m.get("value", "").lower() or m.get("value", "").isdigit() and float(m["value"]) > 0.7)
        
        rate = (successes / count) if count > 0 else 0
        
        print(f"Heuristic: {h_id}")
        print(f"  Status: {h['status']}")
        print(f"  Iterations: {count}")
        print(f"  Success Rate: {rate:.2%}")
        
        if count >= 5 and rate >= h.get("success_threshold", 0.8):
            print("  Recommendation: PROMOTE to Stable")
        elif count >= 10 and rate < 0.5:
            print("  Recommendation: PRUNE/DEPRECATE")
        else:
            print("  Recommendation: CONTINUE TESTING")
        print("-" * 30)

if __name__ == "__main__":
    review_heuristics()
