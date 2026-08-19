"""Replay the fight_env parity fixtures through the RDDL model, frame-for-frame.

The RDDL model in this directory is a formal specification of the same combat
core as `fight_env/`. Python stays ground truth: the model is correct iff it
reproduces `parity/trajectories/*.json` exactly, which is the same contract the
Unity C# port is held to.

Requires pyRDDLGym (not part of the project venv):

    pip install pyRDDLGym

Run:  python rddl/check_parity.py
"""

import json
import sys
from pathlib import Path

import pyRDDLGym

HERE = Path(__file__).parent
FIXTURES = HERE.parent / "parity" / "trajectories"

# FighterTask int (as serialized in the fixtures) -> RDDL enum object name
TASK = {
    0: "none", 1: "stance", 2: "attack1", 5: "dead", 6: "defense",
    7: "stunned", 8: "hurt", 9: "parry", 12: "riposte",
}
# ActionType int -> action-fluent name
ACTION = {0: None, 1: "act_attack", 2: "act_block", 3: "act_parry"}

SCENARIOS = ("attack_vs_idle", "attack_vs_block", "parry_then_riposte")


def _noop():
    return {f"{a}___{s}": False
            for a in ("act_attack", "act_block", "act_parry")
            for s in ("a", "b")}


def main() -> int:
    env = pyRDDLGym.make(str(HERE / "duel_domain.rddl"),
                         str(HERE / "duel_instance.rddl"),
                         vectorized=False)

    total_bad = 0
    for name in SCENARIOS:
        fixture = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
        state, _ = env.reset()
        problems = []

        for frame in fixture["frames"]:
            if frame["frame"] == -1:  # initial snapshot, before any tick
                continue

            action = _noop()
            for side, key in (("a", "agent_action"), ("b", "opponent_action")):
                fluent = ACTION[frame[key]]
                if fluent:
                    action[f"{fluent}___{side}"] = True

            print(action)

            state, _reward, terminated, _truncated, _ = env.step(action)

            expected = {"a": frame["agent"], "b": frame["opponent"]}
            for side in ("a", "b"):
                got = (state[f"curtask___{side}"],
                       int(state[f"foff___{side}"][1:]),
                       state[f"hp___{side}"],
                       state[f"stam___{side}"])
                want = (TASK[expected[side]["task"]],
                        expected[side]["frame_offset"],
                        expected[side]["hp"],
                        expected[side]["stamina"])
                if got != want:
                    problems.append(
                        f"    frame {frame['frame']:2d} side {side}: "
                        f"rddl={got}  python={want}")

            if terminated:
                break

        n_frames = len(fixture["frames"]) - 1
        status = "MATCH" if not problems else f"{len(problems)} MISMATCHES"
        print(f"[{name}] {status}  ({n_frames} frames x 2 fighters)")
        for line in problems:
            print(line)
        total_bad += len(problems)

    env.close()
    print(f"\ntotal mismatches: {total_bad}")
    return 1 if total_bad else 0


if __name__ == "__main__":
    sys.exit(main())
