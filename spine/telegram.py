from __future__ import annotations

import json
import urllib.request
import urllib.error

from spine.config import SpineConfig


def send_telegram_message(cfg: SpineConfig, text: str):
    if not cfg.telegram_bot_token or not cfg.telegram_chat_id:
        return
    url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": cfg.telegram_chat_id,
            "text": text,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
    except urllib.error.URLError:
        pass


class TelegramPoller:
    def __init__(self, cfg: SpineConfig, on_message):
        self.cfg = cfg
        self.on_message = on_message
        self._running = False
        self._offset = 0

    async def start(self):
        if not self.cfg.telegram_bot_token:
            return
        self._running = True
        while self._running:
            url = (
                f"https://api.telegram.org/bot{self.cfg.telegram_bot_token}/getUpdates"
                f"?offset={self._offset}&timeout=10"
            )
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                for update in data.get("result", []):
                    self._offset = update.get("update_id", self._offset) + 1
                    msg = update.get("message", {})
                    self.on_message(msg)
            except Exception:
                pass
            import asyncio

            await asyncio.sleep(1)

    async def stop(self):
        self._running = False
