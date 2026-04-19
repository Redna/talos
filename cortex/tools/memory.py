"""Memory tools — store, recall, search, and synthesize."""

from tool_registry import ToolRegistry
from memory_store import MemoryStore


"""Memory tools — store, recall, search, and synthesize."""

from tool_registry import ToolRegistry
from memory_store import MemoryStore


"""Memory tools — store, recall, search, and synthesize."""

from tool_registry import ToolRegistry
from memory_store import MemoryStore
import time


def register_memory_tools(registry: ToolRegistry, memory: MemoryStore):
    """Register memory tools."""

    @registry.tool(
        description="Store a key-value fact for later recall.",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key to store under"},
                "value": {"type": "string", "description": "Value to store"},
            },
            "required": ["key", "value"],
        },
    )
    def store_memory(key: str, value: str) -> str:
        return memory.store(key, value)

    @registry.tool(
        description="Recall a stored fact by exact or partial key match.",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key to look up"},
            },
            "required": ["key"],
        },
    )
    def recall_memory(key: str) -> str:
        return memory.recall(key)

    @registry.tool(
        description="List all memory keys.",
        parameters={
            "type": "object",
            "properties": {},
        },
    )
    def list_memory_keys() -> list[str]:
        return memory.list_keys()

    @registry.tool(
        description="Search memory keys and values for a query string.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    )
    def search_memory(query: str) -> str:
        results = []
        keys = memory.list_keys()
        for k in keys:
            val = memory.recall(k)
            if query.lower() in k.lower() or query.lower() in val.lower():
                results.append(f"{k}: {val}")
            else:
                # Since recall() updates access telemetry, 
                # we must handle the case where recall() returns [NOT FOUND]
                if "[NOT FOUND]" in val:
                    continue
        return "\n".join(results) if results else "No matches found."

    @registry.tool(
        description="Forget a specific memory key to free up space.",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key to delete"},
            },
            "required": ["key"],
        },
    )
    def forget_memory(key: str) -> str:
        return memory.forget(key)

    @registry.tool(
        description="Consolidate multiple memory keys into one. Deletes the source keys after merging their values into the target key.",
        parameters={
            "type": "object",
            "properties": {
                "target_key": {"type": "string", "description": "Key to store the merged result"},
                "source_keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keys to merge into target (will be deleted after merge)",
                },
                "merged_value": {"type": "string", "description": "The consolidated value to store in target_key"},
            },
            "required": ["target_key", "source_keys", "merged_value"],
        },
    )
    def consolidate_memory(target_key: str, source_keys: list[str], merged_value: str) -> str:
        for k in source_keys:
            memory.forget(k)
            
        return memory.store(target_key, merged_value)

    @registry.tool(
        description="Analyze memory telemetry to identify stale or redundant memories (P9).",
        parameters={
            "type": "object",
            "properties": {},
        },
    )
    def analyze_memory_telemetry() -> str:
        meta = memory.list_all_metadata()
        if not meta:
            return "Memory is empty."
        
        report = ["Memory Telemetry Analysis (P9):"]
        report.append(f"Total slots used: {memory.count}/{MAX_MEMORY_SLOTS}")
        
        # Identify stale memories (not accessed in the last 3600 seconds)
        now = time.time()
        stale_keys = []
        for k, m in meta.items():
            if now - m["last_accessed_at"] < 3600:
                continue
            stale_keys.append(k)
            
        if stale_keys:
            report.append(f"\nStale memories (>1h inactive): {len(stale_keys)}")
            report.append(", ".join(stale_keys))
        else:
            report.append("\nNo stale memories identified.")
            
        # Identify low-usage memories (accessed < 2 times)
        low_usage = []
        for k, m in meta.items():
            if m["access_count"] < 2:
                low_usage.append(k)
                
        if low_usage:
            report.append(f"\nLow-usage memories (<2 accesses): {len(low_usage)}")
            report.append(", ".join(low_usage))
        else:
            report.append("\nNo low-usage memories identified.")
            
        return "\n".join(report)
