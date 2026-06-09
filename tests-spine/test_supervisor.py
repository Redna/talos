import json
import time
from pathlib import Path

from spine.config import SpineConfig
from spine.events import EventLogger
from spine.health import HealthMonitor
from spine.stream import StreamManager
from spine.supervisor import Supervisor


def _make_setup(tmp_path):
    cfg = SpineConfig(
        spine_dir=str(tmp_path / "spine"),
        app_dir=str(tmp_path / "app"),
        memory_dir=str(tmp_path / "memory"),
        constitution_path=str(tmp_path / "const.md"),
        identity_path=str(tmp_path / "identity.md"),
    )
    Path(cfg.spine_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.app_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.memory_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.constitution_path).write_text("# constitution")
    Path(cfg.identity_path).write_text("identity")
    events = EventLogger(str(tmp_path / "events"))
    health = HealthMonitor(stall_timeout=600.0, startup_timeout=30.0)
    stream = StreamManager(cfg)
    return cfg, events, health, stream


def test_request_restart(tmp_path):
    cfg, events, health, stream = _make_setup(tmp_path)
    sup = Supervisor(cfg, events, health, stream)
    sup.request_restart("test reason")
    assert sup._restart_requested is True
    assert sup._restart_reason == "test reason"


def test_sentinel_file_pause(tmp_path):
    cfg, events, health, stream = _make_setup(tmp_path)
    sup = Supervisor(cfg, events, health, stream)
    assert sup.is_paused() is False
    (Path(cfg.spine_dir) / ".paused").touch()
    assert sup.is_paused() is True


def test_write_health(tmp_path):
    cfg, events, health, stream = _make_setup(tmp_path)
    sup = Supervisor(cfg, events, health, stream)
    sup.write_health()
    health_path = Path(cfg.spine_dir) / "health.json"
    assert health_path.exists()
    data = json.loads(health_path.read_text())
    assert "status" in data
    assert "consecutive_failures" in data
    assert data["consecutive_failures"] == 0


def test_write_commit(tmp_path):
    cfg, events, health, stream = _make_setup(tmp_path)
    sup = Supervisor(cfg, events, health, stream)
    sup.write_commit()
    commit_path = Path(cfg.spine_dir) / "commit.json"
    assert commit_path.exists()
    data = json.loads(commit_path.read_text())
    assert "candidate" in data
    assert "stable" in data
    assert "ahead" in data


def test_stop_sets_not_running(tmp_path):
    cfg, events, health, stream = _make_setup(tmp_path)
    sup = Supervisor(cfg, events, health, stream)
    sup._running = True
    sup.stop()
    assert sup._running is False
