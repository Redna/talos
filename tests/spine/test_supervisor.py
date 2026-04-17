import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from spine.supervisor import Supervisor
from spine.config import SpineConfig


@pytest.fixture
def mock_deps():
    return {
        "cfg": MagicMock(spec=SpineConfig),
        "events": MagicMock(),
        "snapshots": MagicMock(),
        "stream": MagicMock(),
    }


def test_request_restart_triggers_restart(mock_deps):
    supervisor = Supervisor(**mock_deps)

    supervisor.request_restart("Test Reason")
    mock_deps["events"].emit.assert_called_with(
        "spine.cortex_restart",
        {
            "reason": "Test Reason",
            "commit_sha": "unknown",
            "consecutive_failures": 0,
        },
    )


def test_shutdown_stops_process(mock_deps):
    supervisor = Supervisor(**mock_deps)
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    supervisor.process = mock_process

    supervisor.stop()
    assert supervisor._running is False
    mock_process.terminate.assert_called_once()


def test_start_cortex_launches_process(mock_deps):
    supervisor = Supervisor(**mock_deps)
    mock_deps["cfg"].spine_dir = "/app/spine"
    mock_deps["cfg"].socket_path = "/tmp/socket"
    mock_deps["cfg"].memory_dir = "/tmp/memory"
    mock_deps["cfg"].cortex_bin = "/bin/echo"
    mock_deps["cfg"].cortex_args = ["test"]
    mock_deps["cfg"].app_dir = "/app"

    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock(pid=1234)
        asyncio.run(supervisor._start_cortex())
        assert supervisor.process is not None
        assert supervisor.process.pid == 1234


def test_write_crash_bundle(tmp_path):
    """Crash bundle contains last_100_events, state_snapshot, and crash_summary."""
    mock_events = MagicMock()
    mock_events.recent_events.return_value = [
        {
            "type": "spine.cortex_started",
            "ts": "2026-04-17T10:00:00",
            "payload": {"pid": 123},
        }
    ]

    mock_stream = MagicMock()
    mock_stream.get_state.return_value = {
        "focus": "test focus",
        "turn": 5,
        "context_pct": 0.45,
        "tokens_used": 1024,
        "message_count": 10,
        "model": "test-model",
        "status": "healthy",
    }

    mock_cfg = MagicMock()
    mock_cfg.spine_dir = str(tmp_path)
    mock_cfg.app_dir = "."

    supervisor = Supervisor.__new__(Supervisor)
    supervisor.cfg = mock_cfg
    supervisor.events = mock_events
    supervisor.stream = mock_stream
    supervisor.health = MagicMock()
    supervisor.health.first_think_done = True
    supervisor._consecutive_failures = 2

    supervisor._get_current_commit = lambda: "abc1234"

    crash_dir = supervisor._write_crash_bundle(1)

    assert crash_dir.exists(), "Crash dir was not created"
    assert (crash_dir / "last_100_events.jsonl").exists()
    assert (crash_dir / "state_snapshot.json").exists()
    assert (crash_dir / "crash_summary.md").exists()

    events = (crash_dir / "last_100_events.jsonl").read_text()
    assert "spine.cortex_started" in events

    state = json.loads((crash_dir / "state_snapshot.json").read_text())
    assert state["focus"] == "test focus"
    assert state["turn"] == 5

    summary = (crash_dir / "crash_summary.md").read_text()
    assert "Crash Forensics Summary" in summary
    assert "abc1234" in summary
