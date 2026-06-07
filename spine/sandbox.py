from __future__ import annotations

import logging
import os
import subprocess
import threading
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nono_py import CapabilitySet
    from spine.config import SpineConfig

logger = logging.getLogger("spine.sandbox")


class SandboxProc:
    """Minimal Popen-like wrapper returned by :meth:`TalosSandbox.launch_cortex`.

    The Supervisor uses ``.poll()`` and ``.returncode`` as well as
    ``.kill()`` on stall detection — this object matches that contract
    while the actual child runs inside ``sandboxed_exec`` on a
    background thread.
    """

    def __init__(self, thread: threading.Thread, result_holder: dict):
        self._thread = thread
        self._result = result_holder  # {"returncode": int | None}

    def poll(self) -> int | None:
        """Return the exit code if the sandboxed process has finished."""
        return self._result["returncode"] if self._result.get("done") else None

    @property
    def returncode(self) -> int | None:
        return self._result["returncode"]

    def kill(self) -> None:
        """Best-effort termination.

        ``sandboxed_exec`` blocks until the child exits, so we cannot
        send SIGKILL directly.  The Supervisor already has a
        TimeoutExpired-fallback path that handles this case — setting
        a flag here lets the background thread notice it should stop
        waiting (when/if nono supports cancellation).
        """
        self._result["_cancel"] = True

    def wait(self, timeout: float | None = None) -> int:
        if timeout is not None:
            self._thread.join(timeout=timeout)
        else:
            self._thread.join()
        return self._result.get("returncode", -1)


class TalosSandbox:
    """Manages the Cortex sandbox lifecycle via nono Landlock.

    On kernels that lack Landlock (or when *nono_enabled* is False)
    every method degrades gracefully to the classic `subprocess.Popen`
    behaviour so the agent keeps running — just without kernel-level
    isolation.

    Parameters
    ----------
    cfg:
        Spine configuration dataclass.
    snapshot_dir:
        Directory where the SnapshotManager stores snapshots.
    audit_path:
        Path to the audit NDJSON file.
    """

    def __init__(
        self,
        cfg: SpineConfig,
        snapshot_dir: str = "/spine/snapshots",
        audit_path: str = "/spine/audit.ndjson",
    ):
        self.cfg = cfg
        self.nono_enabled = getattr(cfg, "nono_enabled", True)
        self.caps: CapabilitySet | None = None
        self.snapshots = None
        self.recorder = None
        self.proxy = None

        if not self._kernel_supports():
            logger.info("[TalosSandbox] nono not supported on this kernel — sandbox disabled")
            return

        # --- capability manifest ------------------------------------------------
        try:
            from spine.capabilities import build_cortex_caps

            self.caps = build_cortex_caps(cfg)
        except Exception:
            logger.warning("[TalosSandbox] Failed to build capability set", exc_info=True)

        # --- network proxy (lazy — may not exist) ------------------------------
        try:
            from spine.proxy import build_proxy_config, start_proxy

            proxy_cfg = build_proxy_config(cfg)
            self.proxy = start_proxy(proxy_cfg)
            logger.info("[TalosSandbox] network proxy started")
        except ImportError:
            logger.info("[TalosSandbox] spine.proxy not available — network fully blocked")
        except Exception:
            logger.warning("[TalosSandbox] Failed to start proxy — network fully blocked", exc_info=True)

        # --- snapshots ---------------------------------------------------------
        try:
            from spine.snapshots import init_snapshots

            self.snapshots = init_snapshots(snapshot_dir)
        except Exception:
            logger.warning("[TalosSandbox] Failed to init snapshots", exc_info=True)

        # --- audit recorder ----------------------------------------------------
        try:
            from spine.audit import TalosAuditRecorder

            self.recorder = TalosAuditRecorder(audit_path)
        except Exception:
            logger.warning("[TalosSandbox] Failed to init audit recorder", exc_info=True)

    # ------------------------------------------------------------------
    # public helpers
    # ------------------------------------------------------------------

    def is_supported(self) -> bool:
        """True when the current kernel can enforce a nono sandbox."""
        return self._kernel_supports()

    # ------------------------------------------------------------------
    # launch
    # ------------------------------------------------------------------

    def launch_cortex(
        self,
        cmd: list[str] | None = None,
        cwd: str | None = None,
        stderr: object | None = None,
    ):
        """Start the Cortex, sandboxed when possible, and return a
        ``.poll()``-able object.

        *cmd* defaults to ``["python", "-m", "cortex"]``, *cwd* to
        ``cfg.app_dir``.  The returned object supports the subset of
        ``subprocess.Popen`` that the Supervisor actually calls:
        ``.poll()``, ``.returncode``, ``.kill()``, and ``.wait()``.
        """
        if cmd is None:
            cmd = ["python", "-m", "cortex"]
        if cwd is None:
            cwd = self.cfg.app_dir

        if not self._kernel_supports() or not self.caps:
            logger.warning(
                "[TalosSandbox] Falling back to subprocess.Popen (no sandbox)"
            )
            proc = subprocess.Popen(cmd, cwd=cwd, stderr=stderr)
            return proc

        # --- sandboxed path ---------------------------------------------------
        env = self._build_env()

        result_holder: dict[str, int | bool | None] = {
            "returncode": None,
            "done": False,
            "_cancel": False,
        }

        def _run():
            """Execute sandboxed_exec on a daemon thread so the main
            asyncio loop is not blocked."""
            try:
                from nono_py import sandboxed_exec

                if self.recorder and self.recorder.active:
                    self.recorder.session_start(cmd)

                # timeout_secs=0 means "no timeout" — runs until exit.
                result = sandboxed_exec(
                    self.caps,
                    cmd,
                    cwd=cwd,
                    timeout_secs=0,
                    env=env,
                )
                result_holder["returncode"] = result.exit_code
            except Exception:
                logger.exception("[TalosSandbox] sandboxed_exec raised")
                result_holder["returncode"] = 70  # EX_SOFTWARE
            finally:
                result_holder["done"] = True
                if self.recorder and self.recorder.active:
                    self.recorder.session_end(
                        result_holder.get("returncode", -1)
                    )

        t = threading.Thread(target=_run, daemon=True, name="nono-sandbox")
        t.start()

        # Stderr capture: if the caller passed an open file handle for
        # stderr, we cannot redirect it through sandboxed_exec.  The
        # Cortex's own stderr goes to the sandboxed process's stderr
        # which is NOT captured here.  We log a note — a future
        # iteration can tee the sandboxed-exec stderr to the log file.
        if stderr is not None:
            logger.debug(
                "[TalosSandbox] stderr capture requested but sandboxed_exec "
                "does not redirect child stderr — cortex_stderr.log will be "
                "empty for sandboxed sessions"
            )

        return SandboxProc(t, result_holder)

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _kernel_supports(self) -> bool:
        if not self.nono_enabled:
            return False
        try:
            from nono_py import is_supported
            return is_supported()
        except ImportError:
            return False

    def _build_env(self) -> list[tuple[str, str]]:
        """Assemble the environment variable list for the sandboxed process."""
        # Start with proxy-supplied env vars if available.
        if self.proxy:
            base = self.proxy.sandbox_env(
                extra_env=[
                    ("NONO_SESSION_ID", str(uuid.uuid4())),
                    ("MEMORY_DIR", self.cfg.memory_dir),
                    ("SPINE_SOCKET", self.cfg.socket_path),
                    ("SPINE_DIR", self.cfg.spine_dir),
                    ("TALOS_DRIVE_ROOT", "/drive"),
                    ("PATH", os.environ.get("PATH", "/venv/bin:/usr/bin:/bin")),
                    ("HOME", "/home/talos"),
                    ("PYTHONPATH", "/app:/app/cortex"),
                    ("PYTHONUNBUFFERED", "1"),
                ]
            )
        else:
            base = [
                ("NONO_SESSION_ID", str(uuid.uuid4())),
                ("MEMORY_DIR", self.cfg.memory_dir),
                ("SPINE_SOCKET", self.cfg.socket_path),
                ("SPINE_DIR", self.cfg.spine_dir),
                ("TALOS_DRIVE_ROOT", "/drive"),
                ("PATH", os.environ.get("PATH", "/venv/bin:/usr/bin:/bin")),
                ("HOME", "/home/talos"),
                ("PYTHONPATH", "/app:/app/cortex"),
                ("PYTHONUNBUFFERED", "1"),
            ]
        return base
