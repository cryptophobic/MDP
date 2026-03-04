from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Tuple, Optional

from fight_env.config import BASE_STAMINA_RESTORE_VALUE_PER_TICK
from fight_env.player.events import Events


class FighterState(IntEnum):
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


TimelineEvents = Dict[int, Tuple[Events]]

@dataclass
class StateData:
    state_type: FighterState
    priority: int = 0
    base_stamina_cost: int = 0
    base_stamina_cost_frame: int = 0

    duration: int = 0
    loop: bool = False
    events: TimelineEvents = field(default_factory=TimelineEvents)

    interruptible: bool = False

@dataclass
class StateTimeline:
    frame_number: int = 0
    start_frame_number: int = 0
    duration: int = 0
    loop: bool = False

    def tick(self) -> bool:
        self.frame_number += 1
        if self.loop:
            self.frame_number %= self.duration

        return self.expired

    @property
    def expired(self) -> bool:
        return self.frame_number >= self.duration


states_data: Dict[FighterState, StateData] = {
    # Top level
    FighterState.DEAD: StateData(
        state_type=FighterState.DEAD,
        priority=100,
        duration=5,
        events={3: (Events.DEAD,)}
    ),

    # System level
    FighterState.STUNNED: StateData(
        state_type=FighterState.STUNNED,
        priority=50,
        base_stamina_cost_frame=-BASE_STAMINA_RESTORE_VALUE_PER_TICK,
        duration=0,
        loop=True,
    ),
    FighterState.HURT: StateData(
        state_type=FighterState.HURT,
        priority=90,
        base_stamina_cost=2,
        duration=2
    ),

    # User level
    FighterState.ATTACK_1: StateData(
        state_type=FighterState.ATTACK_1,
        priority=50,
        base_stamina_cost=2,
        duration=4,
        events={ 2: (Events.ATTACK,) }
    ),
    FighterState.PARRY: StateData(
        state_type=FighterState.PARRY,
        priority=50,
        base_stamina_cost=2,
        duration=4,
        events={ 1: (Events.PARRY,) },
    ),
    FighterState.RIPOSTE: StateData(
        state_type=FighterState.RIPOSTE,
        priority=50,
        base_stamina_cost=2,
        duration=5,
        events={ 3: (Events.CRITICAL_ATTACK,)}
    ),
    FighterState.DEFENSE: StateData(
        state_type=FighterState.DEFENSE,
        priority=50,
        duration=1,
        events={ 0: (Events.BLOCK,) }
    ),

    # Fallback
    FighterState.IDLE: StateData(
        state_type=FighterState.IDLE,
        base_stamina_cost_frame=-BASE_STAMINA_RESTORE_VALUE_PER_TICK,
        interruptible=True,
        duration=0,
        loop=True,
    )
}