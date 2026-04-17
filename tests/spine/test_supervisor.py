import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from spine.supervisor import Supervisor
from spine.config import SpineConfig

@pytest.fixture
def mock_deps():
    return {
        "cfg": MagicMock(spec=SpineConfig),
        "events": MagicMock(),
        "stream": MagicMock(),
        "health": MagicMock(),
        "snapshot": MagicMock(),
        "tasks": MagicMock(),
    }

def test_request_restart_triggers_restart(mock_deps):
    supervisor = Supervisor(**mock_deps)
    
    # Use a synchronous wrapper or just call the async method via asyncio.run
    with patch.object(supervisor, '_restart_cortex', new_callable=AsyncMock) as mock_restart:
        asyncio.run(supervisor.request_restart("Test Reason"))
        mock_restart.assert_called_once()
        mock_deps["events"].emit.assert_called_with("spine.restart_requested", {"reason": "Test Reason"})

def test_shutdown_stops_process(mock_deps):
    supervisor = Supervisor(**mock_deps)
    mock_process = MagicMock()
    supervisor._cortex_process = mock_process
    
    asyncio.run(supervisor.shutdown())
    assert supervisor._is_shutting_down is True
    mock_process.terminate.assert_called_once()

def test_start_cortex_launches_process(mock_deps):
    supervisor = Supervisor(**mock_deps)
    mock_deps["cfg"].spine_dir = "/app/spine"
    
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock(pid=1234)
        asyncio.run(supervisor.start_cortex())
        assert supervisor._cortex_process is not None
        assert supervisor._cortex_process.pid == 1234
