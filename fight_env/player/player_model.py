from dataclasses import dataclass, field
from typing import Optional

from fight_env.player.events import Response, Responses
from fight_env.player.stats import Stats
from fight_env.player.tasks import FighterTask, TaskTimeline, tasks_data
from fight_env.protocols.state_protocol import StateProtocol
from fight_env.ticker import ticker


@dataclass
class PlayerModel(StateProtocol):

    task: FighterTask = FighterTask.NONE
    state_next: FighterTask = FighterTask.NONE
    stamina_cost_frame: int = 0
    timeline: Optional[TaskTimeline] = field(default_factory=TaskTimeline)
    stats: Stats = field(default_factory=Stats)

    is_dead: bool = False

    hp: int = 0
    stamina: int = 0

    def apply_state_next(self):
        if self.state_next != FighterTask.NONE:
            self._enter_state(self.state_next)
            self.state_next = FighterTask.NONE

    def apply_stamina_costs(self):
        self.stamina_next -= self.stamina_cost_frame

    def _enter_state(self, state: FighterTask):
        self.state = state
        state_data = tasks_data[state]
        self.timeline = TaskTimeline(
            start_frame_number=ticker.state,
            frame_number=TASK_UNINITIALISED,
            duration=state_data.duration,
            loop=state_data.loop
        )

        self.stamina_next -= state_data.base_stamina_cost
        self.stamina_cost_frame = state_data.base_stamina_cost_frame

    def finalise_last_frame(self):
        self.hp = self.hp_next
        self.stamina = self.stamina_next

        if self.state_next != FighterTask.NONE:
            self.enter_state(self.state_next)


    def process_incoming_events(self, response: Response):
        if response.type == Responses.DEAD:
            self.is_dead = True
            return


