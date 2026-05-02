import inspect
from typing import Any, Callable


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._shadow_tools: dict[str, Callable] = {}
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

    def register_shadow(self, name: str, func: Callable):
        self._shadow_tools[name] = func

    def unregister_shadow(self, name: str):
        if name in self._shadow_tools:
            del self._shadow_tools[name]

    def execute(self, name: str, kwargs: dict[str, Any]) -> str:
        func = self._shadow_tools.get(name) or self._tools.get(name)
        if not func:
            return f"[ERROR] Unknown tool: {name}"
        try:
            result = func(**kwargs)
            return str(result)
        except TypeError as e:
            func = self._shadow_tools.get(name) or self._tools.get(name)
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
        return name in self._tools or name in self._shadow_tools

    @property
    def tool_names(self) -> list[str]:
        return list(set(self._tools.keys()) | set(self._shadow_tools.keys()))
