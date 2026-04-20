import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tool_registry import ToolRegistry
from spine_client import SpineClient


def test_read_file_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    assert registry.has_tool("read_file")


def test_write_file_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    assert registry.has_tool("write_file")


def test_patch_file_registers():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    assert registry.has_tool("patch_file")


def test_write_file_creates(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    fpath = str(tmp_path / "test.txt")
    result = registry.execute("write_file", {"path": fpath, "content": "hello"})
    assert "WRITTEN" in result
    assert Path(fpath).read_text() == "hello"


def test_write_file_creates_dirs(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    fpath = str(tmp_path / "sub" / "dir" / "test.txt")
    result = registry.execute("write_file", {"path": fpath, "content": "nested"})
    assert "WRITTEN" in result
    assert Path(fpath).read_text() == "nested"


def test_write_file_rejects_spine_path():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    result = registry.execute(
        "write_file", {"path": "/app/spine/config.json", "content": "bad"}
    )
    assert "BLOCKED" in result or "spine" in result.lower()


def test_read_file_happy(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    fpath = str(tmp_path / "test.txt")
    Path(fpath).write_text("line1\nline2\nline3\n")
    result = registry.execute("read_file", {"path": fpath})
    assert "line1" in result
    assert "line3" in result


def test_read_file_line_range(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    fpath = str(tmp_path / "test.txt")
    Path(fpath).write_text("line1\nline2\nline3\nline4\n")
    result = registry.execute(
        "read_file", {"path": fpath, "start_line": 2, "end_line": 3}
    )
    assert "line2" in result
    assert "line3" in result
    assert "line1" not in result
    assert "line4" not in result


def test_read_file_not_found():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    result = registry.execute("read_file", {"path": "/nonexistent/file.txt"})
    assert "[ERROR]" in result


def test_patch_file_rejects_spine_path():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    result = registry.execute(
        "patch_file", {"path": "/app/spine/main.py", "patch": "whatever"}
    )
    assert "BLOCKED" in result or "spine" in result.lower()
