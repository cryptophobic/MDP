"""Task-specific checks: does the domain model *this* problem?

Parsing and simulating only prove that a domain is well-formed RDDL.  These
checks ask whether the mechanics the task description asked for are actually
present.  Registry keys are task file names without the extension.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .simulate import Trace

#: Shelf stock range fixed by tasks/shelves.txt.
SHELF_MIN, SHELF_MAX = 0, 10


@dataclass(frozen=True)
class SemanticCheck:
    """A check plus the rollout length it needs to be meaningful."""

    func: Callable[[Trace], list[str]]
    steps: int


def _shelves(trace: Trace) -> list[str]:
    problems: list[str] = []
    fluents = trace.fluent_names()

    if "stock" not in fluents:
        return [
            "The domain has no state-fluent named `stock`. The task requires the "
            "per-shelf inventory to be a state-fluent called `stock(shelf)`; the "
            f"state-fluents found were: {', '.join(sorted(fluents)) or 'none'}."
        ]

    stock_values = trace.values_of("stock")
    out_of_range = [v for v in stock_values if not (SHELF_MIN <= v <= SHELF_MAX)]
    if out_of_range:
        problems.append(
            f"Shelf stock left the allowed range [{SHELF_MIN}, {SHELF_MAX}]: saw "
            f"{min(out_of_range)}..{max(out_of_range)} during the rollout. Clamp the "
            f"stock CPF, for example "
            f"`stock'(?s) = max[0, min[CAPACITY, stock(?s) - ...]];`."
        )

    restock_actions = [name for name in trace.action_names if name.split("___", 1)[0] == "restock"]
    if not restock_actions:
        problems.append(
            "The domain has no action-fluent named `restock`. The task requires a "
            "per-shelf replenishment action `restock(shelf)`; the actions found were: "
            f"{', '.join(sorted(trace.action_names)) or 'none'}."
        )
    elif not any(
        bool(value)
        for action in trace.actions
        for name, value in action.items()
        if name.split("___", 1)[0] == "restock"
    ):
        problems.append(
            f"Over {len(trace.actions)} random steps the `restock` action was never "
            f"applied, which means it is permanently blocked. Check the "
            f"`action-preconditions` section and `max-nondef-actions` in the instance."
        )

    if stock_values and min(stock_values) > SHELF_MIN:
        problems.append(
            f"No shelf ever ran out over {len(trace.actions)} steps (the lowest stock "
            f"seen was {min(stock_values)}). Demand is apparently never subtracted "
            f"from stock: the `stock` CPF must decrease it every step, e.g. "
            f"`stock'(?s) = max[0, stock(?s) - DEMAND(?s) + ...];`."
        )
    return problems


def _duel(trace: Trace) -> list[str]:
    """Placeholder: the duel task has no semantic checks yet."""
    return []


SEMANTIC_CHECKS: dict[str, SemanticCheck] = {
    "shelves": SemanticCheck(func=_shelves, steps=300),
    "duel": SemanticCheck(func=_duel, steps=200),
}


def steps_for(task: str, default: int) -> int:
    check = SEMANTIC_CHECKS.get(task)
    return max(default, check.steps) if check else default


def check(task: str, trace: Trace) -> list[str]:
    """Run the checks registered for *task*; unknown tasks check nothing."""
    entry = SEMANTIC_CHECKS.get(task)
    return entry.func(trace) if entry else []
