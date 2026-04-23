import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from seed_agent import (
    RepetitionDetector,
    _build_hud,
    LOW_VALUE_TOOLS,
    LOW_VALUE_THRESHOLD,
    MAX_TOOL_CALLS_PER_TURN,
)
from state import AgentState


class TestRepetitionDetector:
    def test_at_threshold(self):
        d = RepetitionDetector(window=20, threshold=5)
        for _ in range(5):
            d.record("some_tool", {"arg": "val"})
        assert d.is_stalled()

    def test_reset(self):
        d = RepetitionDetector(window=20, threshold=5)
        for _ in range(5):
            d.record("some_tool", {})
        assert d.is_stalled()
        d.reset()
        assert not d.is_stalled()


def test_build_hud(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "focus.md").write_text("# Focus")
    (memory_dir / "lessons.md").write_text("# Lessons")
    state = AgentState(memory_dir)
    hud = _build_hud(state)
    assert hud["memory_file_count"] == 2
    assert hud["urgency"] == "nominal"
