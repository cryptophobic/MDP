from dataclasses import dataclass, field
from typing import Optional, List

from fight_env.player.refs.events import Event, Response
from fight_env.player.refs.intents import Intent
from fight_env.player.stats import Stats
from fight_env.player.refs.tasks import FighterTask, TaskTimeline


@dataclass
class PlayerModel:
    task: FighterTask = FighterTask.NONE
    timeline: TaskTimeline = field(default_factory=TaskTimeline)
    stats: Stats = field(default_factory=Stats)
    current_event: Event = field(default_factory=list)
    current_responses: List[Response] = field(default_factory=list)
    requested_action: Optional[Intent] = field(default=None)

    stamina_cost_frame: int = 0
    stamina_cost_enter_task: int = 0

    is_dead: bool = False

    hp: int = 0
    stamina: int = 0
