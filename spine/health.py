from __future__ import annotations

import time


class HealthMonitor:
    def __init__(self, stall_timeout: float, startup_timeout: float):
        self.stall_timeout = stall_timeout
        self.startup_timeout = startup_timeout
        self.last_event_time: float = 0.0
        self.cortex_start_time: float = 0.0
        self.first_think_done: bool = False

    def record_event(self):
        self.last_event_time = time.time()

    def record_first_think(self):
        self.first_think_done = True

    def cortex_started(self):
        self.cortex_start_time = time.time()
        self.first_think_done = False
        self.last_event_time = time.time()

    def is_stalled(self) -> bool:
        if self.last_event_time == 0.0:
            return True
        return time.time() - self.last_event_time > self.stall_timeout

    def is_startup_failure(self, exit_code: int) -> bool:
        if self.first_think_done:
            return False
        return time.time() - self.cortex_start_time < self.startup_timeout
