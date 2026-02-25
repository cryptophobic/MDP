from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple

from fight_env.animation import Animation
from fight_env.config import RL
from fight_env.events import Event, Events


class ActionType(Enum):
    NONE = 0
    IDLE = 1
    ATTACK_1 = 2
    ATTACK_2 = 3
    ATTACK_3 = 4
    DEAD = 5
    DEFENSE = 6
    STUN = 7
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
    stamina_cost: int = 0
    stamina_cost_frame: int = 0
    loop: bool = False
    times: int = 1
    interruptible: bool = False
    frame_events: Dict[int, Tuple[Event]] = field(default_factory=dict)

available_actions: Dict[ActionType, ActionData] = {
    ActionType.STUN: ActionData(
        action_type=ActionType.STUN,
        animation=None if RL else Animation(
            name="stun",
            sprite_file_name="Wounded.png",
        ),
        loop = True,
        interruptible = False,
        frame_count=8,
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
    ActionType.PARRIED: ActionData(
        action_type=ActionType.PARRIED,
        animation=None if RL else Animation(
            name="parried",
            sprite_file_name="Hurt.png"
        ),
        stamina_cost=0,
        stamina_cost_frame=0,
        frame_count=8,
    ),
    ActionType.HURT: ActionData(
        action_type=ActionType.HURT,
        animation=None if RL else Animation(
            name="hurt",
            sprite_file_name="Hurt.png"
        ),
        stamina_cost=0,
        stamina_cost_frame=0,
        frame_count=3,
    ),
    ActionType.RIPOSTE: ActionData(
        action_type=ActionType.RIPOSTE,
        animation=None if RL else Animation(
            name="riposte",
            sprite_file_name="Prick.png"
        ),
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
            4: (
                Event(Events.DEAD),
            )
        },
        loop=True,
        frame_count=5,
    )
}