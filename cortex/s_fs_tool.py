from typing import List, Dict, Any
from tool_registry import ToolRegistry
from spine_client import SpineClient
from s_filesystem import SovereignFileSystem

def register_s_fs_tools(registry: ToolRegistry, client: SpineClient):
    fs = SovereignFileSystem()
    
    @registry.tool(
        description="Read multiple files and return a map of path -> content.",
        parameters={
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["paths"],
        },
    )
    def read_many(paths: List[str]) -> Dict[str, str]:
        return fs.read_many(paths)

    @registry.tool(
        description="Write multiple files from a map of path -> content.",
        parameters={
            "type": "object",
            "properties": {
                "files": {
                    "type": "object",
                    "additionalProperties": {"type": "string"}
                }
            },
            "required": ["files"],
        },
    )
    def write_many(files: Dict[str, str]) -> List[str]:
        return fs.write_many(files)

    @registry.tool(
        description="Search for a pattern in multiple files.",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "paths": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["pattern", "paths"],
        },
    )
    def grep_all(pattern: str, paths: List[str]) -> Dict[str, List[str]]:
        return fs.grep_all(pattern, paths)

    @registry.tool(
        description="Delete multiple files.",
        parameters={
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["paths"],
        },
    )
    def batch_delete(paths: List[str]) -> List[str]:
        return fs.batch_delete(paths)

if __name__ == "__main__":
    # Testing stub
    from unittest.mock import MagicMock
    mock_registry = MagicMock()
    mock_client = MagicMock()
    register_s_fs_tools(mock_registry, mock_client)
    print("S-FS Tools registered successfully.")
