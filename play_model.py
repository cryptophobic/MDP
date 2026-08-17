import time
import pygame
import numpy as np
from stable_baselines3 import PPO

from fight_env.inventory.armour import ArmourTypes
from fight_env.inventory.shields import Shields
from fight_env.inventory.weapons import Weapons
from fight_env.bots.aggressive import Aggressive
from fight_env.config import FRAME_DURATION
from fight_env.gym_env import ACTION_TO_IDX, AGENT_ACTIONS
from fight_env.orchestrator.orchestrator import Orchestrator
from fight_env.player.player import Player
from fight_env.player.refs.intents import ActionType
from fight_env.ui.render import Render


model1 = PPO.load("fight_ppo")
model2 = PPO.load("fight_ppo")

fighter1 = Player(name="fighter1")
fighter1.set_armour(ArmourTypes.LIGHT_ARMOUR)
fighter1.set_shield(Shields.BUCKLER)
fighter1.set_weapon(Weapons.GLADIUS)

fighter2 = Player(name="opponent")
fighter2.set_armour(ArmourTypes.LIGHT_ARMOUR)
fighter2.set_shield(Shields.BUCKLER)
fighter2.set_weapon(Weapons.GLADIUS)

orchestrator = Orchestrator([fighter1, fighter2])
bot = Aggressive(fighter2, fighter1)
render = Render(fighter1, fighter2)


def get_obs(f1, f2):
    opponent_snapshot = f2.make_snapshot()
    agent_snapshot = f1.make_snapshot()
    return np.array([
        agent_snapshot.hp,
        agent_snapshot.stamina,
        ACTION_TO_IDX.get(agent_snapshot.task, 0),
        agent_snapshot.frame_offset,
        opponent_snapshot.hp,
        ACTION_TO_IDX.get(opponent_snapshot.task, 0),
        opponent_snapshot.frame_offset,
    ], dtype=np.float32)


dt = time.perf_counter()
threshold = (dt * 1000) + FRAME_DURATION

strike = False
rng = np.random.default_rng(42)

while not fighter1.is_dead and not fighter2.is_dead:
    render.handle_input()
    dt = time.perf_counter()
    if (dt * 1000) > threshold:
        threshold += FRAME_DURATION

        # Model picks action
        obs = get_obs(fighter1, fighter2)
        action, _ = model1.predict(obs, deterministic=True)
        agent_action = AGENT_ACTIONS[int(action)]
        if agent_action != ActionType.NONE:
            fighter1.request_intent(agent_action)

        obs = get_obs(fighter2, fighter1)
        action, _ = model2.predict(obs, deterministic=True)
        agent_action = AGENT_ACTIONS[int(action)]
        if agent_action != ActionType.NONE:
            fighter2.request_intent(agent_action)

        bot.next_move()

        orchestrator.flow()
        render.draw()
    else:
        time.sleep(0.001)

# Wait for key press before closing
waiting = True
while waiting:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
            waiting = False