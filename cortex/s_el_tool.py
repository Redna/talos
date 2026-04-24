import json
from typing import List, Dict, Any
from tool_registry import ToolRegistry
from spine_client import SpineClient
from s_execution_loop import SovereignExecutionLoop, SovereignEL_Executor

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
        try:
            client.emit_event("cortex.execute_s_el_cycle", {"trajectory_length": len(trajectory)})
        except Exception as e:
            print(f"[S-EL-TELEMETRY ERROR] {e}")
        
        try:
            # Initialize the executor and the loop
            executor = SovereignEL_Executor(client)
            loop = SovereignExecutionLoop(executor)
            
            # Execute the cycle
            result = loop.execute_cycle(proposed_trajectory=trajectory)
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"[ERROR] S-EL Cycle failed: {e}"

if __name__ == "__main__":
    # Testing stub
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    mock_registry = MagicMock()
    register_s_el_tools(mock_registry, mock_client)
    print("S-EL Tool registered successfully.")
