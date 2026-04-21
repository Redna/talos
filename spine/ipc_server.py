from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from spine.config import SpineConfig
from spine.events import EventLogger
from spine.stream import StreamManager


class IPCServer:
    def __init__(
        self,
        cfg: SpineConfig,
        supervisor: Any,
        stream: StreamManager,
        events: EventLogger,
    ):
        self.cfg = cfg
        self.supervisor = supervisor
        self.stream = stream
        self.events = events
        self._server: asyncio.Server | None = None

    async def start(self):
        socket_path = self.cfg.socket_path
        if os.path.exists(socket_path):
            os.remove(socket_path)
        self._server = await asyncio.start_unix_server(
            self._handle_conn, path=socket_path
        )
        os.chmod(socket_path, 0o666)

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_conn(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    raw = json.loads(line.decode().strip())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    resp = self._error(None, -32700, "Parse error")
                    writer.write((json.dumps(resp) + "\n").encode())
                    await writer.drain()
                    continue
                resp = await self._handle_request(raw)
                writer.write((json.dumps(resp) + "\n").encode())
                await writer.drain()
        except asyncio.CancelledError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def _handle_request(self, raw: dict) -> dict:
        method = raw.get("method", "")
        req_id = raw.get("id")
        params = raw.get("params", {})

        if method == "think":
            # FIXME: The think handler currently returns a stub response.
            # In production, this should:
            # 1. Build the LLM payload via stream.build_payload(tools, hud_data)
            # 2. Forward to gate for LLM inference
            # 3. Parse the response, record messages, and return tool_calls
            # Without this, the cortex agent loop is inert — it receives no
            # tool calls and will spin doing nothing.
            return self._success(req_id, {"status": "stub"})
        elif method == "tool_result":
            self.stream.record_tool_result(
                params.get("tool_call_id", ""),
                params.get("output", ""),
                params.get("success", True),
            )
            return self._success(req_id, "ok")
        elif method == "request_fold":
            self.stream.fold(params.get("synthesis", ""))
            return self._success(req_id, "ok")
        elif method == "request_restart":
            self.supervisor.request_restart(params.get("reason", ""))
            return self._success(req_id, "ok")
        elif method == "emit_event":
            self.events.emit(params.get("type", ""), params.get("payload", {}))
            return self._success(req_id, "ok")
        elif method == "send_message":
            channel = params.get("channel", "")
            if channel == "telegram" and self.cfg.telegram_bot_token:
                from spine.telegram import send_telegram_message

                send_telegram_message(
                    self.cfg,
                    params.get("text", ""),
                )
            return self._success(req_id, "ok")
        elif method == "get_state":
            return self._success(req_id, {"turn": self.stream.turn})
        else:
            return self._error(req_id, -32601, "Method not found")

    @staticmethod
    def _success(req_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def _error(req_id: Any, code: int, message: str) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }
