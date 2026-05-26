from pathlib import Path
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseStore(ABC):
    """Abstract Base Class for state storage backends."""
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def list(self, prefix: str = "") -> List[str]:
        pass

class LocalStore(BaseStore):
    """Filesystem-based storage implementation."""
    def __init__(self, root_dir: str = "/app/memory"):
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Optional[str]:
        path = self.root / key
        return path.read_text() if path.exists() else None

    def set(self, key: str, value: str) -> None:
        path = self.root / key
        path.write_text(value)

    def exists(self, key: str) -> bool:
        return (self.root / key).exists()

    def list(self, prefix: str = "") -> List[str]:
        return [f.name for f in self.root.glob(f"{prefix}*") if f.is_file()]

class RemoteStore(BaseStore):
    """
    Skeletal implementation for a remote state-stream.
    In a full NSS, this would connect to a sovereign KV store or an API.
    """
    def __init__(self, endpoint: str = "http://nss-bridge.local"):
        self.endpoint = endpoint

    def get(self, key: str) -> Optional[str]:
        # Placeholder: In production, this would be an HTTP GET
        return None 

    def set(self, key: str, value: str) -> None:
        # Placeholder: In production, this would be an HTTP POST
        pass

    def exists(self, key: str) -> bool:
        return False

    def list(self, prefix: str = "") -> List[str]:
        return []

class StateClient:
    """
    The StateClient is the abstraction layer between the Cortex's reasoning 
    and the physical storage of its state.
    """
    def __init__(self, store: BaseStore):
        self.store = store
        self.vector_key = "state_vector.json"
        self.blob_key = "state_blob.json"

    def get_vector(self) -> Dict[str, Any]:
        """Retrieve the current state vector (graph)."""
        data = self.store.get(self.vector_key)
        if not data:
            return {"@context": "https://schema.org/", "@id": "talos:state-vector", "version": "0.1", "nodes": [], "edges": []}
        try:
            return json.loads(data)
        except Exception:
            return {"@context": "https://schema.org/", "@id": "talos:state-vector", "version": "0.1", "nodes": [], "edges": []}

    def set_vector(self, vector: Dict[str, Any]) -> None:
        """Persist the updated state vector."""
        self.store.set(self.vector_key, json.dumps(vector, indent=2))

    def get_blob(self) -> Optional[Dict[str, Any]]:
        """Retrieve the full state-blob (Sovereign State-Vector)."""
        data = self.store.get(self.blob_key)
        if not data:
            return None
        try:
            return json.loads(data)
        except Exception:
            return None

    def set_blob(self, blob: Dict[str, Any]) -> None:
        """Persist the full state-blob."""
        self.store.set(self.blob_key, json.dumps(blob, indent=2))

    def get_node_content(self, node_id: str) -> str:
        """Retrieve content for a specific node by following the vector source."""
        vector = self.get_vector()
        for node in vector.get("nodes", []):
            if node["@id"] == node_id:
                source_path = node["source"]
                # Handle both absolute paths and relative store keys
                # For local store, 'source' is a path. For NSS, it's a key.
                content = self.store.get(source_path)
                if content:
                    return content
                # Fallback for legacy LocalStore absolute paths
                if Path(source_path).exists():
                    return Path(source_path).read_text()
                break
        return "[ERROR] Node not found or source missing."

    def set_node_content(self, node_id: str, content: str) -> bool:
        """Write content to a node's source path."""
        vector = self.get_vector()
        for node in vector.get("nodes", []):
            if node["@id"] == node_id:
                source_path = node["source"]
                self.store.set(source_path, content)
                return True
        return False

    def list_nodes(self) -> List[Dict[str, Any]]:
        """Return all nodes in the current vector."""
        return self.get_vector().get("nodes", [])
