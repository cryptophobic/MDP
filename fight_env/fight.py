from typing import Tuple

from fight_env.state.actions import ActionType
from fight_env.state.events import Events, Responses, Event, resolution_table, Response
from fight_env.state.state import State

def resolve_fighters(event1: Event, event2: Event) -> Tuple[Response, Response]:
    for events_tuple in [
        (event1.type, event2.type),
        (event1.type, Events.ANY)]:
        rules = resolution_table.get(events_tuple)
        if rules is not None:
            for rule in rules:
                if rule.when(event1, event2):
                    return rule.emit(event1, event2)

    return Response(Responses.NONE), Response(Responses.NONE)


class Fight:
    def __init__(self, fighter1: State, fighter2: State):
        self.fighter1 = fighter1
        self.fighter2 = fighter2

    def update_state(self):
        self.fighter1.resolve_next_action()
        self.fighter2.resolve_next_action()

        if self.fighter1.current_action == ActionType.STUNNED:
            self.fighter2.request_alternative(ActionType.RIPOSTE)

        if self.fighter2.current_action == ActionType.STUNNED:
            self.fighter1.request_alternative(ActionType.RIPOSTE)

        self.fighter1.apply_action()
        self.fighter2.apply_action()

    def resolve_combat(self) -> Tuple[Response, Response, Response, Response]:
        fighter1_event = self.fighter1.get_current_events()
        fighter2_event = self.fighter2.get_current_events()

        f1_res, f2_res = resolve_fighters(fighter1_event, fighter2_event)
        self.fighter1.process_response(f1_res)
        self.fighter2.process_response(f2_res)

        f2_res2, f1_res2 = resolve_fighters(fighter2_event, fighter1_event)
        self.fighter1.process_response(f1_res2)
        self.fighter2.process_response(f2_res2)

        return f1_res, f1_res2, f2_res, f2_res2