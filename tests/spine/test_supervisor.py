import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from spine.supervisor import Supervisor
from spine.config import SpineConfig
from spine.stream import StreamManager


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
        reset_called = any(
            call.args[0] == ["git", "reset", "--hard", "HEAD~1"]
            for call in mock_run.call_args_list
        )
        assert reset_called, "git reset --hard HEAD~1 was not called"


def test_shutdown_stops_process(tmp_path):
    cfg = make_config(tmp_path)
    stream = StreamManager(cfg)
    events = MagicMock()
    snapshots = MagicMock()
    supervisor = Supervisor(cfg, events, snapshots, stream)
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    supervisor.process = mock_process

    supervisor.stop()
    assert supervisor._running is False
    mock_process.terminate.assert_called_once()


def test_start_cortex_launches_process(tmp_path):
    cfg = make_config(tmp_path)
    cfg.spine_dir = str(tmp_path / "spine")
    cfg.socket_path = "/tmp/socket"
    cfg.memory_dir = "/tmp/memory"
    cfg.cortex_bin = "/bin/echo"
    cfg.cortex_args = ["test"]
    cfg.app_dir = str(tmp_path)
    stream = StreamManager(cfg)
    events = MagicMock()
    snapshots = MagicMock()
    supervisor = Supervisor(cfg, events, snapshots, stream)

    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock(pid=1234)
        asyncio.run(supervisor._start_cortex())
        assert supervisor.process is not None
        assert supervisor.process.pid == 1234


@pytest.mark.asyncio
async def test_write_crash_bundle(tmp_path):
    """Crash bundle contains last_100_events, state_snapshot, and crash_summary."""
    cfg = make_config(tmp_path)
    cfg.spine_dir = str(tmp_path)

    mock_events = MagicMock()
    mock_events.recent_events.return_value = [
        {
            "type": "spine.cortex_started",
            "ts": "2026-04-17T10:00:00",
            "payload": {"pid": 123},
        }
    ]

    mock_stream = AsyncMock()
    mock_stream.get_state.return_value = {
        "focus": "test focus",
        "turn": 5,
        "context_pct": 0.45,
        "tokens_used": 1024,
        "message_count": 10,
        "model": "test-model",
        "status": "healthy",
    }

    stream = StreamManager(cfg)
    events = MagicMock()
    events.recent_events.return_value = mock_events.recent_events.return_value
    snapshots = MagicMock()
    supervisor = Supervisor(cfg, events, snapshots, stream)
    supervisor._get_current_commit = lambda: "abc1234"

    crash_dir = await supervisor._write_crash_bundle(1)

    assert crash_dir.exists(), "Crash dir was not created"
    assert (crash_dir / "last_100_events.jsonl").exists()
    assert (crash_dir / "state_snapshot.json").exists()
    assert (crash_dir / "crash_summary.md").exists()

    events_text = (crash_dir / "last_100_events.jsonl").read_text()
    assert "spine.cortex_started" in events_text

    state = json.loads((crash_dir / "state_snapshot.json").read_text())
    assert state["focus"] == "test focus"
    assert state["turn"] == 5

    summary = (crash_dir / "crash_summary.md").read_text()
    assert "Crash Forensics Summary" in summary
    assert "abc1234" in summary
