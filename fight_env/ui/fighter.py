from typing import Optional
import pygame
from fight_env.state import State

class Fighter:
    def __init__(self, x: int, y: int, facing_right: bool = True):
        self.x = x
        self.y = y
        self.facing_right = facing_right
        self.state: Optional[State] = None
        self.frame_timer = 0

    def set_state(self, state: State):
        self.state = state

    def update(self, dt: int):
        action = self.state.get_current_action()
        animation = action.animation
        if not animation:
            return

        self.frame_timer += dt
        if self.frame_timer >= animation.frame_duration:
            self.frame_timer = 0
            self.state.next_frame()

    def get_current_frame(self) -> Optional[pygame.Surface]:
        action = self.state.get_current_action()
        animation = action.animation
        if animation:
            frame = animation.frames[self.state.current_action_frame]
            if not self.facing_right:
                return pygame.transform.flip(frame, True, False)
            return frame
        return None