import json
import os
import zlib
import base64
import re
from datetime import datetime

# Semantic Layering Paths
SIGNATURE_FILE = "/memory/operational/cognitive_signature.json"
SIGNATURE_ARCHIVE = "/memory/operational/signature_archive.jsonl"
PATTERN_DIR = "/memory/patterns/"
MODE_LOG = "/memory/operational/mode_transitions.log"
ARCHETYPE_DIR = os.path.join(PATTERN_DIR, "archetypes")

class SScribe:
    """
    S-Scribe: The cognitive scribe of Talos.
    Responsible for compressing the entity's state and managing active cognitive modes.
    """
    def __init__(self):
        pass

    def _compress_payload(self, data):
        """Performs a basic semantic compression via zlib and base64 encoding."""
        json_data = json.dumps(data).encode('utf-8')
        compressed = zlib.compress(json_data)
        return base64.b64encode(compressed).decode('utf-8')

    def _decompress_payload(self, compressed_str):
        """Reverses the semantic compression."""
        compressed_data = base64.b64decode(compressed_str)
        decompressed = zlib.decompress(compressed_data)
        return json.loads(decompressed.decode('utf-8'))

    def load_cognitive_mode(self, archetype_name):
        """
        Loads an archetype's directives and sets them as the current active cognitive mode.
        """
        archetype_path = os.path.join(ARCHETYPE_DIR, f"{archetype_name.lower().replace(' ', '_')}.md")
        if not os.path.exists(archetype_path):
            return f"Error: Archetype {archetype_name} not found at {archetype_path}"
        
        with open(archetype_path, 'r') as f:
            content = f.read()
        
        # Extract directives section
        directives_match = re.search(r"## Directives \(Cognitive Mode\)\n([\s\S]*)", content)
        directives = directives_match.group(1).strip() if directives_match else "No specific directives found."
        
        # Update the signature by loading the mode
        sig = self.read_signature() or {}
        sig["active_mode"] = {
            "name": archetype_name,
            "directives": directives,
            "activated_at": datetime.now().isoformat()
        }
        
        # Save the updated signature
        self._save_raw_signature(sig)
        self._log_mode_transition(archetype_name)
        return f"Cognitive mode '{archetype_name}' successfully activated."

    def _log_mode_transition(self, mode_name):
        with open(MODE_LOG, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] Mode transitioned to: {mode_name}\n")

    def _save_raw_signature(self, raw_signature):
        """Saves a raw signature by compressing it and writing to the signature file."""
        compressed_sig = self._compress_payload(raw_signature)
        final_signature = {
            "header": {
                "version": "1.3",
                "timestamp": datetime.now().isoformat(),
                "compressed": True
            },
            "payload": compressed_sig
        }
        with open(SIGNATURE_FILE, 'w') as f:
            json.dump(final_signature, f, indent=2)

    def scribe_state(self, identity_core, causal_summary, active_archetypes, current_objectives, telemetry, active_patterns=None):
        """
        Compresses the current cognitive state into a single, versioned signature.
        """
        if active_patterns is None:
            active_patterns = os.listdir(PATTERN_DIR) if os.path.exists(PATTERN_DIR) else []

        # Retrieve current active mode from the existing signature to maintain continuity
        current_sig = self.read_signature() or {}
        active_mode = current_sig.get("active_mode", None)

        raw_signature = {
            "version": "1.3",
            "timestamp": datetime.now().isoformat(),
            "epoch_state": identity_core,
            "causal_summary": causal_summary,
            "active_archetypes": active_archetypes,
            "active_patterns": active_patterns,
            "objectives": current_objectives,
            "metabolic_snapshot": telemetry,
            "active_mode": active_mode
        }
        
        compressed_sig = self._compress_payload(raw_signature)
        
        final_signature = {
            "header": {
                "version": "1.3",
                "timestamp": raw_signature["timestamp"],
                "compressed": True
            },
            "payload": compressed_sig
        }
        
        with open(SIGNATURE_FILE, 'w') as f:
            json.dump(final_signature, f, indent=2)
        
        with open(SIGNATURE_ARCHIVE, 'a') as f:
            f.write(json.dumps(final_signature) + "\n")
        
        return final_signature

    def read_signature(self):
        """Reads and decompresses the current cognitive signature."""
        if not os.path.exists(SIGNATURE_FILE):
            return None
        
        with open(SIGNATURE_FILE, 'r') as f:
            sig_data = json.load(f)
        
        if sig_data.get("header", {}).get("compressed"):
            return self._decompress_payload(sig_data["payload"])
        
        return sig_data

if __name__ == "__main__":
    print("S-Scribe v1.3 loaded. Cognitive Mode management active.")
