from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Tuple, Optional

from fight_env.config import BASE_STAMINA_RESTORE_VALUE_PER_TICK
from fight_env.player.events import Events


class FighterTask(IntEnum):
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
class TaskData:
    task_type: FighterTask
    priority: int = 0
    base_stamina_cost: int = 0
    base_stamina_cost_frame: int = 0

    duration: int = 0
    loop: bool = False
    events: TimelineEvents = field(default_factory=TimelineEvents)

    interruptible: bool = False

@dataclass
class TaskTimeline:
    frame_number: int = 0
    start_frame_number: int = 0
    duration: int = 0
    loop: bool = False

    @property
    def frame_offset(self) -> int:
        offset = self.frame_number - self.start_frame_number
        return offset if self.loop else offset % self.duration

    def tick(self):
        self.frame_number += 1

    @property
    def expired(self) -> bool:
        return self.frame_offset >= self.duration


tasks_data: Dict[FighterTask, TaskData] = {
    # Top level
    FighterTask.DEAD: TaskData(
        task_type=FighterTask.DEAD,
        priority=100,
        duration=5,
        events={3: (Events.DEAD,)}
    ),

    # System level
    FighterTask.STUNNED: TaskData(
        task_type=FighterTask.STUNNED,
        priority=50,
        base_stamina_cost_frame=-BASE_STAMINA_RESTORE_VALUE_PER_TICK,
        duration=0,
        loop=True,
        events={0: (Events.STUNNED,)},
    ),
    FighterTask.HURT: TaskData(
        task_type=FighterTask.HURT,
        priority=90,
        base_stamina_cost=2,
        duration=2
    ),

    # User level
    FighterTask.ATTACK_1: TaskData(
        task_type=FighterTask.ATTACK_1,
        priority=50,
        base_stamina_cost=2,
        duration=4,
        events={
            0: (Events.ATTACK_STARTED,),
            2: (Events.ATTACK,)
        }
    ),
    FighterTask.PARRY: TaskData(
        task_type=FighterTask.PARRY,
        priority=50,
        base_stamina_cost=2,
        duration=4,
        events={ 1: (Events.PARRY,) },
    ),
    FighterTask.RIPOSTE: TaskData(
        task_type=FighterTask.RIPOSTE,
        priority=50,
        base_stamina_cost=2,
        duration=5,
        events={ 3: (Events.CRITICAL_ATTACK,)}
    ),
    FighterTask.DEFENSE: TaskData(
        task_type=FighterTask.DEFENSE,
        priority=50,
        duration=1,
        events={ 0: (Events.BLOCK,) }
    ),

    # Fallback
    FighterTask.IDLE: TaskData(
        task_type=FighterTask.IDLE,
        base_stamina_cost_frame=-BASE_STAMINA_RESTORE_VALUE_PER_TICK,
        interruptible=True,
        duration=0,
        loop=True,
    ),
    FighterTask.NONE: TaskData(
        task_type=FighterTask.NONE,
    )
}