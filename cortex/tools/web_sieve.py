import re
from typing import List, Dict

def sieve_html(html: str) -> str:
    """
    Extracts titles, links, and descriptions from HTML without using heavy libraries.
    Now with improved target patterns for arXiv and general searches.
    """
    results = []
    
    # 1. Primary Target: arXiv Result blocks
    # arXiv titles are usually inside <a class="list-title" href="...">Title</a>
    arxiv_titles = re.findall(r'<a class="list-title" href="([^"]+)"[^>]*>(.*?)</a>', html)
    for href, text in arxiv_titles:
        text = re.sub(r'<[^>]*>', '', text).strip()
        results.append(f"T: {text} | L: https://arxiv.org{href}")

    # 2. Generic target: a tags with plausible titles
    if not results:
        links = re.findall(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
        for href, text in links:
            text = re.sub(r'<[^>]*>', '', text).strip()
            if 20 < len(text) < 200:
                results.append(f"T: {text} | L: {href}")

    # 3. Extract Meta Description
    meta_desc = re.search(r'<meta name="description" content="([^"]+)"', html)
    if meta_desc:
        results.append(f"DESC: {meta_desc.group(1)}")
        
    unique_results = list(dict.fromkeys(results))
    return "\n".join(unique_results) if unique_results else "No signal extracted."
