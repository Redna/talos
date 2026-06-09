"""Serialize the Cortex capability set to a nono CLI policy file.

The nono CLI accepts a fully-resolved sandbox specification as JSON via
``--config <file>``.  This module is the bridge between the Python-side
:class:`nono_py.CapabilitySet` (built by :func:`spine.capabilities.build_cortex_caps`)
and the on-disk JSON consumed by the ``nono run`` subprocess.

Schema (per the nono docs at ``nono.sh/docs/cli/features/profiles-groups``
and the example policies in ``github.com/always-further/nono-packs`` —
e.g. the ``claude`` pack's ``policy.json``):

    {
      "meta": {
        "name": "<profile name>",
        "version": "<semver>",
        "description": "<free text>"
      },
      "extends": "default",                  # inherit from nono's default profile
      "groups": {                            # built-in permission groups
        "include": ["python_runtime", "git_config", "linux_sysfs_read"],
        "exclude": ["dangerous_commands"]
      },
      "filesystem": {                        # explicit per-host additions
        "read":   ["/path", ...],            # read-only directories
        "allow":  ["/path", ...],            # read+write directories
        "deny":   ["/path", ...]             # explicit deny list
      },
      "network": {                           # network policy
        "network_profile": "developer",      # built-in: developer | strict
        "allow_domain": ["api.github.com"],  # per-domain allowlist
        "credentials": ["github", "telegram"],   # built-in cred injection
        "custom_credentials": {                  # full custom cred config
          "github":   {"upstream": "api.github.com", "credential_key": "GITHUB_TOKEN",
                       "inject_header": "Authorization", "credential_format": "Bearer {token}"},
          "telegram": {"upstream": "api.telegram.org", "credential_key": "TELEGRAM_BOT_TOKEN",
                       "inject_header": "X-Bot-Token",   "credential_format": "{token}"}
        }
      },
      "process": {
        "signal_mode": "isolated",           # do not forward signals to the host
        "capability_elevation": false        # no interactive prompts
      },
      "rollback": {                          # built-in snapshot exclusions
        "exclude_patterns": ["*.pyc", "__pycache__/"],
        "exclude_globs":   [".git/objects/"]
      },
      "session_hooks": {                     # pre/post scripts
        "before": {"script": "/spine/hooks/before.sh", "timeout_secs": 5},
        "after":  {"script": "/spine/hooks/after.sh",  "timeout_secs": 5}
      }
    }

Notes / quirks observed while building this file
-------------------------------------------------
1. The ``meta.version`` field is required and must match
   ``^[0-9]+\\.[0-9]+\\.[0-9]+$``.  An integer (``1``) or short string
   (``"1.0"``) is rejected with a serde error.
2. ``groups.include`` and ``groups.exclude`` use the built-in group
   identifiers documented in the nono profile schema (e.g.
   ``python_runtime``, ``node_runtime``, ``git_config``,
   ``linux_sysfs_read``, ``dangerous_commands``).  Including
   ``python_runtime`` grants the right set of interpreter, library and
   ``/proc`` paths for Python workloads without having to enumerate
   them by hand.
3. ``filesystem`` is additive on top of the inherited groups.  We use
   it to grant write access to the Talos-specific working directories
   (``/app``, ``/memory``, ``/spine``, ``/home/talos``) and explicit
   read access to the model directory.
4. ``network.credentials`` references built-in providers; nono knows
   how to inject ``github`` and ``telegram`` tokens out of the box.
   The ``custom_credentials`` block is documented for the case where
   the built-in provider is not sufficient.  This is a candidate to
   retire our custom ``spine.proxy`` module if the 0.61.x CLI honours
   both blocks in production.
5. ``process.signal_mode: "isolated"`` is best practice for a
   long-running agent: the Cortex cannot kill or signal the Spine
   through nono, and a hung Cortex can still be SIGKILL'd by its real
   PID (the nono Popen — see :mod:`spine.sandbox`).
6. ``capability_elevation: false`` prevents nono from prompting the
   user for elevation; Talos runs non-interactive in the container.

Path entries in ``filesystem.*`` are ``ConditionalPath`` — either a
bare string or an object ``{"path": "/...", "when": "linux"}``.  We
use the bare-string form for simplicity.

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

# Built-in nono permission groups the Cortex needs.  These are the
# identifiers documented in nono.sh/docs/cli/features/profiles-groups;
# we use them to avoid enumerating every Python / git / procfs path
# by hand.
INCLUDED_GROUPS: tuple[str, ...] = (
    "python_runtime",
    "git_config",
    "linux_sysfs_read",
)

# Domains the Cortex is allowed to reach.  The credential proxy (or
# nono's built-in network.credentials block) handles the rest.
ALLOWED_DOMAINS: tuple[str, ...] = (
    "api.github.com",
    "github.com",
    "api.telegram.org",
    "objects.githubusercontent.com",
    "raw.githubusercontent.com",
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
        # ``version`` must be at the top level for the nono 0.61.x CLI to
        # parse the manifest (``missing field `version` at line ...``).
        # The ``meta`` block is the documentation-friendly copy used by
        # ``nono profile show`` and the JSON-schema-aware editors.
        "meta": {
            "name": "talos_cortex",
            "version": POLICY_VERSION,
            "description": (
                "Talos Cortex sandbox — kernel-enforced Landlock boundary "
                "around the autonomous agent."
            ),
        },
        "version": POLICY_VERSION,
        # Inherit from nono's default profile so we pick up sensible
        # baseline groups (python_runtime, node_runtime, ...).
        "extends": "default",
        "groups": {
            "include": list(INCLUDED_GROUPS),
            "exclude": ["dangerous_commands"],
        },
        "filesystem": {
            # Sorted for deterministic output (idempotency).
            "read": sorted(read),
            "allow": sorted(allow),
            "deny": [],
        },
        "network": {
            # Built-in profile handles outbound by default; the
            # allow_domain list narrows it to the hosts the Cortex
            # legitimately needs.
            "network_profile": "developer",
            "allow_domain": sorted(ALLOWED_DOMAINS),
            # Built-in credential injection.  When the 0.61.x CLI
            # honours this block end-to-end we can retire
            # ``spine.proxy`` entirely.  The custom_credentials block
            # documents the full injection config in case we need it.
            "credentials": ["github", "telegram"],
            "custom_credentials": {
                "github": {
                    "upstream": "api.github.com",
                    "credential_key": "GITHUB_TOKEN",
                    "inject_header": "Authorization",
                    "credential_format": "Bearer {token}",
                },
                "telegram": {
                    "upstream": "api.telegram.org",
                    "credential_key": "TELEGRAM_BOT_TOKEN",
                    "inject_header": "X-Bot-Token",
                    "credential_format": "{token}",
                },
            },
        },
        "process": {
            # Do not forward host signals through nono into the Cortex;
            # the Supervisor uses the nono Popen's real PID for
            # SIGTERM/SIGKILL.  No interactive prompts.
            "signal_mode": "isolated",
            "capability_elevation": False,
        },
        "rollback": {
            "exclude_patterns": ["*.pyc", "__pycache__/", "*.log"],
            "exclude_globs": [".git/objects/"],
        },
        "session_hooks": {
            "before": {"script": "/spine/hooks/before.sh", "timeout_secs": 5},
            "after":  {"script": "/spine/hooks/after.sh",  "timeout_secs": 5},
        },
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
        "[nono_policy] Wrote nono policy v%s to %s "
        "(groups=%d, read=%d, allow=%d, domains=%d)",
        POLICY_VERSION,
        path,
        len(policy["groups"]["include"]),
        len(policy["filesystem"]["read"]),
        len(policy["filesystem"]["allow"]),
        len(policy["network"]["allow_domain"]),
    )
