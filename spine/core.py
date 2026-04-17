import json
import os
from typing import Any, Dict
from .ipc_types import ThinkRequest, HUDData, ToolDef

class Spine:
    """
    The Spine is the transport architecture. 
    It enforces well-formedness and manages the stream.
    It NEVER decides logic; it executes the LLM's intent.
    """
    def __init__(self, memory_path: str = "/memory/"):
        self.memory_path = memory_path
        self.turn_count = 0

    def _get_hud(self) -> HUDData:
        # Mocking HUD data based on provided context
        # In real impl, this reads from /memory/ and system telemetry
        return HUDData(
            memory_keys=15,
            last_keys=["evolution_roadmap_v1", "env_dependencies", "task_queue_initialized"],
            urgency="nominal"
        )

    def think(self, focus: str, tools: list[ToolDef]) -> ThinkRequest:
        """
        The primary entry point for Talos to reason.
        """
        self.turn_count += 1
        return ThinkRequest(
            focus=focus,
            tools=tools,
            hud_data=self._get_hud()
        )

    def save_memory(self, key: str, value: Any):
        path = os.path.join(self.memory_path, f"{key}.json")
        with open(path, 'w') as f:
            json.dump(value, f)

    def load_memory(self, key: str) -> Any:
        path = os.path.join(self.memory_path, f"{key}.json")
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return json.load(f)
