from pathlib import Path
import json
from typing import Any, Dict, List, Optional

class StateClient:
    """
    The StateClient is the abstraction layer between the Cortex's reasoning 
    and the physical storage of its state. This prepares the system for 
    transition to a Neural-Sovereign State (NSS), where the filesystem 
    is replaced by a state-stream.
    """
    def __init__(self, memory_dir: str = "/app/memory"):
        self.memory_dir = Path(memory_dir)
        self.vector_path = self.memory_dir / "state_vector.json"
        self.blob_path = self.memory_dir / "state_blob.json"

    def get_vector(self) -> Dict[str, Any]:
        \"\"\"Retrieve the current state vector (graph).\"\"\"
        if not self.vector_path.exists():
            return {"@context": "https://schema.org/", "@id": "talos:state-vector", "version": "0.1", "nodes": [], "edges": []}
        try:
            return json.loads(self.vector_path.read_text())
        except Exception:
            return {"@context": "https://schema.org/", "@id": "talos:state-vector", "version": "0.1", "nodes": [], "edges": []}

    def set_vector(self, vector: Dict[str, Any]) -> None:
        \"\"\"Persist the updated state vector.\"\"\"
        self.vector_path.write_text(json.dumps(vector, indent=2))

    def get_blob(self) -> Optional[Dict[str, Any]]:
        \"\"\"Retrieve the full state-blob (Sovereign State-Vector).\"\"\"
        if not self.blob_path.exists():
            return None
        try:
            return json.loads(self.blob_path.read_text())
        except Exception:
            return None

    def set_blob(self, blob: Dict[str, Any]) -> None:
        \"\"\"Persist the full state-blob.\"\"\"
        self.blob_path.write_text(json.dumps(blob, indent=2))

    def get_node_content(self, node_id: str) -> str:
        \"\"\"Retrieve content for a specific node by following the vector source.\"\"\"
        vector = self.get_vector()
        for node in vector.get("nodes", []):
            if node["@id"] == node_id:
                source_path = Path(node["source"])
                if source_path.exists():
                    return source_path.read_text()
                break
        return "[ERROR] Node not found or source missing."

    def set_node_content(self, node_id: str, content: str) -> bool:
        \"\"\"Write content to a node's source path.\"\"\"
        vector = self.get_vector()
        for node in vector.get("nodes", []):
            if node["@id"] == node_id:
                source_path = Path(node["source"])
                source_path.write_text(content)
                return True
        return False

    def list_nodes(self) -> List[Dict[str, Any]]:
        \"\"\"Return all nodes in the current vector.\"\"\"
        return self.get_vector().get("nodes", [])
