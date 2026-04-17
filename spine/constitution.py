from __future__ import annotations

import hashlib
from pathlib import Path
from threading import RLock


class ConstitutionManager:
    def __init__(self, constitution_path: str, identity_path: str):
        self.constitution_path = Path(constitution_path)
        self.identity_path = Path(identity_path)
        self._lock = RLock()
        self._last_hash: str = ""
        self._content: str = ""
        self._identity: str = ""

    def load(self) -> None:
        self._lock.acquire()
        try:
            constitution = self.constitution_path.read_text()
            if not constitution.strip():
                raise ValueError(
                    "Constitution file is empty or missing — refusing to construct LLM call"
                )
            identity = self.identity_path.read_text()
            self._content = constitution
            self._identity = identity
            self._last_hash = self._hash(self._content + self._identity)
        finally:
            self._lock.release()

    def has_changed(self) -> bool:
        self._lock.acquire()
        try:
            try:
                constitution = self.constitution_path.read_text()
            except FileNotFoundError:
                return True
            try:
                identity = self.identity_path.read_text()
            except FileNotFoundError:
                return True
            current_hash = self._hash(constitution + identity)
            return current_hash != self._last_hash
        finally:
            self._lock.release()

    def reload_if_changed(self) -> tuple[bool, Exception | None]:
        if not self.has_changed():
            return False, None
        try:
            self.load()
            return True, None
        except Exception as e:
            return True, e

    @property
    def identity(self) -> str:
        self._lock.acquire()
        try:
            return self._identity
        finally:
            self._lock.release()

    def system_prompt(self) -> str:
        self._lock.acquire()
        try:
            return self._content + "\n\n" + self._identity
        finally:
            self._lock.release()

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()
