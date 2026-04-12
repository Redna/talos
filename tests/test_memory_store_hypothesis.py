"""
Property-based tests for MemoryStore using hypothesis.
Invariants:
  - store then recall always returns the original value (exact key)
  - capacity constraint: cannot exceed MAX_MEMORY_SLOTS
  - key length constraint: rejects keys > 100 chars
  - forget then recall yields NOT FOUND
  - list_keys reflects all stored keys
  - count always equals len(list_keys)
  - persistence: data survives re-instantiation
  - overwrite existing key updates value
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "cortex"))

from memory_store import MemoryStore, MAX_MEMORY_SLOTS
from hypothesis import given, assume, settings, HealthCheck
from hypothesis.strategies import text, lists, tuples


key_strategy = text(min_size=1, max_size=100)
value_strategy = text(min_size=0, max_size=500)
valid_key = text(
    min_size=1, max_size=99, alphabet="abcdefghijklmnopqrstuvwxyz_-0123456789"
)
valid_value = text(min_size=1, max_size=200)


def fresh_dir():
    return Path(tempfile.mkdtemp())


@given(key=valid_key, value=valid_value)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_store_then_recall_exact_match(key, value):
    d = fresh_dir()
    mem = MemoryStore(d)
    result = mem.store(key, value)
    assert result == f"[STORED] {key}"
    assert mem.recall(key) == value


@given(key=text(min_size=101, max_size=200))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_rejects_oversized_keys(key):
    d = fresh_dir()
    mem = MemoryStore(d)
    result = mem.store(key, "x")
    assert "[ERROR]" in result
    assert "too long" in result.lower()


@given(keys=lists(valid_key, min_size=0, max_size=MAX_MEMORY_SLOTS + 5, unique=True))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_capacity_constraint(keys):
    d = fresh_dir()
    mem = MemoryStore(d)
    for i, k in enumerate(keys):
        result = mem.store(k, f"v_{i}")
        if i < MAX_MEMORY_SLOTS:
            assert "[STORED]" in result
        else:
            assert "[ERROR]" in result
            assert "full" in result.lower()


@given(key=valid_key, value=valid_value)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_forget_then_recall_not_found(key, value):
    d = fresh_dir()
    mem = MemoryStore(d)
    mem.store(key, value)
    forget_result = mem.forget(key)
    assert "[FORGOTTEN]" in forget_result
    recall_result = mem.recall(key)
    assert "[NOT FOUND]" in recall_result


@given(key=valid_key)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_forget_nonexistent_is_not_found(key):
    d = fresh_dir()
    mem = MemoryStore(d)
    result = mem.forget(key)
    assert "[NOT FOUND]" in result


@given(
    pairs=lists(
        tuples(valid_key, valid_value),
        min_size=1,
        max_size=20,
        unique_by=lambda p: p[0],
    )
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_list_keys_reflects_stores(pairs):
    d = fresh_dir()
    mem = MemoryStore(d)
    for k, v in pairs:
        mem.store(k, v)
    assert set(mem.list_keys()) == {k for k, v in pairs}


@given(
    pairs=lists(
        tuples(valid_key, valid_value),
        min_size=0,
        max_size=30,
        unique_by=lambda p: p[0],
    )
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_count_equals_list_keys_length(pairs):
    d = fresh_dir()
    mem = MemoryStore(d)
    for k, v in pairs:
        mem.store(k, v)
    assert mem.count == len(mem.list_keys())


@given(key=valid_key, value=valid_value)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_persistence_across_reinstantiation(key, value):
    d = fresh_dir()
    mem = MemoryStore(d)
    mem.store(key, value)
    mem2 = MemoryStore(d)
    assert mem2.recall(key) == value


@given(key=valid_key, value=valid_value)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_partial_match_recall(key, value):
    assume(len(key) >= 3)
    substring = key[1:-1]
    assume(len(substring) >= 1)
    d = fresh_dir()
    mem = MemoryStore(d)
    mem.store(key, value)
    assert mem.recall(substring) == value


@given(
    pairs=lists(
        tuples(valid_key, valid_value),
        min_size=1,
        max_size=10,
        unique_by=lambda p: p[0],
    )
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_overwrite_existing_key(pairs):
    d = fresh_dir()
    mem = MemoryStore(d)
    k, v1 = pairs[0]
    mem.store(k, v1)
    v2 = "overwritten"
    mem.store(k, v2)
    assert mem.recall(k) == v2
    assert mem.count == 1
