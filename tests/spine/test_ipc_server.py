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
