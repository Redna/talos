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
    def test_below_threshold(self):
        d = RepetitionDetector(window=20, threshold=5)
        for _ in range(4):
            d.record("some_tool", {"arg": "val"})
        assert not d.is_stalled()

    def test_at_threshold(self):
        d = RepetitionDetector(window=20, threshold=5)
        for _ in range(5):
            d.record("some_tool", {"arg": "val"})
        assert d.is_stalled()

    def test_low_value_tool(self):
        d = RepetitionDetector(window=20, threshold=5)
        for _ in range(4):
            d.record("bash_command", {"command": "cat file"})
        assert d.is_stalled()

    def test_reset(self):
        d = RepetitionDetector(window=20, threshold=5)
        for _ in range(5):
            d.record("some_tool", {})
        assert d.is_stalled()
        d.reset()
        assert not d.is_stalled()

    def test_alternating_no_false_positive(self):
        d = RepetitionDetector(window=20, threshold=5)
        for i in range(10):
            d.record("tool_a" if i % 2 == 0 else "tool_b", {})
        assert not d.is_stalled()

    def test_stall_report(self):
        d = RepetitionDetector(window=20, threshold=5)
        for _ in range(5):
            d.record("reflect", {"topic": "progress"})
        report = d.get_stall_report()
        assert "reflect" in report


def test_max_tool_calls_per_turn():
    assert 1 <= MAX_TOOL_CALLS_PER_TURN <= 20


def test_build_hud(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "focus.md").write_text("# Focus")
    (memory_dir / "lessons.md").write_text("# Lessons")
    state = AgentState(memory_dir)
    hud = _build_hud(state)
    assert hud["memory_file_count"] == 2
    assert hud["urgency"] == "nominal"
