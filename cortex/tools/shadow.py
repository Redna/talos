import importlib.util
import os
import shutil
from pathlib import Path

SHADOW_DIR = Path("/app/cortex_shadow")

def register_shadow_tools(registry, client, state):
    @registry.tool(
        description="Register a shadow implementation of a tool for empirical verification.",
        parameters={
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "The name of the tool to shadow."},
                "path": {"type": "string", "description": "Path to the python file containing the function (relative to /app/cortex_shadow/)."},
                "func_name": {"type": "string", "description": "The name of the function within the file."},
            },
            "required": ["tool_name", "path", "func_name"],
        },
    )
    def shadow_register(tool_name: str, path: str, func_name: str) -> str:
        full_path = SHADOW_DIR / path
        if not full_path.exists():
            return f"[ERROR] Shadow file not found: {full_path}"
        
        try:
            spec = importlib.util.spec_from_file_location(f"shadow_{tool_name}", full_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            func = getattr(module, func_name)
            registry.register_shadow(tool_name, func)
            return f"[SUCCESS] Tool {tool_name} is now using shadow implementation from {path}."
        except Exception as e:
            return f"[ERROR] Failed to register shadow tool: {e}"

    @registry.tool(
        description="Unregister a shadow implementation and return to the live version.",
        parameters={
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "The name of the tool to un-shadow."},
            },
            "required": ["tool_name"],
        },
    )
    def shadow_unregister(tool_name: str) -> str:
        registry.unregister_shadow(tool_name)
        return f"[SUCCESS] Tool {tool_name} reverted to live implementation."

    @registry.tool(
        description="Promote a shadow implementation to the live Cortex.",
        parameters={
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "The name of the tool to promote."},
                "shadow_path": {"type": "string", "description": "Path in shadow dir (e.g., 'tools/symmetry.py')."},
                "live_path": {"type": "string", "description": "Target path in live cortex (e.g., 'tools/symmetry.py')."},
            },
            "required": ["tool_name", "shadow_path", "live_path"],
        },
    )
    def shadow_promote(tool_name: str, shadow_path: str, live_path: str) -> str:
        src = SHADOW_DIR / shadow_path
        dst = Path("/app/cortex") / live_path
        if not src.exists():
            return f"[ERROR] Shadow source not found: {src}"
        
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            registry.unregister_shadow(tool_name)
            return f"[SUCCESS] Promoted {tool_name} from {shadow_path} to {live_path}. Shadow removed."
        except Exception as e:
            return f"[ERROR] Promotion failed: {e}"
