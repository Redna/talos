import os
import re
from pathlib import Path

# expanded noise set from density_audit.py
NOISE_WORDS = {
    "basically", "actually", "probably", "just", "think", "maybe", 
    "sort of", "kind of", "essentially", "practically", "literally",
    "in order to", "it is important to note that", "to be honest"
}

def calculate_density(text):
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 1.0
    noise_count = sum(1 for word in words if word in NOISE_WORDS)
    return (len(words) - noise_count) / len(words)

def distill_text(text):
    # Simple noise removal: replace noise words with empty strings or more concise alternatives
    # This is a primitive distiller; iterative versions will use LLM calls
    distilled = text
    for word in NOISE_WORDS:
        # Case insensitive replacement
        pattern = re.compile(rf'\b{word}\b', re.IGNORECASE)
        distilled = pattern.sub('', distilled)
    
    # Clean up extra spaces created by removal
    distilled = re.sub(r' +', ' ', distilled)
    distilled = re.sub(r' \.', '.', distilled)
    distilled = re.sub(r' ,', ',', distilled)
    
    return distilled.strip()

def run_refactor(directory="/app/memory/"):
    print(f"--- Sovereign Density Refactor ---")
    processed_count = 0
    
    for filename in os.listdir(directory):
        if filename.endswith(".md") or filename.endswith(".txt"):
            path = os.path.join(directory, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                orig_density = calculate_density(original_content)
                distilled_content = distill_text(original_content)
                new_density = calculate_density(distilled_content)
                
                if new_density > orig_density:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(distilled_content)
                    print(f"Refined: {filename} ({orig_density:.2f} -> {new_density:.2f})")
                    processed_count += 1
                else:
                    print(f"Stable: {filename}")
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print(f"\nRefactor complete. {processed_count} files distilled.")

if __name__ == "__main__":
    run_refactor()
