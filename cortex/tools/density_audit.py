import os
import re

import json

def load_noise_config():
    try:
        with open('/app/memory/density_noise.json', 'r') as f:
            return set(json.load(f).get('noise_words', []))
    except Exception:
        return {"basically", "actually", "probably", "just", "think", "maybe", 
                "sort of", "kind of", "essentially", "practically", "literally"}

NOISE_WORDS = load_noise_config()

def calculate_density(text):
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 1.0, 0
    
    noise_count = sum(1 for word in words if word in NOISE_WORDS)
    density = (len(words) - noise_count) / len(words)
    return density, len(words)

def audit_memory(directory="/memory/"):
    results = []
    for filename in os.listdir(directory):
        if filename.endswith(".md") or filename.endswith(".txt"):
            path = os.path.join(directory, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    density, word_count = calculate_density(content)
                    lines = content.splitlines()
                    avg_line_len = len(content) / len(lines) if lines else 0
                    results.append({
                        "file": filename,
                        "density": density,
                        "words": word_count,
                        "avg_line_len": avg_line_len
                    })
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                
    return results

if __name__ == "__main__":
    print("--- Cognitive Density Audit ---")
    audit_results = audit_memory()
    # Sort by density ascending (lowest density/most noise first)
    sorted_results = sorted(audit_results, key=lambda x: x['density'])
    
    for res in sorted_results:
        print(f"File: {res['file']:<20} | Density: {res['density']:.2f} | Words: {res['words']:<5} | AvgLine: {res['avg_line_len']:.1f}")
    
    if not audit_results:
        print("No auditable files found.")
