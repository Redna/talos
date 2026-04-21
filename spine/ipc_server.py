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
        gate_proxy: Any | None = None,
    ):
        self.cfg = cfg
        self.supervisor = supervisor
        self.stream = stream
        self.events = events
        self.gate_proxy = gate_proxy
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
            if not self.gate_proxy:
                return self._error(req_id, -32000, "No gate proxy configured")
            hud = params.get("hud_data", {})
            hud.setdefault("turn", self.stream.turn)
            payload = self.stream.build_payload(
                params.get("tools", []),
                hud,
            )
        try:
            result = self.gate_proxy.call(
                messages=payload,
                tools=params.get("tools", []),
                turn=self.stream.turn,
            )
        except Exception as e:
            self.events.emit("spine.gate_error", {"error": str(e)})
            return self._error(req_id, -32000, f"Gate error: {e}")
        assistant_content = result.get("assistant_message", "")
        raw_tool_calls = result.get("tool_calls", [])
            openai_tool_calls = (
                [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for tc in raw_tool_calls
                ]
                if raw_tool_calls
                else None
            )
            self.stream.add_message(
                {
                    "role": "assistant",
                    "content": assistant_content,
                    "tool_calls": openai_tool_calls,
                    "_turn": self.stream.turn + 1,
                }
            )
            self.stream.turn += 1
            hud_data = params.get("hud_data", {})
            hud_data["turn"] = self.stream.turn
            hud_data["context_pct"] = result.get("context_pct", 0.0)
            self.stream.set_hud(hud_data)
            self.stream.write_state(
                focus=hud_data.get("focus", ""),
                context_pct=result.get("context_pct", 0.0),
                urgency=hud_data.get("urgency", "nominal"),
            )
            self.events.emit(
                "spine.think",
                {
                    "turn": self.stream.turn,
                    "context_pct": result.get("context_pct", 0.0),
                    "tokens_used": result.get("tokens_used", 0),
                },
            )
            return self._success(
                req_id,
                {
                    "tool_calls": raw_tool_calls,
                    "context_pct": result.get("context_pct", 0.0),
                    "tokens_used": result.get("tokens_used", 0),
                    "turn": self.stream.turn,
                    "assistant_message": assistant_content,
                },
            )
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
