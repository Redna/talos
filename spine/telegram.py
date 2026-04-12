from __future__ import annotations

import httpx

from spine.config import SpineConfig


def send_telegram_message(cfg: SpineConfig, text: str):
    if not cfg.telegram_bot_token or cfg.telegram_chat_id == 0:
        return
    url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    data = {"chat_id": str(cfg.telegram_chat_id), "text": text}
    try:
        with httpx.Client() as client:
            client.post(url, data=data)
    except Exception:
        pass
