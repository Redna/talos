from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime
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
            if self._consecutive_failures > 0 and self._running:
                backoff = min(5 * self._consecutive_failures, 60)
                logger.info(
                    f"[Spine] Backing off {backoff}s before restart (consecutive failures: {self._consecutive_failures})"
                )
                self.events.emit(
                    "spine.restart_backoff",
                    {
                        "backoff_seconds": backoff,
                        "consecutive_failures": self._consecutive_failures,
                    },
                )
                await asyncio.sleep(backoff)

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
        self._restart_requested.clear()
        self._restore_pristine_spine()
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
                await self._handle_cortex_exit(retcode)
                return

            try:
                await asyncio.wait_for(self._restart_requested.wait(), timeout=30.0)
                logger.info("[Spine] Restart requested")
                self.process.terminate()
                await asyncio.get_event_loop().run_in_executor(None, self.process.wait)
                return
            except asyncio.TimeoutError:
                if self.health.is_stalled():
                    logger.info("[Spine] Cortex stall detected")
                    self.events.emit("spine.stall_detected", {})
                    self.process.terminate()
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.process.wait
                    )
                    return

    async def _write_crash_bundle(self, exit_code: int) -> Path:
        """Write crash forensics bundle to /spine/crashes/{timestamp}/."""
        crash_dir = (
            Path(self.cfg.spine_dir)
            / "crashes"
            / datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        )
        crash_dir.mkdir(parents=True, exist_ok=True)

        recent = self.events.recent_events(100)
        (crash_dir / "last_100_events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in recent)
        )

        state = await self.stream.get_state()
        (crash_dir / "state_snapshot.json").write_text(
            json.dumps(state, indent=2, default=str)
        )

        commit_sha = self._get_current_commit()
        summary = f"""# Crash Forensics Summary

**Timestamp:** {datetime.now().isoformat()}
**Exit Code:** {exit_code}
**Commit:** {commit_sha}
**Consecutive Failures:** {self._consecutive_failures}
**First Think Done:** {self.health.first_think_done}
**Last Focus:** {state.get("focus", "unknown")}
**Turn:** {state.get("turn", 0)}
**Context %:** {state.get("context_pct", 0.0):.1%}
**Tokens Used:** {state.get("tokens_used", 0):,}

## Recent Events (last 5)

"""
        for event in recent[-5:]:
            summary += f"- {event.get('type')} @ {event.get('ts')}: {json.dumps(event.get('payload', {}))}\n"

        (crash_dir / "crash_summary.md").write_text(summary)
        logger.info(f"[Spine] Crash bundle written: {crash_dir}")
        return crash_dir

    async def _handle_cortex_exit(self, exit_code: int):
        crash_dir = await self._write_crash_bundle(exit_code)
        self.events.emit("spine.crash_bundle_written", {"path": str(crash_dir)})
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
            self.stream.queue_system_notice(
                f"[SYSTEM | Cortex exited after successful operation (exit code {exit_code}). "
                f"No revert applied.]"
            )
            return

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
            result = subprocess.run(
                ["git", "reset", "--hard", f"HEAD~{depth}"],
                cwd=app_dir,
                capture_output=True,
            )
            if result.returncode != 0:
                logger.error(f"[Spine] git reset failed: {result.stderr.decode()}")
                return
            subprocess.run(
                ["git", "clean", "-fd"],
                cwd=app_dir,
                capture_output=True,
            )
        except Exception as e:
            logger.error(f"[Spine] Failed to revert commits: {e}")

    def _restore_pristine_spine(self):
        pristine = Path("/spine_pristine")
        target = Path(self.cfg.app_dir) / "spine"
        if pristine.is_dir() and target.is_dir():
            try:
                subprocess.run(
                    ["cp", "-a", str(pristine) + "/.", str(target)],
                    check=True,
                    capture_output=True,
                )
                logger.info("[Spine] Restored pristine spine files")
            except Exception as e:
                logger.error(f"[Spine] Failed to restore pristine spine: {e}")

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
