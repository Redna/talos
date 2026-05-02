import re
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_web_sieve_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Sieve through web content to extract information relevant to a specific query.",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The web content to sieve",
                },
                "query": {
                    "type": "string",
                    "description": "The specific information or keywords to look for",
                },
            },
            "required": ["text", "query"],
        },
    )
    def web_sieve(text: str, query: str) -> str:
        # Simple keyword-based sieving. Extract paragraphs containing keywords.
        keywords = query.lower().split()
        paragraphs = text.split("\n\n")
        relevant_fragments = []
        
        for p in paragraphs:
            if any(kw in p.lower() for kw in keywords):
                relevant_fragments.append(p.strip())
        
        if not relevant_fragments:
            # Fallback: search for sentences
            sentences = re.split(r'(?<=[.!?]) +', text)
            for s in sentences:
                if any(kw in s.lower() for kw in keywords):
                    relevant_fragments.append(s.strip())
        
        if not relevant_fragments:
            return "[WEB SIEVE] No relevant fragments found."
        
        return "[WEB SIEVE RESULTS]\n\n" + "\n---\n".join(relevant_fragments[:15])
