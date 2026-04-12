from __future__ import annotations

import asyncio
import logging
import signal
import sys
from pathlib import Path

from spine.config import load_config
from spine.events import EventLogger
from spine.snapshot import SnapshotManager
from spine.stream import StreamManager
from spine.supervisor import Supervisor
from spine.ipc_server import IPCServer
from spine.control_plane import ControlPlane

logging.basicConfig(level=logging.INFO, format="[Spine] %(message)s")
logger = logging.getLogger("spine")


async def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "/spine/spine_config.json"
    cfg = load_config(config_path)

    for dir_path in [
        f"{cfg.spine_dir}/events",
        f"{cfg.spine_dir}/snapshots",
        f"{cfg.spine_dir}/crashes",
    ]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    logger.info(
        f"[Spine] Starting with config: GateURL={cfg.gate_url} Socket={cfg.socket_path}"
    )

    event_logger = EventLogger(f"{cfg.spine_dir}/events")
    snapshot_mgr = SnapshotManager(f"{cfg.spine_dir}/snapshots", cfg.snapshot_interval)
    stream_mgr = StreamManager(cfg)
    supervisor = Supervisor(cfg, event_logger, snapshot_mgr, stream_mgr)
    control_plane = ControlPlane(cfg, supervisor, stream_mgr, event_logger)
    ipc_server = IPCServer(cfg, supervisor, stream_mgr, event_logger)

    await ipc_server.start()
    await control_plane.start()

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
    await control_plane.stop()
    event_logger.close()
    logger.info("[Spine] Stopped.")


if __name__ == "__main__":
    asyncio.run(main())
