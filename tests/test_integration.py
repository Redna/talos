import json
import pytest
from pathlib import Path
from spine.config import SpineConfig
from spine.stream import StreamManager
from spine.events import EventLogger
from spine.health import HealthMonitor
from spine.supervisor import Supervisor


@pytest.fixture
def full_setup(tmp_path):
    cfg = SpineConfig()
    cfg.socket_path = str(tmp_path / "test.sock")
    cfg.spine_dir = str(tmp_path / "spine")
    cfg.constitution_path = str(tmp_path / "CONSTITUTION.md")
    cfg.identity_path = str(tmp_path / "identity.md")
    cfg.memory_dir = str(tmp_path / "memory")
    cfg.app_dir = str(tmp_path / "app")
    Path(cfg.constitution_path).write_text("# Principles\nAgency.")
    Path(cfg.identity_path).write_text("# Identity\nTalos.")
    Path(cfg.spine_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.memory_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.app_dir).mkdir(parents=True, exist_ok=True)
    events = EventLogger(str(Path(cfg.spine_dir) / "events"))
    stream = StreamManager(cfg)
    health = HealthMonitor(stall_timeout=600.0, startup_timeout=30.0)
    supervisor = Supervisor(cfg, events, health, stream)
    return cfg, stream, supervisor, events


def test_stream_fork_and_state_file(full_setup):
    """Test that fold archives trajectory, resets messages, and writes state."""
    cfg, stream, supervisor, events = full_setup
    stream.add_message({"role": "user", "content": "hello"})
    stream.add_message({"role": "assistant", "content": "thinking..."})
    stream.add_message({"role": "tool", "tool_call_id": "c1", "content": "result"})
    stream.write_state(focus="testing", context_pct=0.5)

    state_file = Path(cfg.spine_dir) / "state.json"
    assert state_file.exists()

    count_before = len(stream.messages)
    stream.fold("Synthesis of the conversation")

    assert len(stream.messages) == 2
    assert stream.messages[-1]["content"] == "Synthesis of the conversation"

    archive_dir = Path(cfg.spine_dir) / "trajectories"
    archives = list(archive_dir.glob("*.json"))
    assert len(archives) == 1
    archived = json.loads(archives[0].read_text())
    assert len(archived) == count_before


def test_supervisor_writes_health(full_setup):
    """Test that supervisor writes health.json."""
    cfg, stream, supervisor, events = full_setup
    supervisor.write_health()
    health_file = Path(cfg.spine_dir) / "health.json"
    assert health_file.exists()
    data = json.loads(health_file.read_text())
    assert "status" in data


def test_supervisor_writes_commit(full_setup):
    """Test that supervisor writes commit.json."""
    cfg, stream, supervisor, events = full_setup
    supervisor.write_commit()
    commit_file = Path(cfg.spine_dir) / "commit.json"
    assert commit_file.exists()


def test_cortex_tool_registry_integration():
    """Test tool registry with all tool registrations."""
    from tool_registry import ToolRegistry
    from unittest.mock import MagicMock
    from state import AgentState
    from tools.executive import register_executive_tools
    from tools.file_ops import register_file_ops_tools
    from tools.physical import register_physical_tools
    from tools.git_ops import register_git_ops_tools

    reg = ToolRegistry()
    client = MagicMock()
    state = AgentState(Path("/tmp/test_integration_state"))

    register_executive_tools(reg, client, state)
    register_file_ops_tools(reg, client)
    register_physical_tools(reg, client)
    register_git_ops_tools(reg, client)

    schemas = reg.get_schemas()
    assert len(schemas) >= 13  # 4 executive + 3 file_ops + 3 physical + 3 git_ops

    names = [s["function"]["name"] for s in schemas]
    assert "set_focus" in names
    assert "fold_context" in names
    assert "bash_command" in names
    assert "read_file" in names
    assert "write_file" in names
    assert "git_commit" in names


def test_stall_detection_in_stream(full_setup):
    """Test stall detection across stream messages."""
    cfg, stream, supervisor, events = full_setup
    for _ in range(6):
        stream.add_message(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {"name": "bash_command"},
                        "id": "c1",
                        "type": "function",
                    }
                ],
            }
        )
        stream.add_message({"role": "tool", "tool_call_id": "c1", "content": "output"})

    assert stream.detect_stall()
    assert stream._stall_notices_sent >= 1


def test_memory_directory_scan_in_hud(full_setup):
    """Test HUD builder scans /memory/ for .md files."""
    from seed_agent import _build_hud
    from state import AgentState

    cfg, stream, supervisor, events = full_setup
    memory_dir = Path(cfg.memory_dir)
    (memory_dir / "focus.md").write_text("# Focus")
    (memory_dir / "lessons.md").write_text("# Lessons")
    (memory_dir / "roadmap.md").write_text("# Roadmap")

    state = AgentState(memory_dir)
    hud = _build_hud(state)
    assert hud["memory_file_count"] == 3
    assert (
        "focus.md" in hud["last_files"]
        or "lessons.md" in hud["last_files"]
        or "roadmap.md" in hud["last_files"]
    )
