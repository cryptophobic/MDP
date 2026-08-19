"""Gymnasium environment backed by the RDDL model instead of fight_env.

Drop-in replacement for `fight_env.gym_env.FightEnv`: same Discrete(4) action
space, same 7-float observation vector, same scripted opponent.

The combat rules come from `duel_domain.rddl`; the opponent does NOT. Bots call
`random.random()` and are kept out of the formal core, exactly as they are kept
out of the C# port -- so `@b`'s action is computed in Python and handed to the
model through its action fluents, the same way `check_parity.py` feeds fixtures.

`Aggressive` is reused unmodified. It only ever calls two methods on the objects
it is constructed with -- `opponent.make_snapshot()` and
`player.request_intent(...)` -- so two small stand-ins are enough; nothing is
monkeypatched and `Player` is not involved.

Requires pyRDDLGym (not part of the project venv):  pip install pyRDDLGym
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import gymnasium as gym
import numpy as np
import pyRDDLGym
from gymnasium import spaces

from fight_env.bots.aggressive import Aggressive
from fight_env.config import DEFAULT_HP, DEFAULT_STAMINA, STAMINA_BOTTOM_LIMIT
# Reused rather than re-declared: the observation encoder already exists in four
# places (see CLAUDE.md) and must not gain a fifth.
from fight_env.gym_env import ACTION_TO_IDX, AGENT_ACTIONS
from fight_env.player.refs.intents import ActionType
from fight_env.player.refs.tasks import FighterTask

HERE = Path(__file__).parent
DOMAIN = HERE / "duel_domain.rddl"
INSTANCE = HERE / "duel_instance.rddl"

# RDDL `task` enum object -> FighterTask
RDDL_TASK_TO_FIGHTER_TASK = {
    "none": FighterTask.NONE,
    "stance": FighterTask.FIGHTING_STANCE,
    "attack1": FighterTask.ATTACK_1,
    "defense": FighterTask.DEFENSE,
    "stunned": FighterTask.STUNNED,
    "hurt": FighterTask.HURT,
    "parry": FighterTask.PARRY,
    "riposte": FighterTask.RIPOSTE,
    "dead": FighterTask.DEAD,
}

# ActionType -> the action fluent that carries it (NONE = no fluent set)
ACTION_TO_FLUENT = {
    ActionType.NONE: None,
    ActionType.ATTACK: "act_attack",
    ActionType.BLOCK: "act_block",
    ActionType.PARRY: "act_parry",
}


@dataclass
class BotSnapshot:
    """The four fields `Aggressive` actually reads off a PlayerSnapshot."""
    task: FighterTask
    frame_offset: int
    stamina: int
    max_stamina: int


class _Observed:
    """Stands in for the Player the bot watches."""

    def __init__(self):
        self.snapshot: Optional[BotSnapshot] = None

    def make_snapshot(self) -> BotSnapshot:
        return self.snapshot


class _Acting:
    """Stands in for the Player the bot controls; records the intent."""

    def __init__(self):
        self.action = ActionType.NONE

    def request_intent(self, action: ActionType, ttl: int = 1) -> None:
        self.action = action


class RDDLFightEnv(gym.Env):
    """Same contract as fight_env.gym_env.FightEnv, driven by the RDDL model.

    Observation (7 floats):
        [my_hp, my_stamina, my_action, my_frame, opp_hp, opp_action, opp_frame]
    Actions (4 discrete):
        0=NONE, 1=ATTACK, 2=BLOCK, 3=PARRY
    """

    metadata = {"render_modes": [None]}

    def __init__(self, max_steps: int = 500,
                 domain: Path = DOMAIN, instance: Path = INSTANCE):
        super().__init__()

        self.observation_space = spaces.Box(
            low=np.array([0, STAMINA_BOTTOM_LIMIT, 0, 0, 0, 0, 0], dtype=np.float32),
            high=np.array([DEFAULT_HP, DEFAULT_STAMINA, 8, 8, DEFAULT_HP, 8, 8], dtype=np.float32),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(4)

        self._env = pyRDDLGym.make(str(domain), str(instance), vectorized=False)
        self._max_stamina = int(self._env.model.non_fluents["MAXSTAM"])

        # the real bot, wired to stand-ins instead of Players
        self._acting = _Acting()
        self._observed = _Observed()
        self.bot = Aggressive(self._acting, self._observed)

        self.max_steps = max_steps
        self.step_count = 0
        self._state: Dict[str, Any] = {}

    # --------------------------------------------------------------- outcome
    @property
    def agent_is_dead(self) -> bool:
        return bool(self._state.get("dead___a", False))

    @property
    def opponent_is_dead(self) -> bool:
        return bool(self._state.get("dead___b", False))

    # ------------------------------------------------------------------ obs
    def _get_obs(self) -> np.ndarray:
        s = self._state
        return np.array([
            s["hp___a"],
            s["stam___a"],
            ACTION_TO_IDX.get(RDDL_TASK_TO_FIGHTER_TASK[s["curtask___a"]], 0),
            self._offset("a"),
            s["hp___b"],
            ACTION_TO_IDX.get(RDDL_TASK_TO_FIGHTER_TASK[s["curtask___b"]], 0),
            self._offset("b"),
        ], dtype=np.float32)

    def _offset(self, side: str) -> int:
        return int(self._state[f"foff___{side}"][1:])   # "@f3"/"f3" -> 3

    # ------------------------------------------------------------------ bot
    def _opponent_action(self) -> ActionType:
        """Run the real Aggressive over the current RDDL state.

        `next_move()` is called before the tick and reads a snapshot of its
        opponent (side @a) taken at that moment -- which is exactly the state
        this env is holding right now, before `step` advances it.
        """
        self._observed.snapshot = BotSnapshot(
            task=RDDL_TASK_TO_FIGHTER_TASK[self._state["curtask___a"]],
            frame_offset=self._offset("a"),
            stamina=int(self._state["stam___a"]),
            max_stamina=self._max_stamina,
        )
        self._acting.action = ActionType.NONE
        self.bot.next_move()
        return self._acting.action

    # ---------------------------------------------------------------- gym api
    def reset(self, *, seed: Optional[int] = None,
              options: Optional[Dict[str, Any]] = None):
        super().reset(seed=seed)
        self._state, _ = self._env.reset(seed=seed)
        self.step_count = 0
        return self._get_obs(), {}

    def step(self, action: int):
        self.step_count += 1

        rddl_action = {}
        agent_fluent = ACTION_TO_FLUENT[AGENT_ACTIONS[action]]
        if agent_fluent:
            rddl_action[f"{agent_fluent}___a"] = True
        opponent_fluent = ACTION_TO_FLUENT[self._opponent_action()]
        if opponent_fluent:
            rddl_action[f"{opponent_fluent}___b"] = True

        self._state, reward, terminated, _truncated, info = self._env.step(rddl_action)
        truncated = self.step_count >= self.max_steps

        return self._get_obs(), float(reward), bool(terminated), truncated, info

    def close(self):
        self._env.close()
