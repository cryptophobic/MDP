from typing import Protocol, runtime_checkable, Optional

from fight_env.player.tasks import FighterTask, TaskTimeline


@runtime_checkable
class StateProtocol(Protocol):
    task: FighterTask
    stamina: int
    hp: int
    timeline: Optional[TaskTimeline]
    stamina_cost_frame: int
