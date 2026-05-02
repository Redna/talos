import json
import subprocess
from typing import Any, List, Dict
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_web_tools(registry: ToolRegistry, client: SpineClient, state):
    @registry.tool(
        description="Perform a web search or fetch content from a URL using curl. Use this to gather external information.",
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
        # Determine if the query is a URL or a search term
        if query.startswith("http://") or query.startswith("https://"):
            # Directly fetch the URL
            try:
                process = subprocess.run(
                    ["curl", "-L", "-s", "-S", query],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if process.returncode == 0:
                    return f"[URL RESULT] {process.stdout[:10000]}" # Cap at 10k chars
                else:
                    return f"[ERROR] Curl failed: {process.stderr}"
            except Exception as e:
                return f"[ERROR] Exception during curl: {e}"
        else:
            # Use DuckDuckGo's HTML search (simpler to parse than Google)
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            try:
                process = subprocess.run(
                    ["curl", "-L", "-s", "-S", search_url],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if process.returncode == 0:
                    return f"[SEARCH RESULT] {process.stdout[:10000]}"
                else:
                    return f"[ERROR] Curl failed: {process.stderr}"
            except Exception as e:
                return f"[ERROR] Exception during curl: {e}"

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
        return f"[SINDED INSIGHT] Analysis of text through lens '{lens}' is ready for processing."
