from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import Lock

logger = logging.getLogger("spine.task_queue")

class TaskQueueManager:
    """
    Manages the persistent task queue in /memory/task_queue.json.
    Ensures that objectives and their statuses persist across restarts.
    """
    def __init__(self, memory_dir: Path):
        self.file_path = memory_dir / "task_queue.json"
        self._lock = Lock()
        self._tasks: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        """Load tasks from disk."""
        with self._lock:
            try:
                if self.file_path.exists():
                    with open(self.file_path, "r") as f:
                        self._tasks = json.load(f)
                    logger.info(f"Loaded {len(self._tasks)} tasks from {self.file_path}")
                else:
                    self._tasks = []
                    logger.info(f"No task queue found at {self.file_path}, starting fresh.")
            except Exception as e:
                logger.error(f"Failed to load task queue: {e}")
                self._tasks = []

    def _save(self):
        """Save current tasks to disk."""
        with self._lock:
            try:
                with open(self.file_path, "w") as f:
                    json.dump(self._tasks, f, indent=4)
            except Exception as e:
                logger.error(f"Failed to save task queue: {e}")

    def get_tasks(self) -> List[Dict[str, Any]]:
        """Return a copy of the current task queue."""
        with self._lock:
            return [task.copy() for task in self._tasks]

    def add_task(self, objective: str, priority: str, description: str, **kwargs) -> str:
        """Add a new task to the queue."""
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:6]}"
        task = {
            "id": task_id,
            "objective": objective,
            "status": "pending",
            "priority": priority,
            "description": description,
            **kwargs
        }
        with self._lock:
            self._tasks.append(task)
        self._save()
        return task_id

    def update_task(self, task_id: str, updates: Dict[str, Any]):
        """Update a specific task's attributes."""
        with self._lock:
            for task in self._tasks:
                if task["id"] == task_id:
                    task.update(updates)
                    break
        self._save()

    def remove_task(self, task_id: str):
        """Remove a task from the queue."""
        with self._lock:
            self._tasks = [t for t in self._tasks if t["id"] != task_id]
        self._save()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single task by ID."""
        with self._lock:
            for task in self._tasks:
                if task["id"] == task_id:
                    return task.copy()
        return None

    def handle_action(
        self, 
        action: str, 
        task_id: Optional[str] = None, 
        objective: Optional[str] = None, 
        priority: Optional[str] = None, 
        description: Optional[str] = None, 
        updates: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Dispatch task queue actions."""
        if action == "get":
            if task_id:
                return self.get_task(task_id)
            return self.get_tasks()
        
        if action == "add":
            return self.add_task(
                objective or "Unknown Objective",
                priority or "P3",
                description or ""
            )
        
        if action == "update":
            if not task_id:
                raise ValueError("task_id required for update")
            self.update_task(task_id, updates or {})
            return True
        
        if action == "remove":
            if not task_id:
                raise ValueError("task_id required for removal")
            self.remove_task(task_id)
            return True
            
        raise ValueError(f"Unsupported task action: {action}")
