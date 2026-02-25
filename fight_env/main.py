from typing import Tuple

from fight_env.actions import ActionType
from fight_env.bots.aggressive import Aggressive
from fight_env.config import FRAME_DURATION
from fight_env.events import Events, Responses, Event
from fight_env.ui.render import Render
from fight_env.state import State
from config import RL
import time
import pygame


def _resolve_fighters(event1: Event, event2: Event) -> Tuple[Responses, Responses]:
    event1_res = Responses.NONE
    event2_res = Responses.NONE

    if event1.type == Events.DEAD:
        event1_res = Responses.DEAD
        event2_res = Responses.WON

    if event1.type == Events.ATTACK or event1.type == Events.RIPOSTE:
        match event2.type:
            case Events.BLOCK:
                event1_res = Responses.HAS_BEEN_BLOCKED
                event2_res = Responses.HAS_BLOCKED
            case Events.PARRY:
                event1_res = Responses.HAS_BEEN_PARRIED
                event2_res = Responses.HAS_PARRIED
            case _:
                if event1.type == Events.RIPOSTE:
                    event1_res = Responses.HAS_RIPOSTED
                    event2_res = Responses.HAS_BEEN_RIPOSTED
                else:
                    event1_res = Responses.HAS_ATTACKED
                    event2_res = Responses.HAS_BEEN_ATTACKED

    return event1_res, event2_res

class FightingGame:
    def __init__(self):
        self.fighter1 = State(name="fighter1")
        self.fighter2 = State(name="fighter2")
        self.aggressive_bot = Aggressive(self.fighter2, self.fighter1)
        self.render = None
        if not RL:
            self.render = Render(self.fighter1, self.fighter2)

    def update_state(self):
        self.aggressive_bot.next_move()
        self.fighter1.resolve_next_action()
        self.fighter2.resolve_next_action()

        fighter1_stunned = self.fighter1.action_candidate == ActionType.STUN or (self.fighter1.current_action == ActionType.STUN and self.fighter1.action_candidate == ActionType.NONE)
        fighter2_stunned = self.fighter2.action_candidate == ActionType.STUN or (self.fighter2.current_action == ActionType.STUN and self.fighter2.action_candidate == ActionType.NONE)

        if fighter1_stunned and self.fighter2.action_candidate == ActionType.ATTACK_1:
            self.fighter2.action_candidate = ActionType.RIPOSTE

        if fighter2_stunned and self.fighter1.action_candidate == ActionType.ATTACK_1:
            self.fighter1.action_candidate = ActionType.RIPOSTE

        self.fighter1.apply_action()
        self.fighter2.apply_action()

    def step(self) -> None:

        fighter1_event = self.fighter1.get_current_events()
        fighter2_event = self.fighter2.get_current_events()

        fighter1_res, fighter2_res = _resolve_fighters(fighter1_event, fighter2_event)

        self.fighter1.process_response(fighter1_res)
        self.fighter2.process_response(fighter2_res)

        fighter2_res, fighter1_res = _resolve_fighters(fighter2_event, fighter1_event)

        self.fighter1.process_response(fighter1_res)
        self.fighter2.process_response(fighter2_res)

    def run(self):
        if not RL:
            dt = time.perf_counter()
            threshold = (dt * 1000) + FRAME_DURATION
            while not self.fighter1.is_dead and not self.fighter2.is_dead:
                self.render.handle_input()
                dt = time.perf_counter()
                if (dt * 1000) > threshold:
                    threshold += FRAME_DURATION
                    self.update_state()
                    self.render.draw()
                    self.step()
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