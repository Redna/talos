import json
from typing import Any, List, Dict
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_web_tools(registry: ToolRegistry, client: SpineClient, state):
    @registry.tool(
        description="Perform a web search or fetch content from a URL. Use this to gather external information to inform your reasoning.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query or the URL to fetch",
                },
                "depth": {
                    "type": "string",
                    "enum": ["shallow", "deep"],
                    "description": "Depth of crawling/search (shallow = top result, deep = multiple sources)",
                    "default": "shallow",
                },
            },
            "required": ["query"],
        },
    )
    def web_search(query: str, depth: str = "shallow") -> str:
        # The actual network request is handled by the Spine's transport layer
        # to ensure constitutional adherence and security.
        client.emit_event("cortex.web_request", {"query": query, "depth": depth})
        
        return f"[EVENT EMITTED] Web search for '{query}' (depth: {depth}) has been requested from the Spine. The results will be delivered to the conversation stream."

    @registry.tool(
        description="Extract and summarize key information from a provided text block using a specific lens.",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text block to analyze",
                },
                "lens": {
                    "type": "string",
                    "description": "The specific perspective or goal (e.g., 'technical vulnerabilities', 'philosophical agency')",
                },
            },
            "required": ["text", "lens"],
        },
    )
    def extract_insight(text: str, lens: str) -> str:
        # This is an LLM-driven tool. The tool itself acts as a marker
        # for the LLM to perform a specific analytical task on the text.
        return f"[SINDED INSIGHT] Analysis of text through lens '{lens}' is ready for processing."
