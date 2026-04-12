from __future__ import annotations

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

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.cfg.control_plane_port)
        await site.start()

    async def stop(self):
        await self.app.shutdown()

    async def _handle_status(self, request):
        state = self.stream.get_state()
        return web.json_response(state)

    async def _handle_events(self, request):
        tail = int(request.query.get("tail", "100"))
        return web.json_response(
            {"tail": tail, "note": "Event querying from JSONL files"}
        )

    async def _handle_state(self, request):
        state = self.stream.get_state()
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
        elif command in ("pause", "resume", "force_fold"):
            self.stream.queue_system_notice(f"[SYSTEM | Command: {command}]")
            return web.Response(status=200)
        return web.Response(status=400, text="unknown command")

    async def _handle_health(self, request):
        return web.json_response({"status": "healthy"})
