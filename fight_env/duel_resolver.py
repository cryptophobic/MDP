from typing import Tuple, List

from fight_env.player.events import Event, Response, Events, resolution_table, Responses

def _resolve(event1: Event, event2: Event) -> Tuple[Response, Response]:
    for events_tuple in [
        (event1.type, event2.type),
        (event1.type, Events.ANY)]:
        rules = resolution_table.get(events_tuple)
        if rules is not None:
            for rule in rules:
                if rule.when(event1, event2):
                    return rule.emit(event1, event2)

    return Response(Responses.NONE), Response(Responses.NONE)

def resolve_duelists(event1: Event, event2: Event) -> Tuple[List[Response], List[Response]]:
    f1_res, f2_res = _resolve(event1, event2)
    f2_res2, f1_res2 = _resolve(event2, event1)

    return [f1_res, f1_res2], [f2_res, f2_res2]


