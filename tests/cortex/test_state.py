import sys
import json
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "talos" / "cortex"))

from state import AgentState


def test_set_focus_persists():
    tmp = tempfile.mkdtemp()
    try:
        state = AgentState(tmp)
        old = state.set_focus("investigate anomaly")
        assert old is None
        assert state.current_focus == "investigate anomaly"

        state2 = AgentState(tmp)
        assert state2.current_focus == "investigate anomaly"
    finally:
        shutil.rmtree(tmp)


def test_resolve_focus_clears():
    tmp = tempfile.mkdtemp()
    try:
        state = AgentState(tmp)
        state.set_focus("fix bug")
        old = state.resolve_focus("bug fixed")
        assert old == "fix bug"
        assert state.current_focus is None

        state2 = AgentState(tmp)
        assert state2.current_focus is None
    finally:
        shutil.rmtree(tmp)


def test_error_streak_persists_across_save_load():
    tmp = tempfile.mkdtemp()
    try:
        state = AgentState(tmp)
        state.error_streak = 5
        state.total_tokens_consumed = 1000
        state.save()

        state2 = AgentState(tmp)
        assert state2.error_streak == 5
        assert state2.total_tokens_consumed == 1000
    finally:
        shutil.rmtree(tmp)


def test_default_values():
    tmp = tempfile.mkdtemp()
    try:
        state = AgentState(tmp)
        assert state.current_focus is None
        assert state.error_streak == 0
        assert state.total_tokens_consumed == 0
    finally:
        shutil.rmtree(tmp)
