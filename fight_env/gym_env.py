from typing import Optional, Dict, Any

import gymnasium as gym
from gymnasium import spaces
import numpy as np

from fight_env.config import DEFAULT_HP, STAMINA_BOTTOM_LIMIT, DEFAULT_STAMINA
from fight_env.inventory.armour import ArmourTypes
from fight_env.inventory.shields import Shields
from fight_env.inventory.weapons import Weapons
from fight_env.bots.aggressive import Aggressive
from fight_env.orchestrator.orchestrator import Orchestrator

from fight_env.player.player import Player
from fight_env.player.refs.events import Responses
from fight_env.player.refs.intents import ActionType
from fight_env.player.refs.tasks import FighterTask

# Compact mapping: ActionType -> 0..8 for observation space
ACTION_TO_IDX = {
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

# Agent actions -> ActionType
AGENT_ACTIONS = [
    ActionType.NONE,      # 0: do nothing
    ActionType.ATTACK,  # 1: attack
    ActionType.BLOCK,   # 2: block
    ActionType.PARRY,     # 3: parry
]


class FightEnv(gym.Env):
    """
    Gymnasium env for the fighting game.

    Observation (7 floats):
        [my_hp, my_stamina, my_action, my_frame, app_hp, opp_action, opp_frame]

    Actions (4 discrete):
        0=NONE, 1=ATTACK_1, 2=DEFENSE, 3=PARRY
    """

    metadata = {"render_modes": [None]}

    def __init__(self, max_steps: int = 500):
        super().__init__()

        self.observation_space = spaces.Box(
            low=np.array([0, STAMINA_BOTTOM_LIMIT, 0, 0, 0, 0, 0], dtype=np.float32),
            high=np.array([DEFAULT_HP, DEFAULT_STAMINA, 8, 8, DEFAULT_HP, 8, 8], dtype=np.float32),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(4)

        self.max_steps = max_steps
        self.agent: Optional[Player] = None
        self.opponent: Optional[Player] = None
        self.orchestrator: Optional[Orchestrator] = None
        self.bot: Optional[Aggressive] = None
        self.step_count = 0

    def _get_obs(self) -> np.ndarray:
        opponent_model = self.opponent._model
        agent_model = self.agent._model
        return np.array([
            agent_model.hp,
            agent_model.stamina,
            ACTION_TO_IDX.get(agent_model.task, 0),
            agent_model.timeline.frame_offset,
            opponent_model.hp,
            ACTION_TO_IDX.get(opponent_model.task, 0),
            opponent_model.timeline.frame_offset,
        ], dtype=np.float32)

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None):
        super().reset(seed=seed)
        self.agent = Player(name="agent")
        self.agent.set_armour(ArmourTypes.LIGHT_ARMOUR)
        self.agent.set_shield(Shields.BUCKLER)
        self.agent.set_weapon(Weapons.GLADIUS)

        self.opponent = Player(name="opponent")
        self.opponent.set_armour(ArmourTypes.LIGHT_ARMOUR)
        self.opponent.set_shield(Shields.BUCKLER)
        self.opponent.set_weapon(Weapons.GLADIUS)

        self.orchestrator = Orchestrator([self.agent, self.opponent])
        self.bot = Aggressive(self.opponent, self.agent)
        self.step_count = 0
        return self._get_obs(), {}

    def step(self, action: int):
        self.step_count += 1

        # 1. Set actions: agent's choice + bot's choice
        agent_action = AGENT_ACTIONS[action]
        if agent_action != ActionType.NONE:
            self.agent.request_intent(agent_action)
        self.bot.next_move()

        # 2. Update state (resolve, riposte promotion, apply)
        (f1_res, f2_res), (f1_res2, f2_res2) = self.orchestrator.flow()

        # 3. Resolve combat and get responses
        model = self.agent._model
        stats = model.stats
        base_damage = stats.weapon.base_damage
        critical_damage = stats.weapon.critical_damage

        # 4. Compute reward (f1 = agent, f2 = opponent)
        reward = 0.0
        if f1_res.type == Responses.HAS_ATTACKED:
            reward += 0.3 if f1_res.value == base_damage else 1.0
        if f1_res.type == Responses.HAS_PARRIED:
            reward += 0.5
        if f1_res2.type == Responses.HAS_BEEN_ATTACKED:
            reward -= 0.3 if f1_res2.value == base_damage else 1.0

        # 5. Check terminal conditions
        terminated = self.agent.is_dead or self.opponent.is_dead
        truncated = self.step_count >= self.max_steps

        if self.opponent.is_dead:
            reward += 5.0
        if self.agent.is_dead:
            reward -= 5.0

        return self._get_obs(), reward, terminated, truncated, {}