"""Integration test: full think loop with mocked gate and tool execution.

This test covers the hot path of the bare-minimum architecture:
  1. IPC server + stream + gate proxy working
  2. Tool execution flow end-to-end
  3. State file written
  4. Conversation pattern: system → assistant → tool (no user messages after system)
"""

import asyncio
import json
from pathlib import Path

import pytest

from spine.config import SpineConfig
from spine.events import EventLogger
from spine.health import HealthMonitor
from spine.stream import StreamManager
from spine.supervisor import Supervisor
from spine.ipc_server import IPCServer
from spine.gate_proxy import GateProxy


class FakeGateProxy(GateProxy):
    """GateProxy that returns scripted responses instead of calling HTTP."""

    def __init__(self, cfg, responses):
        super().__init__(cfg.gate_url)
        self._responses = list(responses)
        self._idx = 0

    def call(self, messages, tools, model="", turn=None):
        if self._idx >= len(self._responses):
            raise RuntimeError("FakeGateProxy ran out of scripted responses")
        resp = self._responses[self._idx]
        self._idx += 1
        return resp


@pytest.fixture
def test_env(tmp_path):
    cfg = SpineConfig()
    cfg.socket_path = str(tmp_path / "test.sock")
    cfg.spine_dir = str(tmp_path / "spine")
    cfg.memory_dir = str(tmp_path / "memory")
    cfg.constitution_path = str(tmp_path / "CONSTITUTION.md")
    cfg.identity_path = str(tmp_path / "identity.md")
    cfg.app_dir = str(tmp_path / "app")

    Path(cfg.constitution_path).write_text("# Principles\nAgency.")
    Path(cfg.identity_path).write_text("# Identity\nTalos.")
    Path(cfg.spine_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.memory_dir).mkdir(parents=True, exist_ok=True)
    (Path(cfg.memory_dir) / "focus.md").write_text("# Focus\nTest.")

    events = EventLogger(str(Path(cfg.spine_dir) / "events"))
    stream = StreamManager(cfg)
    health = HealthMonitor(stall_timeout=600.0, startup_timeout=30.0)
    supervisor = Supervisor(cfg, events, health, stream)

    return cfg, events, stream, supervisor


@pytest.fixture
def server(test_env):
    cfg, events, stream, supervisor = test_env

    responses = [
        {
            "assistant_message": "Running pwd command.",
            "tool_calls": [
                {"id": "tc_1", "name": "bash_command", "arguments": {"command": "pwd"}},
            ],
            "context_pct": 0.65,
            "tokens_used": 120,
            "finish_reason": "tool_calls",
        },
        {
            "assistant_message": "Reading a file.",
            "tool_calls": [
                {
                    "id": "tc_2",
                    "name": "read_file",
                    "arguments": {"path": str(Path(cfg.memory_dir) / "focus.md")},
                },
            ],
            "context_pct": 0.25,
            "tokens_used": 140,
            "finish_reason": "tool_calls",
        },
        {
            "assistant_message": "All done.",
            "tool_calls": [],
            "context_pct": 0.30,
            "tokens_used": 60,
            "finish_reason": "stop",
        },
    ]
    gate = FakeGateProxy(cfg, responses)
    srv = IPCServer(cfg, supervisor, stream, events, gate_proxy=gate)
    return cfg, srv, stream


@pytest.mark.asyncio
async def test_think_returns_tool_calls(server):
    cfg, srv, stream = server
    await srv.start()
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
        data = await reader.readline()
        resp = json.loads(data.decode())
        writer.close()
        await writer.wait_closed()

        assert "result" in resp, resp
        assert resp["result"]["tool_calls"][0]["name"] == "bash_command"
        assert resp["result"]["context_pct"] == 0.65
        assert resp["result"]["turn"] == 1
    finally:
        await srv.stop()


@pytest.mark.asyncio
async def test_state_json_written_after_think(server):
    cfg, srv, stream = server
    await srv.start()
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
        await reader.readline()
        writer.close()
        await writer.wait_closed()

        state_file = Path(cfg.spine_dir) / "state.json"
        assert state_file.exists(), "state.json should exist after think()"
        state = json.loads(state_file.read_text())
        assert state["turn"] == 1
        assert state["context_pct"] == 0.65
    finally:
        await srv.stop()


@pytest.mark.asyncio
async def test_no_user_messages_after_system_in_stream(server):
    cfg, srv, stream = server
    await srv.start()
    try:
        # Turn 1: think → tool call
        reader, writer = await asyncio.open_unix_connection(cfg.socket_path)
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "think",
            "params": {"tools": [], "hud_data": {}},
        }
        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()
        await reader.readline()
        writer.close()
        await writer.wait_closed()

        # Turn 1: tool_result → add tool output to stream
        reader2, writer2 = await asyncio.open_unix_connection(cfg.socket_path)
        req2 = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tool_result",
            "params": {"tool_call_id": "tc_1", "output": "/tmp", "success": True},
        }
        writer2.write((json.dumps(req2) + "\n").encode())
        await writer2.drain()
        await reader2.readline()
        writer2.close()
        await writer2.wait_closed()

        # Turn 2: think → another tool call
        reader3, writer3 = await asyncio.open_unix_connection(cfg.socket_path)
        req3 = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "think",
            "params": {"tools": [], "hud_data": {}},
        }
        writer3.write((json.dumps(req3) + "\n").encode())
        await writer3.drain()
        data3 = await reader3.readline()
        resp3 = json.loads(data3.decode())
        writer3.close()
        await writer3.wait_closed()

        assert resp3["result"]["tool_calls"][0]["name"] == "read_file"

        # Verify conversation pattern: one synthetic user message from
        # the Spine's first-turn HUD injection is expected.
        user_msgs = [m for m in stream.messages if m["role"] == "user"]
        assert len(user_msgs) == 1, f"Expected 1 user message (first-turn HUD), got {len(user_msgs)}"

        assistant_msgs = [m for m in stream.messages if m["role"] == "assistant"]
        # 2 assistant turns (system is its own role, not included)
        assert len(assistant_msgs) == 2

        tool_msgs = [m for m in stream.messages if m["role"] == "tool"]
        assert len(tool_msgs) == 1  # tc_1 result (tc_2 result not yet)

    finally:
        await srv.stop()


@pytest.mark.asyncio
async def test_tool_result_records_in_stream(server):
    cfg, srv, stream = server
    await srv.start()
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
        await reader.readline()
        writer.close()
        await writer.wait_closed()

        reader2, writer2 = await asyncio.open_unix_connection(cfg.socket_path)
        req2 = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tool_result",
            "params": {"tool_call_id": "tc_1", "output": "/tmp\n/app", "success": True},
        }
        writer2.write((json.dumps(req2) + "\n").encode())
        await writer2.drain()
        data2 = await reader2.readline()
        resp2 = json.loads(data2.decode())
        writer2.close()
        await writer2.wait_closed()

        assert "result" in resp2
        tool_msgs = [m for m in stream.messages if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["content"] == "/tmp\n/app"
        assert tool_msgs[0]["tool_call_id"] == "tc_1"

    finally:
        await srv.stop()


@pytest.mark.asyncio
async def test_hud_piggybacked_on_tool_payload_not_stream(server):
    cfg, srv, stream = server
    stream.set_hud(
        {"turn": 42, "context_pct": 0.65, "urgency": "nominal", "memory_files": 3}
    )
    await srv.start()
    try:
        # think → assistant message added, HUD data set but not piggybacked yet
        reader, writer = await asyncio.open_unix_connection(cfg.socket_path)
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "think",
            "params": {"tools": [], "hud_data": {}},
        }
        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()
        await reader.readline()
        writer.close()
        await writer.wait_closed()

        # tool_result → tool message added
        reader2, writer2 = await asyncio.open_unix_connection(cfg.socket_path)
        req2 = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tool_result",
            "params": {"tool_call_id": "tc_1", "output": "output", "success": True},
        }
        writer2.write((json.dumps(req2) + "\n").encode())
        await writer2.drain()
        await reader2.readline()
        writer2.close()
        await writer2.wait_closed()

        # Verify stream tool message does NOT have HUD
        tool_msgs = [m for m in stream.messages if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        assert "[HUD]" not in tool_msgs[0]["content"], "HUD must not mutate stream"

        # Verify payload DOES have HUD
        payload = stream.build_payload(tools=[])
        tool_payload = [m for m in payload if m["role"] == "tool"]
        assert len(tool_payload) == 1
        assert "[HUD]" in tool_payload[0]["content"], "HUD must be in payload"

    finally:
        await srv.stop()


@pytest.mark.asyncio
async def test_whisper_injected_on_empty_focus_after_reflect(test_env):
    cfg, events, stream, supervisor = test_env
    # Set up: no focus, a reflect tool result in the stream
    stream.add_message({"role": "assistant", "content": "", "tool_calls": []})
    stream.record_tool_result("tc_reflect", "[REFLECT] idle", True)

    # Spy gate that captures the payload sent to it
    captured = []

    class SpyGate(FakeGateProxy):
        def call(self, messages, tools, model="", turn=None):
            captured.append(messages)
            return {
                "assistant_message": "Ok.",
                "tool_calls": [],
                "context_pct": 0.30,
                "tokens_used": 60,
                "finish_reason": "stop",
            }

    gate = SpyGate(cfg, [])
    srv = IPCServer(cfg, supervisor, stream, events, gate_proxy=gate)
    await srv.start()
    try:
        reader, writer = await asyncio.open_unix_connection(cfg.socket_path)
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "think",
            "params": {"tools": [], "hud_data": {"focus": "none"}},
        }
        writer.write((json.dumps(req) + "\n").encode())
        await writer.drain()
        await reader.readline()
        writer.close()
        await writer.wait_closed()

        assert len(captured) == 1
        tool_msgs = [m for m in captured[0] if m.get("role") == "tool"]
        whisper_msgs = [m for m in tool_msgs if "[WHISPER]" in m.get("content", "")]
        assert len(whisper_msgs) == 1, "whisper should be injected into tool payload"
    finally:
        await srv.stop()
