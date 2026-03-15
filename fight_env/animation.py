from dataclasses import dataclass
from typing import List

import pygame

from fight_env.config import FRAME_DURATION, RESOURCES_DIR, FRAME_SIZE


def get_resources_path(file_name: str):
    return RESOURCES_DIR / file_name

@dataclass
class Animation:
    name: str
    frames: List[pygame.Surface]
    frame_count: int
    frame_duration: int  # ms per frame

    def __init__(self, name: str, sprite_file_name: str,
                 frame_size: int = FRAME_SIZE, frame_duration: int = FRAME_DURATION):
        sprite_sheet = pygame.image.load(get_resources_path(sprite_file_name))
        frame_count = sprite_sheet.get_width() // frame_size
        self.name = name
        self.frame_duration = frame_duration
        self.frame_count = frame_count
        self.frames = []
        self.current_frame = 0
        for i in range(frame_count):
            frame = sprite_sheet.subsurface((i * frame_size, 0, frame_size, frame_size))
            self.frames.append(frame)

    def get_frame(self, ahead):
        index = ahead % self.frame_count
        return self.frames[index]
