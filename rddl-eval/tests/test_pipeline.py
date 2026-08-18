"""Cascade order and the repair loop, with a stub in place of the model."""

from __future__ import annotations

from pathlib import Path

import pytest

from rddl_eval.pipeline import PASS, feedback_message, run_once, validate

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
VALID_TEXT = (FIXTURES / "valid" / "shelves.rddl").read_text()


class StubClient:
    """Replays canned replies instead of calling LM Studio."""

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls: list[list[dict]] = []

    def complete(self, messages: list[dict], temperature: float | None = None) -> str:
        self.calls.append([dict(m) for m in messages])
        return self.replies.pop(0)


def test_validation_stops_at_extract():
    result = validate("I am afraid I cannot do that.", task="shelves")
    assert result.level == "extract"
    assert result.problems


def test_validation_stops_at_lint_before_parsing():
    text = (FIXTURES / "invalid" / "07_prime_on_rhs.rddl").read_text()
    result = validate(text, task="shelves")
    assert result.level == "lint"
    assert "right-hand side" in result.problems[0]


def test_lint_warnings_survive_into_a_later_level():
    """A warning must not stop the cascade, but must still be reported."""
    text = (FIXTURES / "invalid" / "14_missing_state_invariants.rddl").read_text()
    result = validate(text, task="shelves", steps=5)
    assert result.level != "lint"
    assert any("state-invariants" in w for w in result.warnings)


def test_repair_loop_stops_once_the_model_gets_it_right():
    broken = (FIXTURES / "invalid" / "07_prime_on_rhs.rddl").read_text()
    client = StubClient([broken, VALID_TEXT])
    result = run_once(
        client=client,
        system_prompt="system",
        task_text="task",
        task="shelves",
        repairs=1,
        steps=30,
    )
    assert [a.level for a in result.attempts] == ["lint", PASS]
    assert result.passed
    assert not result.passed_first_try
    assert result.first_failure_level == "lint"

    # the repair turn carries the previous answer and the feedback
    second_call = client.calls[1]
    assert [m["role"] for m in second_call] == ["system", "user", "assistant", "user"]
    assert second_call[2]["content"] == broken
    assert "right-hand side" in second_call[3]["content"]


def test_repair_loop_respects_the_round_budget():
    broken = (FIXTURES / "invalid" / "07_prime_on_rhs.rddl").read_text()
    client = StubClient([broken, broken, broken])
    result = run_once(
        client=client,
        system_prompt="system",
        task_text="task",
        task="shelves",
        repairs=1,
    )
    assert len(result.attempts) == 2
    assert len(client.calls) == 2
    assert not result.passed
    assert result.final_level == "lint"


def test_zero_repairs_means_one_attempt():
    client = StubClient(["nothing usable here"])
    result = run_once(
        client=client, system_prompt="s", task_text="t", task="shelves", repairs=0
    )
    assert len(result.attempts) == 1
    assert result.first_failure_level == "extract"


def test_run_result_serialises_the_whole_dialogue():
    client = StubClient(["no blocks at all"])
    result = run_once(
        client=client, system_prompt="s", task_text="t", task="shelves", repairs=0
    )
    payload = result.to_dict()
    assert payload["task"] == "shelves"
    assert payload["first_failure_level"] == "extract"
    assert payload["attempts"][0]["response"] == "no blocks at all"
    assert [m["role"] for m in payload["messages"]] == ["system", "user", "assistant"]


def test_feedback_message_lists_every_problem():
    result = validate("nothing here", task="shelves")
    message = feedback_message(result)
    assert "`extract`" in message
    assert "1." in message
    assert "```rddl" in message


def test_build_system_prompt_keeps_rddl_braces(tmp_path):
    from rddl_eval.cli import build_system_prompt

    prompt = tmp_path / "p.txt"
    prompt.write_text("before\n{spec}\nafter {not a placeholder} {0}")
    spec = tmp_path / "s.rst"
    spec.write_text("SPEC BODY {?x : type}")

    built = build_system_prompt(str(prompt), str(spec))
    assert "SPEC BODY {?x : type}" in built
    assert "{not a placeholder} {0}" in built
    assert "{spec}" not in built


def test_build_system_prompt_requires_the_placeholder(tmp_path):
    from rddl_eval.cli import build_system_prompt

    prompt = tmp_path / "p.txt"
    prompt.write_text("no placeholder here")
    spec = tmp_path / "s.rst"
    spec.write_text("spec")
    with pytest.raises(SystemExit):
        build_system_prompt(str(prompt), str(spec))


def test_llm_client_reports_a_dead_server():
    from rddl_eval.llm import LLMError, LMStudioClient

    client = LMStudioClient(endpoint="http://127.0.0.1:9/v1/chat/completions", timeout=2)
    with pytest.raises(LLMError) as excinfo:
        client.complete([{"role": "user", "content": "hi"}])
    assert "127.0.0.1:9" in str(excinfo.value)
    assert "Status: Running" in str(excinfo.value)
