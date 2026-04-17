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
        self.app.router.add_get("/commit", self._handle_commit)
        self.app.router.add_post("/message", self._handle_message)
        self.app.router.add_post("/command", self._handle_command)
        self.app.router.add_get("/health", self._handle_health)

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

    async def _handle_events(self, request):
        tail = int(request.query.get("tail", "100"))
        events_dir = Path(self.cfg.spine_dir) / "events"
        all_events = []
        for jsonl_file in sorted(events_dir.glob("*.jsonl"), reverse=True):
            for line in jsonl_file.read_text().splitlines():
                try:
                    all_events.append(json.loads(line))
                except (json.JSONDecodeError, ValueError):
                    pass
        return web.json_response(all_events[-tail:])

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
        health = {"status": "healthy"}
        if hasattr(self.supervisor, "health") and self.supervisor.health:
            h = self.supervisor.health
            if hasattr(h, "is_stalled") and h.is_stalled():
                health["status"] = "stalled"
            if (
                hasattr(h, "first_think_done")
                and not h.first_think_done
                and h.cortex_start_time > 0
            ):
                health["status"] = "starting"
        if hasattr(self.supervisor, "_consecutive_failures"):
            health["consecutive_failures"] = self.supervisor._consecutive_failures
        return web.json_response(health)

    async def _handle_commit(self, request):
        commit_info = {}
        try:
            candidate_path = Path(self.cfg.spine_dir) / "last_candidate_commit"
            stable_path = Path(self.cfg.spine_dir) / "last_stable_commit"
            if candidate_path.exists():
                commit_info["candidate"] = candidate_path.read_text().strip()
                try:
                    result = subprocess.run(
                        [
                            "git",
                            "-C",
                            self.cfg.app_dir,
                            "log",
                            "-1",
                            "--format=%s",
                            commit_info["candidate"],
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    commit_info["candidate_msg"] = result.stdout.strip()
                except Exception:
                    pass
            if stable_path.exists():
                commit_info["stable"] = stable_path.read_text().strip()
            if "candidate" in commit_info and "stable" in commit_info:
                try:
                    result = subprocess.run(
                        [
                            "git",
                            "-C",
                            self.cfg.app_dir,
                            "rev-list",
                            "--count",
                            f"{commit_info['stable']}..{commit_info['candidate']}",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    commit_info["ahead"] = int(result.stdout.strip())
                except Exception:
                    pass
        except Exception:
            pass
        return web.json_response(commit_info)
