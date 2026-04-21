import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from spine.ipc_types import (
    ToolDef,
    HUDData,
    ThinkRequest,
    ToolResultRequest,
    RequestFoldRequest,
    RequestRestartRequest,
    SendMessageRequest,
    EmitEventRequest,
    ToolCallResult,
    ThinkResponse,
    JSONRPCRequest,
    RPCError,
    JSONRPCResponse,
)


def test_tool_def():
    t = ToolDef(
        name="read_file",
        description="Read a file",
        parameters={"path": {"type": "string"}},
    )
    assert t.name == "read_file"
    assert t.description == "Read a file"
    assert t.parameters == {"path": {"type": "string"}}


def test_hud_data_defaults():
    h = HUDData(memory_file_count=10, last_files=["a.py", "b.py"], urgency="high")
    assert h.memory_file_count == 10
    assert h.last_files == ["a.py", "b.py"]
    assert h.urgency == "high"
    assert h.spend == 0.0


def test_hud_data_with_spend():
    h = HUDData(memory_file_count=5, last_files=[], urgency="low", spend=1.5)
    assert h.spend == 1.5


def test_think_request():
    hud = HUDData(memory_file_count=0, last_files=[], urgency="normal")
    t = ThinkRequest(
        focus="fix bug",
        tools=[ToolDef(name="bash", description="Run command", parameters={})],
        hud_data=hud,
    )
    assert t.focus == "fix bug"
    assert len(t.tools) == 1
    assert t.tools[0].name == "bash"
    assert t.hud_data.urgency == "normal"


def test_tool_result_request():
    r = ToolResultRequest(tool_call_id="call_1", output="ok", success=True)
    assert r.tool_call_id == "call_1"
    assert r.output == "ok"
    assert r.success is True


def test_request_fold_request():
    f = RequestFoldRequest(synthesis="summary text")
    assert f.synthesis == "summary text"


def test_request_restart_request():
    r = RequestRestartRequest(reason="context overflow")
    assert r.reason == "context overflow"


def test_send_message_request():
    m = SendMessageRequest(channel="general", text="hello")
    assert m.channel == "general"
    assert m.text == "hello"


def test_emit_event_request():
    e = EmitEventRequest(type="error", payload={"msg": "fail"})
    assert e.type == "error"
    assert e.payload == {"msg": "fail"}


def test_tool_call_result():
    tc = ToolCallResult(id="call_1", name="bash", arguments={"command": "ls"})
    assert tc.id == "call_1"
    assert tc.name == "bash"
    assert tc.arguments == {"command": "ls"}


def test_think_response():
    tc = ToolCallResult(id="c1", name="bash", arguments={})
    r = ThinkResponse(
        assistant_message="done",
        tool_calls=[tc],
        context_pct=0.5,
        turn=3,
        tokens_used=100,
        folded=False,
    )
    assert r.assistant_message == "done"
    assert len(r.tool_calls) == 1
    assert r.context_pct == 0.5
    assert r.turn == 3
    assert r.tokens_used == 100
    assert r.folded is False


def test_jsonrpc_request():
    r = JSONRPCRequest(jsonrpc="2.0", id=1, method="think", params={"focus": "x"})
    assert r.jsonrpc == "2.0"
    assert r.id == 1
    assert r.method == "think"
    assert r.params == {"focus": "x"}


def test_rpc_error():
    e = RPCError(code=-32600, message="Invalid Request")
    assert e.code == -32600
    assert e.message == "Invalid Request"


def test_jsonrpc_response_result():
    r = JSONRPCResponse(jsonrpc="2.0", id=1, result={"status": "ok"})
    assert r.jsonrpc == "2.0"
    assert r.id == 1
    assert r.result == {"status": "ok"}
    assert r.error is None


def test_jsonrpc_response_error():
    err = RPCError(code=-32600, message="Invalid Request")
    r = JSONRPCResponse(jsonrpc="2.0", id=1, error=err)
    assert r.error.code == -32600
    assert r.result is None
