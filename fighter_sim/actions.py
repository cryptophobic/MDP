from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

from fighter.events import Event, Events
from fighter.fighter_env import ActionType

class ActionTypes(Enum):
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
    action_type: ActionTypes
    animation: str
    total_frames: int
    interruptable: bool
    frame_events: Dict[int, List[Event]]

actions: Dict[ActionTypes, ActionData] = {
    ActionTypes.IDLE: ActionData(
        ActionTypes.IDLE,
        "Fighting_Stance.png",
        6,
        True,
        {}
    ),
    ActionTypes.ATTACK_1: ActionData(
        ActionTypes.ATTACK_1,
        "Attack_1.png",
        4,
        False,
        {
            2: [
                Event(Events.ATTACK, 1)
            ]
        },
    ),
    ActionTypes.PARRY: ActionData(
        ActionTypes.PARRY,
        "Parry.png",
        4,
        False,
        {}
    ),
    ActionTypes.DEFENSE: ActionData(
        ActionTypes.DEFENSE,
        "Defense.png",
        1,
        False,
        {}
    )
}