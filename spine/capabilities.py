from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nono_py import CapabilitySet

logger = logging.getLogger("spine.capabilities")


def build_cortex_caps(cfg) -> CapabilitySet:
    """Build a nono CapabilitySet for the Cortex sandbox.

    Policy (permissive — the Cortex can install packages and run bash):
      - Read access: "/" (recursive) — system files, models, data sources.
      - Write access: working directories the Cortex mutates directly.
      - Network: blocked by default (a proxy module handles allowed hosts).

    Missing paths are silently skipped so this function works both
    inside the container and on a dev host (tests, CI).
    """
    try:
        from nono_py import CapabilitySet, AccessMode
    except ImportError:
        logger.warning(
            "[capabilities] nono_py not installed — returning empty CapabilitySet"
        )
        return CapabilitySet()

    caps = CapabilitySet()

    # Broad read access — the Cortex reads system files, models, etc.
    try:
        caps.allow_path("/", AccessMode.READ)
    except Exception:
        logger.warning("[capabilities] Could not allow read on /", exc_info=True)

    # Write-accessible working directories.
    WRITABLE = [
        "/app",
        "/memory",
        "/spine",
        "/models",
        "/home/talos",
        "/tmp",
        "/var/tmp",
        "/venv",
        "/usr/local",
        "/opt",
        "/run",
    ]
    for path in WRITABLE:
        if not os.path.exists(path):
            logger.debug("[capabilities] Skipping missing path: %s", path)
            continue
        try:
            caps.allow_path(path, AccessMode.READ_WRITE)
        except Exception:
            logger.warning("[capabilities] Could not allow write on %s", path, exc_info=True)

    # Network blocked by default (proxy handles allowed hosts).
    caps.block_network()

    return caps
