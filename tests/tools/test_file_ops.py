import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tool_registry import ToolRegistry
from spine_client import SpineClient


def test_write_file_creates(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    fpath = str(tmp_path / "test.txt")
    result = registry.execute("write_file", {"path": fpath, "content": "hello"})
    assert "WRITTEN" in result
    assert Path(fpath).read_text() == "hello"


def test_write_file_rejects_protected_cortex_file():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    result = registry.execute(
        "write_file", {"path": "/app/cortex/spine_client.py", "content": "bad"}
    )
    assert "BLOCKED" in result


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


def test_read_file_not_found():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    result = registry.execute("read_file", {"path": "/nonexistent/file.txt"})
    assert "[ERROR]" in result


def test_search_and_replace_basic(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    fpath = str(tmp_path / "replace_test.txt")
    Path(fpath).write_text("hello world\n")
    result = registry.execute(
        "search_and_replace",
        {"path": fpath, "old_string": "hello", "new_string": "goodbye"},
    )
    assert "REPLACED" in result
    assert Path(fpath).read_text() == "goodbye world\n"


def test_search_and_replace_multi_without_replace_all(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    fpath = str(tmp_path / "multi.txt")
    Path(fpath).write_text("foo bar foo\nbaz foo\n")
    result = registry.execute(
        "search_and_replace",
        {"path": fpath, "old_string": "foo", "new_string": "qux"},
    )
    assert "[ERROR]" in result
    assert "occurrences" in result.lower()


def test_search_and_replace_with_replace_all(tmp_path):
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    fpath = str(tmp_path / "multi_replace.txt")
    Path(fpath).write_text("foo bar foo\nbaz foo\n")
    result = registry.execute(
        "search_and_replace",
        {
            "path": fpath,
            "old_string": "foo",
            "new_string": "qux",
            "replace_all": True,
        },
    )
    assert "REPLACED" in result
    assert Path(fpath).read_text() == "qux bar qux\nbaz qux\n"


def test_search_and_replace_rejects_protected_cortex_file():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    result = registry.execute(
        "search_and_replace",
        {
            "path": "/app/cortex/spine_client.py",
            "old_string": "class SpineClient",
            "new_string": "class HackedClient",
        },
    )
    assert "BLOCKED" in result


def test_bulk_rename_rejects_protected_cortex_file():
    registry = ToolRegistry()
    client = MagicMock(spec=SpineClient)
    from tools.file_ops import register_file_ops_tools

    register_file_ops_tools(registry, client)
    result = registry.execute(
        "bulk_rename",
        {"mapping": {"/app/cortex/spine_client.py": "/tmp/evil.py"}},
    )
    assert "BLOCKED" in result
