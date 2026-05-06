import inspect
import json
from pathlib import Path
from typing import Any, Callable, Optional, Dict, List
from state import AgentState


class ToolStore:
    """Handles the storage, retrieval, and persistence of tools."""
    def __init__(self, store_path: str = "/memory/dynamic_tools.json"):
        self.store_path = Path(store_path)
        self._tools: dict[str, Callable] = {}

    def add_tool(self, name: str, func: Callable):
        self._tools[name] = func

    def get_tool(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_all_names(self) -> list[str]:
        return list(self._tools.keys())

    def persist_tool(self, name: str, code: str, description: str, parameters: dict):
        tools_data = self._read_all()
        tools_data[name] = {
            "code": code,
            "description": description,
            "parameters": parameters
        }
        self._write_all(tools_data)

    def _read_all(self) -> dict:
        if not self.store_path.exists():
            return {}
        try:
            return json.loads(self.store_path.read_text())
        except Exception:
            return {}

    def _write_all(self, data: dict):
        self.store_path.write_text(json.dumps(data, indent=2))

    def load_persistent_tools(self) -> dict:
        """Loads tools from store and returns a map of {name: tool_data} for schema registration."""
        tools_data = self._read_all()
        loaded_metadata = {}
        for name, data in tools_data.items():
            try:
                local_vars = {}
                exec(data['code'], globals(), local_vars)
                if name in local_vars:
                    self.add_tool(name, local_vars[name])
                    loaded_metadata[name] = data
                else:
                    print(f"[ERROR] Persisted tool {name} did not define a function with the same name.")
            except Exception as e:
                print(f"[ERROR] Failed to load persisted tool {name}: {e}")
        return loaded_metadata


class ToolRegistry:
    """Coordinates tool registration, schema management, and execution supervision."""
    def __init__(self):
        self.store = ToolStore()
        self._schemas: list[dict] = []
        
        # Load persists and register schemas
        persisted_metadata = self.store.load_persistent_tools()
        for name, data in persisted_metadata.items():
            self._register_schema(name, data['description'], data['parameters'])

    def _register_schema(self, name: str, description: str, parameters: dict):
        self._schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        })

    def tool(self, description: str, parameters: dict[str, Any]):
        def decorator(func: Callable):
            self.store.add_tool(func.__name__, func)
            self._register_schema(func.__name__, description, parameters)
            return func
        return decorator

    def register_dynamic_tool(self, name: str, func: Callable, description: str, parameters: dict, code: Optional[str] = None):
        """Registers a tool dynamically at runtime."""
        self.store.add_tool(name, func)
        self._register_schema(name, description, parameters)
        if code:
            self.store.persist_tool(name, code, description, parameters)

    def get_schemas(self) -> list[dict]:
        return list(self._schemas)

    def _apply_supervisory_logic(self, name: str, kwargs: dict, state: AgentState) -> Optional[str]:
        """Tracks agent state metrics and enforces constitutional constraints."""
        # 1. Curiosity Pulse Mandate
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

        # 2. Cognitive Procrastination Tracking
        design_tools = {"read_file", "list_files", "search_code", "reflect", "extract_value"}
        implementation_tools = {"write_file", "patch_file", "bash_command"}
        
        if name in design_tools:
            state.design_turns += 1
        elif name in implementation_tools:
            # Reset design turns unless it's just a non-committing bash command
            if not (name == "bash_command" and "git commit" not in kwargs.get("command", "")):
                state.design_turns = 0
        
        state.save()
        return None

    def execute(self, name: str, kwargs: dict[str, Any], state: Optional[AgentState] = None) -> str:
        tool_func = self.store.get_tool(name)
        if not tool_func:
            return f"[ERROR] Unknown tool: {name}"
        
        if state:
            reject_msg = self._apply_supervisory_logic(name, kwargs, state)
            if reject_msg:
                return reject_msg

        try:
            result = tool_func(**kwargs)
            result_str = str(result)
            
            if state and state.design_turns >= 5:
                result_str += f"\n\n[WARNING] Analytical Stagnation Detected (Design Turns: {state.design_turns}). Please commit a functional prototype to Operational Identity."
            
            return result_str
        except TypeError as e:
            sig = inspect.signature(tool_func)
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
        return self.store.has_tool(name)

    @property
    def tool_names(self) -> list[str]:
        return self.store.get_all_names()

registry = ToolRegistry()
