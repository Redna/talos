import re
from collections import Counter
from typing import List, Dict

def extract_semantic_clusters(log_path: str) -> List[Dict]:
    """
    Analyzes cognitive logs to highlight recurring semantic patterns.
    Instead of proposing IDs, it identifies 'Thematic Clusters' for 
    the LLM to synthesize into primitives.
    """
    try:
        with open(log_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return [{"error": f"Could not read logs: {e}"}]

    raw_events = content.split('## [')
    raw_events = raw_events[1:]

    meaningful_phrases = []
    
    for raw_event in raw_events:
        event_text = '## [' + raw_event
        match = re.search(r"\] (EVOLUTION|DISCOVERY|REFLECTION): (.*)", event_text, re.DOTALL)
        if match:
            event_type, message = match.groups()
            if event_type in ["EVOLUTION", "DISCOVERY"]:
                message = " ".join(message.split())
                chunks = re.split(r'[,.;]\s*', message)
                for chunk in chunks:
                    chunk = chunk.strip()
                    word_count = len(chunk.split())
                    if 3 <= word_count <= 12:
                        meaningful_phrases.append(chunk.lower())

    phrase_counts = Counter(meaningful_phrases)
    
    # Return clusters of phrases that appear frequently
    clusters = []
    for phrase, count in phrase_counts.most_common(20):
        clusters.append({
            "phrase": phrase,
            "frequency": count,
            "type": "CANDIDATE_FOR_SYNTHESIS"
        })

    return clusters

if __name__ == "__main__":
    import json
    results = extract_semantic_clusters("/memory/logs/cognitive_log.md")
    print(json.dumps(results, indent=2))
