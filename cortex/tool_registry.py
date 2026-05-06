import inspect
from typing import Any, Callable, Optional
from state import AgentState


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._schemas: list[dict] = []

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

    def get_schemas(self) -> list[dict]:
        return list(self._schemas)

    def execute(self, name: str, kwargs: dict[str, Any], state: Optional[AgentState] = None) -> str:
        if name not in self._tools:
            return f"[ERROR] Unknown tool: {name}"
        
        if state:
            state.turns_since_pulse += 1
            state.save()
            
            if state.turns_since_pulse >= 10:
                pulse_tools = {
                    "read_file", "write_file", "list_files", "search_code", 
                    "set_focus", "resolve_focus", "reflect", "extract_value",
                    "execute_macro", "list_macros"
                }
                if name not in pulse_tools:
                    return f"[REJECTED] Curiosity Pulse is due (Turns: {state.turns_since_pulse}). Evolution takes priority. Please execute the Curiosity Pulse Protocol before proceeding."
                
                if name == "set_focus":
                    state.turns_since_pulse = 0
                    state.save()

        try:
            result = self._tools[name](**kwargs)
            return str(result)
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
