import json
import os
from dataclasses import dataclass, fields


@dataclass
class SpineConfig:
    gate_url: str = "http://localhost:4000/v1/chat/completions"
    socket_path: str = "/tmp/spine.sock"
    spine_dir: str = "/spine"
    app_dir: str = "/app"
    memory_dir: str = "/memory"
    constitution_path: str = "/app/CONSTITUTION.md"
    identity_path: str = "/app/identity.md"
    context_threshold_pct: float = 0.85
    fold_advisory_pct: float = 0.60
    fold_forced_pct: float = 0.75
    fold_emergency_pct: float = 0.85
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    stall_timeout: float = 300.0
    nono_enabled: bool = True


def load_config(path: str) -> SpineConfig:
    cfg = SpineConfig()
    # Environment overrides for secrets/sensitive config
    cfg.telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    cfg.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", cfg.telegram_chat_id)
    if "NONO_ENABLED" in os.environ:
        cfg.nono_enabled = os.environ["NONO_ENABLED"].strip().lower() in ("1", "true", "yes")
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    valid_fields = {f.name for f in fields(SpineConfig)}
    for k, v in data.items():
        if k in valid_fields:
            setattr(cfg, k, v)
    # Environment overrides applied *after* the JSON load so the
    # dry-run compose can swap the gate URL (production uses
    # http://gate:4000, dry-run uses http://gate-dryrun:4000) and
    # the stall_timeout (300s in production, 15s in dry-run so a
    # single stall-detection cycle completes in seconds) without
    # needing a separate spine_config.json.
    if "GATE_URL" in os.environ:
        cfg.gate_url = os.environ["GATE_URL"]
    if "STALL_TIMEOUT" in os.environ:
        try:
            cfg.stall_timeout = float(os.environ["STALL_TIMEOUT"])
        except ValueError:
            pass
    return cfg
