from __future__ import annotations

import logging

logger = logging.getLogger("spine.snapshots")


def init_snapshots(session_dir: str = "/spine/snapshots"):
    """Create and return a nono SnapshotManager for the Cortex working tree.

    Returns the SnapshotManager on success, or None if nono is unavailable
    or the kernel does not support Landlock snapshots.
    """
    try:
        from nono_py import SnapshotManager, ExclusionConfig
    except ImportError:
        logger.info("[snapshots] nono_py not installed — snapshots disabled")
        return None

    try:
        mgr = SnapshotManager(
            session_dir=session_dir,
            tracked_paths=["/app", "/memory", "/spine"],
            exclusion=ExclusionConfig(
                exclude_patterns=["__pycache__", "*.pyc", "node_modules", ".git"],
            ),
        )
        # Create baseline as a best-effort — if it fails (e.g. on a
        # non-Landlock kernel), that is OK; the caller handles None.
        mgr.create_baseline()
        logger.info(
            "[snapshots] Baseline snapshot created at %s", session_dir
        )
        return mgr
    except Exception:
        logger.warning(
            "[snapshots] Failed to initialise SnapshotManager — snapshots disabled",
            exc_info=True,
        )
        return None
