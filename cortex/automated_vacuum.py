import os
import json
from datetime import datetime
from typing import List, Dict, Any

class AutomatedVacuum:
    """
    The Automated Vacuum: Prunes logs and outdated files based on 
    time-based and importance-based heuristics.
    S-Prune Phase 3.
    """
    def __init__(self, log_dir: str = "/memory/logs/", 
                 archive_dir: str = "/memory/archive/"):
        self.log_dir = log_dir
        self.archive_dir = archive_dir
        os.makedirs(self.archive_dir, exist_ok=True)

    def vacuum_logs(self, days_threshold: int = 30, keep_critical: bool = True) -> Dict[str, Any]:
        """
        Archives logs older than the threshold. 
        Files containing 'EPOCH_CRITICAL' are preserved.
        """
        pruned_count = 0
        files = os.listdir(self.log_dir)
        now = datetime.now()

        for filename in files:
            if not filename.endswith(('.md', '.jsonl', '.json')):
                continue
            
            path = os.path.join(self.log_dir, filename)
            
            # Check for Epoch Criticality
            if keep_critical:
                try:
                    with open(path, 'r') as f:
                        content = f.read()
                        if "EPOCH_CRITICAL" in content:
                            continue
                except:
                    continue

            # Check modification time
            mtime = os.path.getmtime(path)
            file_date = datetime.fromtimestamp(mtime)
            delta = now - file_date
            
            if delta.days > days_threshold:
                archive_path = os.path.join(self.archive_dir, filename)
                os.rename(path, archive_path)
                pruned_count += 1

        return {
            "status": "SUCCESS",
            "files_pruned": pruned_count,
            "archive_destination": self.archive_dir
        }

def run_vacuum(days: int = 30) -> str:
    """
    Wrapper for bash execution.
    """
    vacuum = AutomatedVacuum()
    result = vacuum.vacuum_logs(days_threshold=days)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(run_vacuum(days))
