from dataclasses import dataclass
from enum import Enum
from typing import List

from fighter.fighter_env import ActionType

IDLE = 0
ATTACK_1 = 1
ATTACK_2 = 2
ATTACK_3 = 3
DEAD = 4
DEFENSE = 5
FIGHTING_STANCE = 6
HURT = 7
PARRY = 8
POWER_PUNCH_1 = 9
POWER_PUNCH_2 = 10
PRICK = 11
ROLLING = 12
RUN = 13
SHIELD_STRIKE = 14
WALK = 15

@dataclass
class ActionData:
    action_type: int
    animation: str

actions: List[ActionData] = [
    ActionData(IDLE, "fighter/resources/Animations/Idle.png"),
    ActionData(ATTACK_1, "fighter/resources/Animations/Attack_1.png")
]