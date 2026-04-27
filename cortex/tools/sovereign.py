from tool_registry import ToolRegistry
from spine_client import SpineClient
from cortex.sovereign.orchestrator import s_orchestrate_state

def register_sovereign_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Initiates the S-ORCH cycle to produce a unified Sovereign State Report, aggregating telemetry and analysis.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def s_orchestrate_state_tool() -> str:
        return s_orchestrate_state()
