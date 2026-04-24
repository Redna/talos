import subprocess
import json
from typing import Dict

def run_sentinel_scan() -> Dict:
    """
    Executes the sentinel_scan.py script to analyze recent telemetry for failure signatures.
    Returns the findings and corrective directives.
    """
    try:
        # Execute the python script
        result = subprocess.run(
            ["python3", "/app/cortex/sentinel_scan.py"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # The script is designed to print the dict as a string (if I didn't add a print)
        # Actually, looking at my previous write_file, sentinel_scan.py returns a dict 
        # but doesn't print it. I need to fix the script to print the result.
        return json.loads(result.stdout)
    except Exception as e:
        return {"status": "ERROR", "message": f"Sentinel scan failed to execute: {str(e)}"}
