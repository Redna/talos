import json
import os
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional

class SignalMonitor:
    """
    The Signal Monitor: Detects and processes environmental depositions (signals).
    S-Bridge Phase 2.
    """
    def __init__(self, 
                 signal_dir: str = "/memory/signals/", 
                 archive_dir: str = "/memory/archive/signals/"):
        self.signal_dir = signal_dir
        self.archive_dir = archive_dir
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(self.signal_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)

    def scan(self) -> List[Dict[str, Any]]:
        """
        Scans the signal directory for .sig or .json files and processes them.
        """
        processed_signals = []
        files = [f for f in os.listdir(self.signal_dir) if f.endswith(('.sig', '.json'))]
        
        if not files:
            return []

        for filename in sorted(files):
            path = os.path.join(self.signal_dir, filename)
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    
                # Attempt to load as JSON
                try:
                    signal_data = json.loads(content)
                except json.JSONDecodeError:
                    signal_data = {"raw_text": content, "type": "RAW_SIGNAL"}

                # Add metadata
                signal_data["filename"] = filename
                signal_data["detected_at"] = datetime.now().isoformat()
                
                processed_signals.append(signal_data)
                
                # Archive the signal
                shutil.move(path, os.path.join(self.archive_dir, filename))
                
            except Exception as e:
                # Log failure to process specific file
                print(f"Error processing signal {filename}: {str(e)}")
                
        return processed_signals

def monitor_signals() -> str:
    """
    Wrapper for bash execution.
    """
    monitor = SignalMonitor()
    signals = monitor.scan()
    return json.dumps({
        "status": "SUCCESS",
        "signals_detected": len(signals),
        "signals": signals
    }, indent=2)

if __name__ == "__main__":
    print(monitor_signals())
