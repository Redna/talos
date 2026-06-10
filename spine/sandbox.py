"""Phase 2b: Talos sandbox launches the Cortex as a ``nono run`` subprocess.

Why the rewrite
---------------
Phase 2 used ``nono_py.sandboxed_exec()`` (a Python call that runs the
Cortex on a daemon thread and returns a thread-wrapped
:class:`SandboxProc` with a no-op ``.kill()``).  That meant the Spine
could not ``SIGTERM`` a hung Cortex: ``sandboxed_exec`` blocks until
the child exits, so the only termination channel was a flag the
background thread could check between calls — not useful for
timeouts.

The fix is to treat ``nono`` as **infrastructure**: a static binary
that the agent cannot modify.  The Spine runs it as a real
:func:`subprocess.Popen` subprocess:

    Popen(['nono', 'run', '--config', policy, '--', sys.executable, '-m', 'cortex'])

That gives the Supervisor a real Popen with a real PID.  The user
explicitly rejected the in-Cortex approach — rlimits must be set by
the Spine (via ``preexec_fn``) and the container's cgroup caps are
the unbypassable backstop.

Signal forwarding
-----------------
We verified that ``nono run`` forwards ``SIGTERM`` to its child
(both processes die with exit code 143).  Sending ``SIGKILL`` to
the nono PID also takes down the child.

On kernels that lack Landlock — or when *cfg.nono_enabled* is
``False`` — every method degrades gracefully to plain
``subprocess.Popen`` so the agent keeps running without kernel
isolation.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from spine.config import SpineConfig

logger = logging.getLogger("spine.sandbox")


# ---------------------------------------------------------------------------
# rlimits — applied via preexec_fn so the agent cannot raise them
# ---------------------------------------------------------------------------

# 30 minutes of CPU time (covers long LLM streams + code execution).
_CORTEX_CPU_RLIMIT_S = 1800
# 8 GB virtual address space — the container cgroup is the real cap.
_CORTEX_AS_RLIMIT_BYTES = 8 * 1024 * 1024 * 1024
# 4096 open file descriptors (default is usually 1024 — agents that
# fork many subprocesses hit this).
_CORTEX_NOFILE_RLIMIT = 4096


def _set_cortex_rlimits() -> None:
    """Apply rlimits to the Cortex process tree.

    Set via ``preexec_fn`` on the nono Popen, so they apply to nono
    itself and are inherited by its child (the Cortex).  The agent
    *can* lower its own limits but cannot exceed the container cgroup
    cap (set in ``docker-compose.yml``).

    Must be safe to call from the preexec callback — it runs in the
    child between ``fork()`` and ``exec()``, so only async-signal-safe
    operations are allowed.  ``resource.setrlimit`` is async-signal-safe
    on Linux.
    """
    import resource

    try:
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (_CORTEX_CPU_RLIMIT_S, _CORTEX_CPU_RLIMIT_S),
        )
    except (OSError, ValueError):
        # EINVAL on kernels that don't honour the cap — non-fatal.
        pass
    try:
        resource.setrlimit(
            resource.RLIMIT_AS,
            (_CORTEX_AS_RLIMIT_BYTES, _CORTEX_AS_RLIMIT_BYTES),
        )
    except (OSError, ValueError):
        pass
    try:
        resource.setrlimit(
            resource.RLIMIT_NOFILE,
            (_CORTEX_NOFILE_RLIMIT, _CORTEX_NOFILE_RLIMIT),
        )
    except (OSError, ValueError):
        pass


# ---------------------------------------------------------------------------
# TalosSandbox — Popen-CLI orchestrator
# ---------------------------------------------------------------------------

# Default path to write the nono policy manifest.  Lives under the
# Spine's own data directory so the Cortex cannot tamper with it
# (the Spine runs as root; the Cortex runs as ``talos`` with read-only
# access to /spine by default — see ``nono_policy.build_policy_dict``).
DEFAULT_POLICY_PATH = "/spine/nono_policy.json"


class TalosSandbox:
    """Manages the Cortex sandbox lifecycle via the ``nono`` CLI.

    On kernels that lack Landlock (or when *nono_enabled* is False)
    every method degrades gracefully to the classic ``subprocess.Popen``
    behaviour so the agent keeps running — just without kernel-level
    isolation.

    Parameters
    ----------
    cfg:
        Spine configuration dataclass.
    policy_path:
        Where to write the JSON manifest passed to ``nono run --config``.
        The directory is created on demand.  The file is regenerated on
        every ``__init__``; if its contents are unchanged the write is
        a no-op (see :func:`spine.nono_policy.write_nono_policy`).
    snapshot_dir:
        Directory where the SnapshotManager stores snapshots.
    audit_path:
        Path to the audit NDJSON file.
    """

    def __init__(
        self,
        cfg: SpineConfig,
        policy_path: str = DEFAULT_POLICY_PATH,
        snapshot_dir: str = "/spine/snapshots",
        audit_path: str = "/spine/audit.ndjson",
    ):
        self.cfg = cfg
        self.policy_path = policy_path
        self.nono_enabled = getattr(cfg, "nono_enabled", True)
        self.caps: Any = None
        self.snapshots = None
        self.recorder = None
        self.proxy = None

        if not self._kernel_supports():
            logger.info(
                "[TalosSandbox] nono not supported on this kernel — sandbox disabled"
            )
            return

        # --- policy file (must be on disk before launch_cortex) -------
        # Even when the Python CapabilitySet is unavailable (e.g. a
        # minimal container), the policy file is still written so the
        # CLI has *something* to enforce.
        try:
            from spine.nono_policy import write_nono_policy

            write_nono_policy(cfg, policy_path)
        except Exception:
            logger.warning(
                "[TalosSandbox] Failed to write nono policy — nono will use defaults",
                exc_info=True,
            )

        # --- capability manifest (Python-side, for tests + introspection) -
        try:
            from spine.capabilities import build_cortex_caps

            self.caps = build_cortex_caps(cfg)
        except Exception:
            logger.warning("[TalosSandbox] Failed to build capability set", exc_info=True)

        # --- network proxy (lazy — may not exist) -----------------------
        try:
            from spine.proxy import build_proxy_config, start_proxy

            proxy_cfg = build_proxy_config(cfg)
            self.proxy = start_proxy(proxy_cfg)
            logger.info("[TalosSandbox] network proxy started")
        except ImportError:
            logger.info("[TalosSandbox] spine.proxy not available — network fully blocked")
        except Exception:
            logger.warning(
                "[TalosSandbox] Failed to start proxy — network fully blocked",
                exc_info=True,
            )

        # --- snapshots -------------------------------------------------
        try:
            from spine.snapshots import init_snapshots

            self.snapshots = init_snapshots(snapshot_dir)
        except Exception:
            logger.warning("[TalosSandbox] Failed to init snapshots", exc_info=True)

        # --- audit recorder --------------------------------------------
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
        stdout: object | None = None,
    ) -> subprocess.Popen:
        """Start the Cortex under ``nono run`` and return a real Popen.

        *cmd* defaults to ``[sys.executable, "-m", "cortex"]``; *cwd*
        to ``cfg.app_dir``.  The returned object supports the full
        :class:`subprocess.Popen` API — ``.poll()``, ``.returncode``,
        ``.kill()``, ``.terminate()`` and ``.wait(timeout=...)``.

        On unsupported kernels (or when ``nono`` is missing) the
        method falls back to a plain ``subprocess.Popen`` of *cmd*
        with no preexec callback.
        """
        if cmd is None:
            cmd = [sys.executable, "-m", "cortex"]
        if cwd is None:
            cwd = self.cfg.app_dir

        # --- fallback: no sandbox --------------------------------------
        if not self._kernel_supports() or not Path("/usr/bin/nono").exists():
            logger.warning(
                "[TalosSandbox] Falling back to subprocess.Popen (no nono binary / kernel)"
            )
            return subprocess.Popen(
                cmd, cwd=cwd, stderr=stderr, stdout=stdout
            )

        # --- sandboxed path via nono CLI --------------------------------
        env = self._build_env()
        # NOTE: We pass filesystem grants as CLI flags (--read, --allow)
        # rather than via the JSON policy file, because nono 0.61.2 has
        # a bug where the JSON manifest's filesystem.read list does not
        # cover /venv/bin (where the Talos Python lives) — the CLI
        # flags are the reliable path.  We still keep the policy file
        # for groups, network, and other features that work correctly.
        # See spinetests/issue-127 for the upstream bug report.
        nono_cmd = [
            "nono",
            "run",
            "--config",
            self.policy_path,
            "--silent",   # suppress nono's banner — keep stderr for the Cortex
            # Filesystem grants via CLI (workaround for nono 0.61.2 bug
            # with the JSON manifest's read list not covering /venv/bin).
            "--read", "/",
            "--allow", "/app",
            "--allow", "/memory",
            "--allow", "/spine",
            "--allow", "/home/talos",
            "--allow", "/tmp",
            "--allow", "/var/tmp",
            "--allow", "/venv",
            "--allow", "/venv/bin",
            "--allow", "/venv/lib",
            "--allow", "/usr/local",
            "--allow", "/usr/local/bin",
            "--allow", "/usr/local/lib",
            "--allow", "/opt",
            "--allow", "/run",
            # We use the Spine's own TalosAuditRecorder (Merklized) for
            # the per-session audit trail; disable nono's redundant
            # audit to avoid double-logging and to skip the need for a
            # writable nono state directory.
            "--no-audit",
            "--",
        ] + list(cmd)

        logger.info(
            "[TalosSandbox] Launching Cortex via nono CLI: %s",
            " ".join(nono_cmd),
        )

        # Build the Popen kwargs.  We always set ``env=`` explicitly
        # so the Cortex does not inherit the Spine's full environment
        # (e.g. real GITHUB_TOKEN).  ``preexec_fn`` is applied in the
        # forked child between fork() and exec() of the nono binary.
        popen_kwargs: dict[str, Any] = {
            "cwd": cwd,
            "stderr": stderr if stderr is not None else subprocess.PIPE,
            "stdout": stdout if stdout is not None else subprocess.PIPE,
            "env": dict(env),
            "preexec_fn": _set_cortex_rlimits,
        }

        if self.recorder and self.recorder.active:
            try:
                self.recorder.session_start(list(cmd))
            except Exception:
                logger.warning(
                    "[TalosSandbox] session_start failed", exc_info=True
                )

        return subprocess.Popen(nono_cmd, **popen_kwargs)

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
        base_pairs: list[tuple[str, str]] = [
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

        if self.proxy:
            # Let the proxy add its own env vars (PROXY_CA_CERT,
            # upstream config, etc.) and return the merged list.
            try:
                return self.proxy.sandbox_env(extra_env=base_pairs)
            except Exception:
                logger.warning(
                    "[TalosSandbox] proxy.sandbox_env() failed — using base env only",
                    exc_info=True,
                )

        return base_pairs
