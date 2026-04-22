from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger("spine.gate_proxy")


class GateProxy:
    def __init__(self, gate_url: str, model: str = ""):
        self.gate_url = gate_url
        self.model = model

    def call(
        self,
        messages: list[dict],
        tools: list[dict],
        model: str = "",
        turn: int | None = None,
    ) -> dict[str, Any]:
        body = {
            "messages": messages,
            "tools": tools if tools else None,
            "tool_choice": "auto" if tools else None,
        }
        if turn is not None:
            body["turn"] = turn
        effective_model = model or self.model
        if effective_model:
            body["model"] = effective_model

        with httpx.Client(timeout=600.0) as client:
            resp = client.post(self.gate_url, json=body)
            resp.raise_for_status()
            data = resp.json()

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = data.get("usage", {})

        tool_calls = []
        for tc in message.get("tool_calls", []):
            func = tc.get("function", {})
            args_str = func.get("arguments", "{}")
            try:
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
            except (json.JSONDecodeError, ValueError):
                args = {}
            tool_calls.append(
                {
                    "id": tc.get("id", ""),
                    "name": func.get("name", ""),
                    "arguments": args,
                }
            )

        return {
            "assistant_message": message.get("content", ""),
            "reasoning": message.get("reasoning", ""),
            "tool_calls": tool_calls,
            "context_pct": usage.get("context_pct", 0.0),
            "tokens_used": usage.get("total_tokens", 0),
            "finish_reason": choice.get("finish_reason", ""),
        }
