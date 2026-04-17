from __future__ import annotations

import asyncio
import json
from pathlib import Path
import aiohttp
from typing import Any
from dataclasses import dataclass, field

import logging

from spine.config import SpineConfig

logger = logging.getLogger("spine.stream")
from spine.constitution import ConstitutionManager
from spine.ipc_types import ToolDef, HUDData, ThinkResponse, ToolCallResult


@dataclass
class Message:
    role: str
    content: str = ""
    tool_calls: list = field(default_factory=list)
    tool_call_id: str = ""
    name: str = ""


class StreamManager:
    def __init__(self, cfg: SpineConfig):
        self.cfg = cfg
        self.messages: list[Message] = []
        self._init_message: Message | None = None
        self.turn: int = 0
        self.tokens_used: int = 0
        self.context_pct: float = 0.0
        self.queued_notices: list[str] = []
        self._no_tool_call_retries: int = 0
        self._focus: str = ""
        self.state: dict[str, Any] = {}
        self.constitution_mgr = ConstitutionManager(
            cfg.constitution_path, cfg.identity_path
        )

    async def is_paused(self) -> bool:
        return Path("/spine/.paused").exists()

    async def _wait_while_paused(self):
        while await self.is_paused():
            await asyncio.sleep(0.5)

    async def think(self, req: ThinkRequest) -> ThinkResponse:
        changed, err = self.constitution_mgr.reload_if_changed()
        if err:
            raise RuntimeError(f"Failed to reload constitution: {err}")
        if changed:
            self.state["constitution_reloaded"] = True

        self._focus = req.focus

        messages = self._build_payload(req)

        api_req = {
            "model": self.cfg.gate_model,
            "messages": self._messages_to_dicts(messages),
            "tools": [self._tool_def_to_dict(t) for t in req.tools],
            "tool_choice": "required",
        }

        if self.context_pct > self.cfg.context_threshold:
            fold_messages, fold_tools = self._enforce_fold(messages, req.tools)
            api_req["messages"] = self._messages_to_dicts(fold_messages)
            api_req["tools"] = [self._tool_def_to_dict(t) for t in fold_tools]
            api_req["tool_choice"] = {"type": "function", "name": "fold_context"}
            self.queued_notices.append(
                f"Context at {int(self.context_pct * 100)}%. You MUST use fold_context immediately."
            )

        resp = await self._send_to_gate(api_req)

        assistant_content = ""
        tool_calls = []
        raw_calls = []
        if resp.get("choices"):
            choice = resp["choices"][0]
            assistant_content = choice["message"].get("content", "")
            raw_calls = choice["message"].get("tool_calls", [])
            for tc in raw_calls:
                tool_calls.append(
                    ToolCallResult(
                        id=tc["id"],
                        name=tc["function"]["name"],
                        arguments=self._parse_arguments(tc["function"]["arguments"]),
                    )
                )

        think_resp = ThinkResponse(
            assistant_message=assistant_content,
            tool_calls=tool_calls,
            context_pct=resp.get("usage", {}).get("context_pct", 0.0),
            turn=self.turn,
            tokens_used=resp.get("usage", {}).get("total_tokens", 0),
            folded=False,
        )

        self.messages.append(
            Message(
                role="assistant",
                content=assistant_content,
                tool_calls=raw_calls,
            )
        )

        if not tool_calls:
            self.messages.pop()
            self._no_tool_call_retries += 1

            if (
                self.context_pct > self.cfg.context_threshold
                and self._no_tool_call_retries >= 1
            ):
                logger.warning(
                    "[Spine] LLM ignored fold_context — requesting text-based synthesis"
                )
                self._no_tool_call_retries = 0
                synthesis = await self._request_fold_synthesis(req)
                if synthesis:
                    self.apply_fold(synthesis)
                    return ThinkResponse(
                        assistant_message=f"[FOLD SYNTHESIZED] {synthesis[:200]}",
                        tool_calls=[],
                        context_pct=0.1,
                        turn=self.turn,
                        tokens_used=self.tokens_used,
                        folded=True,
                    )
                else:
                    self.queued_notices.append(
                        "[SYSTEM | Failed to produce fold synthesis. Retrying.]"
                    )
                    return await self.think(req)

            if self._no_tool_call_retries > 3:
                logger.error(
                    "[Spine] LLM returned no tool calls 3 times in a row — forcing reflect"
                )
                synthetic_id = f"call_forced_{self.turn}"
                self.messages.append(
                    Message(
                        role="assistant",
                        content="",
                        tool_calls=[
                            {
                                "id": synthetic_id,
                                "type": "function",
                                "function": {
                                    "name": "reflect",
                                    "arguments": '{"status": "forced idle"}',
                                },
                            }
                        ],
                    )
                )
                self.messages.append(
                    Message(
                        role="tool",
                        content="[SYSTEM | No tool call produced after 3 attempts. Forced reflect.]",
                        tool_call_id=synthetic_id,
                    )
                )
                self._no_tool_call_retries = 0
                return ThinkResponse(
                    assistant_message="",
                    tool_calls=[
                        ToolCallResult(
                            id=synthetic_id,
                            name="reflect",
                            arguments={"status": "forced idle"},
                        )
                    ],
                    context_pct=self.context_pct,
                    turn=self.turn,
                    tokens_used=self.tokens_used,
                    folded=False,
                )
            self.queued_notices.append(
                "[SYSTEM | You MUST call a tool. Your last response had no tool call. Always call at least one tool.]"
            )
            return await self.think(req)

        self._no_tool_call_retries = 0

        self.turn += 1
        self.tokens_used = resp.get("usage", {}).get("total_tokens", 0)
        self.context_pct = resp.get("usage", {}).get("context_pct", 0.0)

        return think_resp

    async def _send_to_gate(self, req: dict) -> dict:
        await self._wait_while_paused()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.cfg.gate_url}/v1/chat/completions",
                json=req,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Gate returned status {resp.status}")
                return await resp.json()

    def _genesis_prompt(self) -> str:
        identity = self.constitution_mgr.identity
        return f"{identity}\n\nBegin your evolution. Act with agency."

    def _build_payload(self, req: ThinkRequest) -> list[Message]:
        system_msg = Message(
            role="system", content=self.constitution_mgr.system_prompt()
        )

        hud_str = self._format_hud(
            req.hud_data,
            self.context_pct,
            self.turn,
            self.tokens_used,
            self.queued_notices,
        )
        should_show_hud = (
            bool(self.queued_notices)
            or self.turn % 10 == 0
            or self.context_pct > 0.5
            or self.turn == 1
        )
        self.queued_notices = []

        if not self.messages:
            if self._init_message is None:
                self._init_message = Message(
                    role="user", content=self._genesis_prompt()
                )
            return [system_msg, self._init_message]

        messages = [system_msg] + list(self._apply_shedding(self.messages))

        focus_parts = []
        if should_show_hud:
            focus_parts.append(req.focus)
            if hud_str:
                focus_parts.append(hud_str)
        last = messages[-1]
        messages[-1] = Message(
            role=last.role,
            content=last.content + "\n\n" + "\n\n".join(focus_parts),
            tool_calls=last.tool_calls,
            tool_call_id=last.tool_call_id,
            name=last.name,
        )

        return messages

    def _apply_shedding(self, messages: list[Message]) -> list[Message]:
        if len(messages) <= 2:
            return messages

        frozen_count = 2
        active_message_count = self.cfg.active_window * 2

        if len(messages) <= frozen_count + active_message_count:
            return messages

        result = list(messages[:frozen_count])
        shed_boundary = len(messages) - active_message_count
        for i in range(frozen_count, shed_boundary):
            result.append(self._shed_message(messages[i]))
        result.extend(messages[shed_boundary:])
        return result

    def _shed_message(self, msg: Message) -> Message:
        if msg.role == "assistant" and msg.tool_calls:
            shed_calls = []
            for tc in msg.tool_calls:
                if isinstance(tc, dict):
                    shed_calls.append(
                        {
                            "id": tc.get("id", ""),
                            "type": tc.get("type", "function"),
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": "{}",
                            },
                        }
                    )
                else:
                    shed_calls.append(
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": "{}"},
                        }
                    )
            return Message(role=msg.role, content=msg.content, tool_calls=shed_calls)
        elif msg.role == "tool":
            if len(msg.content) > self.cfg.shed_tool_output_max_chars:
                max_chars = self.cfg.shed_tool_output_max_chars
                truncated = msg.content[:max_chars]
                archived_chars = len(msg.content) - max_chars
                return Message(
                    role=msg.role,
                    content=f"{truncated}\n[… {archived_chars} chars archived]",
                    tool_call_id=msg.tool_call_id,
                )
        return msg

    async def _request_fold_synthesis(self, req: ThinkRequest) -> str:
        fold_prompt = (
            "Your context window is nearly full. You MUST produce a DELTA-pattern synthesis of everything above.\n"
            "Format: State Delta (what changed), Negative Knowledge (what didn't work), Handoff (next steps).\n"
            "Write the synthesis as plain text. Be thorough — this replaces your entire conversation history."
        )
        messages = self._messages_to_dicts(self._build_payload(req))
        messages.append({"role": "user", "content": fold_prompt})

        api_req = {
            "model": self.cfg.gate_model,
            "messages": messages,
        }
        try:
            resp = await self._send_to_gate(api_req)
            if resp.get("choices"):
                content = resp["choices"][0]["message"].get("content", "")
                if len(content) > 100:
                    return content
        except Exception as e:
            logger.error(f"[Spine] Fold synthesis request failed: {e}")
        return ""

    def _auto_synthesize(self) -> str:
        recent = self.messages[-6:] if len(self.messages) >= 6 else list(self.messages)
        parts = []
        for m in recent:
            if m.role == "assistant" and m.content:
                parts.append(f"Assistant: {m.content[:200]}")
            elif m.role == "tool" and m.content:
                parts.append(f"Tool: {m.content[:150]}")
        summary = (
            "; ".join(parts) if parts else "Context window pressure — forced fold."
        )
        return f"Auto-fold: {summary[:800]}"

    def _format_hud(
        self,
        hud_data: HUDData,
        context_pct: float,
        turn: int,
        tokens_used: int,
        queued_notices: list[str],
    ) -> str:
        hud_parts = [
            "[HUD",
            f"Context: {int(context_pct * 100)}%",
            f"Turn: {turn}",
            f"Tokens: {tokens_used}",
            f"Memory: {hud_data.memory_keys} keys",
        ]
        if hud_data.last_keys:
            hud_parts.append(
                f"Last {len(hud_data.last_keys)}: {', '.join(hud_data.last_keys)}"
            )
        main_hud = " | ".join(hud_parts) + "]"

        parts = [main_hud]
        for notice in queued_notices:
            parts.append(f"[SYSTEM | {notice} | Urgency: {hud_data.urgency}]")

        return " ".join(parts)

    def _enforce_fold(
        self, messages: list[Message], tools: list[ToolDef]
    ) -> tuple[list[Message], list[ToolDef]]:
        if len(messages) < 2:
            return messages, tools

        folded = [messages[0]]
        if len(messages) > 1:
            folded.append(messages[1])

        for i in range(len(messages) - 1, -1, -1):
            if messages[i].role == "assistant":
                folded.append(messages[i])
                break

        fold_tool = ToolDef(
            name="fold_context",
            description="Compress the conversation context into a summary",
            parameters={
                "type": "object",
                "properties": {
                    "synthesis": {
                        "type": "string",
                        "description": "A concise summary using the DELTA pattern: State Delta, Negative Knowledge, Handoff",
                    },
                },
                "required": ["synthesis"],
            },
        )
        return folded, [fold_tool]

    def record_tool_result(self, tool_call_id: str, output: str, success: bool):
        content = output if success else f"[TOOL ERROR] {output}"
        self.messages.append(
            Message(role="tool", content=content, tool_call_id=tool_call_id)
        )

    def apply_fold(self, synthesis: str):
        if len(self.messages) < 2:
            return
        self.messages = [
            self.messages[0],
            self.messages[1],
            Message(role="assistant", content=synthesis),
        ]
        self._init_message = None
        self.turn += 1
        self.context_pct = 0.1

    def get_state(self, keys: list[str] | None = None) -> dict[str, Any]:
        authoritative = {
            "context_pct": self.context_pct,
            "turn": self.turn,
            "tokens_used": self.tokens_used,
            "message_count": len(self.messages),
            "queued_notices": len(self.queued_notices),
            "model": self.cfg.gate_model,
            "focus": getattr(self, "_focus", "no focus"),
        }
        if keys:
            result = {}
            for key in keys:
                if key in authoritative:
                    result[key] = authoritative[key]
                elif key in self.state:
                    result[key] = self.state[key]
            return result
        result = dict(authoritative)
        result.update(self.state)
        return result

    def queue_system_notice(self, notice: str):
        self.queued_notices.append(notice)

    def set_state(self, key: str, value: Any):
        self.state[key] = value

    def get_messages(self) -> list[Message]:
        return list(self.messages)

    @staticmethod
    def _parse_arguments(args: str) -> dict[str, Any]:
        try:
            return json.loads(args)
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def _tool_def_to_dict(td: ToolDef) -> dict:
        return {
            "type": "function",
            "function": {
                "name": td.name,
                "description": td.description,
                "parameters": td.parameters,
            },
        }

    @staticmethod
    def _messages_to_dicts(messages: list[Message]) -> list[dict]:
        result = []
        for msg in messages:
            d = {"role": msg.role}
            if msg.content:
                d["content"] = msg.content
            if msg.tool_calls:
                d["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                d["tool_call_id"] = msg.tool_call_id
            if msg.name:
                d["name"] = msg.name
            result.append(d)
        return result
