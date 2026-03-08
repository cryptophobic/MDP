from dataclasses import dataclass

class ActionType(IntEnum):
    NONE = 0
    ATTACK = 1
    BLOCK = 2
    PARRY = 3

@dataclass(frozen=True)
class Intent:
    action: ActionType
    ttl: int = 0
