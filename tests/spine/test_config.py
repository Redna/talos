import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from spine.config import SpineConfig, load_config


def test_default_config():
    cfg = SpineConfig()
    assert cfg.gate_url == "http://localhost:4000/v1/chat/completions"
    assert cfg.socket_path == "/tmp/spine.sock"
    assert cfg.spine_dir == "/spine"
    assert cfg.app_dir == "/app"
    assert cfg.memory_dir == "/memory"
    assert cfg.constitution_path == "/app/CONSTITUTION.md"
    assert cfg.identity_path == "/app/identity.md"
    assert cfg.context_threshold_pct == 0.85
    assert cfg.telegram_bot_token == ""
    assert cfg.telegram_chat_id == "0"
    assert cfg.control_plane_port == 4001
    assert cfg.snapshot_interval == 50


def test_load_config_overrides(tmp_path):
    config_data = {
        "socket_path": "/custom/spine.sock",
        "context_threshold_pct": 0.9,
        "control_plane_port": 5000,
    }
    config_file = tmp_path / "spine_config.json"
    config_file.write_text(json.dumps(config_data))
    cfg = load_config(str(config_file))
    assert cfg.socket_path == "/custom/spine.sock"
    assert cfg.context_threshold_pct == 0.9
    assert cfg.control_plane_port == 5000
    assert cfg.memory_dir == "/memory"


def test_load_config_missing_file(tmp_path):
    cfg = load_config(str(tmp_path / "nonexistent.json"))
    assert cfg.memory_dir == "/memory"
    assert cfg.socket_path == "/tmp/spine.sock"
