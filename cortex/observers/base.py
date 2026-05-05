from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseObserver(ABC):
    """
    Base class for all Sovereign Observers.
    Observers are responsible for monitoring specific dimensions of the agent's state
    and emitting "signals" when gaps, fragilities, or opportunities are detected.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def observe(self) -> List[Dict[str, Any]]:
        """
        Perform the observation and return a list of signals.
        Each signal should be a dictionary containing:
        - 'level': (INFO, WARNING, CRITICAL)
        - 'signal': The actual discovery
        - 'evidence': Supporting data
        """
        pass
