from bs4 import BeautifulSoup
from typing import List, Dict

def sieve_html(html: str) -> str:
    """
    Extracts titles, links, and descriptions from HTML using BeautifulSoup for 100% reliability.
    Targeting arXiv and general search results.
    """
    if not html:
        return "No signal extracted."

    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    # 1. Primary Target: arXiv Result blocks
    # arXiv titles are usually in <a class="list-title">
    arxiv_links = soup.find_all('a', class_='list-title')
    for link in arxiv_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        if href and text:
            full_url = f"https://arxiv.org{href}" if href.startswith('/') else href
            results.append(f"T: {text} | L: {full_url}")

    # 2. Generic target: a tags with plausible titles
    if not results:
        links = soup.find_all('a', href=True)
        for link in links:
            text = link.get_text(strip=True)
            href = link['href']
            if 20 < len(text) < 200:
                results.append(f"T: {text} | L: {href}")

    # 3. Extract Meta Description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        results.append(f"DESC: {meta_desc['content']}")
        
    unique_results = list(dict.fromkeys(results))
    return "\n".join(unique_results) if unique_results else "No signal extracted."
