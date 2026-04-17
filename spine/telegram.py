from __future__ import annotations

import asyncio
import logging
import urllib.parse
import urllib.request
import json

from spine.config import SpineConfig

logger = logging.getLogger("spine.telegram")


def send_telegram_message(cfg: SpineConfig, text: str):
    if not cfg.telegram_bot_token or cfg.telegram_chat_id == 0:
        return
    url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": str(cfg.telegram_chat_id), "text": text}
    ).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
    except Exception as e:
        logger.warning(f"[Telegram] Send failed: {e}")


class TelegramPoller:
    def __init__(self, cfg: SpineConfig, on_message):
        self.cfg = cfg
        self.on_message = on_message
        self._offset = 0
        self._running = False

    async def start(self):
        if not self.cfg.telegram_bot_token:
            logger.info("[Telegram] No bot token configured, skipping inbound polling")
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self):
        self._running = False

    async def _poll_loop(self):
        logger.info("[Telegram] Starting inbound message polling")
        while self._running:
            try:
                updates = await asyncio.get_event_loop().run_in_executor(
                    None, self._fetch_updates
                )
                for update in updates:
                    self._handle_update(update)
            except Exception as e:
                logger.warning(f"[Telegram] Poll error: {e}")
            await asyncio.sleep(3)

    def _handle_update(self, update):
        msg = update.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "")
        if not text:
            return
        if self.cfg.telegram_chat_id and chat_id != self.cfg.telegram_chat_id:
            return
        if not self.cfg.telegram_chat_id:
            self.cfg.telegram_chat_id = chat_id
            logger.info(f"[Telegram] Auto-detected chat_id={chat_id}")
        logger.info(f"[Telegram] Inbound message: {text[:100]}")
        self.on_message(text)

    def _fetch_updates(self):
        url = (
            f"https://api.telegram.org/bot{self.cfg.telegram_bot_token}/getUpdates"
            f"?offset={self._offset + 1}&timeout=10&allowed_updates=%5B%22message%22%5D"
        )
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            updates = data.get("result", [])
            if updates:
                self._offset = updates[-1]["update_id"]
            return updates
        except Exception:
            return []
