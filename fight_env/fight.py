from typing import Tuple

from fight_env.actions import ActionType
from fight_env.events import Events, Responses, Event
from fight_env.state import State


def resolve_fighters(event1: Event, event2: Event) -> Tuple[Responses, Responses]:
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


class Fight:
    def __init__(self, fighter1: State, fighter2: State):
        self.fighter1 = fighter1
        self.fighter2 = fighter2

    def update_state(self):
        self.fighter1.resolve_next_action()
        self.fighter2.resolve_next_action()

        fighter1_stunned = (
            self.fighter1.action_candidate == ActionType.STUN
            or (self.fighter1.current_action == ActionType.STUN and self.fighter1.action_candidate == ActionType.NONE)
        )
        fighter2_stunned = (
            self.fighter2.action_candidate == ActionType.STUN
            or (self.fighter2.current_action == ActionType.STUN and self.fighter2.action_candidate == ActionType.NONE)
        )

        if fighter1_stunned and self.fighter2.action_candidate == ActionType.ATTACK_1:
            self.fighter2.action_candidate = ActionType.RIPOSTE

        if fighter2_stunned and self.fighter1.action_candidate == ActionType.ATTACK_1:
            self.fighter1.action_candidate = ActionType.RIPOSTE

        self.fighter1.apply_action()
        self.fighter2.apply_action()

    def resolve_combat(self) -> Tuple[Responses, Responses, Responses, Responses]:
        fighter1_event = self.fighter1.get_current_events()
        fighter2_event = self.fighter2.get_current_events()

        f1_res, f2_res = resolve_fighters(fighter1_event, fighter2_event)
        self.fighter1.process_response(f1_res)
        self.fighter2.process_response(f2_res)

        f2_res2, f1_res2 = resolve_fighters(fighter2_event, fighter1_event)
        self.fighter1.process_response(f1_res2)
        self.fighter2.process_response(f2_res2)

        return f1_res, f1_res2, f2_res, f2_res2