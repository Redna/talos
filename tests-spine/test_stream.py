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
    sm.add_message({"role": "assistant", "content": "thinking"})
    assert any(m["content"] == "thinking" for m in sm.messages)


def test_record_tool_result(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "assistant", "content": "", "tool_calls": []})
    sm.record_tool_result("tc_1", "output text", True)
    last = sm.messages[-1]
    assert last["role"] == "tool"
    assert last["tool_call_id"] == "tc_1"


def test_hud_piggybacks_on_tool_result(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "assistant", "content": "", "tool_calls": []})
    sm.add_message({"role": "tool", "tool_call_id": "tc_1", "content": "result"})
    sm.set_hud({"turn": 1, "context_pct": 0.65, "urgency": "nominal", "memory_files": 3})
    payload = sm.build_payload(tools=[])
    tool_msgs = [m for m in payload if m["role"] == "tool"]
    assert any("[HUD]" in m["content"] for m in tool_msgs)


def test_hud_does_not_mutate_stream(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "assistant", "content": "", "tool_calls": []})
    sm.add_message({"role": "tool", "tool_call_id": "tc_1", "content": "result"})
    sm.set_hud({"turn": 1, "context_pct": 0.5, "urgency": "nominal", "memory_files": 3})
    payload = sm.build_payload(tools=[])
    tool_msg = [m for m in sm.messages if m["role"] == "tool"][-1]
    assert "[HUD]" not in tool_msg["content"]


def test_hud_no_user_message(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "assistant", "content": "", "tool_calls": []})
    sm.add_message({"role": "tool", "tool_call_id": "tc_1", "content": "result"})
    sm.set_hud({"turn": 1, "context_pct": 0.5, "urgency": "nominal", "memory_files": 3})
    payload = sm.build_payload(tools=[])
    user_msgs = [m for m in payload if m["role"] == "user"]
    assert len(user_msgs) == 0


def test_notices_piggyback_on_tool_result(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "assistant", "content": "", "tool_calls": []})
    sm.add_message({"role": "tool", "tool_call_id": "tc_1", "content": "result"})
    sm.queue_system_notice("STALL DETECTED: bash_command called 5 times")
    payload = sm.build_payload(tools=[])
    tool_msgs = [m for m in payload if m["role"] == "tool"]
    assert any("STALL" in m["content"] for m in tool_msgs)
    user_msgs = [m for m in payload if m["role"] == "user"]
    assert len(user_msgs) == 0


def test_no_user_messages_after_system(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "assistant", "content": "thinking", "tool_calls": []})
    sm.add_message({"role": "tool", "tool_call_id": "tc_1", "content": "result"})
    sm.set_hud({"turn": 1, "context_pct": 0.5, "urgency": "nominal", "memory_files": 3})
    sm.queue_system_notice("NOTICE")
    payload = sm.build_payload(tools=[])
    user_msgs = [m for m in payload if m["role"] == "user"]
    assert len(user_msgs) == 0


def test_hud_piggyback_resets_on_new_tool_result(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "assistant", "content": "", "tool_calls": []})
    sm.add_message({"role": "tool", "tool_call_id": "tc_1", "content": "result1"})
    sm.set_hud({"turn": 1, "context_pct": 0.5, "urgency": "nominal", "memory_files": 3})
    payload1 = sm.build_payload(tools=[])
    sm.add_message({"role": "assistant", "content": "", "tool_calls": []})
    sm.add_message({"role": "tool", "tool_call_id": "tc_2", "content": "result2"})
    sm.set_hud(
        {"turn": 2, "context_pct": 0.6, "urgency": "elevated", "memory_files": 4}
    )
    payload2 = sm.build_payload(tools=[])
    tool2_msgs = [
        m for m in payload2 if m["role"] == "tool" and "result2" in m.get("content", "")
    ]
    assert len(tool2_msgs) == 1
    assert "[HUD]" in tool2_msgs[0]["content"]


def test_fold_archives_and_resets(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "assistant", "content": "thinking..."})
    sm.add_message({"role": "tool", "tool_call_id": "c1", "content": "ok"})
    count_before = len(sm.messages)
    sm.fold("Synthesis of what happened")
    assert len(sm.messages) == 2
    assert sm.messages[-1]["role"] == "user"
    assert sm.messages[-1]["content"] == "[FOLD SYNTHESIS]\nSynthesis of what happened"
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
    for t in ["read_file", "write_file", "bash_command", "reflect", "send_message"]:
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


def test_messages_copy_on_insert(spine_config):
    sm = StreamManager(spine_config)
    original = {"role": "assistant", "content": "hello"}
    sm.add_message(original)
    original["content"] = "mutated"
    assert sm.messages[1]["content"] == "hello"


def test_build_payload_deep_copy(spine_config):
    sm = StreamManager(spine_config)
    sm.add_message({"role": "assistant", "content": "hello"})
    payload = sm.build_payload(tools=[])
    payload[1]["content"] = "mutated"
    assert sm.messages[1]["content"] == "hello"
