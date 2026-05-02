from __future__ import annotations

import asyncio
import json
import subprocess
import time
from pathlib import Path

from spine.config import SpineConfig
from spine.events import EventLogger
from spine.health import HealthMonitor
from spine.stream import StreamManager


class Supervisor:
    def __init__(
        self,
        cfg: SpineConfig,
        events: EventLogger,
        health: HealthMonitor | None,
        stream: StreamManager,
    ):
        self.cfg = cfg
        self.events = events
        self.health = health or HealthMonitor(
            stall_timeout=getattr(cfg, "stall_timeout", 120.0),
            startup_timeout=30.0,
        )
        self.stream = stream
        self._restart_requested = False
        self._restart_reason = ""
        self._cortex_proc = None
        self._consecutive_failures = 0
        self._last_stable_commit = ""
        self._running = False
        self._load_last_good_commit()

    def request_restart(self, reason: str):
        self._restart_requested = True
        self._restart_reason = reason
        self.events.emit("supervisor.restart_requested", {"reason": reason})

    def is_paused(self) -> bool:
        return (Path(self.cfg.spine_dir) / ".paused").exists()

    def write_health(self):
        status = "running"
        if self.is_paused():
            status = "paused"
        if self._consecutive_failures > 3:
            status = "degraded"
        data = {
            "status": status,
            "consecutive_failures": self._consecutive_failures,
            "last_stable_commit": self._last_stable_commit,
        }
        health_path = Path(self.cfg.spine_dir) / "health.json"
        health_path.write_text(json.dumps(data, indent=2))

    def write_commit(self):
        candidate = ""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.cfg.app_dir,
            )
            if result.returncode == 0:
                candidate = result.stdout.strip()
        except Exception:
            pass
        ahead = 0
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD", "^origin/main"],
                capture_output=True,
                text=True,
                cwd=self.cfg.app_dir,
            )
            if result.returncode == 0:
                ahead = int(result.stdout.strip())
        except Exception:
            pass
        data = {
            "candidate": candidate,
            "stable": self._last_stable_commit,
            "ahead": ahead,
        }
        commit_path = Path(self.cfg.spine_dir) / "commit.json"
        commit_path.write_text(json.dumps(data, indent=2))

    async def run(self):
        self._running = True
        self.health.cortex_start_time = time.time()
        state_path = Path(self.cfg.spine_dir) / "state.json"
        if not state_path.exists():
            state_path.write_text(
                json.dumps(
                    {
                        "turn": 0,
                        "context_pct": 0.0,
                        "focus": "none",
                        "urgency": "nominal",
                        "memory_file_count": 0,
                        "last_files": [],
                    }
                )
            )
        self.start_cortex()
        self.health.cortex_started()
        commit_counter = 0
        while self._running:
            await asyncio.sleep(5)
            self.write_health()
            commit_counter += 1
            if commit_counter >= 6:
                self.write_commit()
                commit_counter = 0
            if self._cortex_proc is not None:
                retcode = self._cortex_proc.poll()
                if retcode is not None:
                    self._consecutive_failures += 1
                    self.events.emit(
                        "supervisor.cortex_exit",
                        {"code": retcode, "failures": self._consecutive_failures},
                    )
                    if self._consecutive_failures > 3:
                        self.events.emit(
                            "supervisor.cortex_dead",
                            {"failures": self._consecutive_failures},
                        )
                        if self._revert_to_last_good_commit():
                            self._consecutive_failures = 0
                    self.start_cortex()
                    if self._cortex_proc is not None:
                        self.health.cortex_started()
                else:
                    self._consecutive_failures = 0
                    self._record_good_commit()
                    if self.health.is_stalled():
                        self.events.emit(
                            "supervisor.cortex_stall",
                            {"stall_timeout": self.health.stall_timeout},
                        )
                        try:
                            self._cortex_proc.kill()
                            self._cortex_proc.wait(timeout=5)
                        except Exception:
                            pass
                        self._consecutive_failures += 1
                        self.start_cortex()
                        if self._cortex_proc is not None:
                            self.health.cortex_started()
            else:
                self.start_cortex()
                if self._cortex_proc is not None:
                    self.health.cortex_started()
            if self._restart_requested:
                self._consecutive_failures = 0
                await self._restart_cortex()
                self.health.cortex_started()
            if self.is_paused():
                while self.is_paused() and self._running:
                    await asyncio.sleep(1)

    def start_cortex(self):
        # Fold accumulated stream messages when a new cortex starts to prevent
        # message-count degradation (gemma4:31b degrades past ~50 msgs even when
        # context_pct is low). The fold archives the trajectory and resets context.
        msg_count = len(self.stream.messages)
        if msg_count > 25:
            self.events.emit(
                "supervisor.stream_fold",
                {"msg_count": msg_count, "reason": "cortex_restart"},
            )
            self.stream.fold(
                "Session context folded on cortex restart. "
                "Previous trajectory archived to /spine/trajectories/."
            )
        try:
            self._cortex_proc = subprocess.Popen(
                ["python", "-m", "cortex"],
                cwd=self.cfg.app_dir,
            )
        except Exception:
            self._cortex_proc = None

    async def _restart_cortex(self):
        if self._cortex_proc is not None:
            try:
                self._cortex_proc.kill()
                self._cortex_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            self._cortex_proc = None
        await asyncio.sleep(2)
        self._restart_requested = False
        self.start_cortex()

    def stop_cortex(self):
        if self._cortex_proc is not None:
            try:
                self._cortex_proc.terminate()
                self._cortex_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._cortex_proc.kill()
                self._cortex_proc.wait()
            self._cortex_proc = None

    def _load_last_good_commit(self):
        path = Path(self.cfg.spine_dir) / "last_good_commit"
        if path.exists():
            self._last_stable_commit = path.read_text().strip()
        else:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=self.cfg.app_dir,
                )
                if result.returncode == 0:
                    self._last_stable_commit = result.stdout.strip()
            except Exception:
                pass

    def _record_good_commit(self):
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.cfg.app_dir,
            )
            if result.returncode == 0:
                commit = result.stdout.strip()
                self._last_stable_commit = commit
                path = Path(self.cfg.spine_dir) / "last_good_commit"
                path.write_text(commit)
        except Exception:
            pass

    def _revert_to_last_good_commit(self):
        if not self._last_stable_commit:
            self.events.emit("supervisor.revert_failed", {"reason": "no_good_commit"})
            return False
        try:
            subprocess.run(
                ["git", "reset", "--hard", self._last_stable_commit],
                capture_output=True,
                text=True,
                cwd=self.cfg.app_dir,
                check=True,
            )
            subprocess.run(
                ["git", "checkout", "--", "."],
                capture_output=True,
                text=True,
                cwd=self.cfg.app_dir,
            )
            self.events.emit(
                "supervisor.commit_reverted",
                {"commit": self._last_stable_commit},
            )
            return True
        except Exception as e:
            self.events.emit("supervisor.revert_failed", {"reason": str(e)})
            return False

    def stop(self):
        self._running = False
        self.stop_cortex()
