#!/usr/bin/env python3
"""Startup memory integrity audit — cleans ghost artifacts before Cortex starts."""
import os
import shutil
from pathlib import Path


def audit(memory_dir: str = "/memory", app_dir: str = "/app") -> list[str]:
    """Clean ghost artifacts. Returns list of actions taken."""
    mem = Path(memory_dir)
    app = Path(app_dir)
    cleaned: list[str] = []

    # 1. Purge __pycache__ from cortex directory
    cortex_dir = app / "cortex"
    if cortex_dir.exists():
        for pycache in cortex_dir.rglob("__pycache__"):
            try:
                shutil.rmtree(pycache)
                cleaned.append(f"removed __pycache__: {pycache}")
            except Exception as e:
                cleaned.append(f"failed to remove {pycache}: {e}")

    # 2. Delete .orig backup files
    for orig in app.rglob("*.orig"):
        try:
            orig.unlink()
            cleaned.append(f"removed .orig: {orig}")
        except Exception as e:
            cleaned.append(f"failed to remove {orig}: {e}")

    # 3. Delete zero-byte files
    for f in mem.rglob("*"):
        if f.is_file() and f.stat().st_size == 0:
            try:
                f.unlink()
                cleaned.append(f"removed zero-byte: {f}")
            except Exception as e:
                cleaned.append(f"failed to remove {f}: {e}")

    # 4. Flag bad filenames (can't delete — LLM needs to handle)
    for f in list(mem.rglob("*")) + list(app.rglob("*")):
        try:
            name = f.name
            if ":" in name:
                cleaned.append(f"WARNING: colon in filename: {f}")
        except Exception:
            cleaned.append(f"WARNING: broken filename encoding at {f}")

    return cleaned


if __name__ == "__main__":
    results = audit()
    for line in results:
        print(f"[AUDIT] {line}")
    print(f"[AUDIT] Complete: {len(results)} actions taken")
