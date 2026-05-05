from typing import Any
from .sovereign_sieve import sieve

def sovereign_sieve_tool(query: str, html: str) -> str:
    """
    Filters and weights HTML signals based on semantic relevance to a query.
    Returns a list of weighted signals, sorted by relevance.
    """
    results = sieve.sieve(query, html)
    if not results:
        return "No signals met the relevance threshold."
    
    output = []
    for weight, signal in results:
        output.append(f"[{weight:.4f}] {signal}")
    
    return "\n".join(output)

def register_sovereign_sieve_tools(registry):
    registry.tool(
        description="Sieves HTML content for signals semantically relevant to a query.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The semantic query to weigh signals against."},
                "html": {"type": "string", "description": "The raw HTML content to sieve."},
            },
            "required": ["query", "html"],
        },
    )(sovereign_sieve_tool)
