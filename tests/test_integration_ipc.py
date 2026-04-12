import asyncio
import json
import threading
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from spine.config import SpineConfig
from spine.events import EventLogger
from spine.ipc_server import IPCServer
from spine.snapshot import SnapshotManager
from spine.stream import StreamManager
from spine.supervisor import Supervisor


def make_env(tmp_path):
    cfg = SpineConfig()
    cfg.socket_path = str(tmp_path / "test.sock")
    cfg.constitution_path = str(tmp_path / "CONSTITUTION.md")
    cfg.identity_path = str(tmp_path / "identity.md")
    cfg.spine_dir = str(tmp_path / "spine_dir")
    cfg.gate_url = "http://localhost:9999"
    Path(cfg.constitution_path).write_text("# Principles\nAgency.")
    Path(cfg.identity_path).write_text("# Identity\nYou are Talos.")
    Path(cfg.spine_dir).mkdir(parents=True, exist_ok=True)
    events = EventLogger(str(tmp_path / "events"))
    snapshots = SnapshotManager(str(tmp_path / "snapshots"), 10)
    stream = StreamManager(cfg)
    supervisor = Supervisor(cfg, events, snapshots, stream)
    server = IPCServer(cfg, supervisor, stream, events)
    return server, stream, supervisor, events, cfg


class ServerRunner:
    def __init__(self, server):
        self.server = server
        self.loop = asyncio.new_event_loop()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        for _ in range(50):
            if Path(self.server.cfg.socket_path).exists():
                return
            time.sleep(0.05)
        raise RuntimeError("Server socket not created in time")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.server.start())
        self.loop.run_forever()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        if self._thread:
            self._thread.join(timeout=5)
        self.loop.close()


def _rpc(socket_path: str, method: str, params: dict) -> dict:
    import socket

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(socket_path)
    sock.settimeout(5)
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    sock.sendall((json.dumps(request) + "\n").encode())
    data = b""
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        data += chunk
        if b"\n" in data:
            break
    sock.close()
    return json.loads(data.decode().strip())


@pytest.fixture
def running_server(tmp_path):
    server, stream, sup, events, cfg = make_env(tmp_path)
    for method_name, return_value in [
        ("_send_to_gate", None),
    ]:
        pass
    runner = ServerRunner(server)
    runner.start()
    yield server, stream, cfg, runner
    runner.stop()


def test_ipc_get_state(running_server):
    server, stream, cfg, runner = running_server
    stream.turn = 42
    stream.tokens_used = 1000
    resp = _rpc(cfg.socket_path, "get_state", {})
    assert resp["result"]["turn"] == 42
    assert resp["result"]["tokens_used"] == 1000


def test_ipc_tool_result(running_server):
    server, stream, cfg, runner = running_server
    resp = _rpc(
        cfg.socket_path,
        "tool_result",
        {"tool_call_id": "tc_1", "output": "file listing", "success": True},
    )
    assert resp["result"] == "ok"
    assert len(stream.messages) == 1
    assert stream.messages[0].role == "tool"
    assert stream.messages[0].content == "file listing"


def test_ipc_request_fold(running_server):
    server, stream, cfg, runner = running_server
    from spine.stream import Message

    stream.messages = [
        Message(role="system", content="sys"),
        Message(role="user", content="hi"),
    ]
    resp = _rpc(cfg.socket_path, "request_fold", {"synthesis": "delta summary"})
    assert resp["result"] == "ok"
    assert len(stream.messages) == 3
    assert stream.messages[-1].content == "delta summary"


def test_ipc_emit_event(running_server):
    server, stream, cfg, runner = running_server
    resp = _rpc(
        cfg.socket_path,
        "emit_event",
        {"type": "integration_test", "payload": {"detail": "hello"}},
    )
    assert resp["result"] == "ok"


def test_ipc_unknown_method(running_server):
    server, stream, cfg, runner = running_server
    resp = _rpc(cfg.socket_path, "nonexistent", {})
    assert "error" in resp
    assert resp["error"]["code"] == -32601


def test_ipc_think_via_socket(running_server):
    server, stream, cfg, runner = running_server
    gate_response = {
        "choices": [
            {
                "message": {
                    "content": "I will list the files.",
                    "tool_calls": [
                        {
                            "id": "tc_think_1",
                            "type": "function",
                            "function": {
                                "name": "shell",
                                "arguments": '{"command": "ls"}',
                            },
                        }
                    ],
                }
            }
        ],
        "usage": {"total_tokens": 150, "context_pct": 0.3},
    }

    async def _fake_send(self, req):
        return gate_response

    with patch.object(StreamManager, "_send_to_gate", new=_fake_send):
        resp = _rpc(
            cfg.socket_path,
            "think",
            {
                "focus": "list files",
                "tools": [
                    {
                        "name": "shell",
                        "description": "Run a shell command",
                        "parameters": {"type": "object"},
                    }
                ],
                "hud_data": {
                    "memory_keys": 5,
                    "last_keys": ["a", "b"],
                    "urgency": "nominal",
                },
            },
        )
        assert "result" in resp
        result = resp["result"]
        assert result["assistant_message"] == "I will list the files."
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "shell"
        assert result["context_pct"] == 0.3
        assert result["turn"] == 0
        assert result["tokens_used"] == 150


def test_spine_client_think(running_server):
    from cortex.spine_client import SpineClient

    server, stream, cfg, runner = running_server
    gate_response = {
        "choices": [
            {"message": {"content": "Hello!", "tool_calls": []}},
        ],
        "usage": {"total_tokens": 50, "context_pct": 0.1},
    }

    async def _fake_send(self, req):
        return gate_response

    with patch.object(StreamManager, "_send_to_gate", new=_fake_send):
        client = SpineClient(socket_path=cfg.socket_path)
        result = client.think(
            focus="greet",
            tools=[{"name": "shell", "description": "Run shell", "parameters": {}}],
            hud_data={"memory_keys": 0, "last_keys": [], "urgency": "low"},
        )
        assert result["assistant_message"] == "Hello!"
        assert result["tool_calls"] == []
        assert result["turn"] == 0


def test_spine_client_get_state(running_server):
    from cortex.spine_client import SpineClient

    server, stream, cfg, runner = running_server
    stream.turn = 7
    client = SpineClient(socket_path=cfg.socket_path)
    result = client.get_state(keys=["turn"])
    assert result["turn"] == 7


def test_spine_client_tool_result(running_server):
    from cortex.spine_client import SpineClient

    server, stream, cfg, runner = running_server
    client = SpineClient(socket_path=cfg.socket_path)
    result = client.tool_result(tool_call_id="tc_1", output="done", success=True)
    assert result == "ok"
    assert len(stream.messages) == 1


def test_full_cortex_cycle(running_server):
    from cortex.spine_client import SpineClient

    server, stream, cfg, runner = running_server
    call_count = [0]
    gate_responses = [
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "tc_cycle_1",
                                "type": "function",
                                "function": {
                                    "name": "shell",
                                    "arguments": '{"command": "ls /app"}',
                                },
                            }
                        ],
                    }
                }
            ],
            "usage": {"total_tokens": 200, "context_pct": 0.25},
        },
        {
            "choices": [
                {"message": {"content": "I see the files. Done.", "tool_calls": []}}
            ],
            "usage": {"total_tokens": 100, "context_pct": 0.35},
        },
    ]

    async def _fake_send(self, req):
        idx = min(call_count[0], len(gate_responses) - 1)
        call_count[0] += 1
        return gate_responses[idx]

    with patch.object(StreamManager, "_send_to_gate", new=_fake_send):
        client = SpineClient(socket_path=cfg.socket_path)

        think1 = client.think(
            focus="explore workspace",
            tools=[{"name": "shell", "description": "Run shell", "parameters": {}}],
            hud_data={"memory_keys": 2, "last_keys": ["k1"], "urgency": "nominal"},
        )
        assert len(think1["tool_calls"]) == 1
        assert think1["tool_calls"][0]["name"] == "shell"

        client.tool_result(
            tool_call_id="tc_cycle_1",
            output="seed_agent.py\nspine/\ntests/",
            success=True,
        )

        think2 = client.think(
            focus="continue",
            tools=[{"name": "shell", "description": "Run shell", "parameters": {}}],
            hud_data={"memory_keys": 2, "last_keys": ["k1"], "urgency": "nominal"},
        )
        assert think2["assistant_message"] == "I see the files. Done."
        assert think2["tool_calls"] == []

        assert stream.turn == 2
        assert len(stream.messages) >= 3
