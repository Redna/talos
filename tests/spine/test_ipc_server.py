import asyncio
from unittest.mock import MagicMock, AsyncMock

from spine.ipc_server import IPCServer
from spine.config import SpineConfig
from spine.stream import StreamManager


def make_config(tmp_path):
    from pathlib import Path

    cfg = SpineConfig()
    cfg.socket_path = str(tmp_path / "test.sock")
    cfg.constitution_path = str(tmp_path / "CONSTITUTION.md")
    cfg.identity_path = str(tmp_path / "identity.md")
    cfg.spine_dir = str(tmp_path / "spine")
    Path(cfg.constitution_path).write_text("# Principles\nAgency.")
    Path(cfg.identity_path).write_text("# Identity\nYou are Talos.")
    return cfg


def test_handle_unknown_method():
    cfg = SpineConfig()
    stream = StreamManager(cfg)
    events = MagicMock()
    sup = MagicMock()
    server = IPCServer(cfg, sup, stream, events)
    result = asyncio.get_event_loop().run_until_complete(
        server._handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "unknown", "params": {}}
        )
    )
    assert result["error"]["code"] == -32601


def test_handle_get_state():
    cfg = SpineConfig()
    stream = StreamManager(cfg)
    stream.turn = 5
    events = MagicMock()
    sup = MagicMock()
    server = IPCServer(cfg, sup, stream, events)
    result = asyncio.get_event_loop().run_until_complete(
        server._handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "get_state", "params": {}}
        )
    )
    assert result["result"]["turn"] == 5


def test_handle_emit_event():
    cfg = SpineConfig()
    stream = StreamManager(cfg)
    events = MagicMock()
    sup = MagicMock()
    server = IPCServer(cfg, sup, stream, events)
    result = asyncio.get_event_loop().run_until_complete(
        server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "emit_event",
                "params": {"type": "test", "payload": {"key": "val"}},
            }
        )
    )
    assert result["result"] == "ok"
    events.emit.assert_called_once()


def test_parse_think():
    cfg = SpineConfig()
    stream = StreamManager(cfg)
    events = MagicMock()
    sup = MagicMock()
    server = IPCServer(cfg, sup, stream, events)
    params = {
        "focus": "test focus",
        "tools": [
            {
                "name": "shell",
                "description": "Run shell",
                "parameters": {"type": "object"},
            }
        ],
        "hud_data": {"memory_keys": 3, "last_keys": ["a", "b"], "urgency": "nominal"},
    }
    think_req = server._parse_think(params)
    assert think_req.focus == "test focus"
    assert len(think_req.tools) == 1
    assert think_req.tools[0].name == "shell"
    assert think_req.hud_data.memory_keys == 3


def test_error_response():
    result = IPCServer._error_response(1, -32601, "Method not found")
    assert result["error"]["code"] == -32601
    assert result["error"]["message"] == "Method not found"


def test_success_response():
    result = IPCServer._success_response(5, {"key": "value"})
    assert result["jsonrpc"] == "2.0"
    assert result["id"] == 5
    assert result["result"] == {"key": "value"}


def test_handle_tool_result():
    cfg = SpineConfig()
    stream = StreamManager(cfg)
    events = MagicMock()
    sup = MagicMock()
    server = IPCServer(cfg, sup, stream, events)
    result = asyncio.get_event_loop().run_until_complete(
        server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tool_result",
                "params": {"tool_call_id": "tc1", "output": "ok", "success": True},
            }
        )
    )
    assert result["result"] == "ok"
    assert len(stream.messages) == 1


def test_handle_request_fold():
    cfg = SpineConfig()
    stream = StreamManager(cfg)
    stream.messages = [
        __import__("spine.stream", fromlist=["Message"]).Message(
            role="system", content="sys"
        ),
        __import__("spine.stream", fromlist=["Message"]).Message(
            role="user", content="hi"
        ),
    ]
    events = MagicMock()
    sup = MagicMock()
    server = IPCServer(cfg, sup, stream, events)
    result = asyncio.get_event_loop().run_until_complete(
        server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "request_fold",
                "params": {"synthesis": "summary"},
            }
        )
    )
    assert result["result"] == "ok"
