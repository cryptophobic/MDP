from dataclasses import dataclass
from enum import IntEnum

class Move(IntEnum):
    IDLE=0; LIGHT=1; HEAVY=2; BLOCK=3; PARRY=4; RIPOSTE=5

@dataclass(frozen=True)
class MoveSpec:
    startup: int
    active: int
    recovery: int
    damage: int
    stun: int
    blockable: bool = True
    parryable: bool = True

MOVES = {
    Move.LIGHT:  MoveSpec(startup=1, active=1, recovery=1, damage=1, stun=1),
    Move.HEAVY:  MoveSpec(startup=2, active=1, recovery=2, damage=2, stun=2),
    Move.BLOCK:  MoveSpec(startup=0, active=999, recovery=0, damage=0, stun=0),
    # ...
}
