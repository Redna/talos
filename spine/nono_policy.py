"""Serialize the Cortex capability set to a nono CLI policy file.

The nono CLI accepts a fully-resolved sandbox specification as JSON via
``--config <file>``.  This module is the bridge between the Python-side
:class:`nono_py.CapabilitySet` (built by :func:`spine.capabilities.build_cortex_caps`)
and the on-disk JSON consumed by the ``nono run`` subprocess.

Schema (reverse-engineered from the nono 0.61.x source — ``nono run --help``
advertises ``-c, --config <FILE>  Capability manifest file (JSON). A
fully-resolved sandbox specification``; the schema is embedded in the
binary at ``capability_manifest_types.rs`` and can be dumped with
``nono profile schema``):

    {
      "version": "<MAJOR>.<MINOR>.<PATCH>",   # semver string, required
      "filesystem": {                          # required
        "read":        ["/path", ...],         # read-only directories
        "allow":       ["/path", ...],         # read+write directories
        "write":       ["/path", ...],         # write-only directories
        "allow_file":  ["/path", ...],         # read+write single files
        "read_file":   ["/path", ...],         # read-only single files
        "write_file":  ["/path", ...],         # write-only single files
        "deny":        ["/path", ...],         # explicit deny list
      },
      "network": {                             # optional
        "block": <bool>                        # in the current 0.61 CLI the
                                               # network section is not parsed
                                               # from JSON — outbound is
                                               # always allowed at the kernel
                                               # layer.  Application-level
                                               # egress is enforced by the
                                               # nono credential proxy.
      },
      "process": {                             # optional
        "exec_strategy": "<string>",
        "process_info_mode": "<string>",
        "signal_mode": "<string>"
      }
    }

Path entries are ``ConditionalPath`` — either a bare string or an
object ``{"path": "/...", "when": "linux"}``.  We use the bare-string
form for simplicity.

Notes / quirks observed while building this file
-------------------------------------------------
1. The ``version`` field is required and must match
   ``^[0-9]+\\.[0-9]+\\.[0-9]+$``.  An integer (``1``) or short string
   (``"1.0"``) is rejected with a serde error.
2. The ``fs`` / ``allow_read`` / ``allow_read_write`` aliases some
   Google searches report do **not** exist on the 0.61.x CLI — the
   correct keys are ``read`` (read-only) and ``allow`` (read+write).
   ``SandboxState`` (returned by the Python ``SandboxState.to_json()``)
   uses a different ``fs`` array; that schema is the *runtime*
   representation, not the manifest.
3. The dev host I tested on is unable to grant ``/`` read recursively
   through the JSON config (the directory the executable lives in is
   only covered by the implicit ``system_read_linux_core`` group, which
   the manifest schema does not surface).  In the runtime container
   the situation is different: the Cortex's python lives at
   ``/venv/bin/python`` and ``/venv`` is granted read+write, so the
   manifest is sufficient.
4. Network blocking is *not* represented in the policy — the runtime
   layer uses the nono credential proxy (``spine.proxy``) to enforce
   egress.  Setting ``"network": {"block": true}`` in the policy has
   no observable effect with the current nono build; we keep the field
   as a hint for future versions.

The :func:`write_nono_policy` function is idempotent: calling it twice
with the same config produces byte-identical output, so the Supervisor
can safely regenerate the policy on every restart without causing
spurious diffs.
"""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from spine.config import SpineConfig

logger = logging.getLogger("spine.nono_policy")

# The nono manifest version this writer targets.  Bump only when the
# nono schema changes in an incompatible way.
POLICY_VERSION = "1.0.0"

# Mirror of the writable-path list in ``build_cortex_caps``.  Kept as a
# module constant so the policy writer and the Python-side
# ``CapabilitySet`` builder share the same source of truth (and stay in
# sync if paths change).
WRITABLE_PATHS: tuple[str, ...] = (
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
)

# The root of the filesystem is granted read-only access.  /etc, /var
# and /usr follow implicitly because Landlock's hierarchy rule grants
# access to children of an allow-listed parent.
READ_PATHS: tuple[str, ...] = (
    "/",
)


def build_policy_dict(cfg: SpineConfig) -> dict[str, Any]:
    """Build the in-memory policy dict for *cfg* without touching disk.

    The returned dict matches the schema described in the module
    docstring.  Paths that do not exist on the current host are silently
    omitted so the policy writer is usable on a dev host as well as in
    the runtime container.
    """
    read = [p for p in READ_PATHS if os.path.exists(p)]
    allow = [p for p in WRITABLE_PATHS if os.path.exists(p)]

    return {
        "version": POLICY_VERSION,
        "filesystem": {
            # Sorted for deterministic output (idempotency).
            "read": sorted(read),
            "allow": sorted(allow),
        },
        # The CLI does not currently parse the network section, but
        # we keep the field for forward compatibility.  See module
        # docstring "Notes / quirks" item 4.
        "network": {"block": False},
    }


def write_nono_policy(cfg: SpineConfig, path: str) -> None:
    """Write the Cortex nono policy JSON to *path*.

    The file is written atomically (write-to-temp + rename) so a partial
    write cannot leave nono reading a half-formed manifest.  Existing
    files with identical contents are left untouched, which makes the
    function idempotent and friendly to ``git``-style snapshot tools.

    Parameters
    ----------
    cfg:
        The :class:`spine.config.SpineConfig`.  Currently only used as
        a placeholder for per-config customisation; the actual
        writable-path list is module-level (mirrored from
        :func:`spine.capabilities.build_cortex_caps`).
    path:
        Destination file.  The parent directory is created if it does
        not exist.  The writer does *not* require nono to be installed.
    """
    policy = build_policy_dict(cfg)

    target_dir = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(target_dir, exist_ok=True)

    # Idempotency: skip the write if the existing file already matches
    # the desired contents.  Avoids spurious mtime changes on every
    # restart (helpful for ``inotify``-based snapshot tools).
    serialised = json.dumps(policy, indent=2, sort_keys=False) + "\n"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                if f.read() == serialised:
                    logger.debug(
                        "[nono_policy] Policy at %s is up to date — skipping write",
                        path,
                    )
                    return
        except OSError:
            # If we cannot read the existing file, fall through and
            # overwrite it.
            pass

    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(serialised)
    os.replace(tmp_path, path)
    logger.info(
        "[nono_policy] Wrote nono policy v%s to %s (read=%d, allow=%d)",
        POLICY_VERSION,
        path,
        len(policy["filesystem"]["read"]),
        len(policy["filesystem"]["allow"]),
    )
