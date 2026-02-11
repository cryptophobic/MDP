from enum import Enum

class Events(Enum):
    ATTACK = 1
    HURT = 2
    BLOCK = 3
    BLOCKED = 4
    PARRY = 5
    PARRIED = 6

class Event:
    type: Events
    value: int
