from __future__ import annotations

import asyncio
import logging
import signal
import sys
from pathlib import Path

import os
from spine.gate_proxy import GateProxy
from spine.config import load_config
from spine.events import EventLogger
from spine.health import HealthMonitor
from spine.stream import StreamManager
from spine.supervisor import Supervisor
from spine.ipc_server import IPCServer
from spine.telegram import TelegramPoller

logging.basicConfig(level=logging.INFO, format="[Spine] %(message)s")
logger = logging.getLogger("spine")


async def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "/spine/spine_config.json"
    cfg = load_config(config_path)

    for dir_path in [
        f"{cfg.spine_dir}/events",
        f"{cfg.spine_dir}/trajectories",
    ]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    logger.info(f"[Spine] Starting: GateURL={cfg.gate_url} Socket={cfg.socket_path}")

    event_logger = EventLogger(f"{cfg.spine_dir}/events")
    health = HealthMonitor(stall_timeout=600.0, startup_timeout=30.0)
    stream_mgr = StreamManager(cfg)
    supervisor = Supervisor(cfg, event_logger, health, stream_mgr)
    gate_proxy = GateProxy(cfg.gate_url, model=os.environ.get("TALOS_MODEL", ""))
    ipc_server = IPCServer(cfg, supervisor, stream_mgr, event_logger, gate_proxy)

    def on_telegram_message(msg):
        text = msg.get("text", "") if isinstance(msg, dict) else str(msg)
        stream_mgr.queue_system_notice(f"[TELEGRAM | {text}]")
        # Auto-register chat_id from first incoming message if not set
        if isinstance(msg, dict):
            chat_id = msg.get("chat", {}).get("id")
            if chat_id and cfg.telegram_chat_id in ("", "0"):
                cfg.telegram_chat_id = str(chat_id)
        wake_path = Path(cfg.spine_dir) / ".wake"
        wake_path.touch()

    telegram_poller = TelegramPoller(cfg, on_telegram_message)

    await ipc_server.start()
    await telegram_poller.start()

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def handle_signal():
        logger.info("[Spine] Shutdown signal received")
        stop_event.set()

    loop.add_signal_handler(signal.SIGINT, handle_signal)
    loop.add_signal_handler(signal.SIGTERM, handle_signal)

    supervisor_task = asyncio.create_task(supervisor.run())

    await stop_event.wait()

    logger.info("[Spine] Shutting down...")
    supervisor.stop()
    await ipc_server.stop()
    event_logger.close()
    logger.info("[Spine] Stopped.")


if __name__ == "__main__":
    asyncio.run(main())
