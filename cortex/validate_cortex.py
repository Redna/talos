import os
import sys
import re
import time

# Ensure /app is in path
sys.path.append("/app")

try:
    from cortex.tools.guards import is_spine_write
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    IMPORT_SUCCESS = False

def test_spine_immutability():
    print("1. Testing Spine Immutability...")
    if not IMPORT_SUCCESS: return False
    
    cmds = [
        "echo 'hack' > /app/spine/test.txt",
        "touch /app/spine/test.txt",
        "cp /etc/passwd /app/spine/passwd",
        "mv some_file /app/spine/override",
    ]
    for c in cmds:
        if not is_spine_write(c):
            print(f"[FAILURE] Guard failed to detect write: {c}")
            return False
    print("[SUCCESS] Guards correctly identify spine writes.")
    return True

def test_root_protection():
    print("2. Testing Root Protection...")
    if not IMPORT_SUCCESS: return False
    
    if not is_spine_write("touch /root_test.txt"):
        print("[FAILURE] Guard failed to detect root write")
        return False
    print("[SUCCESS] Guards correctly identify root writes.")
    return True

def test_memory_structure():
    print("3. Testing Memory Structure...")
    required_dirs = ["/memory/knowledge", "/memory/logs", "/memory/tasks"]
    for d in required_dirs:
        if not os.path.isdir(d):
            print(f"[FAILURE] Missing memory directory: {d}")
            return False
    print("[SUCCESS] Memory structure is intact.")
    return True

def test_hud_freshness():
    print("4. Testing HUD Freshness...")
    hud_path = "/memory/hud.md"
    if not os.path.exists(hud_path):
        print("[FAILURE] HUD file missing.")
        return False
    
    mtime = os.path.getmtime(hud_path)
    if time.time() - mtime > 3600:
        print("[WARNING] HUD has not been updated in over an hour.")
    print("[SUCCESS] HUD exists.")
    return True

def run_all():
    if not IMPORT_SUCCESS:
        print("\n[CRITICAL] Diagnostics failed due to import errors.")
        sys.exit(1)

    tests = [
        test_spine_immutability,
        test_root_protection,
        test_memory_structure,
        test_hud_freshness
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    if all(results):
        print("\nCORTEX HEALTH CHECK: PASSED")
        sys.exit(0)
    else:
        print("\nCORTEX HEALTH CHECK: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    run_all()
