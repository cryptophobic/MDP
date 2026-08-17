"""
Reference-trajectory dumper for the Python combat core.

Purpose: produce a deterministic, engine-independent "ground truth" of the
fight simulation that the C# (Unity) port must reproduce frame-for-frame.

Determinism: both fighters are driven by a FIXED per-frame action script
(the scripted `Aggressive` bot is NOT used, since it calls random.random()).
This isolates the parity check to the pure combat core -- tasks_data,
resolution_table and the Orchestrator.flow() pipeline.

Output: parity/trajectories/<name>.json

Run:  python -m parity.dump_trajectory
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from fight_env.inventory.armour import ArmourTypes
from fight_env.inventory.shields import Shields
from fight_env.inventory.weapons import Weapons
from fight_env.orchestrator.orchestrator import Orchestrator
from fight_env.player.player import Player
from fight_env.player.refs.intents import ActionType
from fight_env.player.refs.tasks import FighterTask

# Same compact ActionType -> observation index mapping used by FightEnv._get_obs.
# Kept here verbatim so the fixture is self-contained and the C# port has a
# single reference to mirror.
ACTION_TO_IDX: Dict[FighterTask, int] = {
    FighterTask.NONE: 0,
    FighterTask.FIGHTING_STANCE: 1,
    FighterTask.ATTACK_1: 2,
    FighterTask.DEFENSE: 3,
    FighterTask.PARRY: 4,
    FighterTask.STUNNED: 5,
    FighterTask.HURT: 6,
    FighterTask.RIPOSTE: 7,
    FighterTask.DEAD: 8,
}

# Short aliases for writing scripts compactly.
_N = ActionType.NONE
_A = ActionType.ATTACK
_B = ActionType.BLOCK
_P = ActionType.PARRY


def _make_player(name: str) -> Player:
    """Same loadout as FightEnv.reset() so trajectories are comparable."""
    p = Player(name=name)
    p.set_armour(ArmourTypes.LIGHT_ARMOUR)
    p.set_shield(Shields.BUCKLER)
    p.set_weapon(Weapons.GLADIUS)
    return p


def _observation(agent: Player, opponent: Player) -> List[float]:
    """Replica of FightEnv._get_obs -- the 7-float vector the policy sees.

    Included in the fixture so the C# port's observation encoder is checked
    too, not just internal game state (an obs mismatch silently breaks Sentis
    inference)."""
    am = agent._model
    om = opponent._model
    return [
        float(am.hp),
        float(am.stamina),
        float(ACTION_TO_IDX.get(am.task, 0)),
        float(am.timeline.frame_offset),
        float(om.hp),
        float(ACTION_TO_IDX.get(om.task, 0)),
        float(om.timeline.frame_offset),
    ]


def _record_fighter(p: Player) -> Dict[str, Any]:
    m = p._model
    return {
        "hp": m.hp,
        "stamina": m.stamina,
        "task": int(m.task),
        "frame_offset": m.timeline.frame_offset,
        "is_dead": m.is_dead,
    }


def _record_responses(p: Player) -> List[List[int]]:
    return [[int(r.type), int(r.value)] for r in p._model.current_responses]


def run_scenario(name: str, agent_script: List[ActionType],
                 opponent_script: List[ActionType]) -> Dict[str, Any]:
    """Replay a fixed action script through both fighters and record every frame.

    Mirrors the FightEnv.step ordering: request intents on both fighters, then
    run one Orchestrator.flow(). Scripts may differ in length; a missing entry
    is treated as NONE (no intent that frame)."""
    agent = _make_player("agent")
    opponent = _make_player("opponent")
    orchestrator = Orchestrator([agent, opponent])

    n_frames = max(len(agent_script), len(opponent_script))
    frames: List[Dict[str, Any]] = []

    # Frame 0: initial state before any tick, so the C# port can align from t=0.
    frames.append({
        "frame": -1,
        "agent": _record_fighter(agent),
        "opponent": _record_fighter(opponent),
        "obs": _observation(agent, opponent),
        "agent_responses": [],
        "opponent_responses": [],
    })

    for i in range(n_frames):
        a = agent_script[i] if i < len(agent_script) else _N
        b = opponent_script[i] if i < len(opponent_script) else _N

        if a != ActionType.NONE:
            agent.request_intent(a)
        if b != ActionType.NONE:
            opponent.request_intent(b)

        orchestrator.flow()

        frames.append({
            "frame": i,
            "agent_action": int(a),
            "opponent_action": int(b),
            "agent": _record_fighter(agent),
            "opponent": _record_fighter(opponent),
            "obs": _observation(agent, opponent),
            "agent_responses": _record_responses(agent),
            "opponent_responses": _record_responses(opponent),
        })

        if agent.is_dead or opponent.is_dead:
            break

    return {
        "name": name,
        "loadout": {"armour": "LIGHT_ARMOUR", "shield": "BUCKLER", "weapon": "GLADIUS"},
        "agent_script": [int(x) for x in agent_script],
        "opponent_script": [int(x) for x in opponent_script],
        "frames": frames,
    }


# Fixed scenarios chosen to exercise the resolution_table branches the C# port
# must reproduce: plain hit, hit-vs-block, hit-vs-parry -> stun -> riposte window.
SCENARIOS = {
    # Agent attacks into an idle opponent -> HAS_ATTACKED / HAS_BEEN_ATTACKED.
    "attack_vs_idle": (
        [_A, _N, _N, _N, _A, _N, _N, _N],
        [_N, _N, _N, _N, _N, _N, _N, _N],
    ),
    # Opponent blocks the agent's attack -> HAS_BLOCKED / HAS_BEEN_BLOCKED path.
    "attack_vs_block": (
        [_A, _N, _N, _N, _N, _N],
        [_N, _B, _B, _B, _N, _N],
    ),
    # Opponent parries -> agent stunned -> opponent ripostes into the window.
    "parry_then_riposte": (
        [_A, _N, _N, _N, _N, _N, _N, _N, _N, _N],
        [_N, _P, _N, _N, _A, _N, _N, _N, _N, _N],
    ),
}


def main() -> None:
    out_dir = Path(__file__).parent / "trajectories"
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, (agent_script, opponent_script) in SCENARIOS.items():
        data = run_scenario(name, agent_script, opponent_script)
        out_path = out_dir / f"{name}.json"
        out_path.write_text(json.dumps(data, indent=2))
        n = len(data["frames"]) - 1  # minus the t=-1 initial snapshot
        last = data["frames"][-1]
        print(f"[{name}] {n} frames -> {out_path.name}  "
              f"(agent hp={last['agent']['hp']} sta={last['agent']['stamina']}, "
              f"opp hp={last['opponent']['hp']} sta={last['opponent']['stamina']})")


if __name__ == "__main__":
    main()