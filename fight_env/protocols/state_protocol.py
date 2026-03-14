from typing import Protocol, runtime_checkable, Optional, List

from fight_env.player.events import Event, Response
from fight_env.player.stats import Stats
from fight_env.player.tasks import FighterTask, TaskTimeline


@runtime_checkable
class StateProtocol(Protocol):
    task: FighterTask
    stamina: int
    stats: Stats
    hp: int
    timeline: Optional[TaskTimeline]
    stamina_cost_frame: int
    stamina_cost_enter_task: int
    current_event: Event
    current_responses: List[Response]
