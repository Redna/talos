from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from pathlib import Path

from spine.config import SpineConfig
from spine.events import EventLogger
from spine.health import HealthMonitor
from spine.snapshot import SnapshotManager
from spine.stream import StreamManager

logger = logging.getLogger("spine.supervisor")


class Supervisor:
    def __init__(
        self,
        cfg: SpineConfig,
        events: EventLogger,
        snapshots: SnapshotManager,
        stream: StreamManager,
    ):
        self.cfg = cfg
        self.events = events
        self.snapshots = snapshots
        self.stream = stream
        self.health = HealthMonitor(cfg.stall_timeout, cfg.startup_timeout)
        self.process: subprocess.Popen | None = None
        self._consecutive_failures = 0
        self._running = True
        self._restart_requested = asyncio.Event()

    async def run(self):
        while self._running:
            await self._start_cortex()
            await self._watch_cortex()

    def stop(self):
        self._running = False
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def request_restart(self, reason: str):
        commit_sha = self._get_current_commit()
        self.events.emit(
            "spine.cortex_restart",
            {
                "reason": reason,
                "commit_sha": commit_sha,
                "consecutive_failures": self._consecutive_failures,
            },
        )
        self._restart_requested.set()

    async def _start_cortex(self):
        env = dict(os.environ)
        env["SPINE_SOCKET"] = self.cfg.socket_path
        env["MEMORY_DIR"] = self.cfg.memory_dir
        env["SPINE_DIR"] = self.cfg.spine_dir

        cmd = [self.cfg.cortex_bin] + self.cfg.cortex_args
        logger.info(f"[Spine] Starting Cortex: {' '.join(cmd)}")
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=self.cfg.app_dir,
                env=env,
            )
            self.health.cortex_started()
            self.events.emit("spine.cortex_started", {"pid": self.process.pid})
        except Exception as e:
            logger.error(f"[Spine] Failed to start Cortex: {e}")
            self.events.emit("spine.cortex_start_failed", {"error": str(e)})
            await asyncio.sleep(5)

    async def _watch_cortex(self):
        if not self.process:
            return

        while self._running:
            retcode = self.process.poll()
            if retcode is not None:
                self._handle_cortex_exit(retcode)
                return

            try:
                await asyncio.wait_for(self._restart_requested.wait(), timeout=30.0)
                logger.info("[Spine] Restart requested")
                self.process.terminate()
                self.process.wait()
                return
            except asyncio.TimeoutError:
                if self.health.is_stalled():
                    logger.info("[Spine] Cortex stall detected")
                    self.events.emit("spine.stall_detected", {})
                    self.process.terminate()
                    self.process.wait()
                    return

    def _handle_cortex_exit(self, exit_code: int):
        commit_sha = self._get_current_commit()
        self.events.emit(
            "spine.cortex_crash",
            {
                "exit_code": exit_code,
                "commit_sha": commit_sha,
                "consecutive_failures": self._consecutive_failures,
            },
        )

        if self.health.first_think_done:
            self._consecutive_failures = 0

        if self.health.is_startup_failure(exit_code):
            logger.info(
                f"[Spine] Cortex startup failure (exit {exit_code}) — reverting last commit"
            )
            self.events.emit(
                "spine.startup_failure",
                {
                    "exit_code": exit_code,
                    "commit_sha": commit_sha,
                    "consecutive_failures": self._consecutive_failures,
                },
            )
            self._consecutive_failures += 1
            self._revert_commit(1)
            self.stream.queue_system_notice(
                f"[SYSTEM | Cortex startup failure (exit code {exit_code}). "
                f"Reverted 1 commit. Consecutive failures: {self._consecutive_failures}]"
            )
            return

        self._consecutive_failures += 1
        depth = min(self._consecutive_failures, self.cfg.max_reversal_depth)
        if depth > 0:
            self._revert_commit(depth)

        if self._consecutive_failures >= self.cfg.max_reversal_depth:
            self.events.emit(
                "spine.system_override",
                {
                    "message": "Maximum reversal depth reached. Abandoning approach.",
                    "commit_sha": commit_sha,
                    "consecutive_failures": self._consecutive_failures,
                },
            )

        self.stream.queue_system_notice(
            f"[SYSTEM | Cortex crashed (exit code {exit_code}). "
            f"Reverted {depth} commit(s). Consecutive failures: {self._consecutive_failures}]"
        )

    def _revert_commit(self, depth: int):
        app_dir = self.cfg.app_dir
        try:
            # 1. Revert the code
            subprocess.run(
                ["git", "reset", "--hard", f"HEAD~{depth}"],
                cwd=app_dir,
                capture_output=True,
                check=True
            )
            subprocess.run(
                ["git", "clean", "-fd"],
                cwd=app_dir,
                capture_output=True,
                check=True
            )
            
            # 2. Restore the memory state to synchronize with the code revert
            # This prevents "Zombie Crash Loops" where old code meets new/corrupt state.
            if self.snapshots.restore(self.cfg.memory_dir):
                logger.info(f"[Spine] Memory state synchronized with code revert (depth={depth})")
            else:
                logger.warning("[Spine] Code reverted, but no valid memory snapshot found to restore")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"[Spine] Git revert failed: {e}")
        except Exception as e:
            logger.error(f"[Spine] Failed to revert commits/state: {e}")
    def _get_current_commit(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.cfg.app_dir,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()[:8]
        except Exception:
            return "unknown"
