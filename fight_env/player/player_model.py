from dataclasses import dataclass
from typing import Optional

from fight_env.player.events import Response, Responses
from fight_env.player.states import FighterState, StateTimeline, states_data, STATE_UNINITIALISED
from fight_env.ticker import ticker


@dataclass
class PlayerModel:

    state: FighterState = FighterState.NONE
    state_next: FighterState = FighterState.NONE
    stamina_cost_frame: int = 0
    stamina_cost_state: int = 0
    timeline: Optional[StateTimeline] = None

    is_dead: bool = False

    hp: int = 0
    stamina: int = 0

    hp_next: int = 0
    stamina_next: int = 0

    def enter_state(self, state: FighterState):
        self.state = state
        state_data = states_data[state]
        self.timeline = StateTimeline(
            start_frame_number=ticker.state,
            frame_number=STATE_UNINITIALISED,
            duration=state_data.duration,
            loop=state_data.loop
        )

        self.stamina_cost_state = state_data.base_stamina_cost
        self.stamina_cost_frame = state_data.base_stamina_cost_frame

    def finalise_last_frame(self):
        self.hp = self.hp_next
        self.stamina = self.stamina_next

        if self.state_next != FighterState.NONE:
            self.enter_state(self.state_next)

    def start_new_frame(self):
        if self.timeline.frame_number == STATE_UNINITIALISED:
            self.stamina_next -= self.stamina_cost_state

        self.timeline.tick()
        self.stamina_next -= self.stamina_cost_frame

    def process_incoming_events(self, response: Response):
        if response.type == Responses.DEAD:
            self.is_dead = True
            return


