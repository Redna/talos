import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tool_registry import ToolRegistry
from spine_client import SpineClient


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


def test_git_push_rejects_main():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.git_ops import register_git_ops_tools

    register_git_ops_tools(registry, client)
    result = registry.execute("git_push", {"remote": "origin", "branch": "main"})
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
