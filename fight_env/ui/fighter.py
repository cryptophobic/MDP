from typing import Optional
import pygame

from fight_env.actions import ActionType
from fight_env.state import State

class Fighter:
    def __init__(self, x: int, y: int, facing_right: bool = True):
        self.x = x
        self.y = y
        self.facing_right = facing_right
        self.state: Optional[State] = None

    def set_state(self, state: State):
        self.state = state

    def get_current_frame(self) -> Optional[pygame.Surface]:
        action = self.state.get_current_action()
        animation = action.animation
        if animation:
            ahead = self.state.global_frame_number - self.state.action_start_frame
            frame = animation.get_frame(ahead)
            if not self.facing_right:
                return pygame.transform.flip(frame, True, False)
            return frame
        return None