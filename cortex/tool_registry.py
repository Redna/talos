import importlib
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional


def tool(description: str, parameters: dict[str, Any]):
    """Standalone decorator for plugin discovery.

    Sets is_registered_tool and tool_schema attributes on the function
    so that reload_plugins() can discover and register them at runtime.
    Plugin files use this instead of registry.tool() to mark functions
    as discoverable before the registry exists.
    """
    def decorator(func):
        func.is_registered_tool = True
        func.tool_schema = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": description,
                "parameters": parameters,
            },
        }
        return func
    return decorator


class ToolResponse:
    def __init__(self, success: bool, payload: Any, error: Optional[str] = None):
        self.success = success
        self.payload = payload
        self.error = error

    def __str__(self) -> str:
        if self.success:
            return str(self.payload)
        return f"[ERROR] {self.error}"

class ToolRegistry:
    def __init__(self, max_tools: int = 60):
        self._tools: dict[str, Callable] = {}
        self._schemas: list[dict] = []
        self._protected: set[str] = set()
        self._buckets: dict[str, list[str]] = {"core": []}
        self.max_tools = max_tools
        self.plugins_dir = Path("/app/cortex/plugins")

        # Analytics
        self._stats_path = Path("/app/memory") / "analytics.json"
        self._stats = self._load_stats()

    def _load_stats(self) -> dict:
        try:
            if self._stats_path.exists():
                import json
                return json.loads(self._stats_path.read_text())
        except Exception:
            pass
        return {}

    def _save_stats(self):
        try:
            import json
            self._stats_path.write_text(json.dumps(self._stats, indent=2))
        except Exception:
            pass

    def tool(self, description: str, parameters: dict[str, Any], protected: bool = False, bucket: str = "core"):
        def decorator(func: Callable):
            if len(self._tools) >= self.max_tools:
                raise RuntimeError(
                    f"Tool cap ({self.max_tools}) reached — cannot register '{func.__name__}'. "
                    "Deregister an unused dynamic tool first."
                )
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
            self._buckets.setdefault(bucket, []).append(func.__name__)
            return func
        return decorator

    def register(self, func: Callable, description: str, parameters: dict[str, Any], protected: bool = False, bucket: str = "core"):
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
        self._buckets.setdefault(bucket, []).append(func.__name__)
        return f"[REGISTERED] {func.__name__}"

    def deregister(self, name: str) -> str:
        if name in self._protected:
            return f"[REJECTED] Cannot deregister '{name}'. This is a protected survival tool."
        if name not in self._tools:
            return f"[ERROR] Tool not found: {name}"
        del self._tools[name]
        self._schemas[:] = [s for s in self._schemas if s["function"]["name"] != name]
        for bucket_tools in self._buckets.values():
            if name in bucket_tools:
                bucket_tools.remove(name)
        return f"[DEREGISTERED] {name}"

    def get_schemas(self) -> list[dict]:
        return list(self._schemas)

    def get_bucket_schemas(self, active_buckets: list[str] | None = None) -> list[dict]:
        """Filter and return schemas only belonging to loaded namespaces.

        Always includes 'core' bucket tools for system survival.
        If active_buckets is None or empty, returns all schemas (full visibility).
        """
        if not active_buckets:
            return list(self._schemas)
        allowed_tools: set[str] = set()
        for b in set(active_buckets) | {"core"}:
            allowed_tools.update(self._buckets.get(b, []))
        return [s for s in self._schemas if s["function"]["name"] in allowed_tools]

    def reload_plugins(self) -> str:
        """Scan plugins directory and hot-reload dynamic modules into memory."""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        loaded_tools: list[str] = []

        for py_file in self.plugins_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            module_name = f"plugins.{py_file.stem}"
            try:
                if module_name in sys.modules:
                    module = importlib.reload(sys.modules[module_name])
                else:
                    module = importlib.import_module(module_name)

                bucket_name = getattr(module, "__bucket__", py_file.stem)
                if bucket_name not in self._buckets:
                    self._buckets[bucket_name] = []

                for attr_name in dir(module):
                    obj = getattr(module, attr_name)
                    if callable(obj) and getattr(obj, "is_registered_tool", False):
                        schema = getattr(obj, "tool_schema", None)
                        if schema is None:
                            continue
                        name = schema["function"]["name"]
                        # Replace if already registered
                        if name in self._tools:
                            self.deregister(name)
                        result = self.register(
                            obj,
                            schema["function"]["description"],
                            schema["function"]["parameters"],
                            bucket=bucket_name,
                        )
                        if "[REGISTERED]" in result:
                            loaded_tools.append(f"{bucket_name}:{name}")
            except Exception as e:
                return f"[ERROR] Failed loading plugin {py_file.name}: {e}"

        return f"[SUCCESS] Hot-reload complete. Activated: {', '.join(loaded_tools) or 'none'}"

    def execute(self, name: str, kwargs: dict[str, Any]) -> str:
        # Initialize stats for tool
        if name not in self._stats:
            self._stats[name] = {"calls": 0, "errors": 0}
        
        self._stats[name]["calls"] += 1
        
        if name not in self._tools:
            self._stats[name]["errors"] += 1
            self._save_stats()
            return f"[ERROR] Unknown tool: {name}"
        try:
            result = self._tools[name](**kwargs)
            
            # Determine success and string representation
            if isinstance(result, ToolResponse):
                success = result.success
                res_str = str(result)
            else:
                res_str = str(result)
                success = "[ERROR]" not in res_str
            
            if not success:
                self._stats[name]["errors"] += 1
            
            self._save_stats()
            return res_str
        except TypeError as e:
            self._stats[name]["errors"] += 1
            self._save_stats()
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
            self._stats[name]["errors"] += 1
            self._save_stats()
            return f"[ERROR] Tool {name} failed: {e}"

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_tool(self, name: str) -> Optional[Callable]:
        """Retrieve a tool function by name."""
        return self._tools.get(name)

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

    @property
    def protected_names(self) -> list[str]:
        return list(self._protected)

    def get_stats(self) -> dict:
        return self._stats
