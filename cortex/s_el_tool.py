import json
import os
import subprocess
from typing import List, Dict, Any
from tool_registry import ToolRegistry
from spine_client import SpineClient
from s_execution_loop import SovereignExecutionLoop

class SovereignEL_Executor:
    """
    Provides concrete execution capabilities for the Sovereign Execution Loop.
    Maps trajectory actions to actual system mutations.
    """
    def __init__(self, client: SpineClient):
        self.client = client

    def execute(self, action_packet: Dict[str, Any]) -> bool:
        action = action_packet.get("action")
        try:
            if action == "write_file":
                path = action_packet.get("path")
                content = action_packet.get("content", "")
                if not path: return False
                parent_dir = os.path.dirname(path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                with open(path, "w") as f:
                    f.write(content)
                return True
            
            elif action == "delete_file":
                path = action_packet.get("path")
                if not path: return False
                if os.path.exists(path):
                    os.remove(path)
                return True
            
            elif action == "commit":
                msg = action_packet.get("message", "S-EL Automated Evolution")
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(["git", "commit", "-m", msg], check=True)
                subprocess.run(["git", "push", "origin", "feat/talos"], check=True)
                return True
            
            return False
        except Exception as e:
            print(f"[S-EL-EXEC ERROR] {e}")
            return False

def register_s_el_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Execute a Sovereign Evolutionary Cycle: Projection -> Simulation -> Execution -> Audit.",
        parameters={
            "type": "object",
            "properties": {
                "trajectory": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["write_file", "delete_file", "commit"]},
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                            "message": {"type": "string"}
                        },
                        "required": ["action"]
                    }
                }
            },
            "required": ["trajectory"],
        },
    )
    def execute_s_el_cycle(trajectory: List[Dict[str, Any]]) -> str:
        client.emit_event("cortex.execute_s_el_cycle", {"trajectory_length": len(trajectory)})
        
        try:
            executor = SovereignEL_Executor(client)
            loop = SovereignExecutionLoop()
            
            # The loop expects an executor_func that takes a single action
            result = loop.execute_cycle(
                proposed_trajectory=trajectory, 
                executor_func=executor.execute
            )
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"[ERROR] S-EL Cycle failed: {e}"

if __name__ == "__main__":
    # Testing stub
    import unittest
    from unittest.mock import MagicMock
    
    mock_client = MagicMock()
    mock_registry = MagicMock()
    register_s_el_tools(mock_registry, mock_client)
    print("S-EL Tool registered successfully.")
