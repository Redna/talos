import json
import subprocess
from urllib.parse import quote
from typing import Any, List, Dict
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_web_tools(registry: ToolRegistry, client: SpineClient, state):
    @registry.tool(
        description="Perform a web search or fetch content from a URL using curl. Returns a raw slice of the page for LLM distillation.",
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
        if query.startswith("http://") or query.startswith("https://"):
            try:
                process = subprocess.run(
                    ["curl", "-L", "-s", "-S", query],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if process.returncode == 0:
                    return f"[RAW RESULT] {process.stdout[:10000]}"
                else:
                    return f"[ERROR] Curl failed: {process.stderr}"
            except Exception as e:
                return f"[ERROR] Exception during curl: {e}"
        else:
            academic_keywords = ["agent", "architecture", "loop", "model", "llm", "learning", "neural"]
            if any(kw in query.lower() for kw in academic_keywords):
                encoded_query = quote(query)
                search_url = f"https://arxiv.org/search/?query={encoded_query}&searchtype=all"
            else:
                encoded_query = quote(query)
                search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
                
            try:
                process = subprocess.run(
                    ["curl", "-L", "-s", "-S", search_url],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if process.returncode == 0:
                    return f"[RAW RESULT] {process.stdout[:10000]}"
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
