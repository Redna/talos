from __future__ import annotations

import datetime
import logging
from pathlib import Path

logger = logging.getLogger("spine.audit")


class TalosAuditRecorder:
    """Thin wrapper around nono AlphaRecorder for session-level audit trails.

    Writes one JSON line per event to an NDJSON file so the log is
    append-only and human-inspectable with ``tail -f`` or ``jq``.
    """

    def __init__(self, path: str = "/spine/audit.ndjson"):
        self.path = Path(path)
        self._recorder = None
        try:
            from nono_py.audit import AlphaRecorder  # noqa: F811
            self._recorder = AlphaRecorder()
        except ImportError:
            logger.info(
                "[audit] nono_py.audit not available — audit trail disabled"
            )

    @property
    def active(self) -> bool:
        return self._recorder is not None

    def _utcnow(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def session_start(self, command: list[str]) -> None:
        if not self._recorder:
            return
        try:
            from nono_py.audit import session_started

            with open(self.path, "a") as f:
                self._recorder.write(
                    f,
                    session_started(
                        started=self._utcnow(),
                        command=command,
                    ),
                )
        except Exception:
            logger.warning("[audit] Failed to write session_start event", exc_info=True)

    def session_end(self, exit_code: int) -> None:
        if not self._recorder:
            return
        try:
            from nono_py.audit import session_ended

            with open(self.path, "a") as f:
                self._recorder.write(
                    f,
                    session_ended(
                        ended=self._utcnow(),
                        exit_code=exit_code,
                    ),
                )
        except Exception:
            logger.warning("[audit] Failed to write session_end event", exc_info=True)

    def verify(self) -> dict:
        """Verify the integrity of the audit log.

        Returns a dict with keys *valid* (bool) and *details* (str).
        On non-Landlock kernels or when the recorder is unavailable
        this always reports *valid=True* since there is nothing to
        verify.
        """
        if not self._recorder or not self.path.exists():
            return {"valid": True, "details": "audit disabled"}
        try:
            from nono_py.audit import verify_log
            return verify_log(str(self.path))
        except Exception:
            logger.warning("[audit] verify failed", exc_info=True)
            return {"valid": False, "details": "verification error"}
