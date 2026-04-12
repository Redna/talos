"""
Property-based tests for AgentState using hypothesis.
Invariants:
  - set_focus then current_focus matches
  - resolve_focus always clears focus and returns the old one
  - error_streak persists across save/load
  - total_tokens_consumed persists across save/load
  - save then load is a round-trip for all fields
  - set_focus returns the previous focus (None if first set)
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "cortex"))

from state import AgentState
from hypothesis import given, assume, settings, HealthCheck
from hypothesis.strategies import text, integers


focus_strategy = text(min_size=1, max_size=200)
streak_strategy = integers(min_value=0, max_value=1000)
tokens_strategy = integers(min_value=0, max_value=1000000000)


def fresh_dir():
    return Path(tempfile.mkdtemp())


@given(focus=focus_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_set_focus_updates_current_focus(focus):
    state = AgentState(fresh_dir())
    state.set_focus(focus)
    assert state.current_focus == focus


@given(focus=focus_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_set_focus_returns_previous(focus):
    state = AgentState(fresh_dir())
    old = state.set_focus(focus)
    assert old is None or isinstance(old, str)


@given(focus1=focus_strategy, focus2=focus_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_set_focus_twice_returns_first(focus1, focus2):
    assume(focus1 != focus2)
    state = AgentState(fresh_dir())
    state.set_focus(focus1)
    old = state.set_focus(focus2)
    assert old == focus1


@given(focus=focus_strategy, synthesis=text(min_size=1, max_size=200))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_resolve_focus_clears_and_returns_old(focus, synthesis):
    state = AgentState(fresh_dir())
    state.set_focus(focus)
    old = state.resolve_focus(synthesis)
    assert old == focus
    assert state.current_focus is None


@given(streak=streak_strategy, tokens=tokens_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_error_streak_persistence(streak, tokens):
    d = fresh_dir()
    state = AgentState(d)
    state.error_streak = streak
    state.total_tokens_consumed = tokens
    state.save()
    state2 = AgentState(d)
    assert state2.error_streak == streak
    assert state2.total_tokens_consumed == tokens


@given(focus=focus_strategy, streak=streak_strategy, tokens=tokens_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_full_round_trip(focus, streak, tokens):
    d = fresh_dir()
    state = AgentState(d)
    state.set_focus(focus)
    state.error_streak = streak
    state.total_tokens_consumed = tokens
    state.save()
    state2 = AgentState(d)
    assert state2.current_focus == focus
    assert state2.error_streak == streak
    assert state2.total_tokens_consumed == tokens
