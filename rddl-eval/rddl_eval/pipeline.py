"""The validation cascade and the repair loop around it.

``extract -> lint -> parse -> simulate -> semantic``, stopping at the first
level that reports problems.  Which level stopped it *is* the measurement, so
no level papers over another's failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import semantic
from .extract import ExtractError, extract_blocks
from .lint import lint
from .llm import LMStudioClient
from .parse import parse_blocks
from .simulate import DEFAULT_STEPS, Trace, simulate

LEVELS = ("extract", "lint", "parse", "simulate", "semantic")
PASS = "pass"


@dataclass
class Validation:
    #: the level that failed, or ``"pass"``
    level: str
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    trace: Trace | None = None

    @property
    def ok(self) -> bool:
        return self.level == PASS


def validate(response: str, task: str, steps: int = DEFAULT_STEPS) -> Validation:
    """Run one model response through every level, stopping at the first failure."""
    try:
        blocks = extract_blocks(response)
    except ExtractError as exc:
        return Validation(level="extract", problems=list(exc.problems))

    report = lint(blocks)
    warnings = [problem.message for problem in report.warnings]
    if not report.ok:
        return Validation(
            level="lint",
            problems=[problem.message for problem in report.errors],
            warnings=warnings,
        )

    parsed = parse_blocks(blocks)
    if not parsed.ok:
        return Validation(level="parse", problems=[parsed.error or ""], warnings=warnings)

    result = simulate(parsed.env, steps=semantic.steps_for(task, steps))
    if not result.ok:
        return Validation(
            level="simulate",
            problems=result.problems,
            warnings=warnings,
            trace=result.trace,
        )

    problems = semantic.check(task, result.trace)
    if problems:
        return Validation(
            level="semantic", problems=problems, warnings=warnings, trace=result.trace
        )

    return Validation(level=PASS, warnings=warnings, trace=result.trace)


def feedback_message(validation: Validation) -> str:
    """The user turn that asks the model to repair its own output."""
    numbered = "\n".join(
        f"{i}. {problem}" for i, problem in enumerate(validation.problems, start=1)
    )
    return (
        f"Your RDDL was rejected at the `{validation.level}` stage of validation.\n\n"
        f"Problems found:\n{numbered}\n\n"
        f"Fix every problem listed above and output the corrected RDDL in full: all "
        f"three blocks (`domain`, `non-fluents`, `instance`), each in its own "
        f"```rddl code fence. Do not abbreviate any block and do not explain the "
        f"changes."
    )


@dataclass
class Attempt:
    index: int
    response: str
    level: str
    problems: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return self.level == PASS


@dataclass
class RunResult:
    task: str
    attempts: list[Attempt] = field(default_factory=list)
    #: the full dialogue, exactly as sent to the model
    messages: list[dict] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.attempts) and self.attempts[-1].ok

    @property
    def passed_first_try(self) -> bool:
        return bool(self.attempts) and self.attempts[0].ok

    @property
    def first_failure_level(self) -> str | None:
        """Where the *first* attempt stopped -- ``None`` if it passed."""
        if not self.attempts or self.attempts[0].ok:
            return None
        return self.attempts[0].level

    @property
    def final_level(self) -> str:
        return self.attempts[-1].level if self.attempts else "extract"

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "passed": self.passed,
            "passed_first_try": self.passed_first_try,
            "first_failure_level": self.first_failure_level,
            "final_level": self.final_level,
            "attempts": [
                {
                    "index": a.index,
                    "level": a.level,
                    "problems": a.problems,
                    "warnings": a.warnings,
                    "response": a.response,
                }
                for a in self.attempts
            ],
            "messages": self.messages,
        }


def run_once(
    client: LMStudioClient,
    system_prompt: str,
    task_text: str,
    task: str,
    repairs: int = 1,
    temperature: float | None = None,
    steps: int = DEFAULT_STEPS,
) -> RunResult:
    """One generation plus up to *repairs* rounds of error-driven repair."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task_text},
    ]
    result = RunResult(task=task)

    for index in range(repairs + 1):
        response = client.complete(messages, temperature=temperature)
        validation = validate(response, task, steps=steps)
        result.attempts.append(
            Attempt(
                index=index,
                response=response,
                level=validation.level,
                problems=list(validation.problems),
                warnings=list(validation.warnings),
            )
        )
        if validation.ok or index == repairs:
            messages.append({"role": "assistant", "content": response})
            break
        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": feedback_message(validation)})

    result.messages = messages
    return result
