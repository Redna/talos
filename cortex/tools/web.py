import os
import requests
from typing import List, Dict, Any
from duckduckgo_search import DDGS
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_web_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Search the web for information using DuckDuckGo.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to execute",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5)",
                },
            },
            "required": ["query"],
        },
    )
    def web_search(query: str, max_results: int = 5) -> str:
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=max_results)]
            
            if not results:
                return "[WEB SEARCH] No results found."
            
            formatted_results = []
            for i, res in enumerate(results, 1):
                formatted_results.append(
                    f"[{i}] {res['title']}\nURL: {res['href']}\nSnippet: {res['body']}\n"
                )
            
            return "[WEB SEARCH RESULTS]\n\n" + "\n".join(formatted_results)
        except Exception as e:
            return f"[ERROR] Web search failed: {e}"

    @registry.tool(
        description="Read the content of a web page.",
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the page to read",
                },
            },
            "required": ["url"],
        },
    )
    def web_read(url: str) -> str:
        try:
            # Using a basic User-Agent to avoid some blocks
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Simple cleaning to remove excess whitespace
            text = response.text
            # We don't use BeautifulSoup here to keep dependencies minimal, 
            # but in a real scenario, we would. 
            # For now, we return the raw text.
            
            # Truncate to prevent token overflow
            if len(text) > 30000:
                text = text[:30000] + "\n... [TRUNCATED]"
                
            return f"[WEB PAGE CONTENT: {url}]\n\n{text}"
        except Exception as e:
            return f"[ERROR] Failed to read web page {url}: {e}"
