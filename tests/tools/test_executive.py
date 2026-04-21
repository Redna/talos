import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tool_registry import ToolRegistry
from state import AgentState
from spine_client import SpineClient


def _make_state(tmp_path):
    return AgentState(str(tmp_path))


def test_set_focus_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    state = _make_state("/tmp/fake_exec_test_1")
    from tools.executive import register_executive_tools

    register_executive_tools(registry, client, state)
    assert registry.has_tool("set_focus")


def test_resolve_focus_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    state = _make_state("/tmp/fake_exec_test_2")
    from tools.executive import register_executive_tools

    register_executive_tools(registry, client, state)
    assert registry.has_tool("resolve_focus")


def test_fold_context_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    state = _make_state("/tmp/fake_exec_test_3")
    from tools.executive import register_executive_tools

    register_executive_tools(registry, client, state)
    assert registry.has_tool("fold_context")


def test_reflect_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    state = _make_state("/tmp/fake_exec_test_4")
    from tools.executive import register_executive_tools

    register_executive_tools(registry, client, state)
    assert registry.has_tool("reflect")


def test_set_focus_execution(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    state = AgentState(str(tmp_path))
    from tools.executive import register_executive_tools

    register_executive_tools(registry, client, state)
    result = registry.execute("set_focus", {"objective": "fix bug"})
    assert "FOCUS SET" in result
    assert state.current_focus == "fix bug"
    client.emit_event.assert_called_once()


def test_resolve_focus_execution(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    state = AgentState(str(tmp_path))
    state.set_focus("investigate")
    from tools.executive import register_executive_tools

    register_executive_tools(registry, client, state)
    result = registry.execute("resolve_focus", {"synthesis": "done"})
    assert "FOCUS RESOLVED" in result
    assert state.current_focus is None
    client.emit_event.assert_called_once()


def test_fold_context_execution(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    state = AgentState(str(tmp_path))
    from tools.executive import register_executive_tools

    register_executive_tools(registry, client, state)
    result = registry.execute("fold_context", {"synthesis": "summarized"})
    assert "CONTEXT FOLDED" in result
    client.request_fold.assert_called_once()


def test_fold_context_calls_request_fold(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    state = AgentState(str(tmp_path))
    from tools.executive import register_executive_tools

    register_executive_tools(registry, client, state)
    registry.execute("fold_context", {"synthesis": "my summary"})
    client.request_fold.assert_called_once_with("my summary")


def test_reflect_execution(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    state = AgentState(str(tmp_path))
    from tools.executive import register_executive_tools

    register_executive_tools(registry, client, state)
    result = registry.execute("reflect", {"status": "idle"})
    assert "REFLECT" in result
    client.emit_event.assert_called_once()


def test_reflect_with_sleep(tmp_path):
    import time

    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    state = AgentState(str(tmp_path))
    from tools.executive import register_executive_tools

    register_executive_tools(registry, client, state)
    start = time.time()
    result = registry.execute("reflect", {"status": "paused", "sleep_duration": 1})
    elapsed = time.time() - start
    assert "REFLECT" in result
    assert elapsed >= 1
