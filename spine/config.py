import json
from dataclasses import dataclass, fields


@dataclass
class SpineConfig:
    gate_url: str = "http://localhost:4000/v1/chat/completions"
    socket_path: str = "/tmp/spine.sock"
    spine_dir: str = "/spine"
    app_dir: str = "/app"
    memory_dir: str = "/memory"
    constitution_path: str = "/app/CONSTITUTION.md"
    identity_path: str = "/app/identity.md"
    context_threshold_pct: float = 0.85
    telegram_bot_token: str = ""
    telegram_chat_id: str = "0"
    control_plane_port: int = 4001
    snapshot_interval: int = 50


def load_config(path: str) -> SpineConfig:
    cfg = SpineConfig()
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return cfg
    valid_fields = {f.name for f in fields(SpineConfig)}
    for k, v in data.items():
        if k in valid_fields:
            setattr(cfg, k, v)
    return cfg
