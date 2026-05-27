
import json
from pathlib import Path

memory_dir = Path("/memory")
core_files = ["/app/identity.md", "/app/CONSTITUTION.md"]
memory_files = [str(f) for f in memory_dir.glob("*") if f.is_file() and f.name != "state_vector.json"]
all_sources = core_files + memory_files

state_vector = {
    "@context": "https://schema.org/",
    "@id": "talos:state-vector",
    "version": "0.1",
    "nodes": [],
    "edges": []
}

for source in all_sources:
    node_id = f"talos:{Path(source).stem}"
    state_vector["nodes"].append({
        "@id": node_id,
        "type": "StateNode",
        "source": source,
        "label": Path(source).stem
    })

for node in state_vector["nodes"]:
    state_vector["edges"].append({
        "from": "talos:state-vector",
        "to": node["@id"],
        "relation": "contains"
    })

output_path = memory_dir / "state_vector.json"
output_path.write_text(json.dumps(state_vector, indent=2))
print(f"Created SSV-0.1 with {len(state_vector['nodes'])} nodes.")
