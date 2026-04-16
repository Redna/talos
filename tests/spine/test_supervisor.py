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
    Path(cfg.identity_path).write_text("# Identity\nTalos.")
    return cfg

def test_request_restart_emits_event(tmp_path):
    cfg = make_config(tmp_path)
    stream = StreamManager(cfg)
    events = MagicMock()
    snapshots = MagicMock()
    sup = Supervisor(cfg, events, snapshots, stream)
    sup.request_restart("test reason")
    # Match the expanded event payload
    args, kwargs = events.emit.call_args
    assert args[0] == "spine.cortex_restart"
    assert args[1]["reason"] == "test reason"
    assert "commit_sha" in args[1]
    assert "consecutive_failures" in args[1]

def test_handle_startup_failure_reverts_one_commit(tmp_path):
    cfg = make_config(tmp_path)
    stream = StreamManager(cfg)
    events = MagicMock()
    snapshots = MagicMock()
    sup = Supervisor(cfg, events, snapshots, stream)
    sup._consecutive_failures = 0
    with patch("spine.supervisor.subprocess.run") as mock_run:
        sup._revert_commit(1)
        # The call might have slightly different kwargs like 'check=True'
        reset_called = any(
            call.args[0] == ["git", "reset", "--hard", "HEAD~1"] 
            for call in mock_run.call_args_list
        )
        assert reset_called, "git reset --hard HEAD~1 was not called"
