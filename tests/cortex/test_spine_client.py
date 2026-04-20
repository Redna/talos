import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "talos" / "cortex"))

from spine_client import SpineClient, SpineError


def test_basic_creation():
    client = SpineClient("/tmp/test.sock")
    assert client.socket_path == "/tmp/test.sock"


def test_spine_error_is_exception():
    assert issubclass(SpineError, Exception)
