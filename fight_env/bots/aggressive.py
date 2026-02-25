import random

from fight_env.actions import ActionType
from fight_env.state import State

class Aggressive:
    def __init__(self, state: State, opponent: State):
        self.state = state
        self.opponent = opponent

    def next_move(self):
        if self.opponent.current_action == ActionType.ATTACK_1:
            if self.opponent.current_action_frame == 1:
                if random.random() > 0.3:
                    self.state.request_action(ActionType.DEFENSE)
                    return

        if self.opponent.current_action == ActionType.RIPOSTE:
            if self.opponent.current_action_frame == 2:
                if random.random() > 0.3:
                    self.state.request_action(ActionType.DEFENSE)
                    return

        if self.opponent.current_action == ActionType.STUN:
            if random.random() > 0.3:
                self.state.request_action(ActionType.ATTACK_1)
            return

        if self.state.stamina == self.state.max_stamina:
            if random.random() > 0.3:
                self.state.request_action(ActionType.ATTACK_1)
            return
