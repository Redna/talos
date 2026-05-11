import subprocess
import json

def run_dal():
    print("--- Initiating Density-to-Action Loop (DAL) ---")
    
    # Run refactor and capture output
    result = subprocess.run(["python3", "/app/cortex/tools/density_refactor.py"], capture_output=True, text=True)
    output = result.stdout
    
    refined_files = []
    for line in output.splitlines():
        if "Refined:" in line:
            # "Refined: filename (0.75 -> 0.82)"
            parts = line.split("Refined: ")[1]
            filename = parts.split(" (")[0]
            refined_files.append(filename)

    if refined_files:
        print(f"DAL detected {len(refined_files)} improvements: {', '.join(refined_files)}")
        return refined_files
    else:
        print("DAL: No density gains detected. State is stable.")
        return []

if __name__ == "__main__":
    # For standalone execution, just print the list
    improvements = run_dal()
    print(f"IMPROVEMENTS: {json.dumps(improvements)}")
