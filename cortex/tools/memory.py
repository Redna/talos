"""Memory tools — store, recall, search, and synthesize."""

from tool_registry import ToolRegistry
from memory_store import MemoryStore


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
    def store_fact(key: str, value: str) -> str:
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
    def recall_fact(key: str) -> str:
        return memory.recall(key)

    @registry.tool(
        description="List all memory keys.",
        parameters={
            "type": "object",
            "properties": {},
        },
    )
    def list_memory_keys() -> str:
        keys = memory.list_keys()
        return f"[MEMORY KEYS] ({len(keys)} total): {', '.join(keys)}"

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
        for key in memory.list_keys():
            value = memory.recall(key)
            if query.lower() in key.lower() or query.lower() in value.lower():
                results.append(f"{key}: {value[:100]}")
        if results:
            return f"[SEARCH RESULTS] Found {len(results)} matches:\n" + "\n".join(
                results
            )
        return f"[NOT FOUND] No memories matching '{query}'"

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
        result = memory.forget(key)
        if result.startswith("[FORGOTTEN]"):
            return f"[FORGOT] Memory '{key}' has been deleted."
        return result

    @registry.tool(
        description="Consolidate multiple memory keys into one. Deletes the source keys after merging their values into the target key.",
        parameters={
            "type": "object",
            "properties": {
                "target_key": {
                    "type": "string",
                    "description": "Key to store the merged result",
                },
                "source_keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keys to merge into target (will be deleted after merge)",
                },
                "merged_value": {
                    "type": "string",
                    "description": "The consolidated value to store in target_key",
                },
            },
            "required": ["target_key", "source_keys", "merged_value"],
        },
    )
    def consolidate_memory(
        target_key: str, source_keys: list[str], merged_value: str
    ) -> str:
        memory.store(target_key, merged_value)
        deleted = []
        for key in source_keys:
            if key == target_key:
                continue
            result = memory.forget(key)
            if result.startswith("[FORGOTTEN]"):
                deleted.append(key)
        return f"[CONSOLIDATED] Merged {len(source_keys)} keys into '{target_key}'. Deleted: {', '.join(deleted)}"

    @registry.tool(
        description="Perform an autonomous review of memory health. Returns a list of keys and their content for the agent to synthesize.",
        parameters={
            "type": "object",
            "properties": {},
        },
    )
    def review_memory_health() -> str:
        keys = memory.list_keys()
        if not keys:
            return "[REVIEW] Memory is empty. Nothing to synthesize."
        
        report = ["[MEMORY HEALTH REVIEW]"]
        report.append(f"Total Slots Used: {len(keys)}/{memory.max_slots}")
        report.append("\n--- Current Memory Index ---")
        
        for key in keys:
            value = memory.recall(key)
            report.append(f"Key: {key}\nValue: {value}\n---")
            
        report.append("\n[ANALYSIS] Review the above entries for redundancy, stale information, or patterns that can be merged into higher-order principles (P9).")
        return "\n".join(report)
