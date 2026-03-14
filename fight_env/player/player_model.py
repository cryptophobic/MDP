from dataclasses import dataclass, field
from typing import Optional, List

from fight_env.player.events import Event, Response
from fight_env.player.processing.intent_processing import Intent
from fight_env.player.stats import Stats
from fight_env.player.tasks import FighterTask, TaskTimeline
from fight_env.protocols.state_protocol import StateProtocol


@dataclass
class PlayerModel(StateProtocol):
    task: FighterTask = FighterTask.NONE
    timeline: Optional[TaskTimeline] = field(default_factory=TaskTimeline)
    stats: Stats = field(default_factory=Stats)
    current_event: Event = field(default_factory=list)
    current_responses: List[Response] = field(default_factory=list)
    requested_action: Optional[Intent] = field(default=None)

    stamina_cost_frame: int = 0
    stamina_cost_enter_task: int = 0

    is_dead: bool = False

    hp: int = 0
    stamina: int = 0
