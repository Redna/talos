import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tool_registry import ToolRegistry
from spine_client import SpineClient


def test_bash_command_echo():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute("bash_command", {"command": "echo hello"})
    assert "hello" in result


def test_bash_command_nonzero_exit():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute("bash_command", {"command": "exit 42"})
    assert "[EXIT 42]" in result


def test_bash_command_rejects_blocked_flag_no_verify():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute(
        "bash_command", {"command": "git push --no-verify origin main"}
    )
    assert "[BLOCKED]" in result


def test_bash_command_rejects_blocked_flag_no_gpg():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute(
        "bash_command", {"command": "git commit --no-gpg-sign -m test"}
    )
    assert "[BLOCKED]" in result


def test_send_message_execution():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute("send_message", {"text": "hello world"})
    client.send_message.assert_called_once_with("telegram", "hello world")


def test_request_restart_dirty_repo():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(stdout="M file.py\n", returncode=0),          # git status
            MagicMock(stdout="Saved working directory", returncode=0),  # git stash
            MagicMock(stdout="", returncode=0),                     # git ls-files (no untracked)
        ]
        result = registry.execute("request_restart", {"reason": "stuck loop"})
    assert "[RESTART REQUESTED]" in result
    client.request_restart.assert_called_once_with("stuck loop")
