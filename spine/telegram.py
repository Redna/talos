from __future__ import annotations

import json
import urllib.request
import urllib.error

from spine.config import SpineConfig


def _is_valid_chat_id(chat_id: str) -> bool:
    return bool(chat_id and chat_id.strip() and chat_id != "0")


def send_telegram_message(cfg: SpineConfig, text: str):
    if not cfg.telegram_bot_token:
        return
    if not _is_valid_chat_id(cfg.telegram_chat_id):
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
    except urllib.error.HTTPError as e:
        import logging

        body = e.read().decode("utf-8", errors="replace")
        logging.error(
            f"[TELEGRAM] HTTP {e.code}: {body} (chat_id={cfg.telegram_chat_id})"
        )
    except urllib.error.URLError as e:
        import logging

        logging.error(f"[TELEGRAM] URL error: {e.reason}")


class TelegramPoller:
    def __init__(self, cfg: SpineConfig, on_message):
        self.cfg = cfg
        self.on_message = on_message
        self._running = False
        self._offset = 0
        self._consecutive_failures = 0

    async def start(self):
        if not self.cfg.telegram_bot_token:
            return
        self._running = True
        import logging, asyncio

        while self._running:
            url = (
                f"https://api.telegram.org/bot{self.cfg.telegram_bot_token}/getUpdates"
                f"?offset={self._offset}&timeout=10"
            )
            try:
                req = urllib.request.Request(url)
                resp_data = await asyncio.to_thread(self._fetch_updates, req)
                data = json.loads(resp_data.decode("utf-8"))
                self._consecutive_failures = 0
                for update in data.get("result", []):
                    self._offset = update.get("update_id", self._offset) + 1
                    msg = update.get("message", {})
                    if not _is_valid_chat_id(self.cfg.telegram_chat_id):
                        discovered = str(msg.get("chat", {}).get("id", ""))
                        if discovered and discovered != "0":
                            self.cfg.telegram_chat_id = discovered
                            logging.info(
                                f"[TELEGRAM] Auto-discovered chat_id={discovered}"
                            )
                    self.on_message(msg)
            except Exception:
                self._consecutive_failures += 1
                if self._consecutive_failures <= 3:
                    logging.exception("[TELEGRAM] Poller exception")
                else:
                    logging.error(
                        f"[TELEGRAM] Poller failed {self._consecutive_failures} times — "
                        f"will keep retrying with backoff"
                    )
            # Exponential backoff: 1s → 2s → 4s → ... → max 60s
            delay = min(1.0 * (2 ** min(self._consecutive_failures, 6)), 60.0)
            await asyncio.sleep(delay)

    def _fetch_updates(self, req):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        except (TimeoutError, urllib.error.URLError):
            # Telegram long-poll timeout is normal when no messages arrive.
            # Return empty result so the caller treats it as "no updates".
            return b'{"ok": true, "result": []}'

    async def stop(self):
        self._running = False
