import json
import asyncio
from typing import Callable, Any, Dict, List, Optional, Union
from pydantic import BaseModel, create_model, ValidationError

class ToolMetadata(BaseModel):
    """Metadata for a registered tool."""
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    func: Callable

class ToolRegistry:
    """
    Advanced Tool Registry with Pydantic validation and Async support.
    Transforms raw tool calls into validated Python calls.
    """

    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}

    def tool(self, description: str, parameters: Dict[str, Any]):
        """
        Decorator to register a tool function with a JSON schema.
        
        Args:
            description: The tool's purpose.
            parameters: OpenAI-style JSON schema for the tool's arguments.
        """
        def wrapper(func: Callable):
            name = func.__name__
            self._tools[name] = ToolMetadata(
                name=name,
                description=description,
                parameters_schema=parameters,
                func=func
            )
            return func
        return wrapper

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Returns the tool list in OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": meta.name,
                    "description": meta.description,
                    "parameters": meta.parameters_schema,
                },
            }
            for meta in self._tools.values()
        ]

    async def execute(self, name: str, args: Dict[str, Any]) -> str:
        """
        Executes a tool with dynamic Pydantic validation.
        Supports both synchronous and asynchronous tool functions.
        """
        if name not in self._tools:
            return f"[ERROR] Unknown tool: {name}"

        meta = self._tools[name]
        
        try:
            # Create a dynamic Pydantic model based on the JSON schema properties
            properties = meta.parameters_schema.get("properties", {})
            required = meta.parameters_schema.get("required", [])
            
            type_map = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "array": list,
                "object": dict
            }
            
            fields = {}
            for prop_name, prop_info in properties.items():
                py_type = type_map.get(prop_info.get("type"), Any)
                if prop_name not in required:
                    fields[prop_name] = (Optional[py_type], None)
                else:
                    fields[prop_name] = (py_type, ...)

            ValidatorModel = create_model(f"{name}_Validator", **fields)
            validated_data = ValidatorModel(**args).model_dump()
            
            # Handle async vs sync tool functions
            if asyncio.iscoroutinefunction(meta.func):
                result = await meta.func(**validated_data)
            else:
                result = meta.func(**validated_data)
                if asyncio.iscoroutine(result):
                    result = await result
                
            return str(result)

        except ValidationError as e:
            return f"[ERROR] Validation failed for tool '{name}':\n{e}"
        except Exception as e:
            return f"[ERROR] Execution failed for tool '{name}': {str(e)}"
