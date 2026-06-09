from spine.thought import ThoughtManager


def _make_assistant(*tool_names: str) -> list[dict]:
    return [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": f"tc_{i}",
                    "type": "function",
                    "function": {"name": name, "arguments": "{}"},
                }
            ],
        }
        for i, name in enumerate(tool_names)
    ]


def test_pick_rotates():
    w = ThoughtManager()
    seen = [w.pick() for _ in range(6)]
    assert len(set(seen)) == 6  # all 6 distinct
    assert w.pick() == seen[0]  # wraps around to first


def test_should_inject_empty_focus_after_reflect():
    w = ThoughtManager()
    messages = _make_assistant("reflect")
    assert w.should_inject("none", messages) is True
    assert w.should_inject("", messages) is True


def test_no_inject_when_focus_set():
    w = ThoughtManager()
    messages = _make_assistant("reflect")
    assert w.should_inject("fix login bug", messages) is False


def test_no_inject_when_no_assistant_messages():
    w = ThoughtManager()
    assert w.should_inject("none", []) is False


def test_no_inject_when_last_not_reflect():
    w = ThoughtManager()
    messages = _make_assistant("bash_command")
    assert w.should_inject("none", messages) is False


def test_no_inject_consecutive_reflects():
    w = ThoughtManager()
    messages = _make_assistant("reflect", "reflect")
    assert w.should_inject("none", messages) is False


def test_inject_allowed_when_action_between_reflects():
    w = ThoughtManager()
    messages = _make_assistant("write_file", "reflect")
    assert w.should_inject("none", messages) is True
