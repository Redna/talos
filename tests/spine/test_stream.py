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
    msgs = [
        Message(role="system", content="sys"),
        Message(role="user", content="init"),
        Message(role="assistant", content="thinking"),
        Message(role="user", content="do thing"),
    ]
    folded, tools = sm._enforce_fold(msgs, [])
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
