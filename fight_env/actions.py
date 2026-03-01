from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Dict, Optional, Tuple

from fight_env.animation import Animation
from fight_env.config import RL
from fight_env.events import Event, Events

class ActionType(IntEnum):
    NONE = 0
    IDLE = 1
    ATTACK_1 = 2
    ATTACK_2 = 3
    ATTACK_3 = 4
    DEAD = 5
    DEFENSE = 6
    STUNNED = 7
    HURT = 8
    PARRY = 9
    POWER_PUNCH_1 = 10
    POWER_PUNCH_2 = 11
    RIPOSTE = 12
    ROLLING = 13
    RUN = 14
    SHIELD_STRIKE = 15
    WALK = 16
    PARRIED = 17

@dataclass
class ActionData:
    action_type: ActionType
    animation: Optional[Animation]
    frame_count: int
    interrupt_priority: int = 0
    requestable: bool = False
    alternatives: set[ActionType] = field(default_factory=set)
    stamina_cost: int = 0
    stamina_cost_frame: int = 0
    loop: bool = False
    times: int = 1
    interruptible: bool = False
    frame_events: Dict[int, Tuple[Event]] = field(default_factory=dict)

states: Dict[int, ActionData] = {
    ActionType.STUNNED: ActionData(
        action_type=ActionType.STUNNED,
        animation=None if RL else Animation(
            name="stun",
            sprite_file_name="Wounded.png",
        ),
        interrupt_priority=50,
        loop = True,
        interruptible = False,
        frame_count=0,
    ),
    ActionType.IDLE: ActionData(
        action_type=ActionType.IDLE,
        animation=None if RL else Animation(
            name="stance",
            sprite_file_name="Fighting_Stance.png",
        ),
        loop = True,
        interruptible = True,
        frame_count=0,
    ),
    ActionType.ATTACK_1: ActionData(
        action_type=ActionType.ATTACK_1,
        animation=None if RL else Animation(
            name="attack",
            sprite_file_name="Attack_1.png"
        ),
        requestable=True,
        interrupt_priority=50,
        alternatives={ ActionType.RIPOSTE, },
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
        requestable=True,
        interrupt_priority=50,
        frame_events={
            1: (
                Event(Events.PARRY),
            )
        },
        stamina_cost=2,
        stamina_cost_frame=1,
        frame_count=4,
    ),
    ActionType.HURT: ActionData(
        action_type=ActionType.HURT,
        interrupt_priority=90,
        animation=None if RL else Animation(
            name="hurt",
            sprite_file_name="Hurt.png"
        ),
        stamina_cost=0,
        stamina_cost_frame=0,
        frame_count=2,
    ),
    ActionType.RIPOSTE: ActionData(
        action_type=ActionType.RIPOSTE,
        interrupt_priority=50,
        animation=None if RL else Animation(
            name="riposte",
            sprite_file_name="Prick.png"
        ),
        alternatives={ ActionType.ATTACK_1, },
        frame_events={
            3: (
                Event(Events.RIPOSTE),
            )
        },
        stamina_cost=2,
        stamina_cost_frame=1,
        frame_count=5,
    ),
    ActionType.DEFENSE: ActionData(
        action_type=ActionType.DEFENSE,
        interrupt_priority=50,
        animation=None if RL else Animation(
            name="defense",
            sprite_file_name="Defense.png"
        ),
        requestable=True,
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
        interrupt_priority=100,
        frame_events={
            3: (
                Event(Events.DEAD),
            )
        },
        loop=False,
        frame_count=5,
    )
}