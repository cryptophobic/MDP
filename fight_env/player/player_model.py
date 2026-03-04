from dataclasses import dataclass
from typing import Optional

from fight_env.player.states import FighterState, StateTimeline, states_data
from fight_env.ticker import ticker


@dataclass
class PlayerModel:

    state: FighterState = FighterState.NONE
    state_next: FighterState = FighterState.NONE
    stamina_cost_frame: int = 0
    timeline: Optional[StateTimeline] = None

    hp: int = 0
    stamina: int = 0

    hp_next: int = 0
    stamina_next: int = 0

    def enter_state(self, state: FighterState):
        self.state = state
        state_data = states_data[state]
        self.timeline = StateTimeline(
            start_frame_number=ticker.state,
            frame_number=-1, #uninitialised
            duration=state_data.duration,
            loop=state_data.loop
        )

        self.stamina_next -= state_data.base_stamina_cost
        self.stamina_cost_frame = state_data.base_stamina_cost_frame

    def finalise_last_frame(self):
        self.hp = self.hp_next
        self.stamina = self.stamina_next

        if self.state_next != FighterState.NONE:
            self.enter_state(self.state_next)

    def start_new_frame(self):
        self.timeline.tick()
        self.stamina_next -= self.stamina_cost_frame

