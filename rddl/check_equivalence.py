"""End-to-end equivalence check: RDDLFightEnv vs the original FightEnv.

Both environments run the same scripted `Aggressive` opponent, and the bot is
the only source of randomness in either of them. Seeding the global `random`
module identically therefore makes the two runs comparable step by step: if the
RDDL model, the observation encoder and the bot adapter are all faithful, the
observation vectors must be bit-identical for the whole episode.

The two episodes must be run one after the other, never interleaved -- both
environments draw from the same global `random` stream, so alternating their
steps would hand each of them every second number.

This subsumes the fixture check in `check_parity.py`: it covers hundreds of
steps through states the three hand-written fixtures never reach.

Run:  python -m rddl.check_equivalence
"""

import random
import sys
from typing import List, Tuple

import numpy as np

from fight_env.gym_env import FightEnv
from rddl.train_env import RDDLFightEnv

SEEDS = range(20)
STEPS = 500

Trace = List[Tuple[np.ndarray, float, bool]]


def rollout(env, seed: int) -> Trace:
    """One episode under a fixed agent policy and a fixed bot RNG seed."""
    agent_rng = random.Random(1000 + seed)      # agent actions: same for both envs
    random.seed(seed)                           # bot coin flips: same for both envs
    obs, _ = env.reset(seed=seed)

    trace: Trace = [(obs.copy(), 0.0, False)]
    for _ in range(STEPS):
        obs, reward, terminated, truncated, _ = env.step(agent_rng.randrange(4))
        trace.append((obs.copy(), float(reward), bool(terminated)))
        if terminated or truncated:
            break
    return trace


def main() -> int:
    py_env = FightEnv(max_steps=STEPS)
    rddl_env = RDDLFightEnv(max_steps=STEPS)

    steps = obs_bad = reward_bad = 0
    first = None

    for seed in SEEDS:
        py = rollout(py_env, seed)
        rd = rollout(rddl_env, seed)

        if len(py) != len(rd):
            obs_bad += 1
            first = first or f"seed {seed}: episode lengths differ ({len(py)} vs {len(rd)})"

        for t, (p, r) in enumerate(zip(py, rd)):
            steps += 1
            if not np.array_equal(p[0], r[0]) or p[2] != r[2]:
                obs_bad += 1
                if first is None:
                    first = (f"seed {seed} step {t - 1}\n"
                             f"    python = {p[0]}  terminated={p[2]}\n"
                             f"    rddl   = {r[0]}  terminated={r[2]}")
            if p[1] != r[1]:
                reward_bad += 1

    rddl_env.close()

    print(f"seeds: {len(list(SEEDS))}   steps compared: {steps}")
    print(f"observation/termination mismatches: {obs_bad}")
    print(f"reward mismatches:                  {reward_bad} "
          f"({100.0 * reward_bad / max(steps, 1):.1f}% of steps)")
    if first:
        print("\nfirst divergence:\n" + first)
    if reward_bad and not obs_bad:
        print("\nDynamics are identical -- only the reward differs, which is expected\n"
              "while gym_env.step tests f1_res for HAS_PARRIED and HAS_BEEN_ATTACKED.\n"
              "See docs/rddl-formalization.md section 7.1.")
    return 1 if obs_bad else 0


if __name__ == "__main__":
    sys.exit(main())
