from __future__ import annotations

import json
from pathlib import Path

from aiohttp import web

from spine.config import SpineConfig
from spine.supervisor import Supervisor
from spine.stream import StreamManager
from spine.events import EventLogger


class ControlPlane:
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
        self.app = web.Application()
        self.app.router.add_get("/status", self._handle_status)
        self.app.router.add_get("/events", self._handle_events)
        self.app.router.add_get("/state", self._handle_state)
        self.app.router.add_post("/message", self._handle_message)
        self.app.router.add_post("/command", self._handle_command)
        self.app.router.add_get("/health", self._handle_health)
        self.app.router.add_get("/commit", self._handle_commit)

    async def start(self):
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, "0.0.0.0", self.cfg.control_plane_port)
        await self._site.start()

    async def stop(self):
        await self.app.shutdown()

    async def _handle_status(self, request):
        state = await self.stream.get_state()
        return web.json_response(state)

    async def _handle_state(self, request):
        state = await self.stream.get_state()
        return web.json_response(state)

    async def _handle_message(self, request):
        data = await request.json()
        text = data.get("text", "")
        self.stream.queue_system_notice(text)
        return web.Response(status=200)

    async def _handle_command(self, request):
        data = await request.json()
        command = data.get("command", "")
        if command == "force_restart":
            self.supervisor.request_restart("operator_command")
            return web.Response(status=200)
        elif command == "pause":
            Path("/spine/.paused").touch()
            self.stream.queue_system_notice(
                "[SYSTEM | Paused — waiting for resume or Telegram]"
            )
            return web.Response(status=200)

        elif command == "resume":
            if Path("/spine/.paused").exists():
                Path("/spine/.paused").unlink()
                Path("/spine/.wake").touch()
            return web.Response(status=200)

        elif command == "force_fold":
            self.stream.queue_system_notice(f"[SYSTEM | Command: {command}]")
            return web.Response(status=200)
        return web.Response(status=400, text="unknown command")

    async def _handle_health(self, request):
        return web.json_response({"status": "healthy"})

    async def _handle_commit(self, request):
        candidate_file = Path(self.cfg.spine_dir) / "last_candidate_commit"
        if not candidate_file.exists():
            return web.json_response({})
        try:
            commit_hash = candidate_file.read_text().strip()
            return web.json_response({"candidate": commit_hash})
        except Exception:
            return web.json_response({})
