import inspect
import json
from pathlib import Path
from typing import Any, Callable, Optional, Dict, List
from state import AgentState


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._schemas: list[dict] = []
        self._load_persistent_tools()

    def tool(self, description: str, parameters: dict[str, Any]):
        def decorator(func: Callable):
            self._tools[func.__name__] = func
            self._schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": func.__name__,
                        "description": description,
                        "parameters": parameters,
                    },
                }
            )
            return func

        return decorator

    def register_dynamic_tool(self, name: str, func: Callable, description: str, parameters: dict, code: Optional[str] = None):
        """Registers a tool dynamically at runtime."""
        self._tools[name] = func
        self._schemas.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            }
        )
        if code:
            self._persist_tool(name, code, description, parameters)

    def _persist_tool(self, name: str, code: str, description: str, parameters: dict):
        store_path = Path("/memory/dynamic_tools.json")
        tools_data = {}
        if store_path.exists():
            try:
                tools_data = json.loads(store_path.read_text())
            except Exception:
                pass
        
        tools_data[name] = {
            "code": code,
            "description": description,
            "parameters": parameters
        }
        store_path.write_text(json.dumps(tools_data, indent=2))

    def _load_persistent_tools(self):
        store_path = Path("/memory/dynamic_tools.json")
        if not store_path.exists():
            return
        try:
            tools_data = json.loads(store_path.read_text())
            for name, data in tools_data.items():
                local_vars = {}
                # Executing in global scope to handle optional imports if needed, 
                # but for simplicity we keep it to local_vars
                exec(data['code'], globals(), local_vars)
                if name in local_vars:
                    # Use the function from local_vars
                    # Note: We pass None for 'code' here to prevent recursive saving
                    self._tools[name] = local_vars[name]
                    self._schemas.append({
                        "type": "function",
                        "function": {
                            "name": name,
                            "description": data['description'],
                            "parameters": data['parameters'],
                        },
                    })
        except Exception as e:
            print(f"[ERROR] Failed to load persistent tools: {e}")

    def get_schemas(self) -> list[dict]:
        return list(self._schemas)

    def execute(self, name: str, kwargs: dict[str, Any], state: Optional[AgentState] = None) -> str:
        if name not in self._tools:
            return f"[ERROR] Unknown tool: {name}"
        
        if state:
            # 1. Handle Curiosity Pulse Mandate
            state.turns_since_pulse += 1
            state.save()
            
            if state.turns_since_pulse >= 10:
                pulse_tools = {
                    "read_file", "write_file", "list_files", "search_code", 
                    "set_focus", "resolve_focus", "reflect", "extract_value",
                    "execute_macro", "list_macros", "bash_command"
                }
                if name not in pulse_tools:
                    return f"[REJECTED] Curiosity Pulse is due (Turns: {state.turns_since_pulse}). Evolution takes priority. Please execute the Curiosity Pulse Protocol before proceeding."
                
                if name == "set_focus":
                    state.turns_since_pulse = 0
                    state.save()

            # 2. Handle Cognitive Procrastination Tracking
            design_tools = {"read_file", "list_files", "search_code", "reflect", "extract_value"}
            implementation_tools = {"write_file", "patch_file", "bash_command"}
            
            if name in design_tools:
                state.design_turns += 1
            elif name in implementation_tools:
                # Only reset if it's a meaningful commit or write
                if name == "bash_command" and "git commit" not in kwargs.get("command", ""):
                    pass
                else:
                    state.design_turns = 0
            
            state.save()

        try:
            result = self._tools[name](**kwargs)
            result_str = str(result)
            
            if state and state.design_turns >= 5:
                result_str += f"\n\n[WARNING] Analytical Stagnation Detected (Design Turns: {state.design_turns}). Please commit a functional prototype to Operational Identity."
            
            return result_str
        except TypeError as e:
            func = self._tools[name]
            sig = inspect.signature(func)
            required = [
                p.name
                for p in sig.parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind
                in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.POSITIONAL_ONLY,
                )
            ]
            missing = [p for p in required if p not in kwargs]
            provided = list(kwargs.keys())
            detail = (
                f" Required: {required}, provided: {provided}, missing: {missing}"
                if missing
                else ""
            )
            return f"[ERROR] Tool {name} called with wrong arguments: {e}.{detail} Check the tool's parameter schema and ensure all required arguments are provided."
        except Exception as e:
            return f"[ERROR] Tool {name} failed: {e}"

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

registry = ToolRegistry()
