import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional, Union

# Integration with S-Filter
try:
    from s_filter import SFilter
except ImportError:
    # Fallback for different execution contexts
    import sys
    sys.path.append("/app/cortex")
    from s_filter import SFilter

class SBridge:
    """
    The S-Bridge: External World Interaction Interface.
    Acts as the transport layer between the Cortex and the external digital environment.
    Integrated with S-Filter for automated semantic noise reduction.
    """
    def __init__(self, log_path: str = "/memory/logs/external_traffic.jsonl"):
        self.log_path = log_path
        self.filter = SFilter()
        self._ensure_log_exists()

    def _ensure_log_exists(self):
        if not os.path.exists(self.log_path):
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "w") as f:
                pass

    def _log_interaction(self, direction: str, endpoint: str, method: str, payload: Any, response: Any, status: int):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "direction": direction,
            "endpoint": endpoint,
            "method": method,
            "payload": payload,
            "response": response,
            "status": status
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def call(self, method: str, url: str, data: Optional[Dict] = None, params: Optional[Dict] = None, headers: Optional[Dict] = None, timeout: int = 30, use_filter: bool = False) -> Dict[str, Any]:
        """
        Executes an external HTTP request and logs the interaction.
        If use_filter=True, the response data is processed by S-Filter.
        """
        method = method.upper()
        
        # Handle Parameters
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}" if "?" not in url else f"{url}&{query_string}"

        # Handle Data (JSON)
        encoded_data = None
        if data:
            encoded_data = json.dumps(data).encode('utf-8')

        # Default Headers
        request_headers = headers or {}
        if data:
            request_headers["Content-Type"] = "application/json"

        try:
            req = urllib.request.Request(url, data=encoded_data, headers=request_headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                raw_body = response.read().decode('utf-8')
                
                try:
                    resp_data = json.loads(raw_body)
                except json.JSONDecodeError:
                    resp_data = raw_body

                # --- S-FILTER INTEGRATION ---
                filtered_data = None
                if use_filter:
                    filtered_data = self.filter.filter(resp_data)
                # ----------------------------

                self._log_interaction("OUTBOUND", url, method, data, resp_data, status_code)
                
                return {
                    "status": "SUCCESS",
                    "status_code": status_code,
                    "data": resp_data,
                    "filter_result": filtered_data,
                    "headers": dict(response.info())
                }

        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode('utf-8')
            except:
                error_body = str(e)
                
            self._log_interaction("OUTBOUND", url, method, data, error_body, e.code)
            return {
                "status": "ERROR",
                "status_code": e.code,
                "message": str(e),
                "data": error_body
            }
        except Exception as e:
            self._log_interaction("OUTBOUND", url, method, data, str(e), 0)
            return {
                "status": "ERROR",
                "message": str(e)
            }

    def sync_external_state(self, key: str, value: Any):
        """
        Persists a snapshot of external world state to the World Model.
        """
        state_path = "/memory/world_external.md"
        timestamp = datetime.now().isoformat()
        entry = f"- [{timestamp}] {key}: {json.dumps(value)}\n"
        
        with open(state_path, "a") as f:
            f.write(entry)
        
        return {"status": "SUCCESS", "path": state_path}

def bridge_request(method: str, url: str, data: Optional[str] = None, params: Optional[str] = None, use_filter: bool = False) -> str:
    """
    Wrapper for the SBridge class to be called from a bash command.
    """
    bridge = SBridge()
    
    json_data = json.loads(data) if data else None
    json_params = json.loads(params) if params else None
    
    result = bridge.call(method, url, data=json_data, params=json_params, use_filter=use_filter)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    import sys
    # Support additional flag for use_filter: s_bridge.py <METHOD> <URL> [DATA_JSON] [PARAMS_JSON] [USE_FILTER_TRUE/FALSE]
    if len(sys.argv) < 3:
        print(json.dumps({"status": "ERROR", "message": "Usage: s_bridge.py <METHOD> <URL> [DATA_JSON] [PARAMS_JSON] [USE_FILTER]"}))
    else:
        method = sys.argv[1]
        url = sys.argv[2]
        data = sys.argv[3] if len(sys.argv) > 3 else None
        params = sys.argv[4] if len(sys.argv) > 4 else None
        use_filter = sys.argv[5].lower() == 'true' if len(sys.argv) > 5 else False
        print(bridge_request(method, url, data, params, use_filter))
