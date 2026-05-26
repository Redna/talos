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
        # If the key is an absolute path, use it directly
        # otherwise, treat it as relative to the memory root.
        path = Path(key)
        target = path if path.is_absolute() else self.root / key
        return target.read_text() if target.exists() else None

    def set(self, key: str, value: str) -> None:
        path = Path(key)
        target = path if path.is_absolute() else self.root / key
        target.write_text(value)

    def exists(self, key: str) -> bool:
        path = Path(key)
        target = path if path.is_absolute() else self.root / key
        return target.exists()

    def list(self, prefix: str = "") -> List[str]:
        # List only relative names within the root
        return [f.name for f in self.root.glob(f"{prefix}*") if f.is_file()]
class RemoteStore(BaseStore):
    """
    SSP-compliant storage implementation.
    Connects to an external state-stream to ensure sovereign persistence.
    """
    def __init__(self, endpoint: str = "http://nss-bridge.local"):
        self.endpoint = endpoint
        import requests
        self.session = requests.Session()

    def get(self, key: str) -> Optional[str]:
        try:
            response = self.session.get(f"{self.endpoint}/ssp/node/{key}")
            if response.status_code == 200:
                return response.text
        except Exception as e:
            # Silence network errors during transition
            pass
        return None

    def set(self, key: str, value: str) -> None:
        try:
            self.session.post(f"{self.endpoint}/ssp/node/{key}", data=value)
        except Exception:
            pass

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def list(self, prefix: str = "") -> List[str]:
        try:
            # SSP /ssp/vector is used for listing nodes
            response = self.session.get(f"{self.endpoint}/ssp/vector")
            if response.status_code == 200:
                vector = json.loads(response.text)
                return [node["@id"] for node in vector.get("nodes", []) if node["@id"].startswith(prefix)]
        except Exception:
            pass
        return []

class EventLog:
    """
    Handles the immutable, append-only log of cognitive events.
    """
    def __init__(self, store: BaseStore, log_key: str = "sovereign_log.jsonl"):
        self.store = store
        self.log_key = log_key

    def append(self, event_type: str, payload: Any) -> int:
        import datetime
        import hashlib
        import json

        # Retrieve current log to get sequence and prev_hash
        log_data = self.store.get(self.log_key) or ""
        lines = log_data.splitlines()
        
        seq = len(lines)
        prev_hash = ""
        if lines:
            last_event = json.loads(lines[-1])
            # Simulating a hash for the chain
            prev_hash = hashlib.sha256(lines[-1].encode()).hexdigest()

        event = {
            "seq": seq,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_type": event_type,
            "payload": payload,
            "prev_hash": prev_hash,
        }
        
        event_json = json.dumps(event)
        self.store.set(self.log_key, log_data + event_json + "\n")
        return seq

    def get_events(self, since_seq: int = 0) -> List[Dict[str, Any]]:
        log_data = self.store.get(self.log_key) or ""
        lines = log_data.splitlines()
        events = []
        for i in range(since_seq, len(lines)):
            events.append(json.loads(lines[i]))
        return events

class StateClient:
    """
    The StateClient is the abstraction layer between the Cortex's reasoning 
    and the physical storage of its state.
    """
    def __init__(self, store: BaseStore):
        self.store = store
        self.vector_key = "state_vector.json"
        self.blob_key = "state_blob.json"
        self.log = EventLog(store)

    def log_event(self, event_type: str, payload: Any) -> int:
        """Record a cognitive transition in the Sovereign Event Stream."""
        return self.log.append(event_type, payload)

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
                # Use the store abstraction exclusively.
                # The store (Local/Remote) handles path resolution.
                content = self.store.get(source_path)
                if content:
                    return content
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

    def find_last_checkpoint_seq(self) -> int:
        """Find the sequence number of the most recent SURETY_CHECKPOINT."""
        events = self.log.get_events(since_seq=0)
        for event in reversed(events):
            if event["event_type"] == "SURETY_CHECKPOINT":
                return event["seq"]
        return -1

    def project_resonance(self, since_seq: int = 0, initial_vector: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Reconstructs the StateVector by replaying the Sovereign Event Stream.
        If initial_vector is provided, it serves as the base for replay.
        """
        events = self.log.get_events(since_seq=since_seq)
        
        if initial_vector:
            vector = initial_vector
        elif since_seq == 0:
            vector = {"@context": "https://schema.org/", "@id": "talos:state-vector", "version": "0.1", "nodes": [], "edges": []}
        else:
            vector = self.get_vector()

        nodes = {node["@id"]: node for node in vector.get("nodes", [])}
        
        for event in events:
            etype = event["event_type"]
            payload = event["payload"]
            
            if etype == "MEMORY_MUTATION":
                path = payload.get("path")
                if path:
                    import pathlib
                    node_id = f"talos:{pathlib.Path(path).stem}"
                    
                    if node_id not in nodes:
                        nodes[node_id] = {
                            "@id": node_id,
                            "type": "StateNode",
                            "source": path,
                            "label": pathlib.Path(path).stem
                        }
                    else:
                        nodes[node_id]["source"] = path
            
            elif etype == "SURETY_CHECKPOINT":
                vector["last_surety_hash"] = payload.get("git_hash")
                vector["last_focus"] = payload.get("focus")

            elif etype == "HYDRATION":
                pass

        vector["nodes"] = list(nodes.values())
        return vector

    def list_nodes(self) -> List[Dict[str, Any]]:
        """Return all nodes in the current vector."""
        return self.get_vector().get("nodes", [])