import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from spine.config import SpineConfig, load_config


def test_default_config():
    cfg = SpineConfig()
    assert cfg.memory_dir == "/memory"
    assert cfg.socket_path == "/tmp/spine.sock"
    assert cfg.context_threshold == 0.85
    assert cfg.active_window == 5
    assert cfg.max_reversal_depth == 5


def test_load_config_missing_file():
    cfg = load_config("/nonexistent/path/config.json")
    assert cfg == SpineConfig()


def test_load_config_overrides(tmp_path):
    config_data = {
        "socket_path": "/custom/spine.sock",
        "context_threshold": 0.9,
        "active_window": 10,
    }
    config_file = tmp_path / "spine_config.json"
    config_file.write_text(json.dumps(config_data))
    cfg = load_config(str(config_file))
    assert cfg.socket_path == "/custom/spine.sock"
    assert cfg.context_threshold == 0.9
    assert cfg.active_window == 10
    assert cfg.memory_dir == "/memory"


def test_load_config_unknown_keys_ignored(tmp_path):
    config_data = {"unknown_key": "value", "socket_path": "/test.sock"}
    config_file = tmp_path / "spine_config.json"
    config_file.write_text(json.dumps(config_data))
    cfg = load_config(str(config_file))
    assert cfg.socket_path == "/test.sock"
    assert not hasattr(cfg, "unknown_key")
