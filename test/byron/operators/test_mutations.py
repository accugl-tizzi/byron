"""Tests for bunch mutation operators."""

from collections import Counter

import pytest

import byron
from byron.operators.initializers import random_individual
from byron.operators.mutations import add_macro_to_bunch, remove_macro_from_bunch
from byron.randy import rrandom


def body(population, individual):
    """Dumped lines, without Byron's header comment."""
    return [line for line in population.dump_individual(individual).splitlines()[1:] if line.strip()]


@pytest.fixture
def macro_bunch_top():
    return byron.f.sequence([byron.f.bunch([byron.f.macro("m {v}", v=byron.f.integer_parameter(0, 10**9))], size=(3, 9))])


@pytest.fixture
def frame_bunch_top():
    """A bunch whose pool elements are frames (e.g. statements made of several macros)."""
    statement = byron.f.sequence(["open", byron.f.macro("value {v}", v=byron.f.integer_parameter(0, 10**9)), "close"])
    return byron.f.sequence([byron.f.bunch([statement], size=(2, 6))])


def test_add_inserts_at_random_positions(macro_bunch_top):
    population = byron.classes.Population(macro_bunch_top)
    rrandom.seed(1)
    positions = Counter()
    for _ in range(60):
        parent = random_individual(macro_bunch_top)[0]
        offspring = add_macro_to_bunch(parent)
        if not offspring:  # bunch already at its maximum size
            continue
        before, after = body(population, parent), body(population, offspring[0])
        assert len(after) == len(before) + 1
        index = next(i for i, line in enumerate(after) if i == len(before) or line != before[i])
        positions["last" if index == len(before) else "inside"] += 1
    assert positions["inside"] > 0 and positions["last"] > 0


def test_add_and_remove_work_on_frame_bunches(frame_bunch_top):
    population = byron.classes.Population(frame_bunch_top)
    rrandom.seed(2)
    changes = Counter()
    for _ in range(20):
        parent = random_individual(frame_bunch_top)[0]
        before = body(population, parent)
        for operator, delta in ((add_macro_to_bunch, +3), (remove_macro_from_bunch, -3)):
            offspring = operator(parent)
            if not offspring:  # bunch already at its maximum/minimum size
                continue
            after = body(population, offspring[0])
            assert len(after) == len(before) + delta
            assert after[::3] == ["open"] * (len(after) // 3)  # whole statements, never split
            changes[operator.__name__] += 1
    assert changes["add_macro_to_bunch"] > 0 and changes["remove_macro_from_bunch"] > 0
