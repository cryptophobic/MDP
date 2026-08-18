"""Run a random policy through a compiled environment.

A domain can compile and still be junk: it can blow up at the first step, hand
back NaN, or pay out the same reward whatever happens.  The last case is the
interesting one -- it is what a model produces when the reward expression
ignores both state and action.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .parse import _quiet

DEFAULT_STEPS = 200


@dataclass
class Trace:
    """What a rollout saw, in a form the semantic checks can inspect."""

    #: observation dicts, including the one returned by ``reset``
    states: list[dict] = field(default_factory=list)
    actions: list[dict] = field(default_factory=list)
    rewards: list[float] = field(default_factory=list)
    steps: int = 0
    terminated: bool = False
    truncated: bool = False
    #: grounded action names offered by the environment's action space
    action_names: list[str] = field(default_factory=list)

    def values_of(self, fluent: str) -> list[float]:
        """Every value a fluent took, over all objects and all steps.

        pyRDDLGym grounds ``stock(s1)`` to ``stock___s1``; matching on the
        prefix collects all objects of a lifted fluent at once.
        """
        keys = [key for key in (self.states[0] if self.states else {}) if _base_name(key) == fluent]
        return [state[key] for state in self.states for key in keys if key in state]

    def fluent_names(self) -> set[str]:
        return {_base_name(key) for key in (self.states[0] if self.states else {})}


def _base_name(grounded: str) -> str:
    return grounded.split("___", 1)[0]


@dataclass
class SimulationResult:
    trace: Trace
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def simulate(env, steps: int = DEFAULT_STEPS, seed: int = 42) -> SimulationResult:
    """Roll out a uniformly random policy for at most *steps* steps."""
    from pyRDDLGym.core.policy import RandomAgent

    trace = Trace()
    problems: list[str] = []
    try:
        with _quiet():
            agent = RandomAgent(
                action_space=env.action_space,
                num_actions=env.max_allowed_actions,
                seed=seed,
            )
            trace.action_names = list(env.action_space.keys())
            state, _ = env.reset(seed=seed)
            trace.states.append(dict(state))
            for _ in range(steps):
                action = agent.sample_action(state)
                state, reward, terminated, truncated, _ = env.step(action)
                trace.actions.append(dict(action))
                trace.rewards.append(float(reward))
                trace.states.append(dict(state))
                trace.steps += 1
                if terminated or truncated:
                    trace.terminated = bool(terminated)
                    trace.truncated = bool(truncated)
                    break
    except Exception as exc:  # noqa: BLE001 - a crash mid-rollout is a result
        problems.append(
            f"The simulation crashed after {trace.steps} step(s) with "
            f"{type(exc).__name__}: {exc}"
        )
        return SimulationResult(trace=trace, problems=problems)

    problems.extend(_reward_problems(trace))
    return SimulationResult(trace=trace, problems=problems)


def _reward_problems(trace: Trace) -> list[str]:
    if not trace.rewards:
        return [
            "The simulation produced no steps at all: the episode ended immediately "
            "after reset. Check the horizon and the termination condition."
        ]
    bad = [r for r in trace.rewards if math.isnan(r) or math.isinf(r)]
    if bad:
        return [
            f"The reward was {'NaN' if math.isnan(bad[0]) else 'infinite'} during the "
            f"rollout ({len(bad)} of {len(trace.rewards)} steps). Check for division by "
            f"zero, a logarithm of a non-positive number, or an unbounded penalty in "
            f"the reward expression."
        ]
    if len(trace.rewards) > 1 and len(set(trace.rewards)) == 1:
        return [
            f"The reward was constant ({trace.rewards[0]}) for all {len(trace.rewards)} "
            f"steps of a random rollout. The reward expression apparently depends on "
            f"neither the state nor the action, which makes the task impossible to "
            f"solve. Make the reward a function of the state-fluents and/or the "
            f"action-fluents."
        ]
    return []
