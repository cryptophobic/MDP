from typing import Optional
import pygame

from fight_env.player.refs.animations import animations
from fight_env.player.player_snapshot import PlayerSnapshot

class Fighter:
    def __init__(self, x: int, y: int, facing_right: bool = True):
        self.x = x
        self.y = y
        self.facing_right = facing_right
        self.state: Optional[PlayerSnapshot] = None

    def set_state(self, state: PlayerSnapshot):
        self.state = state

    def get_current_frame(self) -> Optional[pygame.Surface]:
        task = self.state.task
        animation = animations.get(task, None)
        if animation:
            frame = animation.get_frame(self.state.frame_offset)
            if not self.facing_right:
                return pygame.transform.flip(frame, True, False)
            return frame
        return None