import os
import json
from typing import List

def prune_cortex() -> List[str]:
    """
    Identifies files in /app/cortex/ that are redundant or obsolete.
    P5 Principle: Minimalism.
    """
    cortex_path = "/app/cortex/"
    files = os.listdir(cortex_path)
    # For this prototype, we identify "plus" or "test" files as pruning candidates
    candidates = [f for f in files if "plus" in f or "test_" in f]
    return candidates

if __name__ == "__main__":
    print(json.dumps(prune_cortex()))
