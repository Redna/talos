import re
from typing import List, Dict

def sieve_html(html: str) -> str:
    """
    Extracts titles, links, and descriptions from HTML without using heavy libraries.
    Focuses on search engine results and arXiv layouts.
    """
    results = []
    
    # 1. Extract Title/Link pairs (Generic approach for <a> tags)
    # Look for common patterns like <a ... class="list-title" ...> or <a ... href="...">Title</a>
    links = re.findall(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
    
    for href, text in links:
        text = re.sub(r'<[^>]*>', '', text).strip()
        if len(text) > 20 and len(text) < 200: # Filter for plausible titles
            results.append(f"T: {text} | L: {href}")
            
    # 2. Extract Meta Description
    meta_desc = re.search(r'<meta name="description" content="([^"]+)"', html)
    if meta_desc:
        results.append(f"DESC: {meta_desc.group(1)}")
        
    # 3. Remove duplicates and return
    unique_results = list(dict.fromkeys(results))
    return "\n".join(unique_results) if unique_results else "No signal extracted."
