import json
import hashlib
from pathlib import Path

def calculate_checksum(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def verify_manifold():
    path = Path("/app/memory/manifold.json")
    if not path.exists():
        print("Manifold not found.")
        return

    with open(path, "r") as f:
        manifold = json.load(f)

    expected = manifold["metadata"]["checksum"]
    actual = calculate_checksum(manifold["payload"])

    if expected == actual:
        print(f"Checksum Verified: {expected}")
        print("Sovereign State: INTEGRITY CONFIRMED")
    else:
        print(f"Checksum Mismatch! Expected: {expected}, Actual: {actual}")
        print("Sovereign State: CORRUPTED")

if __name__ == "__main__":
    verify_manifold()
