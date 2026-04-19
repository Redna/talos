from pathlib import Path

import asyncio

import pytest

from spine.stream import StreamManager, Message
from spine.config import SpineConfig
from spine.ipc_types import HUDData, ToolDef, ThinkRequest


def make_config(tmp_path):
    cfg = SpineConfig()
    cfg.constitution_path = str(tmp_path / "CONSTITUTION.md")
    cfg.identity_path = str(tmp_path / "identity.md")
    cfg.spine_dir = str(tmp_path / "spine")
    Path(cfg.constitution_path).write_text("# Principles\nAgency.")
    Path(cfg.identity_path).write_text("# Identity\nYou are Talos.")
    return cfg


def test_format_hud(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    hud_data = HUDData(memory_keys=5, last_keys=["key1", "key2"], urgency="nominal")
    hud_str = sm._format_hud(
        hud_data, context_pct=0.45, turn=10, tokens_used=5000, queued_notices=[]
    )
    assert "Context: 45%" in hud_str
    assert "Turn: 10" in hud_str
    assert "Tokens: 5000" in hud_str
    assert "Memory: 5 keys" in hud_str


def test_format_hud_with_notices(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    hud_data = HUDData(memory_keys=3, last_keys=["a"], urgency="elevated")
    hud_str = sm._format_hud(hud_data, 0.7, 5, 3000, ["Folding required"])
    assert "[SYSTEM | Folding required | Urgency: elevated]" in hud_str


def test_apply_shedding_no_shed_needed(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    msgs = [Message(role="system", content="sys"), Message(role="user", content="hi")]
    result = sm._apply_shedding(msgs)
    assert len(result) == 2


def test_apply_shedding_truncates_tool_output(tmp_path):
    cfg = make_config(tmp_path)
    cfg.shed_tool_output_max_chars = 10
    cfg.active_window = 1
    sm = StreamManager(cfg)
    msgs = [
        Message(role="system", content="sys"),
        Message(role="user", content="hi"),
        Message(role="tool", content="A" * 100, tool_call_id="tc1"),
        Message(role="assistant", content="ok"),
        Message(role="user", content="more"),
        Message(role="assistant", content="more ok"),
    ]
    result = sm._apply_shedding(msgs)
    assert len(result) == 6
    assert "archived" in result[2].content


def test_enforce_fold(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm._focus = "test"
    sm.turn = 1
    sm.tokens_used = 0
    msgs = [
        Message(role="system", content="sys"),
        Message(role="user", content="init"),
        Message(role="assistant", content="thinking"),
        Message(role="user", content="do thing"),
    ]
    req = ThinkRequest(
        focus="test",
        tools=[],
        hud_data=HUDData(memory_keys=0, last_keys=[], urgency="nominal"),
    )
    folded, tools = sm._enforce_fold(msgs, [], req)
    assert len(folded) == 3
    assert len(tools) == 1
    assert tools[0].name == "fold_context"


def test_record_tool_result(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.record_tool_result("tc1", "result text", True)
    assert len(sm.messages) == 1
    assert sm.messages[0].role == "tool"
    assert sm.messages[0].content == "result text"


def test_record_tool_result_error(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.record_tool_result("tc1", "error message", False)
    assert sm.messages[0].content == "[TOOL ERROR] error message"


def test_apply_fold(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.messages = [
        Message(role="system", content="sys"),
        Message(role="user", content="init"),
        Message(role="assistant", content="old response"),
        Message(role="user", content="old prompt"),
    ]
    sm.apply_fold("synthesis of old context")
    assert len(sm.messages) == 3
    assert sm.messages[2].content == "synthesis of old context"
    assert sm.context_pct == 0.1


def test_get_state(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.turn = 5
    sm.tokens_used = 1000
    sm.context_pct = 0.5
    state = asyncio.get_event_loop().run_until_complete(sm.get_state())
    assert state["turn"] == 5
    assert state["tokens_used"] == 1000
    assert state["context_pct"] == 0.5


def test_get_state_with_keys(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.turn = 5
    sm.set_state("custom_key", "custom_val")
    state = asyncio.get_event_loop().run_until_complete(
        sm.get_state(["turn", "custom_key"])
    )
    assert state["turn"] == 5
    assert state["custom_key"] == "custom_val"


def test_queue_system_notice(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.queue_system_notice("test notice")
    assert sm.queued_notices == ["test notice"]


def test_hud_appended_to_tool_message(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.messages = [
        Message(role="user", content="init"),
        Message(
            role="assistant",
            content="thinking",
            tool_calls=[
                {
                    "id": "c1",
                    "type": "function",
                    "function": {"name": "reflect", "arguments": "{}"},
                }
            ],
        ),
        Message(role="tool", content="reflected", tool_call_id="c1"),
    ]
    sm.turn = 5
    sm.queue_system_notice("[TELEGRAM | hello]")
    req = ThinkRequest(
        focus="stay on task",
        tools=[],
        hud_data=HUDData(memory_keys=0, last_keys=[], urgency="nominal"),
    )
    payload = sm._build_payload(req)
    tool_msgs = [m for m in payload if m.role == "tool"]
    assert len(tool_msgs) == 1
    assert 'Content: "hello"' in tool_msgs[0].content
    assistant_msgs = [m for m in payload if m.role == "assistant"]
    assert not any("[TELEGRAM | hello]" in m.content for m in assistant_msgs)


def test_notices_survive_if_not_displayed(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.messages = [
        Message(role="user", content="init"),
        Message(
            role="assistant",
            content="thinking",
            tool_calls=[
                {
                    "id": "c1",
                    "type": "function",
                    "function": {"name": "reflect", "arguments": "{}"},
                }
            ],
        ),
        Message(role="tool", content="reflected", tool_call_id="c1"),
    ]
    sm.turn = 7
    sm.queue_system_notice("[TELEGRAM | urgent]")
    req = ThinkRequest(
        focus="stay on task",
        tools=[],
        hud_data=HUDData(memory_keys=0, last_keys=[], urgency="nominal"),
    )
    payload = sm._build_payload(req)
    assert sm.queued_notices == []


def test_notices_preserved_when_hud_not_shown(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.messages = [
        Message(role="user", content="init"),
        Message(role="tool", content="result", tool_call_id="c1"),
    ]
    sm.turn = 3
    sm.queue_system_notice("[TELEGRAM | delayed]")
    req = ThinkRequest(
        focus="stay on task",
        tools=[],
        hud_data=HUDData(memory_keys=0, last_keys=[], urgency="nominal"),
    )
    payload = sm._build_payload(req)
    assert 'Content: "delayed"' in payload[-1].content
    assert sm._pending_notices == []
    assert sm.queued_notices == []


def test_pending_notices_promoted_on_next_cycle(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.messages = [
        Message(role="user", content="init"),
        Message(role="tool", content="result", tool_call_id="c1"),
    ]
    sm.turn = 3
    sm.queue_system_notice("[TELEGRAM | hello]")
    req = ThinkRequest(
        focus="stay on task",
        tools=[],
        hud_data=HUDData(memory_keys=0, last_keys=[], urgency="nominal"),
    )
    payload = sm._build_payload(req)
    assert 'Content: "hello"' in payload[-1].content
    assert sm.queued_notices == []
    assert sm._pending_notices == []
    sm.queue_system_notice("[TELEGRAM | world]")
    payload2 = sm._build_payload(req)
    assert 'Content: "world"' in payload2[-1].content


def test_notices_survive_into_pending_when_hud_not_shown(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.messages = [
        Message(role="user", content="init"),
        Message(role="tool", content="result", tool_call_id="c1"),
    ]
    sm.queue_system_notice("[TELEGRAM | urgent]")
    sm._pending_notices = ["[TELEGRAM | earlier]"]
    sm.turn = 5
    sm.context_pct = 0.1
    payload = sm._build_payload(
        ThinkRequest(
            focus="stay on task",
            tools=[],
            hud_data=HUDData(memory_keys=0, last_keys=[], urgency="nominal"),
        )
    )
    assert sm._pending_notices == []
    assert sm.queued_notices == []
    assert 'Content: "earlier"' in payload[-1].content
    assert 'Content: "urgent"' in payload[-1].content


def test_format_hud_includes_spend_when_nonzero(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    hud_data = HUDData(memory_keys=5, last_keys=["key1"], urgency="nominal", spend=3.50)
    hud_str = sm._format_hud(
        hud_data, context_pct=0.45, turn=10, tokens_used=5000, queued_notices=[]
    )
    assert "Spend: $3.50" in hud_str


def test_format_hud_excludes_spend_when_zero(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    hud_data = HUDData(memory_keys=5, last_keys=["key1"], urgency="nominal", spend=0)
    hud_str = sm._format_hud(
        hud_data, context_pct=0.45, turn=10, tokens_used=5000, queued_notices=[]
    )
    assert "Spend:" not in hud_str


def test_spend_flows_through_build_payload(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.messages = [
        Message(role="user", content="init"),
        Message(
            role="assistant",
            content="thinking",
            tool_calls=[
                {
                    "id": "c1",
                    "type": "function",
                    "function": {"name": "reflect", "arguments": "{}"},
                }
            ],
        ),
        Message(role="tool", content="reflected", tool_call_id="c1"),
    ]
    sm.turn = 5
    sm.queue_system_notice("[TELEGRAM | test]")
    sm.spend = 3.50
    req = ThinkRequest(
        focus="stay on task",
        tools=[],
        hud_data=HUDData(memory_keys=0, last_keys=[], urgency="nominal", spend=0),
    )
    payload = sm._build_payload(req)
    tool_msgs = [m for m in payload if m.role == "tool"]
    assert len(tool_msgs) == 1
    assert "Spend: $3.50" in tool_msgs[0].content


def test_build_backpack(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm._focus = "stay on task"
    sm.turn = 7
    sm.tokens_used = 1234
    sm.messages = [
        Message(role="system", content="sys"),
        Message(role="user", content="init"),
        Message(role="assistant", content="thinking"),
        Message(role="tool", content="tool result one", tool_call_id="tc1"),
        Message(role="assistant", content="more thinking"),
        Message(role="tool", content="tool result two", tool_call_id="tc2"),
        Message(role="assistant", content="final"),
    ]
    req = ThinkRequest(
        focus="stay on task",
        tools=[],
        hud_data=HUDData(
            memory_keys=12, last_keys=["k1", "k2", "k3"], urgency="nominal"
        ),
    )
    backpack = sm._build_backpack(req)
    assert "Focus: stay on task" in backpack
    assert "Turn: 7" in backpack
    assert "Tokens used: 1234" in backpack
    assert "Memory keys: 12" in backpack
    assert "Recent tool outputs:" in backpack
    assert "tool result one" in backpack
    assert "tool result two" in backpack
    assert "[CONTEXT BACKPACK]" in backpack
    assert "[/CONTEXT BACKPACK]" in backpack


def test_enforce_fold_includes_backpack(tmp_path):
    cfg = make_config(tmp_path)
    cfg.memory_dir = str(tmp_path / "memory")
    sm = StreamManager(cfg)
    sm._focus = "fold test"
    sm.turn = 10
    sm.tokens_used = 5000
    sm.messages = [
        Message(role="system", content="sys"),
        Message(role="user", content="init"),
        Message(role="assistant", content="thinking"),
        Message(role="tool", content="result", tool_call_id="tc1"),
    ]
    req = ThinkRequest(
        focus="fold test",
        tools=[],
        hud_data=HUDData(memory_keys=5, last_keys=["a"], urgency="nominal"),
    )
    backpack = sm._build_backpack(req)
    assert "Focus: fold test" in backpack
    assert "Turn: 10" in backpack
    assert "Memory keys: 5" in backpack

    import json
    from pathlib import Path

    sm._save_backpack_to_memory(backpack)
    mem_path = Path(cfg.memory_dir) / "agent_memory.json"
    data = json.loads(mem_path.read_text())
    assert "_fold_backpack" in data
    assert "Focus: fold test" in data["_fold_backpack"]


def test_apply_fold_preserves_last_two_tool_results(tmp_path):
    cfg = make_config(tmp_path)
    sm = StreamManager(cfg)
    sm.messages = [
        Message(role="system", content="sys"),
        Message(role="user", content="init"),
        Message(
            role="assistant",
            content="middle 2",
            tool_calls=[
                {
                    "id": "tc3",
                    "type": "function",
                    "function": {"name": "bash", "arguments": "{}"},
                },
            ],
        ),
        Message(role="tool", content="tool result C", tool_call_id="tc3"),
    ]
    sm.apply_fold("synthesis of old context")
    assert len(sm.messages) == 5
    assert sm.messages[0].role == "system"
    assert sm.messages[1].role == "user"
    assert sm.messages[2].role == "assistant"
    assert sm.messages[2].tool_calls is not None
    assert sm.messages[3].role == "tool"
    assert sm.messages[3].content == "tool result C"
    assert sm.messages[4].role == "assistant"
    assert sm.messages[4].content == "synthesis of old context"
    assert sm.context_pct == 0.1


def test_apply_fold_injects_recall_pair_when_backpack_exists(tmp_path):
    cfg = make_config(tmp_path)
    cfg.memory_dir = str(tmp_path / "memory")
    sm = StreamManager(cfg)
    sm.messages = [
        Message(role="system", content="sys"),
        Message(role="user", content="init"),
        Message(role="assistant", content="work"),
        Message(role="tool", content="result", tool_call_id="tc1"),
    ]
    import json
    from pathlib import Path

    mem_dir = Path(cfg.memory_dir)
    mem_dir.mkdir(exist_ok=True)
    agent_mem = mem_dir / "agent_memory.json"
    agent_mem.write_text(
        json.dumps(
            {"_fold_backpack": "[CONTEXT BACKPACK]\nFocus: test\n[/CONTEXT BACKPACK]"}
        )
    )
    sm.apply_fold("synthesis")
    assert len(sm.messages) == 4
    synthesis_msg = sm.messages[2]
    assert synthesis_msg.role == "assistant"
    assert "synthesis" in synthesis_msg.content
    assert synthesis_msg.tool_calls is not None
    assert len(synthesis_msg.tool_calls) == 1
    assert synthesis_msg.tool_calls[0]["function"]["name"] == "recall_fact"
    assert sm.messages[3].role == "tool"
    assert sm.messages[3].tool_call_id == synthesis_msg.tool_calls[0]["id"]
    assert "[CONTEXT BACKPACK]" in sm.messages[3].content
