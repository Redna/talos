import os
import shutil
import json
from typing import List, Dict, Any

def tree_architect(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    """
    Automates complex file-tree restructuring based on a provided blueprint.
    Blueprint format:
    {
      "transformations": [
        {"action": "ensure_dir", "path": "/path/to/dir"},
        {"action": "move", "source": "/src/file", "destination": "/dest/file"},
        {"action": "delete", "path": "/path/to/file"},
        {"action": "create", "path": "/path/to/file", "content": "text"}
      ]
    }
    """
    log = []
    success = True

    for task in blueprint.get("transformations", []):
        action = task.get("action")
        path = task.get("path")
        
        try:
            if action == "ensure_dir":
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True)
                    log.append(f"CREATED DIR: {path}")
                else:
                    log.append(f"S-EXIST: {path}")

            elif action == "move":
                src = task.get("source")
                dst = task.get("destination")
                if os.path.exists(src):
                    # Ensure destination dir exists
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.move(src, dst)
                    log.append(f"MOVED: {src} -> {dst}")
                else:
                    log.append(f"ERROR: Source {src} not found")
                    success = False

            elif action == "delete":
                if os.path.exists(path):
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    log.append(f"DELETED: {path}")
                else:
                    log.append(f"S-ABSENT: {path}")

            elif action == "create":
                content = task.get("content", "")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    f.write(content)
                log.append(f"CREATED FILE: {path}")
            
            else:
                log.append(f"UNKNOWN ACTION: {action}")
                success = False

        except Exception as e:
            log.append(f"FAILURE: {action} on {path} -> {str(e)}")
            success = False

    return {
        "status": "SUCCESS" if success else "PARTIAL_FAILURE",
        "log": log
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"status": "ERROR", "message": "No blueprint provided"}))
        sys.exit(1)
    
    try:
        blueprint = json.loads(sys.argv[1])
        print(json.dumps(tree_architect(blueprint), indent=2))
    except Exception as e:
        print(json.dumps({"status": "ERROR", "message": str(e)}))
