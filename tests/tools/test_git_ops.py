import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tool_registry import ToolRegistry
from spine_client import SpineClient


def test_git_commit_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    assert registry.has_tool("git_commit")


def test_git_checkout_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    assert registry.has_tool("git_checkout")


def test_git_push_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    assert registry.has_tool("git_push")


def test_git_commit_execution():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = registry.execute("git_commit", {"message": "initial commit"})
    assert "[COMMITTED]" in result or "commit" in result.lower()


def test_git_checkout_rejects_main():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    result = registry.execute("git_checkout", {"branch": "main"})
    assert "[BLOCKED]" in result or "protected" in result.lower()


def test_git_checkout_rejects_master():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    result = registry.execute("git_checkout", {"branch": "master"})
    assert "[BLOCKED]" in result or "protected" in result.lower()


def test_git_checkout_rejects_origin_main():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    result = registry.execute("git_checkout", {"branch": "origin/main"})
    assert "[BLOCKED]" in result or "protected" in result.lower()


def test_git_checkout_allows_feature_branch():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = registry.execute("git_checkout", {"branch": "feature/my-branch"})
    assert "[BLOCKED]" not in result
    assert "protected" not in result.lower()


def test_git_push_rejects_main():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    result = registry.execute("git_push", {"remote": "origin", "branch": "main"})
    assert "[BLOCKED]" in result or "protected" in result.lower()


def test_git_push_rejects_origin_master():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    result = registry.execute("git_push", {"remote": "origin", "branch": "master"})
    assert "[BLOCKED]" in result or "protected" in result.lower()


def test_git_push_allows_feature():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = registry.execute(
            "git_push", {"remote": "origin", "branch": "feature/x"}
        )
    assert "[BLOCKED]" not in result
