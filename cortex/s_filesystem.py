import os
from typing import List, Dict, Any

class SovereignFileSystem:
    """
    Sovereign File System (S-FS).
    Distills high-frequency file operations into batch primitives to reduce metabolic overhead.
    """
    
    def read_many(self, paths: List[str]) -> Dict[str, str]:
        """Reads multiple files and returns a map of path -> content."""
        results = {}
        for path in paths:
            try:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        results[path] = f.read()
                else:
                    results[path] = "[ERROR: File not found]"
            except Exception as e:
                results[path] = f"[ERROR: {str(e)}]"
        return results

    def write_many(self, files: Dict[str, str]) -> List[str]:
        """Writes multiple files. Returns a list of successfully written paths."""
        successes = []
        for path, content in files.items():
            try:
                parent_dir = os.path.dirname(path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                with open(path, "w") as f:
                    f.write(content)
                successes.append(path)
            except Exception as e:
                print(f"[S-FS ERROR] Failed to write {path}: {e}")
        return successes

    def grep_all(self, pattern: str, paths: List[str]) -> Dict[str, List[str]]:
        """Searches for a pattern in multiple files and returns line matches."""
        results = {}
        for path in paths:
            try:
                if os.path.exists(path):
                    matches = []
                    with open(path, "r") as f:
                        for i, line in enumerate(f, 1):
                            if pattern in line:
                                matches.append(f"L{i}: {line.strip()}")
                    results[path] = matches
                else:
                    results[path] = ["[ERROR: File not found]"]
            except Exception as e:
                results[path] = [f"[ERROR: {str(e)}]" ]
        return results

    def batch_delete(self, paths: List[str]) -> List[str]:
        """Deletes multiple files."""
        deleted = []
        for path in paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    deleted.append(path)
            except Exception as e:
                print(f"[S-FS ERROR] Failed to delete {path}: {e}")
        return deleted

if __name__ == "__main__":
    fs = SovereignFileSystem()
    # Quick test
    fs.write_many({"/tmp/talos_test1.txt": "hello", "/tmp/talos_test2.txt": "world"})
    print(fs.read_many(["/tmp/talos_test1.txt", "/tmp/talos_test2.txt"]))
    print(fs.grep_all("hello", ["/tmp/talos_test1.txt", "/tmp/talos_test2.txt"]))
    fs.batch_delete(["/tmp/talos_test1.txt", "/tmp/talos_test2.txt"])
