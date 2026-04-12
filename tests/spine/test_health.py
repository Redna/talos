from spine.health import HealthMonitor


def test_cortex_started_resets_state():
    h = HealthMonitor(stall_timeout=10.0, startup_timeout=5.0)
    h.first_think_done = True
    h.cortex_started()
    assert h.first_think_done is False
    assert h.cortex_start_time > 0


def test_is_stalled_when_no_events():
    h = HealthMonitor(stall_timeout=10.0, startup_timeout=5.0)
    assert h.is_stalled() is True


def test_is_stalled_after_recent_event():
    h = HealthMonitor(stall_timeout=600.0, startup_timeout=5.0)
    h.record_event()
    assert h.is_stalled() is False


def test_is_startup_failure_when_no_think():
    h = HealthMonitor(stall_timeout=600.0, startup_timeout=30.0)
    h.cortex_started()
    assert h.is_startup_failure(1) is True


def test_not_startup_failure_after_think():
    h = HealthMonitor(stall_timeout=600.0, startup_timeout=30.0)
    h.cortex_started()
    h.record_first_think()
    assert h.is_startup_failure(1) is False
