from __future__ import annotations

import asyncio
import json
import os
import time
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
        self._consecutive_high_context = 0
        self._last_tool_event_time: float = 0.0

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
        except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass

    async def _handle_request(self, raw: dict) -> dict:
        # Record heartbeat on every IPC call
        if self.supervisor and self.supervisor.health:
            self.supervisor.health.record_event()

        method = raw.get("method", "")
        req_id = raw.get("id")
        params = raw.get("params", {})

        if method == "think":
            if not self.gate_proxy:
                return self._error(req_id, -32000, "No gate proxy configured")
            hud = params.get("hud_data", {})
            hud.setdefault("turn", self.stream.turn)

            # Inject a synthetic user message on first turn if stream has no user input
            has_user = any(m.get("role") == "user" for m in self.stream.messages)
            if not has_user:
                hud_line = (
                    f"[HUD] turn={hud.get('turn', 0)}"
                    f" context_pct={hud.get('context_pct', 0.0):.2f}"
                    f" urgency={hud.get('urgency', 'nominal')}"
                    f" memory_files={hud.get('memory_files', 0)}"
                    f" focus={hud.get('focus', '')}"
                )
                self.stream.add_message({"role": "user", "content": hud_line})

            payload = self.stream.build_payload(
                params.get("tools", []),
                hud,
            )
            try:
                # Run the blocking gate call in a thread pool so the event loop
                # stays responsive (supervisor health checks, heartbeats, etc.).
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.gate_proxy.call(
                        payload,
                        params.get("tools", []),
                        turn=self.stream.turn + 1,
                    ),
                )
                # Record heartbeat after gate returns so the supervisor does not
                # see a stall during legitimate long gate waits.
                if self.supervisor and self.supervisor.health:
                    self.supervisor.health.record_event()
            except Exception as e:
                self.events.emit("spine.gate_error", {"error": str(e)})
                return self._error(req_id, -32000, f"Gate error: {e}")
            assistant_content = result.get("assistant_message", "")
            assistant_reasoning = result.get("reasoning", "")
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
                    "reasoning": assistant_reasoning,
                    "tool_calls": openai_tool_calls,
                    "_turn": self.stream.turn + 1,
                }
            )
            self.stream.turn += 1
            hud_data = params.get("hud_data", {})
            hud_data["turn"] = self.stream.turn
            hud_data["context_pct"] = result.get("context_pct", 0.0)
            self.stream.set_hud(hud_data)
            ctx_pct = result.get("context_pct", 0.0)
            threshold = getattr(self.cfg, "context_threshold_pct", 0.85)

            # Second signal: spine's own context estimate from message
            # buffer size. Guards against Ollama token-count glitches.
            spine_estimate = self.stream.estimate_context_pct()
            if abs(ctx_pct - spine_estimate) > 0.5:
                self.events.emit(
                    "spine.context_divergence",
                    {
                        "ollama_pct": ctx_pct,
                        "spine_estimate": spine_estimate,
                    },
                )
            # Use spine estimate when Ollama reports nonsense (>100%)
            decision_pct = spine_estimate if ctx_pct > 1.0 else ctx_pct

            # --- Escalating auto-fold guard ---
            # 85% = advisory  |  90% = forced fold  |  95% = emergency (debounced)

            if decision_pct >= 0.90:
                self._consecutive_high_context += 1
                # Debounce at 95% to prevent Ollama glitch-triggered false folds
                if decision_pct >= 0.95 and self._consecutive_high_context < 2:
                    self.stream.queue_system_notice(
                        f"EMERGENCY: Context at {decision_pct:.1%}. One more "
                        f"reading above 95% will force an automatic fold. "
                        f"Call fold_context NOW to control the synthesis."
                    )
                else:
                    self.events.emit(
                        "spine.auto_fold",
                        {
                            "context_pct": decision_pct,
                            "threshold": threshold,
                            "consecutive_readings": self._consecutive_high_context,
                        },
                    )
                    self.stream.fold(
                        f"[AUTO-FOLD] Context at {decision_pct:.1%}. "
                        f"Trajectory archived. Resume from fresh context."
                    )
                    self._consecutive_high_context = 0
            elif decision_pct >= threshold:
                self._consecutive_high_context += 1
                self.stream.queue_system_notice(
                    f"CRITICAL: Context at {decision_pct:.1%}. Auto-fold "
                    f"threshold ({threshold:.0%}) exceeded. Call fold_context "
                    f"immediately with a synthesis of all critical facts. "
                    f"At 90% context, the spine will force a fold."
                )
            else:
                self._consecutive_high_context = 0

            # Telemetry staleness: warn if no tool activity in >60 minutes.
            # Prevents the agent from pattern-matching on fossil data.
            now = time.time()
            if self._last_tool_event_time > 0 and (now - self._last_tool_event_time) > 3600:
                staleness_hours = (now - self._last_tool_event_time) / 3600
                self.stream.queue_system_notice(
                    f"WARNING: No tool activity recorded in {staleness_hours:.1f} "
                    f"hours. Telemetry may be stale. Run a concrete tool "
                    f"(bash_command, write_file, send_message) to verify operation."
                )
            self.stream.write_state(
                focus=hud_data.get("focus", ""),
                context_pct=ctx_pct,
                urgency=hud_data.get("urgency", "nominal"),
            )
            self.events.emit(
                "spine.think",
                {
                    "turn": self.stream.turn,
                    "context_pct": ctx_pct,
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
            self._last_tool_event_time = time.time()
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
