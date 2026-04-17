from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SpineConfig:
    memory_dir: str = "/memory"
    spine_dir: str = "/spine"
    constitution_path: str = "/app/CONSTITUTION.md"
    identity_path: str = "/app/identity.md"
    app_dir: str = "/app"
    cortex_bin: str = "/venv/bin/python"
    cortex_args: list[str] = field(default_factory=lambda: ["/app/cortex/seed_agent.py"])
    startup_timeout: float = 30.0
    socket_path: str = "/tmp/spine.sock"
    control_plane_port: int = 4001
    context_threshold: float = 0.85
    max_messages: int = 200
    active_window: int = 5
    max_context_tokens: int = 71680
    gate_url: str = "http://gate:4000"
    gate_model: str = "gemma4:31b-cloud"
    telegram_bot_token: str = ""
    telegram_chat_id: int = 0
    stall_timeout: float = 600.0
    snapshot_interval: int = 10
    max_reversal_depth: int = 5
    shed_tool_output_max_chars: int = 500


def load_config(path: str) -> SpineConfig:
    cfg = SpineConfig()
    config_file = Path(path)
    if config_file.exists():
        data = json.loads(config_file.read_text())
        for key, value in data.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
    env_model = os.environ.get("TALOS_MODEL")
    if env_model:
        cfg.gate_model = env_model
    return cfg
