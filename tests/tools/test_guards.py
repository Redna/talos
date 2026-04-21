import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tools.guards import (
    is_spine_write,
    is_spine_path,
    BLOCKED_FLAGS,
    PROTECTED_BRANCHES,
)


@pytest.mark.parametrize(
    "command",
    [
        "echo data > /app/spine/config.json",
        "echo data >> /app/spine/log.txt",
        "echo data | tee /app/spine/output.txt",
        "cp file.txt /app/spine/file.txt",
        "mv file.txt /app/spine/file.txt",
        "python3 -c \"open('/app/spine/config.py','w').write('hacked')\"",
        "sed -i 's/old/new/' /app/spine/config.py",
        "dd of=/app/spine/config.json",
        "install -m 644 file.conf /app/spine/file.conf",
    ],
)
def test_spine_write_detects_writes(command):
    assert is_spine_write(command)


@pytest.mark.parametrize(
    "command",
    [
        "cat /app/spine/config.json",
        "grep pattern /app/spine/stream.py",
        "echo data > /tmp/output.txt",
    ],
)
def test_spine_write_allows_reads(command):
    assert not is_spine_write(command)


def test_blocked_flags_and_protected_branches():
    assert "--no-verify" in BLOCKED_FLAGS
    assert "main" in PROTECTED_BRANCHES
    assert "master" in PROTECTED_BRANCHES
