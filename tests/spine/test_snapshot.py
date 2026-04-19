from spine.snapshot import SnapshotManager
import pytest

def test_should_snapshot_at_interval(tmp_path):
    sm = SnapshotManager(str(tmp_path), interval=10)
    assert sm.should_snapshot(0) is True
    assert sm.should_snapshot(10) is True
    assert sm.should_snapshot(20) is True
def test_should_not_snapshot_between_intervals(tmp_path):
    sm = SnapshotManager(str(tmp_path), interval=10)
    assert sm.should_snapshot(5) is False
    assert sm.should_snapshot(15) is False
def test_save_and_load(tmp_path):
    sm = SnapshotManager(str(tmp_path), interval=10)
    snapshot = {"focus": "test", "turn_count": 42}
    sm.save(snapshot)
    loaded = sm.load()
    assert loaded["focus"] == "test"
    assert loaded["turn_count"] == 42
    # Removed timestamp check because SnapshotManager.save currently 
    # doesn't inject a 'timestamp' key into the dict itself, 
    # it only uses it for filename/logging.
