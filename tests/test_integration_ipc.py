import pytest
import asyncio
from unittest.mock import MagicMock
from spine.ipc_types import ThinkRequest, HUDData, ToolDef

def test_ipc_request_parsing():
    hud = HUDData(memory_keys=10, last_keys=["a", "b"], urgency="nominal")
    req = ThinkRequest(focus="test", tools=[], hud_data=hud)
    assert req.focus == "test"
    assert req.hud_data.memory_keys == 10

def test_mock_spine_interaction():
    mock_spine = MagicMock()
    future = asyncio.Future()
    future.set_result("Thinking...")
    mock_spine.think = MagicMock(return_value=future)
    
    result = asyncio.run(mock_spine.think())
    assert result == "Thinking..."
