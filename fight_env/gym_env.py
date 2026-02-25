from typing import Optional, Dict, Any

import gymnasium as gym
from gymnasium import spaces
import numpy as np

from fight_env.actions import ActionType
from fight_env.bots.aggressive import Aggressive
from fight_env.events import Responses
from fight_env.fight import Fight
from fight_env.state import State


# Compact mapping: ActionType -> 0..8 for observation space
ACTION_TO_IDX = {
    ActionType.NONE: 0,
    ActionType.IDLE: 1,
    ActionType.ATTACK_1: 2,
    ActionType.DEFENSE: 3,
    ActionType.PARRY: 4,
    ActionType.STUN: 5,
    ActionType.HURT: 6,
    ActionType.RIPOSTE: 7,
    ActionType.DEAD: 8,
}

# Agent actions -> ActionType
AGENT_ACTIONS = [
    ActionType.NONE,      # 0: do nothing
    ActionType.ATTACK_1,  # 1: attack
    ActionType.DEFENSE,   # 2: block
    ActionType.PARRY,     # 3: parry
]


class FightEnv(gym.Env):
    """
    Gymnasium env for the fighting game.

    Observation (5 floats):
        [my_stamina, my_action, my_frame, opp_action, opp_frame]

    Actions (4 discrete):
        0=NONE, 1=ATTACK_1, 2=DEFENSE, 3=PARRY
    """

    metadata = {"render_modes": [None]}

    def __init__(self, max_steps: int = 500):
        super().__init__()

        self.observation_space = spaces.Box(
            low=np.array([-8, 0, 0, 0, 0], dtype=np.float32),
            high=np.array([20, 8, 8, 8, 8], dtype=np.float32),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(4)

        self.max_steps = max_steps
        self.agent: Optional[State] = None
        self.opponent: Optional[State] = None
        self.fight: Optional[Fight] = None
        self.bot: Optional[Aggressive] = None
        self.step_count = 0

    def _get_obs(self) -> np.ndarray:
        return np.array([
            self.agent.stamina,
            ACTION_TO_IDX.get(self.agent.current_action, 0),
            self.agent.current_action_frame,
            ACTION_TO_IDX.get(self.opponent.current_action, 0),
            self.opponent.current_action_frame,
        ], dtype=np.float32)

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None):
        super().reset(seed=seed)
        self.agent = State(name="agent")
        self.opponent = State(name="opponent")
        self.fight = Fight(self.agent, self.opponent)
        self.bot = Aggressive(self.opponent, self.agent)
        self.step_count = 0
        return self._get_obs(), {}

    def step(self, action: int):
        self.step_count += 1

        # 1. Set actions: agent's choice + bot's choice
        agent_action = AGENT_ACTIONS[action]
        if agent_action != ActionType.NONE:
            self.agent.request_action(agent_action)
        self.bot.next_move()

        # 2. Update state (resolve, riposte promotion, apply)
        self.fight.update_state()

        # 3. Resolve combat and get responses
        f1_res, f1_res2, f2_res, f2_res2 = self.fight.resolve_combat()

        # 4. Compute reward (f1 = agent, f2 = opponent)
        reward = 0.0
        if f1_res == Responses.HAS_ATTACKED:
            reward += 0.3
        if f1_res == Responses.HAS_RIPOSTED:
            reward += 1.0
        if f1_res == Responses.HAS_PARRIED:
            reward += 0.5
        if f1_res2 == Responses.HAS_BEEN_ATTACKED:
            reward -= 0.3
        if f1_res2 == Responses.HAS_BEEN_RIPOSTED:
            reward -= 1.0

        # 5. Check terminal conditions
        terminated = self.agent.is_dead or self.opponent.is_dead
        truncated = self.step_count >= self.max_steps

        if self.opponent.is_dead:
            reward += 5.0
        if self.agent.is_dead:
            reward -= 5.0

        return self._get_obs(), reward, terminated, truncated, {}