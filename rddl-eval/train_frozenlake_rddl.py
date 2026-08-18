"""Tabular Q-learning on a FrozenLake that comes out of RDDL, not out of Gym.

The learning loop is the same one you would write against
``gym.make("FrozenLake-v1")``.  Two adapters carry the whole difference:
pyRDDLGym hands back a *dict of fluents* where Gym hands back an integer, and
it wants a *dict of action-fluents* where Gym wants an action index.

Rendering goes through pyRDDLGym's own visualizer hook rather than round-tripping
images by hand -- see ``envs/frozenlake_viz.py``.
"""

from __future__ import annotations

import argparse
import re
import time

import numpy as np

from envs.frozenlake import GYM_SLIP, MAP_3X3, MAP_4X4, build
from rddl_eval.extract import extract_blocks
from rddl_eval.parse import parse_blocks

#: Order fixes the meaning of every action index in the Q-table.
ACTIONS = ("move_north", "move_south", "move_east", "move_west")
GLYPHS = {"move_north": "^", "move_south": "v", "move_east": ">", "move_west": "<"}

_CELL_KEY = re.compile(r"^at___c(\d+)_(\d+)$")


def make_env(rows: list[str], horizon: int, slip: float = 0.0):
    """Compile the generated RDDL and hand back a pyRDDLGym environment."""
    result = parse_blocks(extract_blocks(build(rows, horizon=horizon, slip=slip)))
    if not result.ok:
        raise SystemExit(f"the generated RDDL did not compile: {result.error}")
    return result.env


def state_index(rows: list[str]):
    """``at___c<r>_<c>`` -> a single integer, row-major, like Gym's FrozenLake."""
    width = len(rows[0])

    def encode(obs: dict) -> int:
        for key, value in obs.items():
            if value:
                m = _CELL_KEY.match(key)
                if m:
                    return int(m.group(1)) * width + int(m.group(2))
        raise RuntimeError(f"no cell is occupied in {obs}")

    return encode


def greedy_policy(Q, rows: list[str]) -> dict:
    """``{(row, col): action_name}`` for every cell the agent can stand on."""
    width = len(rows[0])
    policy = {}
    for r, row in enumerate(rows):
        for c, char in enumerate(row):
            if char in "HG":
                continue
            s = r * width + c
            if Q[s].max() > 0:
                policy[(r, c)] = ACTIONS[int(np.argmax(Q[s]))]
    return policy


def train(env, encode, n_states, episodes, alpha, gamma, seed):
    rng = np.random.default_rng(seed)
    Q = np.zeros((n_states, len(ACTIONS)), dtype=np.float32)

    eps, eps_min = 1.0, 0.05
    eps_decay = (eps - eps_min) / max(1.0, episodes * 0.8)

    wins, curve = 0, []
    window = max(1, episodes // 10)
    started = time.time()

    for episode in range(episodes):
        obs, _ = env.reset(seed=int(rng.integers(1 << 30)))
        s = encode(obs)
        reward, done = 0.0, False

        while not done:
            if rng.random() < eps:
                a = int(rng.integers(len(ACTIONS)))
            else:
                a = int(np.argmax(Q[s]))

            obs, reward, terminated, truncated, _ = env.step({ACTIONS[a]: True})
            done = terminated or truncated
            s2 = encode(obs)

            target = float(reward) if terminated else float(reward) + gamma * np.max(Q[s2])
            Q[s, a] += alpha * (target - Q[s, a])
            s = s2

        wins += int(reward > 0)
        eps = max(eps_min, eps - eps_decay)

        if (episode + 1) % window == 0:
            rate = wins / window
            curve.append((episode + 1, rate))
            print(f"episode {episode + 1:6}/{episodes}  "
                  f"success rate (last {window}): {rate:6.2%}  eps={eps:.2f}")
            wins = 0

    print(f"\ntrained in {time.time() - started:.1f}s")
    return Q, curve


def evaluate(env, encode, Q, rollouts: int, seed: int) -> None:
    """Greedy success rate over many episodes.

    One rollout proves nothing on slippery ice: with SLIP=2/3 a 4-step run and
    a 26-step run are both ordinary samples of the same policy.  Worse, every
    draw downstream of --seed is deterministic, so replaying a single episode
    shows the same sample every time and reads as improbable luck.
    """
    if rollouts <= 0:
        return

    lengths, wins = [], 0
    for i in range(rollouts):
        obs, _ = env.reset(seed=seed + 1_000_000 + i)
        s = encode(obs)
        done, steps, reward = False, 0, 0.0
        while not done:
            obs, reward, terminated, truncated, _ = env.step(
                {ACTIONS[int(np.argmax(Q[s]))]: True})
            done = terminated or truncated
            s = encode(obs)
            steps += 1
        if reward > 0:
            wins += 1
            lengths.append(steps)

    print(f"\ngreedy evaluation over {rollouts} rollouts:")
    print(f"  reached goal   {wins}/{rollouts} ({wins / rollouts:.1%})")
    if lengths:
        lengths.sort()
        print(f"  episode length min {lengths[0]}  "
              f"median {lengths[len(lengths) // 2]}  max {lengths[-1]}")


def print_policy(Q, rows: list[str]) -> None:
    policy = greedy_policy(Q, rows)
    print("\nGreedy policy:")
    for r, row in enumerate(rows):
        cells = []
        for c, char in enumerate(row):
            if char in "HG":
                cells.append(char)
            else:
                cells.append(GLYPHS[policy[(r, c)]] if (r, c) in policy else ".")
        print("   " + "  ".join(cells))


def print_ansi(rows: list[str], here: tuple[int, int]) -> None:
    for r, row in enumerate(rows):
        line = ["@" if (r, c) == here else char for c, char in enumerate(row)]
        print("   " + "  ".join(line))
    print()


def replay(env, encode, Q, rows, render: str, delay: float, gif: str | None,
           caption: str = "greedy policy", seed: int | None = None) -> None:
    """One greedy episode, drawn the way ``--render`` asks for.\n\n    An illustration, not a measurement -- see :func:`evaluate`.\n    """
    width = len(rows[0])
    policy = greedy_policy(Q, rows)
    frames = []

    visual = render == "human" or gif
    if visual:
        from envs.frozenlake_viz import FrozenLakeViz
        env.set_visualizer(FrozenLakeViz, rows=rows, policy=policy,
                           caption=caption)

    print(f"\n--- one greedy rollout (seed {seed}) ---")
    obs, _ = env.reset(seed=seed)
    s = encode(obs)
    if render == "ansi":
        print_ansi(rows, (s // width, s % width))
    if visual:
        frames.append(env.render(to_display=(render == "human")))

    reward, done, step = 0.0, False, 0
    while not done:
        a = int(np.argmax(Q[s]))
        obs, reward, terminated, truncated, _ = env.step({ACTIONS[a]: True})
        done = terminated or truncated
        s = encode(obs)
        step += 1

        print(f"  step {step:2}: {ACTIONS[a]:11} -> cell ({s // width},{s % width})  reward={reward}")
        if render == "ansi":
            print_ansi(rows, (s // width, s % width))
        if visual:
            frames.append(env.render(to_display=(render == "human")))
        if delay and render != "none":
            time.sleep(delay)

    print("GOAL reached." if reward > 0 else "Fell in a hole / timed out.")

    if gif and frames:
        frames[0].save(gif, save_all=True, append_images=frames[1:],
                       duration=int(max(delay, 0.4) * 1000), loop=0)
        print(f"animation -> {gif}")
    if render == "human":
        time.sleep(1.5)


def save_curve(curve, path: str, episodes: int) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs, ys = zip(*curve)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(xs, [y * 100 for y in ys], marker="o", color="#2f6f9f")
    ax.set_xlabel("episode")
    ax.set_ylabel("success rate, %")
    ax.set_title(f"Q-learning on RDDL FrozenLake ({episodes} episodes)")
    ax.set_ylim(-5, 105)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    print(f"curve -> {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default="3x3", choices=["3x3", "4x4"])
    parser.add_argument("--slippery", action="store_true",
                        help="slippery ice: 1/3 intended, 1/3 each perpendicular")
    parser.add_argument("--episodes", type=int, default=2000)
    parser.add_argument("--alpha", type=float, default=0.1)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--horizon", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rollouts", type=int, default=200,
                        help="greedy episodes to measure before drawing one")
    parser.add_argument("--show-seed", type=int, default=None,
                        help="seed for the single rollout that gets drawn")
    parser.add_argument("--render", default="human", choices=["human", "ansi", "none"],
                        help="human = pygame window, ansi = text grid")
    parser.add_argument("--delay", type=float, default=0.4, help="seconds between rendered steps")
    parser.add_argument("--gif", default=None, help="also save the rollout as an animated GIF")
    parser.add_argument("--plot", default=None, help="save the training curve to this PNG")
    args = parser.parse_args()

    rows = MAP_3X3 if args.map == "3x3" else MAP_4X4
    slip = GYM_SLIP if args.slippery else 0.0
    env = make_env(rows, horizon=args.horizon, slip=slip)
    encode = state_index(rows)

    print(f"map {args.map}  states {len(rows) * len(rows[0])}  actions {len(ACTIONS)}  "
          f"horizon {env.horizon}  slip {slip:.3f} "
          f"({'slippery' if slip else 'dry'})")
    for row in rows:
        print("   " + "  ".join(row))
    print()

    Q, curve = train(env, encode, len(rows) * len(rows[0]),
                     args.episodes, args.alpha, args.gamma, args.seed)
    print_policy(Q, rows)
    evaluate(env, encode, Q, args.rollouts, args.seed)
    if args.plot:
        save_curve(curve, args.plot, args.episodes)
    replay(env, encode, Q, rows, args.render, args.delay, args.gif,
           caption=f"greedy policy ({'slippery' if slip else 'dry'} ice)",
           seed=args.show_seed)
    env.close()


if __name__ == "__main__":
    main()
