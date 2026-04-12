"""
Property-based tests for HUD builder using hypothesis.
Invariants:
  - memory_keys always equals memory.count
  - last_keys is never longer than 3
  - last_keys are the most recently added keys (tail of list_keys)
  - urgency is always one of the valid values
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "cortex"))

from state import AgentState
from memory_store import MemoryStore
from hud_builder import build_hud_data
from hypothesis import given, assume, settings, HealthCheck
from hypothesis.strategies import text, lists, sampled_from, tuples


valid_key = text(
    min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz_-0123456789"
)
valid_value = text(min_size=1, max_size=100)
urgency_strategy = sampled_from(["nominal", "elevated", "critical"])
pairs_strategy = lists(
    tuples(valid_key, valid_value),
    min_size=0,
    max_size=30,
    unique_by=lambda p: p[0],
)


def fresh_dir():
    return Path(tempfile.mkdtemp())


@given(pairs=pairs_strategy, urgency=urgency_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_memory_keys_equals_count(pairs, urgency):
    d = fresh_dir()
    state = AgentState(d)
    memory = MemoryStore(d)
    for k, v in pairs:
        memory.store(k, v)
    hud = build_hud_data(state, memory, urgency)
    assert hud["memory_keys"] == memory.count


@given(pairs=pairs_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_last_keys_never_exceeds_three(pairs):
    d = fresh_dir()
    state = AgentState(d)
    memory = MemoryStore(d)
    for k, v in pairs:
        memory.store(k, v)
    hud = build_hud_data(state, memory)
    assert len(hud["last_keys"]) <= 3


@given(pairs=pairs_strategy, urgency=urgency_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_last_keys_subset_of_stored_keys(pairs, urgency):
    assume(len(pairs) > 0)
    d = fresh_dir()
    state = AgentState(d)
    memory = MemoryStore(d)
    for k, v in pairs:
        memory.store(k, v)
    hud = build_hud_data(state, memory, urgency)
    assert set(hud["last_keys"]).issubset(set(memory.list_keys()))


@given(pairs=pairs_strategy, urgency=urgency_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_urgency_passed_through(pairs, urgency):
    d = fresh_dir()
    state = AgentState(d)
    memory = MemoryStore(d)
    for k, v in pairs:
        memory.store(k, v)
    hud = build_hud_data(state, memory, urgency)
    assert hud["urgency"] == urgency


@given(pairs=pairs_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_last_keys_are_tail_of_list_keys(pairs):
    assume(len(pairs) > 0)
    d = fresh_dir()
    state = AgentState(d)
    memory = MemoryStore(d)
    for k, v in pairs:
        memory.store(k, v)
    hud = build_hud_data(state, memory)
    all_keys = memory.list_keys()
    expected = all_keys[-3:] if len(all_keys) >= 3 else all_keys
    assert hud["last_keys"] == expected
