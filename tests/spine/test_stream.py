import json
from pathlib import Path

import pytest

from spine.stream import StreamManager, STALL_WINDOW, STALL_THRESHOLD
from spine.config import SpineConfig


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


def test_messages_append_only(spine_config):
    sm = StreamManager(spine_config)
    initial_len = len(sm.messages)
    sm.add_message({"role": "user", "content": "hello"})
    sm.add_message({"role": "assistant", "content": "hi"})
    assert len(sm.messages) == initial_len + 2
    assert sm.messages[-2]["content"] == "hello"
    assert sm.messages[-1]["content"] == "hi"


def test_fold_archives_and_resets(spine_config):
    sm = StreamManager(spine_config)
    sm.turn = 5
    sm.add_message({"role": "user", "content": "work"})
    sm.add_message({"role": "assistant", "content": "thinking"})
    msg_count = len(sm.messages)
    sm.fold("synthesis of past work")
    traj_dir = Path(spine_config.spine_dir) / "trajectories"
    assert traj_dir.exists()
    traj_files = list(traj_dir.glob("*.json"))
    assert len(traj_files) == 1
    archived = json.loads(traj_files[0].read_text())
    assert len(archived) == msg_count
    assert len(sm.messages) == 2
    assert sm.messages[0]["role"] == "system"
    assert sm.messages[1]["role"] == "assistant"
    assert sm.messages[1]["content"] == "synthesis of past work"
    assert sm.turn == 0


def test_hud_piggyback(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "tool", "tool_call_id": "tc1", "content": "result"})
    sm.piggyback_hud(
        {
            "turn": 3,
            "context_pct": 0.45,
            "urgency": "nominal",
            "memory_files": 5,
            "focus": "stay on task",
        }
    )
    tool_msgs = [m for m in sm.messages if m["role"] == "tool"]
    assert len(tool_msgs) == 1
    assert "[HUD]" in tool_msgs[0]["content"]
    assert "turn=3" in tool_msgs[0]["content"]
    assert "context_pct=0.45" in tool_msgs[0]["content"]
    assert "urgency=nominal" in tool_msgs[0]["content"]
    assert "memory_files=5" in tool_msgs[0]["content"]
    assert "focus=stay on task" in tool_msgs[0]["content"]


def test_hud_piggyback_no_tool_message(spine_config):
    sm = StreamManager(spine_config)
    sm.piggyback_hud(
        {
            "turn": 1,
            "context_pct": 0.2,
            "urgency": "elevated",
            "memory_files": 0,
            "focus": "none",
        }
    )
    user_msgs = [m for m in sm.messages if m["role"] == "user"]
    assert len(user_msgs) == 1
    assert "[HUD]" in user_msgs[0]["content"]


def test_stall_detection(spine_config):
    sm = StreamManager(spine_config)
    for i in range(6):
        sm.add_message(
            {
                "role": "assistant",
                "content": f"turn {i}",
                "tool_calls": [
                    {
                        "id": f"c{i}",
                        "type": "function",
                        "function": {"name": "bash", "arguments": "{}"},
                    }
                ],
            }
        )
    assert sm.detect_stall() is True


def test_no_stall_diverse(spine_config):
    sm = StreamManager(spine_config)
    for i in range(5):
        sm.add_message(
            {
                "role": "assistant",
                "content": f"turn {i}",
                "tool_calls": [
                    {
                        "id": f"c{i}",
                        "type": "function",
                        "function": {"name": f"tool_{i % 5}", "arguments": "{}"},
                    }
                ],
            }
        )
    assert sm.detect_stall() is False


def test_state_file_written(spine_config):
    sm = StreamManager(spine_config)
    (Path(spine_config.memory_dir) / "notes.md").write_text("some notes")
    (Path(spine_config.memory_dir) / "plan.md").write_text("the plan")
    sm.turn = 7
    sm.write_state(focus="testing", context_pct=0.55, urgency="elevated")
    state_path = Path(spine_config.spine_dir) / "state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text())
    assert state["turn"] == 7
    assert state["context_pct"] == 0.55
    assert state["focus"] == "testing"
    assert state["urgency"] == "elevated"
    assert state["memory_file_count"] == 2
    assert set(state["last_files"]) == {"notes.md", "plan.md"}


def test_stall_notices_escalation(spine_config):
    sm = StreamManager(spine_config)
    for detection_round in range(3):
        sm._messages = list(sm._messages)
        for i in range(STALL_THRESHOLD + 1):
            sm.add_message(
                {
                    "role": "assistant",
                    "content": f"turn {detection_round}_{i}",
                    "tool_calls": [
                        {
                            "id": f"c_{detection_round}_{i}",
                            "type": "function",
                            "function": {"name": "bash", "arguments": "{}"},
                        }
                    ],
                }
            )
        sm.detect_stall()
    assert sm._stall_notices_sent == 3
    stall_notices = [n for n in sm.queued_notices if "STALL DETECTED" in n]
    critical_notices = [n for n in sm.queued_notices if "CRITICAL" in n]
    assert len(stall_notices) == 3
    assert len(critical_notices) >= 1


def test_build_payload_includes_notices(spine_config):
    sm = StreamManager(spine_config)
    sm.queue_system_notice("important update")
    payload = sm.build_payload(
        [{"type": "function", "function": {"name": "test"}}],
        {
            "turn": 1,
            "context_pct": 0.1,
            "urgency": "nominal",
            "memory_files": 0,
            "focus": "test",
        },
    )
    notice_msgs = [
        m
        for m in payload
        if m["role"] == "user" and "important update" in m.get("content", "")
    ]
    assert len(notice_msgs) == 1
    assert sm.queued_notices == []


def test_build_payload_returns_copy(spine_config):
    sm = StreamManager(spine_config)
    payload = sm.build_payload(
        [],
        {
            "turn": 0,
            "context_pct": 0.0,
            "urgency": "nominal",
            "memory_files": 0,
            "focus": "",
        },
    )
    assert payload is not sm.messages
    assert payload == sm.messages


def test_record_tool_result(spine_config):
    sm = StreamManager(spine_config)
    sm.record_tool_result("tc1", "output data", True)
    assert sm.messages[-1]["role"] == "tool"
    assert sm.messages[-1]["tool_call_id"] == "tc1"
    assert sm.messages[-1]["content"] == "output data"


def test_stall_resets_on_no_stall(spine_config):
    sm = StreamManager(spine_config)
    for i in range(STALL_THRESHOLD + 1):
        sm.add_message(
            {
                "role": "assistant",
                "content": f"turn {i}",
                "tool_calls": [
                    {
                        "id": f"c{i}",
                        "type": "function",
                        "function": {"name": "bash", "arguments": "{}"},
                    }
                ],
            }
        )
    sm.detect_stall()
    assert sm._stall_notices_sent == 1
    sm._messages = [sm._messages[0]]
    for i in range(3):
        sm.add_message(
            {
                "role": "assistant",
                "content": f"diverse {i}",
                "tool_calls": [
                    {
                        "id": f"d{i}",
                        "type": "function",
                        "function": {"name": f"tool_{i}", "arguments": "{}"},
                    }
                ],
            }
        )
    assert sm.detect_stall() is False
    assert sm._stall_notices_sent == 0


def test_stall_only_scans_window(spine_config):
    sm = StreamManager(spine_config)
    for i in range(STALL_WINDOW + 5):
        sm.add_message(
            {
                "role": "assistant",
                "content": f"old {i}",
                "tool_calls": [
                    {
                        "id": f"old_{i}",
                        "type": "function",
                        "function": {"name": "stale_tool", "arguments": "{}"},
                    }
                ],
            }
        )
    assert sm.detect_stall() is True
    stale_mentions = [n for n in sm.queued_notices if "stale_tool" in n]
    assert len(stale_mentions) >= 1


def test_stall_counts_multiple_calls_per_message(spine_config):
    sm = StreamManager(spine_config)
    for i in range(3):
        sm.add_message(
            {
                "role": "assistant",
                "content": f"turn {i}",
                "tool_calls": [
                    {
                        "id": f"c{i}a",
                        "type": "function",
                        "function": {"name": "read", "arguments": "{}"},
                    },
                    {
                        "id": f"c{i}b",
                        "type": "function",
                        "function": {"name": "read", "arguments": "{}"},
                    },
                ],
            }
        )
    assert sm.detect_stall() is True
    assert any("read" in n for n in sm.queued_notices)


def test_stall_handles_object_tool_calls(spine_config):
    sm = StreamManager(spine_config)
    for i in range(STALL_THRESHOLD + 1):
        sm.add_message(
            {
                "role": "assistant",
                "content": f"turn {i}",
                "tool_calls": [
                    {
                        "id": f"c{i}",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": "{}"},
                    }
                ],
            }
        )
    assert sm.detect_stall() is True
