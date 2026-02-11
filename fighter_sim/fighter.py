from typing import Optional

import pygame

from fighter_sim.animations import Animation
from fighter_sim.fighter_env import ActionType


class Fighter:
    def __init__(self, x: int, y: int, facing_right: bool = True):
        self.x = x
        self.y = y
        self.facing_right = facing_right
        self.animations: dict[ActionType, Animation] = {}
        self.current_action = ActionType.STANCE
        self.current_frame = 0
        self.frame_timer = 0
        self.action_queue: Optional[ActionType] = None

    def add_animation(self, action: ActionType, animation: Animation):
        self.animations[action] = animation

    def request_action(self, action: ActionType):
        """Request a new action. Only executes if current animation is interruptible."""
        current_anim = self.animations.get(self.current_action)
        if current_anim and current_anim.interruptible:
            self._start_action(action)
        else:
            self.action_queue = action

    def _start_action(self, action: ActionType):
        if action in self.animations:
            self.current_action = action
            self.current_frame = 0
            self.frame_timer = 0
            self.action_queue = None

    def update(self, dt: int):
        """Update animation state. dt is delta time in ms."""
        anim = self.animations.get(self.current_action)
        if not anim:
            return

        self.frame_timer += dt
        if self.frame_timer >= anim.frame_duration:
            self.frame_timer = 0
            self.current_frame += 1

            if self.current_frame >= anim.frame_count:
                if anim.loop:
                    self.current_frame = 0
                else:
                    # Animation finished, return to stance or process queue
                    if self.action_queue:
                        self._start_action(self.action_queue)
                    else:
                        self._start_action(ActionType.STANCE)

    def get_current_frame(self) -> Optional[pygame.Surface]:
        anim = self.animations.get(self.current_action)
        if anim and 0 <= self.current_frame < len(anim.frames):
            frame = anim.frames[self.current_frame]
            if not self.facing_right:
                return pygame.transform.flip(frame, True, False)
            return frame
        return None

    def get_state(self) -> tuple:
        """Return current state as (action, frame) tuple for RL observation."""
        return (self.current_action.value, self.current_frame)
