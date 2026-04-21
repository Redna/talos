import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from spine.config import SpineConfig
from spine.events import EventLogger
from spine.ipc_server import IPCServer
from spine.stream import StreamManager


class MockSupervisor:
    def __init__(self):
        self._restart_requested = False
        self._restart_reason = None

    def request_restart(self, reason):
        self._restart_requested = True
        self._restart_reason = reason

    def is_paused(self):
        return False


@pytest.fixture
def ipc_setup(tmp_path):
    cfg = SpineConfig()
    cfg.socket_path = str(tmp_path / "test.sock")
    cfg.spine_dir = str(tmp_path / "spine")
    cfg.constitution_path = str(tmp_path / "CONSTITUTION.md")
    cfg.identity_path = str(tmp_path / "identity.md")
    cfg.memory_dir = str(tmp_path / "memory")
    Path(cfg.spine_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.memory_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.constitution_path).write_text("# Principles\nAgency.")
    Path(cfg.identity_path).write_text("# Identity\nYou are Talos.")
    events = EventLogger(str(Path(cfg.spine_dir) / "events"))
    stream = StreamManager(cfg)
    supervisor = MockSupervisor()
    server = IPCServer(cfg, supervisor, stream, events)
    yield server, cfg, stream, supervisor
    events.close()


def _make_think_setup(tmp_path, gate_proxy=None):
    cfg = SpineConfig()
    cfg.socket_path = str(tmp_path / "test.sock")
    cfg.spine_dir = str(tmp_path / "spine")
    cfg.constitution_path = str(tmp_path / "CONSTITUTION.md")
    cfg.identity_path = str(tmp_path / "identity.md")
    cfg.memory_dir = str(tmp_path / "memory")
    Path(cfg.constitution_path).write_text("# Principles\nAgency.")
    Path(cfg.identity_path).write_text("# Identity\nTalos.")
    Path(cfg.spine_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.memory_dir).mkdir(parents=True, exist_ok=True)
    events = EventLogger(str(Path(cfg.spine_dir) / "events"))
    stream = StreamManager(cfg)
    supervisor = MockSupervisor()
    server = IPCServer(cfg, supervisor, stream, events, gate_proxy=gate_proxy)
    return server, cfg, stream, supervisor


@pytest.mark.asyncio
async def test_ipc_think_with_proxy(tmp_path):
    mock_proxy = MagicMock()
    mock_proxy.call.return_value = {
        "assistant_message": "I'll help",
        "tool_calls": [
            {"id": "c1", "name": "bash_command", "arguments": {"command": "ls"}}
        ],
        "context_pct": 0.35,
        "tokens_used": 120,
        "finish_reason": "tool_calls",
    }
    server, cfg, stream, supervisor = _make_think_setup(tmp_path, gate_proxy=mock_proxy)
    await server.start()
    try:
        reader, writer = await asyncio.open_unix_connection(cfg.socket_path)
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "think",
            "params": {"tools": [], "hud_data": {}},
        }
        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()
        data = await asyncio.wait_for(reader.readline(), timeout=2.0)
        resp = json.loads(data)
        assert resp["result"]["tool_calls"][0]["name"] == "bash_command"
        assert resp["result"]["context_pct"] == 0.35
        assert resp["result"]["turn"] == 1
        writer.close()
        await writer.wait_closed()
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_ipc_think_no_proxy(tmp_path):
    server, cfg, stream, supervisor = _make_think_setup(tmp_path, gate_proxy=None)
    await server.start()
    try:
        reader, writer = await asyncio.open_unix_connection(cfg.socket_path)
        req = {"jsonrpc": "2.0", "id": 1, "method": "think", "params": {}}
        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()
        data = await asyncio.wait_for(reader.readline(), timeout=2.0)
        resp = json.loads(data)
        assert "error" in resp
        writer.close()
        await writer.wait_closed()
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_ipc_server_starts(ipc_setup):
    server, cfg, stream, supervisor = ipc_setup
    await server.start()
    assert Path(cfg.socket_path).exists()
    await server.stop()


@pytest.mark.asyncio
async def test_ipc_tool_result(ipc_setup):
    server, cfg, stream, supervisor = ipc_setup
    await server.start()
    try:
        reader, writer = await asyncio.open_unix_connection(cfg.socket_path)
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tool_result",
            "params": {
                "tool_call_id": "tc1",
                "output": "ok",
                "success": True,
            },
        }
        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()
        data = await asyncio.wait_for(reader.readline(), timeout=2.0)
        resp = json.loads(data)
        assert resp["result"] == "ok"
        assert len(stream.messages) == 2
        assert stream.messages[1]["role"] == "tool"
        assert stream.messages[1]["tool_call_id"] == "tc1"
        writer.close()
        await writer.wait_closed()
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_ipc_request_fold(ipc_setup):
    server, cfg, stream, supervisor = ipc_setup
    stream.add_message({"role": "user", "content": "hello"})
    await server.start()
    try:
        reader, writer = await asyncio.open_unix_connection(cfg.socket_path)
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "request_fold",
            "params": {"synthesis": "summary"},
        }
        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()
        data = await asyncio.wait_for(reader.readline(), timeout=2.0)
        resp = json.loads(data)
        assert resp["result"] == "ok"
        last_msg = stream.messages[-1]
        assert last_msg["role"] == "assistant"
        assert last_msg["content"] == "summary"
        writer.close()
        await writer.wait_closed()
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_ipc_unknown_method(ipc_setup):
    server, cfg, stream, supervisor = ipc_setup
    await server.start()
    try:
        reader, writer = await asyncio.open_unix_connection(cfg.socket_path)
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "bogus_method",
            "params": {},
        }
        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()
        data = await asyncio.wait_for(reader.readline(), timeout=2.0)
        resp = json.loads(data)
        assert resp["error"]["code"] == -32601
        writer.close()
        await writer.wait_closed()
    finally:
        await server.stop()
