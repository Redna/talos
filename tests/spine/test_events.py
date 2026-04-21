import json
from datetime import datetime, timezone
from pathlib import Path

from spine.events import EventLogger


def test_emit_creates_file(tmp_path):
    logger = EventLogger(str(tmp_path))
    logger.emit("test_event", {"key": "value"})
    logger.close()
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1


def test_emit_writes_jsonl(tmp_path):
    logger = EventLogger(str(tmp_path))
    logger.emit("test_event", {"key": "value"})
    logger.close()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    content = (tmp_path / f"{today}.jsonl").read_text()
    lines = content.strip().split("\n")
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["type"] == "test_event"
    assert event["payload"]["key"] == "value"
    assert "ts" in event
