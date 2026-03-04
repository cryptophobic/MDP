from fight_env.bots.aggressive import Aggressive
from fight_env.config import FRAME_DURATION
from fight_env.fight import Fight
from fight_env.inventory.armour import Armour, ArmourTypes
from fight_env.inventory.shields import Shields
from fight_env.inventory.weapons import Weapons
from fight_env.ticker import ticker
from fight_env.ui.render import Render
from fight_env.state.state import State
from config import RL
import time
import pygame


class FightingGame:
    def __init__(self):

        self.fighter1 = State(name="fighter1")
        self.fighter1.stats.armour = ArmourTypes.LIGHT_ARMOUR
        self.fighter1.stats.shield = Shields.BUCKLER
        self.fighter1.stats.weapon = Weapons.GLADIUS
        self.fighter2 = State(name="fighter2")
        self.fighter2.stats.armour = ArmourTypes.LIGHT_ARMOUR
        self.fighter2.stats.shield = Shields.BUCKLER
        self.fighter2.stats.weapon = Weapons.GLADIUS
        self.fight = Fight(self.fighter1, self.fighter2)
        self.aggressive_bot = Aggressive(self.fighter2, self.fighter1)
        self.render = None
        if not RL:
            self.render = Render(self.fighter1, self.fighter2)

    def run(self):
        if not RL:
            dt = time.perf_counter()
            threshold = (dt * 1000) + FRAME_DURATION
            while not self.fighter1.is_dead and not self.fighter2.is_dead:
                self.render.handle_input()
                dt = time.perf_counter()
                if (dt * 1000) > threshold:
                    ticker.tick()
                    threshold += FRAME_DURATION
                    self.aggressive_bot.next_move()
                    self.fight.update_state()
                    self.render.draw()
                    self.fight.resolve_combat()
                else:
                    time.sleep(0.001)
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                        waiting = False

if __name__ == "__main__":
    game = FightingGame()
    game.run()

# claude --resume 88901ca1-5626-4008-83f2-987e1f1785bf