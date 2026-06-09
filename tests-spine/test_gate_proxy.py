import json
import pytest
from unittest.mock import patch, MagicMock
from spine.gate_proxy import GateProxy


@pytest.fixture
def proxy():
    return GateProxy(gate_url="http://localhost:4000/v1/chat/completions")


def test_proxy_creation(proxy):
    assert proxy.gate_url == "http://localhost:4000/v1/chat/completions"


def test_call_returns_tool_calls(proxy):
    fake_response = {
        "id": "chatcmpl-1",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "bash_command",
                                "arguments": '{"command": "ls"}',
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
            "context_pct": 0.35,
        },
    }
    with patch("spine.gate_proxy.httpx.Client") as MockClient:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = fake_response
        mock_client = MockClient.return_value.__enter__.return_value
        mock_client.post.return_value = mock_resp
        result = proxy.call(messages=[{"role": "user", "content": "hello"}], tools=[])
    assert result["tool_calls"][0]["name"] == "bash_command"
    assert result["context_pct"] == 0.35
    assert result["tokens_used"] == 120


def test_call_no_tool_calls(proxy):
    fake_response = {
        "id": "chatcmpl-2",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "I'm thinking about it.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 10,
            "total_tokens": 60,
            "context_pct": 0.2,
        },
    }
    with patch("spine.gate_proxy.httpx.Client") as MockClient:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = fake_response
        mock_client = MockClient.return_value.__enter__.return_value
        mock_client.post.return_value = mock_resp
        result = proxy.call(messages=[{"role": "user", "content": "hello"}], tools=[])
    assert result["tool_calls"] == []
    assert result["assistant_message"] == "I'm thinking about it."


def test_call_connection_error(proxy):
    with patch("spine.gate_proxy.httpx.Client") as MockClient:
        mock_client = MockClient.return_value.__enter__.return_value
        mock_client.post.side_effect = Exception("connection refused")
        with pytest.raises(Exception):
            proxy.call(messages=[], tools=[])


def test_call_parses_tool_arguments(proxy):
    fake_response = {
        "id": "chatcmpl-3",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_a",
                            "type": "function",
                            "function": {
                                "name": "write_file",
                                "arguments": '{"path": "/tmp/x.py", "content": "pass"}',
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "context_pct": 0.1,
        },
    }
    with patch("spine.gate_proxy.httpx.Client") as MockClient:
        mock_resp = MagicMock()
        mock_resp.json.return_value = fake_response
        mock_client = MockClient.return_value.__enter__.return_value
        mock_client.post.return_value = mock_resp
        result = proxy.call(messages=[], tools=[])
    assert result["tool_calls"][0]["arguments"]["path"] == "/tmp/x.py"


def test_model_passed_in_body(proxy):
    proxy_with_model = GateProxy(
        gate_url="http://test/v1/chat/completions", model="gemma4:31b-cloud"
    )
    fake_response = {
        "id": "x",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "hi"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 1,
            "completion_tokens": 1,
            "total_tokens": 2,
            "context_pct": 0.0,
        },
    }
    with patch("spine.gate_proxy.httpx.Client") as MockClient:
        mock_resp = MagicMock()
        mock_resp.json.return_value = fake_response
        mock_client = MockClient.return_value.__enter__.return_value
        mock_client.post.return_value = mock_resp
        proxy_with_model.call(messages=[], tools=[])
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["model"] == "gemma4:31b-cloud"
