from dataclasses import dataclass
from typing import List

import pygame


@dataclass
class Animation:
    name: str
    frames: List[pygame.Surface]
    frame_count: int
    loop: bool
    interruptible: bool
    frame_duration: int  # ms per frame

    def __init__(self, name: str, sprite_sheet: pygame.Surface, frame_count: int,
                 frame_size: int, loop: bool, interruptible: bool, frame_duration: int = 100):
        self.name = name
        self.frame_count = frame_count
        self.loop = loop
        self.interruptible = interruptible
        self.frame_duration = frame_duration
        self.frames = []
        for i in range(frame_count):
            frame = sprite_sheet.subsurface((i * frame_size, 0, frame_size, frame_size))
            self.frames.append(frame)
