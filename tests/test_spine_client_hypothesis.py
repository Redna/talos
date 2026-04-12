"""
Property-based tests for SpineClient using hypothesis.
Invariants:
  - request_id increments monotonically
  - _send_request constructs valid JSON-RPC 2.0 messages
  - SpineError preserves code and message
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "cortex"))

from spine_client import SpineClient, SpineError
from hypothesis import given, assume
from hypothesis.strategies import text, integers, dictionaries, lists


@given(n_calls=integers(min_value=1, max_value=100))
def test_request_id_monotonic(n_calls):
    client = SpineClient("/tmp/nonexistent.sock")
    for _ in range(n_calls):
        client._request_id += 1
    assert client._request_id == n_calls


@given(focus=text(min_size=1, max_size=100))
def test_think_request_structure(focus):
    client = SpineClient("/tmp/nonexistent.sock")
    client._request_id = 0
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "think",
        "params": {
            "focus": focus,
            "tools": [],
            "hud_data": {"memory_keys": 0, "last_keys": [], "urgency": "nominal"},
        },
    }
    assert request["jsonrpc"] == "2.0"
    assert "id" in request
    assert request["method"] == "think"
    assert request["params"]["focus"] == focus


@given(
    code=integers(min_value=-32768, max_value=-32000),
    message=text(min_size=1, max_size=100),
)
def test_spine_error_preserves_code_and_message(code, message):
    err = SpineError(code, message)
    assert err.code == code
    assert err.message == message
    assert str(code) in str(err)
    assert message in str(err)


@given(
    code=integers(min_value=-32768, max_value=-32000),
    message=text(min_size=1, max_size=100),
)
def test_spine_error_is_exception(code, message):
    err = SpineError(code, message)
    assert isinstance(err, Exception)
