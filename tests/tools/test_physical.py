import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tool_registry import ToolRegistry
from spine_client import SpineClient


def test_bash_command_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    assert registry.has_tool("bash_command")


def test_send_message_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    assert registry.has_tool("send_message")


def test_request_restart_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    assert registry.has_tool("request_restart")


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


def test_bash_command_empty_output():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute("bash_command", {"command": "true"})
    assert "[OK]" in result


def test_bash_command_rejects_no_verify():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute(
        "bash_command", {"command": "git commit --no-verify -m test"}
    )
    assert "[BLOCKED]" in result


def test_bash_command_rejects_no_gpg_sign():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute(
        "bash_command", {"command": "git commit --no-gpg-sign -m test"}
    )
    assert "[BLOCKED]" in result


def test_bash_command_rejects_spine_write_redirect():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute(
        "bash_command", {"command": "echo data > /app/spine/config.json"}
    )
    assert "[BLOCKED]" in result


def test_bash_command_rejects_spine_write_append():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute(
        "bash_command", {"command": "echo data >> /app/spine/log.txt"}
    )
    assert "[BLOCKED]" in result


def test_bash_command_rejects_spine_tee():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute(
        "bash_command", {"command": "echo data | tee /app/spine/output.txt"}
    )
    assert "[BLOCKED]" in result


def test_bash_command_rejects_spine_cp():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute(
        "bash_command", {"command": "cp file.txt /app/spine/file.txt"}
    )
    assert "[BLOCKED]" in result


def test_bash_command_rejects_spine_mv():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute(
        "bash_command", {"command": "mv file.txt /app/spine/file.txt"}
    )
    assert "[BLOCKED]" in result


def test_bash_command_allows_reading_spine():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute("bash_command", {"command": "cat /app/spine/config.json"})
    assert "[BLOCKED]" not in result


def test_bash_command_rejects_spine_python_write():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute(
        "bash_command",
        {"command": "python3 -c \"open('/app/spine/config.py','w').write('hacked')\""},
    )
    assert "[BLOCKED]" in result


def test_bash_command_rejects_spine_sed_i():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute(
        "bash_command",
        {"command": "sed -i 's/old/new/' /app/spine/config.py"},
    )
    assert "[BLOCKED]" in result


def test_send_message_execution():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    result = registry.execute("send_message", {"text": "hello world"})
    client.send_message.assert_called_once_with("telegram", "hello world")


def test_request_restart_clean_repo():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        result = registry.execute("request_restart", {"reason": "stuck loop"})
    client.request_restart.assert_called_once()


def test_request_restart_dirty_repo():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.physical import register_physical_tools

    register_physical_tools(registry, client)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="M file.py\n", returncode=0)
        result = registry.execute("request_restart", {"reason": "stuck loop"})
    assert (
        "[BLOCKED]" in result
        or "dirty" in result.lower()
        or "uncommitted" in result.lower()
    )
    client.request_restart.assert_not_called()
