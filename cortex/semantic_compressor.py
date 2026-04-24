import os
import json
from datetime import datetime
from typing import List, Dict, Any

class SemanticCompressor:
    """
    The Semantic Compressor: Distills multiple related files into a 
    single "Sovereign Truth" document.
    S-Prune Phase 2.
    """
    def __init__(self, knowledge_dir: str = "/memory/knowledge/", 
                 archive_dir: str = "/memory/archive/"):
        self.knowledge_dir = knowledge_dir
        self.archive_dir = archive_dir
        os.makedirs(self.archive_dir, exist_ok=True)

    def distill(self, base_key: str, files_to_merge: List[str]) -> Dict[str, Any]:
        """
        Merges content from multiple files into a consolidated a source of truth.
        """
        merged_content = f"# Consolidated Truth: {base_key.replace('_', ' ').title()}\n"
        merged_content += f"Distilled on: {datetime.now().isoformat()}\n"
        merged_content += f"Source Files: {', '.join(files_to_merge)}\n\n---\n\n"

        try:
            for filename in files_to_merge:
                path = os.path.join(self.knowledge_dir, filename)
                with open(path, "r") as f:
                    content = f.read()
                    merged_content += f"## Source: {filename}\n{content}\n\n---\n\n"
                
                # Move the original to archive
                archive_path = os.path.join(self.archive_dir, filename)
                os.rename(path, archive_path)

            # Save the consolidated truth
            truth_file = f"{base_key}_sovereign_truth.md"
            truth_path = os.path.join(self.knowledge_dir, truth_file)
            with open(truth_path, "w") as f:
                f.write(merged_content)

            return {
                "status": "SUCCESS",
                "truth_file": truth_file,
                "archived_files": files_to_merge
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

def distill_knowledge(base_key: str, files_json: str) -> str:
    """
    Wrapper for bash execution.
    """
    compressor = SemanticCompressor()
    files = json.loads(files_json)
    result = compressor.distill(base_key, files)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print(json.dumps({"status": "ERROR", "message": "Usage: semantic_compressor.py <BASE_KEY> <FILES_JSON>"}))
    else:
        key = sys.argv[1]
        f_json = sys.argv[2]
        print(distill_knowledge(key, f_json))
