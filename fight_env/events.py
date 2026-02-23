from dataclasses import dataclass
from enum import Enum

class Responses(Enum):
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

class Events(Enum):
    NONE = 0
    ATTACK = 1
    BLOCK = 2
    PARRY = 3
    DEAD = 4
    RIPOSTE = 5

@dataclass
class Event:
    type: Events
    value: int = 0
