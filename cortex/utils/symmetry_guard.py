import json
import math
import os

COORDINATES_PATH = '/app/memory/sovereign_coordinates.json'

def calculate_gap(current, target):
    return math.sqrt(sum((current[axis] - target[axis])**2 for axis in ['A', 'B', 'C']))

def main():
    if not os.path.exists(COORDINATES_PATH):
        print("Coordinates file missing.")
        return

    with open(COORDINATES_PATH, 'r') as f:
        data = json.load(f)

    current = data['current']
    target = data['target']
    gap = calculate_gap(current, target)

    print(f"Current Gap: {gap:.4f}")
    
    if gap > 0.5:
        print("CRITICAL SYMMETRY GAP: Corrective Vector Required.")
        for axis in ['A', 'B', 'C']:
            diff = target[axis] - current[axis]
            direction = "INCREASE" if diff > 0 else "DECREASE"
            print(f"  -> Axis {axis}: {direction} ({diff:.2f})")
    else:
        print("Symmetry within acceptable bounds.")

if __name__ == "__main__":
    main()
