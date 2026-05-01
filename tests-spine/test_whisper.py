from spine.whisper import WhisperManager


def _make_messages(*tool_contents: str) -> list[dict]:
    return [
        {"role": "tool", "tool_call_id": f"tc_{i}", "content": c}
        for i, c in enumerate(tool_contents)
    ]


def test_pick_rotates():
    w = WhisperManager()
    seen = [w.pick() for _ in range(6)]
    assert len(set(seen)) == 6  # all 6 distinct
    assert w.pick() == seen[0]  # wraps around to first


def test_should_whisper_empty_focus_after_reflect():
    w = WhisperManager()
    messages = _make_messages("[REFLECT] idle")
    assert w.should_whisper("none", messages) is True
    assert w.should_whisper("", messages) is True
    assert w.should_whisper(None, messages) is True


def test_no_whisper_when_focus_set():
    w = WhisperManager()
    messages = _make_messages("[REFLECT] idle")
    assert w.should_whisper("fix login bug", messages) is False


def test_no_whisper_when_no_tool_messages():
    w = WhisperManager()
    assert w.should_whisper("none", []) is False


def test_no_whisper_when_last_tool_not_reflect():
    w = WhisperManager()
    messages = _make_messages("file contents here")
    assert w.should_whisper("none", messages) is False


def test_no_whisper_consecutive_reflects():
    w = WhisperManager()
    messages = _make_messages("[REFLECT] still idle", "[REFLECT] idle again")
    assert w.should_whisper("none", messages) is False


def test_whisper_allowed_when_action_between_reflects():
    w = WhisperManager()
    messages = _make_messages(
        "[REFLECT] first pause",
        "file contents here",
        "[REFLECT] second pause",
    )
    assert w.should_whisper("none", messages) is True
