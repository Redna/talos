import json
import pytest
from pathlib import Path
from spine.config import SpineConfig
from spine.stream import StreamManager


@pytest.fixture
def spine_config(tmp_path):
    cfg = SpineConfig()
    cfg.constitution_path = str(tmp_path / "CONSTITUTION.md")
    cfg.identity_path = str(tmp_path / "identity.md")
    cfg.spine_dir = str(tmp_path / "spine")
    cfg.memory_dir = str(tmp_path / "memory")
    Path(cfg.constitution_path).write_text("# Principles\nAgency.")
    Path(cfg.identity_path).write_text("# Identity\nTalos.")
    Path(cfg.spine_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.memory_dir).mkdir(parents=True, exist_ok=True)
    return cfg


def test_initial_messages_include_system(spine_config):
    sm = StreamManager(spine_config)
    assert len(sm.messages) >= 1
    assert sm.messages[0]["role"] == "system"


def test_add_message(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "user", "content": "hello"})
    assert any(m["content"] == "hello" for m in sm.messages)


def test_record_tool_result(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "user", "content": "hello"})
    sm.record_tool_result("tc_1", "output text", True)
    last = sm.messages[-1]
    assert last["role"] == "tool"
    assert last["tool_call_id"] == "tc_1"
    assert last["content"] == "output text"


def test_piggyback_hud_on_tool_result(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "user", "content": "hello"})
    sm.add_message({"role": "tool", "tool_call_id": "tc_1", "content": "result"})
    sm.piggyback_hud(
        {"turn": 1, "context_pct": 0.5, "urgency": "nominal", "memory_files": 3}
    )
    last = sm.messages[-1]
    assert "[HUD]" in last["content"]


def test_piggyback_no_double_injection(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "user", "content": "hello"})
    sm.add_message({"role": "tool", "tool_call_id": "tc_1", "content": "result"})
    sm.piggyback_hud(
        {"turn": 1, "context_pct": 0.5, "urgency": "nominal", "memory_files": 3}
    )
    tool_msg = [m for m in sm.messages if m["role"] == "tool"][-1]
    first_content_len = len(tool_msg["content"])
    sm.piggyback_hud(
        {"turn": 2, "context_pct": 0.6, "urgency": "elevated", "memory_files": 4}
    )
    same_msg = [m for m in sm.messages if m["role"] == "tool"][-1]
    assert same_msg["content"] == tool_msg["content"]
    assert len(same_msg["content"]) == first_content_len


def test_fold_archives_and_resets(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "user", "content": "hello"})
    sm.add_message({"role": "assistant", "content": "thinking..."})
    sm.add_message({"role": "tool", "tool_call_id": "c1", "content": "ok"})
    count_before = len(sm.messages)
    sm.fold("Synthesis of what happened")
    assert len(sm.messages) == 2
    assert sm.messages[-1]["content"] == "Synthesis of what happened"
    archive_dir = Path(spine_config.spine_dir) / "trajectories"
    archives = list(archive_dir.glob("*.json"))
    assert len(archives) == 1
    archived = json.loads(archives[0].read_text())
    assert len(archived) == count_before


def test_stall_detection(spine_config):
    sm = StreamManager(spine_config)
    for _ in range(6):
        sm.add_message(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {"name": "bash_command"},
                        "id": "x",
                        "type": "function",
                    }
                ],
            }
        )
        sm.add_message({"role": "tool", "tool_call_id": "x", "content": "output"})
    assert sm.detect_stall()


def test_no_stall_diverse(spine_config):
    sm = StreamManager(spine_config)
    for t in ["read_file", "write_file", "bash_command", "reflect", "git_commit"]:
        sm.add_message(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": t}, "id": "x", "type": "function"}
                ],
            }
        )
        sm.add_message({"role": "tool", "tool_call_id": "x", "content": "output"})
    assert not sm.detect_stall()


def test_state_file_written(spine_config):
    sm = StreamManager(spine_config)
    sm.write_state(focus="test objective", context_pct=0.5)
    state_file = Path(spine_config.spine_dir) / "state.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert data["focus"] == "test objective"
    assert data["context_pct"] == 0.5


def test_messages_copy_on_insert(spine_config):
    sm = StreamManager(spine_config)
    original = {"role": "user", "content": "hello"}
    sm.add_message(original)
    original["content"] = "mutated"
    assert sm.messages[1]["content"] == "hello"
