import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tools.guards import (
    BLOCKED_FLAGS,
    PROTECTED_BRANCHES,
)


def test_blocked_flags_and_protected_branches():
    assert "--no-verify" in BLOCKED_FLAGS
    assert "main" in PROTECTED_BRANCHES
    assert "master" in PROTECTED_BRANCHES
