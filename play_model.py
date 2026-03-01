import time
import pygame
import numpy as np
from stable_baselines3 import PPO

from fight_env.inventory.armour import ArmourTypes
from fight_env.inventory.shields import Shields
from fight_env.inventory.weapons import Weapons
from fight_env.state.actions import ActionType
from fight_env.bots.aggressive import Aggressive
from fight_env.config import FRAME_DURATION
from fight_env.fight import Fight
from fight_env.gym_env import ACTION_TO_IDX, AGENT_ACTIONS
from fight_env.state.state import State
from fight_env.ui.render import Render


model = PPO.load("fight_ppo")

fighter1 = State(name="fighter1")
fighter1.stats.armour = ArmourTypes.LIGHT_ARMOUR
fighter1.stats.shield = Shields.BUCKLER
fighter1.stats.weapon = Weapons.GLADIUS

fighter2 = State(name="fighter2")
fighter2.stats.armour = ArmourTypes.LIGHT_ARMOUR
fighter2.stats.shield = Shields.BUCKLER
fighter2.stats.weapon = Weapons.GLADIUS

fight = Fight(fighter1, fighter2)
bot = Aggressive(fighter2, fighter1)
render = Render(fighter1, fighter2)


def get_obs():
    return np.array([
        fighter1.stamina,
        ACTION_TO_IDX.get(fighter1.current_action, 0),
        fighter1.current_action_frame,
        ACTION_TO_IDX.get(fighter2.current_action, 0),
        fighter2.current_action_frame,
    ], dtype=np.float32)


dt = time.perf_counter()
threshold = (dt * 1000) + FRAME_DURATION

while not fighter1.is_dead and not fighter2.is_dead:
    render.handle_input()
    dt = time.perf_counter()
    if (dt * 1000) > threshold:
        threshold += FRAME_DURATION

        # Model picks action
        obs = get_obs()
        action, _ = model.predict(obs, deterministic=True)
        agent_action = AGENT_ACTIONS[int(action)]
        if agent_action != ActionType.NONE:
            fighter1.request_action(agent_action)

        bot.next_move()
        fight.update_state()
        render.draw()
        fight.resolve_combat()
    else:
        time.sleep(0.001)

# Wait for key press before closing
waiting = True
while waiting:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
            waiting = False