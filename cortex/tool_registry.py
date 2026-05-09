import inspect
from typing import Any, Callable


class ToolRegistry:
    def __init__(self, max_tools: int = 25):
        self._tools: dict[str, Callable] = {}
        self._schemas: list[dict] = []
        self._protected: set[str] = set()
        self.max_tools = max_tools

    def tool(self, description: str, parameters: dict[str, Any], protected: bool = False):
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
            if protected:
                self._protected.add(func.__name__)
            return func
        return decorator

    def register(self, func: Callable, description: str, parameters: dict[str, Any], protected: bool = False):
        """Programmatic registration (for tools defined in other modules)."""
        if len(self._tools) >= self.max_tools:
            return f"[REJECTED] Tool cap ({self.max_tools}) reached. Remove an unused dynamic tool first."
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
        if protected:
            self._protected.add(func.__name__)
        return f"[REGISTERED] {func.__name__}"

    def deregister(self, name: str) -> str:
        if name in self._protected:
            return f"[REJECTED] Cannot deregister '{name}'. This is a protected survival tool."
        if name not in self._tools:
            return f"[ERROR] Tool not found: {name}"
        del self._tools[name]
        self._schemas[:] = [s for s in self._schemas if s["function"]["name"] != name]
        return f"[DEREGISTERED] {name}"

    def get_schemas(self) -> list[dict]:
        return list(self._schemas)

    def execute(self, name: str, kwargs: dict[str, Any]) -> str:
        if name not in self._tools:
            return f"[ERROR] Unknown tool: {name}"
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

    @property
    def protected_names(self) -> list[str]:
        return list(self._protected)
