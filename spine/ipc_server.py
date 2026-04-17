from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from spine.config import SpineConfig
from spine.ipc_types import (
    JSONRPCRequest,
    JSONRPCResponse,
    RPCError,
    ThinkRequest,
    ToolResultRequest,
    RequestFoldRequest,
    RequestRestartRequest,
    SendMessageRequest,
    EmitEventRequest,
    GetStateRequest,
)
from spine.supervisor import Supervisor
from spine.stream import StreamManager
from spine.events import EventLogger

logger = logging.getLogger("spine.ipc")


class IPCServer:
    def __init__(
        self,
        cfg: SpineConfig,
        supervisor: Supervisor,
        stream: StreamManager,
        events: EventLogger,
    ):
        self.cfg = cfg
        self.supervisor = supervisor
        self.stream = stream
        self.events = events
        self._server = None
        self._done = asyncio.Event()

    async def start(self):
        socket_path = Path(self.cfg.socket_path)
        if socket_path.exists():
            socket_path.unlink()

        self._server = await asyncio.start_unix_server(
            self._handle_conn,
            path=str(socket_path),
        )
        logger.info(f"[Spine] IPC server listening on {self.cfg.socket_path}")

    async def stop(self):
        self._done.set()
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle_conn(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                try:
                    request = json.loads(data.decode().strip())
                    response = await self._handle_request(request)
                    writer.write((json.dumps(response) + "\n").encode())
                    await writer.drain()
                except (json.JSONDecodeError, KeyError) as e:
                    error_resp = {
                        "jsonrpc": "2.0",
                        "id": 0,
                        "error": {"code": -32700, "message": str(e)},
                    }
                    writer.write((json.dumps(error_resp) + "\n").encode())
                    await writer.drain()
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def _handle_request(self, raw: dict) -> dict:
        req_id = raw.get("id", 0)
        method = raw.get("method", "")
        params = raw.get("params", {})

        try:
            if method == "think":
                think_req = self._parse_think(params)
                result = await self.stream.think(think_req)
                self.supervisor.health.record_event()
                if not self.supervisor.health.first_think_done:
                    self.supervisor.health.record_first_think()
                if self.supervisor.snapshots.should_snapshot(self.stream.turn):
                    self.supervisor.snapshots.save(self.stream.get_state())
                return self._success_response(
                    req_id, self._think_response_to_dict(result)
                )
            elif method == "tool_result":
                self.stream.record_tool_result(
                    params.get("tool_call_id", ""),
                    params.get("output", ""),
                    params.get("success", True),
                )
                return self._success_response(req_id, "ok")
            elif method == "request_fold":
                self.stream.apply_fold(params.get("synthesis", ""))
                return self._success_response(req_id, "ok")
            elif method == "request_restart":
                self.supervisor.request_restart(params.get("reason", ""))
                return self._success_response(req_id, "restarting")
            elif method == "send_message":
                channel = params.get("channel", "")
                text = params.get("text", "")
                if channel == "telegram" and self.cfg.telegram_bot_token:
                    from spine.telegram import send_telegram_message

                    send_telegram_message(self.cfg, text)
                return self._success_response(req_id, "sent")
            elif method == "emit_event":
                self.events.emit(params.get("type", ""), params.get("payload", {}))
                return self._success_response(req_id, "ok")
            elif method == "get_state":
                state = self.stream.get_state(params.get("keys"))
                return self._success_response(req_id, state)
            else:
                return self._error_response(req_id, -32601, "Method not found")
        except Exception as e:
            return self._error_response(req_id, -32000, str(e))

    def _parse_think(self, params: dict) -> ThinkRequest:
        from spine.ipc_types import HUDData, ToolDef

        tools = []
        for t in params.get("tools", []):
            if "function" in t:
                func = t["function"]
                tools.append(
                    ToolDef(
                        name=func["name"],
                        description=func.get("description", ""),
                        parameters=func.get("parameters", {}),
                    )
                )
            else:
                tools.append(
                    ToolDef(
                        name=t["name"],
                        description=t.get("description", ""),
                        parameters=t.get("parameters", {}),
                    )
                )
        hud = params.get("hud_data", {})
        return ThinkRequest(
            focus=params.get("focus", ""),
            tools=tools,
            hud_data=HUDData(
                memory_keys=hud.get("memory_keys", 0),
                last_keys=hud.get("last_keys", []),
                urgency=hud.get("urgency", "nominal"),
            ),
        )

    @staticmethod
    def _think_response_to_dict(resp) -> dict:
        return {
            "assistant_message": resp.assistant_message,
            "tool_calls": [
                {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                for tc in resp.tool_calls
            ],
            "context_pct": resp.context_pct,
            "turn": resp.turn,
            "tokens_used": resp.tokens_used,
            "folded": resp.folded,
        }

    @staticmethod
    def _success_response(req_id: int, result) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def _error_response(req_id: int, code: int, message: str) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }
