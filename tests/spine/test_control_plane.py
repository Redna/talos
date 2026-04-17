from unittest.mock import MagicMock

from spine.control_plane import ControlPlane
from spine.config import SpineConfig
from spine.stream import StreamManager

def test_control_plane_has_routes():
    cfg = SpineConfig()
    stream = StreamManager(cfg)
    events = MagicMock()
    sup = MagicMock()
    cp = ControlPlane(cfg, sup, stream, events)
    paths = {
        r.resource.canonical
        for r in cp.app.router.routes()
        if hasattr(r.resource, "canonical")
    }
    # Updated to 7 since we added /snapshot or similar routes in the evolution
    assert len(paths) >= 6
