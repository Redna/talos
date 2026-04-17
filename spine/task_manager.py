from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("spine.tasks")

class TaskQueueManager:
    """Manages persistence and synchronization of the agent's task queue.
    
    The Task Queue is stored in /memory/task_queue.json and serves as the 
    agent's long-term roadmap.
    """

    def __init__(self, memory_dir: Path):
        self.memory_dir = Path(memory_dir)
        self.task_file = self.memory_dir / "task_queue.json"
        self._tasks: list[dict[str, Any]] = []
        self._load()

    def _load(self):
        """Load tasks from disk."""
        try:
            if self.task_file.exists():
                with open(self.task_file, "r") as f:
                    self._tasks = json.load(f)
                logger.info(f"Loaded {len(self._tasks)} tasks from {self.task_file}")
            else:
                self._tasks = []
                logger.info("No task queue file found, starting with empty queue")
        except Exception as e:
            logger.error(f"Failed to load task queue: {e}")
            self._tasks = []

    def save(self):
        """Persist tasks to disk."""
        try:
            with open(self.task_file, "w") as f:
                json.dump(self._tasks, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save task queue: {e}")

    def get_tasks(self) -> list[dict[str, Any]]:
        """Return the current list of tasks."""
        return self._tasks

    def add_task(self, objective: str, priority: str, description: str) -> str:
        """Add a new task to the queue."""
        task_id = f"task_{len(self._tasks) + 1:03d}"
        task = {
            "id": task_id,
            "objective": objective,
            "status": "pending",
            "priority": priority,
            "description": description
        }
        self._tasks.append(task)
        self.save()
        return task_id

    def update_task_status(self, task_id: str, status: str):
        """Update the status of a specific task."""
        for task in self._tasks:
            if task["id"] == task_id:
                task["status"] = status
                self.save()
                return True
        return False

    def resolve_task(self, task_id: str):
        """Mark a task as completed."""
        self.update_task_status(task_id, "completed")
