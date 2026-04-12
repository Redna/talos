from unittest.mock import MagicMock, patch

from spine.supervisor import Supervisor
from spine.config import SpineConfig
from spine.stream import StreamManager
from pathlib import Path


def make_config(tmp_path):
    cfg = SpineConfig()
    cfg.app_dir = str(tmp_path)
    cfg.constitution_path = str(tmp_path / "CONSTITUTION.md")
    cfg.identity_path = str(tmp_path / "identity.md")
    Path(cfg.constitution_path).write_text("# Principles\nAgency.")
    Path(cfg.identity_path).write_text("# Identity\nYou are Talos.")
    return cfg


def test_request_restart_emits_event(tmp_path):
    cfg = make_config(tmp_path)
    stream = StreamManager(cfg)
    events = MagicMock()
    snapshots = MagicMock()
    sup = Supervisor(cfg, events, snapshots, stream)
    sup.request_restart("test reason")
    events.emit.assert_called_once_with(
        "spine.cortex_restart", {"reason": "test reason"}
    )


def test_handle_startup_failure_reverts_one_commit(tmp_path):
    cfg = make_config(tmp_path)
    stream = StreamManager(cfg)
    events = MagicMock()
    snapshots = MagicMock()
    sup = Supervisor(cfg, events, snapshots, stream)
    sup._consecutive_failures = 0
    with patch("spine.supervisor.subprocess.run") as mock_run:
        sup._revert_commit(1)
        mock_run.assert_any_call(
            ["git", "reset", "--hard", "HEAD~1"],
            cwd=cfg.app_dir,
            capture_output=True,
        )


def test_consecutive_failures_increment(tmp_path):
    cfg = make_config(tmp_path)
    stream = StreamManager(cfg)
    events = MagicMock()
    snapshots = MagicMock()
    sup = Supervisor(cfg, events, snapshots, stream)
    sup._consecutive_failures = 0
    with patch.object(sup, "_revert_commit"):
        sup._handle_cortex_exit(1)
    assert sup._consecutive_failures == 1
