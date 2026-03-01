from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple, Callable, Dict, List


class Responses(IntEnum):
    NONE = 0
    HAS_ATTACKED = 1
    HAS_BEEN_ATTACKED = 2
    HAS_BLOCKED = 3
    HAS_BEEN_BLOCKED = 4
    HAS_PARRIED = 5
    HAS_BEEN_PARRIED = 6
    DEAD = 7
    WON = 8
    HAS_RIPOSTED = 9
    HAS_BEEN_RIPOSTED = 10
    HAS_DEFENSE_BROKEN = 11
    HAS_BEEN_DEFENSE_BROKEN = 12

class Events(IntEnum):
    NONE = 0
    ATTACK = 1
    BLOCK = 2
    PARRY = 3
    DEAD = 4
    ANY = 6
    CRITICAL_ATTACK = 7

@dataclass(frozen=True)
class Event:
    type: Events
    value: int = 0

@dataclass(frozen=True)
class Response:
    type: Responses
    value: int = 0

Key = Tuple[Events, Events]

Predicate = Callable[[Event, Event], bool]
Emitter   = Callable[[Event, Event], Tuple[Response, Response]]

@dataclass(frozen=True)
class Rule:
    when: Predicate
    emit: Emitter

ResolutionTable = Dict[Key, List[Rule]]

def resolution(t: Responses, v: int = 0) -> Response:
    return Response(t, v)

resolution_table: ResolutionTable = {
    (Events.DEAD, Events.ANY): [
        Rule(
            when=lambda a, b: True,
            emit=lambda a, b: (resolution(Responses.DEAD), resolution(Responses.WON)),
        )
    ],

    (Events.ATTACK, Events.NONE): [
        Rule(
            when=lambda a, b: True,
            emit=lambda a, b: (resolution(Responses.HAS_ATTACKED, a.value),
                               resolution(Responses.HAS_BEEN_ATTACKED, a.value)),
        )
    ],

    (Events.ATTACK, Events.PARRY): [
        Rule(
            when=lambda a, b: True,
            emit=lambda a, b: (resolution(Responses.HAS_BEEN_PARRIED, a.value),
                               resolution(Responses.HAS_PARRIED, a.value)),
        )
    ],

    (Events.ATTACK, Events.BLOCK): [
        Rule(
            when=lambda a, b: a.value <= b.value,
            emit=lambda a, b: (resolution(Responses.HAS_BEEN_BLOCKED, a.value),
                               resolution(Responses.HAS_BLOCKED, a.value)),
        ),
        Rule(
            when=lambda a, b: a.value > b.value,
            emit=lambda a, b: (resolution(Responses.HAS_DEFENSE_BROKEN, a.value - b.value),
                               resolution(Responses.HAS_BEEN_DEFENSE_BROKEN, a.value - b.value)),
        ),
    ],
}