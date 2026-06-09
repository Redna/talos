"""
Dry-run metrics collector.

Runs alongside the Spine in ``talos`` container.  Tails the
``/spine/events/*.jsonl`` event log and the dryrun gate's
``/gate/dryrun_log.jsonl`` and produces a summary table at the
end of a run.

What we measure
---------------
- cycle_start / cycle_end  — emitted by the cortex for each tool call
  in the dry-run; we use ``cortex.tool_call`` paired with
  ``cortex.tool_result`` to measure per-cycle latency.
- supervisor.cortex_exit  — counts crash events
- supervisor.cortex_stall — counts stall kills
- supervisor.lazarus_triggered — counts Lazarus protocol firings
- supervisor.commit_reverted — counts the actual reverts
- supervisor.start_failed — counts failed cortex starts (nono timeouts)
- spine.garbage_response — counts LLM garbage responses (proxy for
  IPC trouble)
- spine.gate_error — counts gate errors

We emit a single ``dryrun.metrics`` event at the end of a run with
the full summary, and we write a JSON dump to
``/spine/dryrun_metrics.json`` for the host-side ``talosctl dry-run``
command to read.
"""

from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

# Event types we care about.  Anything not in this set is ignored.
INTERESTING_EVENTS = {
    "cortex.tool_call",
    "cortex.tool_result",
    "supervisor.cortex_exit",
    "supervisor.cortex_stall",
    "supervisor.lazarus_triggered",
    "supervisor.commit_reverted",
    "supervisor.start_failed",
    "spine.garbage_response",
    "spine.gate_error",
    "dryrun.metrics",
    "dryrun.run_complete",
}


@dataclass
class CycleRecord:
    """A single cycle's worth of timing data."""
    turn: int
    tool_name: str
    start_ts: float
    end_ts: Optional[float] = None
    duration_ms: Optional[float] = None
    success: Optional[bool] = None


@dataclass
class DryRunMetrics:
    """Aggregated metrics for a single dry-run session."""
    scenario: str = ""
    started_at: float = field(default_factory=time.time)
    ended_at: float = 0.0
    total_cycles: int = 0
    cycle_times_ms: List[float] = field(default_factory=list)
    crash_count: int = 0
    lazarus_count: int = 0
    stall_count: int = 0
    ipc_error_count: int = 0
    nono_timeout_count: int = 0
    garbage_response_count: int = 0
    gate_error_count: int = 0
    last_good_commit: str = ""
    tool_call_counts: Dict[str, int] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------
    def record_event(self, event: dict) -> None:
        """Update metrics from a single event log entry.

        The event is the same JSON dict that ``EventLogger.emit``
        writes — a top-level ``type`` and ``payload``.
        """
        etype = event.get("type", "")
        payload = event.get("payload", {}) or {}

        if etype == "cortex.tool_call":
            tool = payload.get("tool", "unknown")
            self.tool_call_counts[tool] = self.tool_call_counts.get(tool, 0) + 1

        elif etype == "cortex.tool_result":
            duration = payload.get("duration_ms")
            if isinstance(duration, (int, float)):
                self.cycle_times_ms.append(float(duration))
                self.total_cycles += 1

        elif etype == "supervisor.cortex_exit":
            self.crash_count += 1

        elif etype == "supervisor.cortex_stall":
            self.stall_count += 1

        elif etype in ("supervisor.lazarus_triggered", "supervisor.commit_reverted"):
            self.lazarus_count += 1

        elif etype == "supervisor.start_failed":
            self.nono_timeout_count += 1

        elif etype == "spine.garbage_response":
            self.garbage_response_count += 1

        elif etype == "spine.gate_error":
            self.gate_error_count += 1

        elif etype == "dryrun.run_complete":
            # The cortex wrote its own completion marker.  Useful
            # only as a heartbeat.
            pass

    def finalize(self) -> None:
        self.ended_at = time.time()
        # Read last_good_commit from the spine directory if present.
        last_good = Path("/spine/last_good_commit")
        if last_good.exists():
            try:
                self.last_good_commit = last_good.read_text().strip()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        d = asdict(self)
        d["cycle_time_stats_ms"] = {
            "count": len(self.cycle_times_ms),
            "mean": self.mean(),
            "max": self.max_ms(),
            "p50": self.p(50),
            "p99": self.p(99),
        }
        d["wall_clock_seconds"] = max(0.0, self.ended_at - self.started_at)
        return d

    def mean(self) -> float:
        return statistics.mean(self.cycle_times_ms) if self.cycle_times_ms else 0.0

    def max_ms(self) -> float:
        return max(self.cycle_times_ms) if self.cycle_times_ms else 0.0

    def p(self, pct: int) -> float:
        if not self.cycle_times_ms:
            return 0.0
        ordered = sorted(self.cycle_times_ms)
        # Nearest-rank percentile
        k = max(0, min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1)))))
        return ordered[k]

    def summary_table(self) -> str:
        """Format the metrics as a clean two-column ASCII table.

        We avoid the ``tabulate`` dependency to keep the spine image
        slim.  Output is suitable for ``talosctl dry-run`` printing.
        """
        rows = [
            ("scenario", self.scenario or "unknown"),
            ("total cycles", self.total_cycles),
            ("mean cycle ms", f"{self.mean():.1f}"),
            ("max cycle ms", f"{self.max_ms():.1f}"),
            ("p50 cycle ms", f"{self.p(50):.1f}"),
            ("p99 cycle ms", f"{self.p(99):.1f}"),
            ("crash count", self.crash_count),
            ("lazarus count", self.lazarus_count),
            ("stall count", self.stall_count),
            ("nono timeout count", self.nono_timeout_count),
            ("garbage response count", self.garbage_response_count),
            ("gate error count", self.gate_error_count),
            ("wall clock s", f"{max(0.0, self.ended_at - self.started_at):.2f}"),
            ("last_good_commit", self.last_good_commit[:12] or "(none)"),
        ]
        if self.tool_call_counts:
            rows.append(("", ""))
            rows.append(("tool calls", ""))
            for tool, count in sorted(self.tool_call_counts.items()):
                rows.append((f"  {tool}", count))

        label_w = max(len(r[0]) for r in rows)
        lines = ["  Dry-Run Metrics", "  " + "-" * (label_w + 14)]
        for label, value in rows:
            lines.append(f"  {label.ljust(label_w)} : {value}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Filesystem tailed-collector.  Used by the spine process and the host-side
# ``talosctl dry-run`` command.
# ---------------------------------------------------------------------------
def collect_from_event_log(events_dir: str | Path) -> DryRunMetrics:
    """Read every jsonl in events_dir and produce a fresh metrics object.

    The function is idempotent — calling it twice on the same directory
    returns a metrics object built from *all* events seen so far.  This
    lets the host command call it after the run completes and get the
    same numbers the spine saw live.
    """
    events_dir = Path(events_dir)
    metrics = DryRunMetrics()
    if not events_dir.exists():
        return metrics

    for jsonl in sorted(events_dir.glob("*.jsonl")):
        try:
            with open(jsonl) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if ev.get("type") in INTERESTING_EVENTS:
                        metrics.record_event(ev)
        except OSError:
            continue

    metrics.finalize()
    return metrics


def collect_dryrun_metrics(spine_dir: str | Path = "/spine") -> DryRunMetrics:
    """Convenience wrapper — reads from ``{spine_dir}/events``."""
    return collect_from_event_log(Path(spine_dir) / "events")


def write_metrics(metrics: DryRunMetrics, path: str | Path = "/spine/dryrun_metrics.json") -> None:
    """Dump the metrics to disk for ``talosctl dry-run`` to consume."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(metrics.to_dict(), indent=2))
