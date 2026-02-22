from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple

from fight_env.animation import Animation
from fight_env.config import RL
from fight_env.events import Event, Events


class ActionType(Enum):
    IDLE = 0
    ATTACK_1 = 1
    ATTACK_2 = 2
    ATTACK_3 = 3
    DEAD = 4
    DEFENSE = 5
    STUN = 6
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
    action_type: ActionType
    animation: Optional[Animation]
    frame_count: int
    stamina_cost: int = 0
    stamina_cost_frame: int = 0
    loop: bool = False
    interruptible: bool = False
    frame_events: Dict[int, Tuple[Event]] = field(default_factory=dict)

available_actions: Dict[ActionType, ActionData] = {
    ActionType.STUN: ActionData(
        action_type=ActionType.STUN,
        animation=None if RL else Animation(
            name="stun",
            sprite_file_name="Idle.png",
        ),
        stamina_cost_frame=-1,
        interruptible = True,
        frame_count=6,
    ),
    ActionType.IDLE: ActionData(
        action_type=ActionType.IDLE,
        animation=None if RL else Animation(
            name="stance",
            sprite_file_name="Fighting_Stance.png",
        ),
        loop = True,
        interruptible = True,
        frame_count=6,
    ),
    ActionType.ATTACK_1: ActionData(
        action_type=ActionType.ATTACK_1,
        animation=None if RL else Animation(
            name="attack",
            sprite_file_name="Attack_1.png"
        ),
        frame_events={
            2: (
                Event(Events.ATTACK, 1),
            )
        },
        stamina_cost=2,
        stamina_cost_frame=1,
        frame_count=4,
    ),
    ActionType.PARRY: ActionData(
        action_type=ActionType.PARRY,
        animation=None if RL else Animation(
            name="parry",
            sprite_file_name="Parry.png"
        ),
        frame_events={
            1: (
                Event(Events.PARRY),
            )
        },
        stamina_cost=2,
        stamina_cost_frame=1,
        frame_count=4,
    ),
    ActionType.DEFENSE: ActionData(
        action_type=ActionType.DEFENSE,
        animation=None if RL else Animation(
            name="defense",
            sprite_file_name="Defense.png"
        ),
        frame_events={
            0: (
                Event(Events.BLOCK),
            )
        },
        stamina_cost_frame=1,
        frame_count=1,
    ),
    ActionType.DEAD: ActionData(
        action_type=ActionType.DEAD,
        animation=None if RL else Animation(
            name="dead",
            sprite_file_name="Dead.png",
        ),
        frame_events={
            0: (
                Event(Events.DEAD),
            )
        },
        loop=True,
        frame_count=5,
    )
}