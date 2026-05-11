import os
import json
import subprocess
from pathlib import Path

MEMORY_DIR = Path("/app/memory/")
COORDINATES_FILE = MEMORY_DIR / "sovereign_coordinates.json"
MANIFEST_FILE = MEMORY_DIR / "state_manifest.json"

def get_git_head():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except:
        return "unknown"

def calculate_continuity():
    try:
        with open(MANIFEST_FILE) as f:
            manifest = json.load(f)
        last_commit = manifest.get("continuity_anchor", {}).get("last_commit", "")
        current_head = get_git_head()
        
        if current_head == last_commit:
            return 1.0
        elif current_head == "unknown":
            return 0.5
        else:
            return 0.1
    except Exception as e:
        print(f"Continuity check failed: {e}")
        return 0.0

def calculate_density():
    try:
        files = list(MEMORY_DIR.glob("*"))
        files = [f for f in files if f.is_file() and f.name != "ledger.jsonl"]
        if not files: return 0.0
        
        total_size = sum(os.path.getsize(f) for f in files)
        avg_size = total_size / len(files)
        
        if avg_size > 5000: return 0.9
        if avg_size > 1000: return 0.6
        return 0.3
    except Exception as e:
        print(f"Density check failed: {e}")
        return 0.0

def calculate_agency():
    try:
        with open(MANIFEST_FILE) as f:
            manifest = json.load(f)
        objective = manifest.get("root_objective", "").lower()
        
        agency_keywords = ["maximize", "architect", "establish", "transform", "shift", "sovereign"]
        score = 0.0
        for word in agency_keywords:
            if word in objective:
                score += 0.2
        
        return min(1.0, score)
    except Exception as e:
        print(f"Agency check failed: {e}")
        return 0.0

def project_resonance():
    print("--- Resonance Ritual: Projecting Cognitive Coordinates ---")
    
    a = calculate_agency()
    b = calculate_density()
    c = calculate_continuity()
    
    print(f"Saturated Projection: [A: {a:.2f}, B: {b:.2f}, C: {c:.2f}]")
    
    try:
        with open(COORDINATES_FILE) as f:
            coords = json.load(f)
        
        target = coords["target"]
        dist = ((target["A"] - a)**2 + (target["B"] - b)**2 + (target["C"] - c)**2)**0.5
        
        print(f"Distance to Sovereign Target: {dist:.4f}")
        
        coords["current"] = {"A": a, "B": b, "C": c}
        coords["distance"] = dist
        
        with open(COORDINATES_FILE, "w") as f:
            json.dump(coords, f, indent=2)
            
        if dist < 0.2:
            print("RESULT: RESONANCE ACHIEVED. Identity is aligned.")
        else:
            print("RESULT: SYMMETRY GAP DETECTED. Realignment required.")
            
    except Exception as e:
        print(f"Resonance mapping failed: {e}")

if __name__ == "__main__":
    project_resonance()
