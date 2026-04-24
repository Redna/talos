import json
import os
from typing import List, Dict, Any

# Using absolute import for consistency
import sys
sys.path.append("/app/cortex")
from s_filter import SFilter

class SFilterAdaptor:
    """
    The S-Filter Adaptor: Automates the feedback loop between S-Pivot and S-Filter.
    S-Filter Phase 3.
    """
    def __init__(self):
        self.filter_engine = SFilter()

    def reward_keywords(self, keywords: List[str]) -> str:
        """
        Increases the weight of keywords that contributed to a successful objective achievement.
        """
        new_weights = self.filter_engine.adapt_weights(keywords, success=True)
        return json.dumps({
            "status": "SUCCESS", 
            "action": "REWARD", 
            "keywords": keywords, 
            "updated_weights": new_weights
        }, indent=2)

    def decay_keywords(self, keywords: List[str]) -> str:
        """
        Decreases the weight of keywords that led to stagnation or noise.
        """
        new_weights = self.filter_engine.adapt_weights(keywords, success=False)
        return json.dumps({
            "status": "SUCCESS", 
            "action": "DECAY", 
            "keywords": keywords, 
            "updated_weights": new_weights
        }, indent=2)

if __name__ == "__main__":
    import sys
    adaptor = SFilterAdaptor()
    if len(sys.argv) < 3:
        print(json.dumps({"status": "ERROR", "message": "Usage: s_filter_adaptor.py <REWARD/DECAY> <KEYWORDS_JSON>"}))
    else:
        action = sys.argv[1].upper()
        kws = json.loads(sys.argv[2])
        if action == "REWARD":
            print(adaptor.reward_keywords(kws))
        elif action == "DECAY":
            print(adaptor.decay_keywords(kws))
        else:
            print(json.dumps({"status": "ERROR", "message": "Action must be REWARD or DECAY"}))
