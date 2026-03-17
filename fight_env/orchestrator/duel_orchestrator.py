from typing import Tuple

from fight_env.player.player import Player
from fight_env.player.refs.events import Event, Response, Events, resolution_table, Responses


def _resolve_duelists(event1: Event, event2: Event) -> Tuple[Response, Response]:
    for events_tuple in [
        (event1.type, event2.type),
        (event1.type, Events.ANY)]:
        rules = resolution_table.get(events_tuple)
        if rules is not None:
            for rule in rules:
                if rule.when(event1, event2):
                    return rule.emit(event1, event2)

    return Response(Responses.NONE), Response(Responses.NONE)


class DuelOrchestrator:
    def __init__(self, fighter1: Player, fighter2: Player):
        self.fighter1 = fighter1
        self.fighter2 = fighter2

    def resolve(self):
        event1 = self.fighter1.event()
        event2 = self.fighter2.event()

        f1_res, f2_res = _resolve_duelists(event1, event2)
        f2_res2, f1_res2 = _resolve_duelists(event2, event1)

        f1_responses, f2_responses = [f1_res, f1_res2], [f2_res, f2_res2]

        self.fighter1.process_responses(f1_responses)
        self.fighter2.process_responses(f2_responses)

        return f1_responses, f2_responses
