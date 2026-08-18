"""Smoke test: a known-good fixture all the way through parse and simulate.

Marked ``rddlgym`` because, unlike the lint tests, it needs the compiler:
``pytest -m "not rddlgym"`` skips it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rddl_eval.extract import extract_blocks
from rddl_eval.parse import parse_blocks
from rddl_eval.pipeline import PASS, validate
from rddl_eval.semantic import SEMANTIC_CHECKS, check
from rddl_eval.simulate import Trace, simulate, _reward_problems

pytestmark = pytest.mark.rddlgym

pytest.importorskip("pyRDDLGym")

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
VALID_TEXT = (FIXTURES / "valid" / "shelves.rddl").read_text()


@pytest.fixture(scope="module")
def parsed():
    result = parse_blocks(extract_blocks(VALID_TEXT))
    assert result.ok, result.error
    return result


def test_valid_fixture_compiles(parsed):
    assert parsed.env.horizon == 300
    assert parsed.env.max_allowed_actions == 1


def test_valid_fixture_simulates(parsed):
    result = simulate(parsed.env, steps=50)
    assert result.ok, result.problems
    assert result.trace.steps == 50
    assert len(result.trace.rewards) == 50
    assert set(result.trace.fluent_names()) == {"stock"}


def test_valid_fixture_reaches_pass():
    result = validate(VALID_TEXT, task="shelves")
    assert result.level == PASS, result.problems
    assert result.warnings == []


def test_semantic_checks_run_long_enough_for_the_task(parsed):
    """The shelves checks need 300 steps, not the 200-step default."""
    steps = SEMANTIC_CHECKS["shelves"].steps
    result = simulate(parsed.env, steps=steps)
    assert result.trace.steps == steps
    assert check("shelves", result.trace) == []


def test_parse_reports_a_compiler_error_instead_of_raising():
    broken = VALID_TEXT.replace("stock'(?s) =", "stock(?s)' =")
    result = parse_blocks(extract_blocks(broken))
    assert not result.ok
    assert "stock" in result.error


def test_unwrapped_aggregation_is_accepted_by_the_compiler():
    """Why rule 6 exists: pyRDDLGym never complains, it just means something else."""
    text = (FIXTURES / "invalid" / "06_unwrapped_aggregation.rddl").read_text()
    assert parse_blocks(extract_blocks(text)).ok


# --------------------------------------------------------------------------
# rollout checks, exercised directly on synthetic traces
# --------------------------------------------------------------------------


def _trace(rewards: list[float]) -> Trace:
    return Trace(rewards=rewards, states=[{}], steps=len(rewards))


def test_constant_reward_is_reported():
    assert "constant" in _reward_problems(_trace([-1.0] * 20))[0]


def test_varying_reward_is_accepted():
    assert _reward_problems(_trace([-1.0, 0.0, -2.0])) == []


def test_nan_reward_is_reported():
    assert "NaN" in _reward_problems(_trace([0.0, float("nan"), 1.0]))[0]


def test_infinite_reward_is_reported():
    assert "infinite" in _reward_problems(_trace([0.0, float("inf"), 1.0]))[0]


def test_empty_rollout_is_reported():
    assert "no steps" in _reward_problems(_trace([]))[0]


def test_shelves_semantic_check_notices_a_missing_fluent():
    trace = Trace(states=[{"inventory___s1": 3}], action_names=["restock___s1"])
    problems = check("shelves", trace)
    assert "no state-fluent named `stock`" in problems[0]


def test_shelves_semantic_check_notices_stock_out_of_range():
    trace = Trace(
        states=[{"stock___s1": 0}, {"stock___s1": 42}],
        actions=[{"restock___s1": 1}],
        action_names=["restock___s1"],
    )
    problems = check("shelves", trace)
    assert any("left the allowed range" in p for p in problems)


def test_shelves_semantic_check_notices_stock_that_never_empties():
    trace = Trace(
        states=[{"stock___s1": 5}, {"stock___s1": 6}],
        actions=[{"restock___s1": 1}],
        action_names=["restock___s1"],
    )
    problems = check("shelves", trace)
    assert any("No shelf ever ran out" in p for p in problems)


def test_shelves_semantic_check_notices_a_blocked_restock():
    trace = Trace(
        states=[{"stock___s1": 0}],
        actions=[{"restock___s1": 0}],
        action_names=["restock___s1"],
    )
    problems = check("shelves", trace)
    assert any("never applied" in p for p in problems)


def test_duel_is_a_registered_stub():
    assert check("duel", Trace()) == []


def test_unknown_task_checks_nothing():
    assert check("no-such-task", Trace()) == []
