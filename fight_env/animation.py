from dataclasses import dataclass
from pathlib import Path
from typing import List

import pygame

BASE_DIR = Path(__file__).parent
RESOURCES_DIR = BASE_DIR / "resources" / "Animations"
FRAME_SIZE = 128

def get_resources_path(file_name: str):
    return RESOURCES_DIR / file_name

@dataclass
class Animation:
    name: str
    frames: List[pygame.Surface]
    frame_count: int
    current_action_frame: int
    frame_duration: int  # ms per frame

    def __init__(self, name: str, sprite_file_name: str,
                 frame_size: int = FRAME_SIZE, frame_duration: int = 120):
        sprite_sheet = pygame.image.load(get_resources_path(sprite_file_name))
        frame_count = sprite_sheet.get_width() // frame_size
        self.name = name
        self.frame_duration = frame_duration
        self.frame_count = frame_count
        self.frames = []
        for i in range(frame_count):
            frame = sprite_sheet.subsurface((i * frame_size, 0, frame_size, frame_size))
            self.frames.append(frame)

    def get_frame(self, frame_index: int) -> pygame.Surface:
        frame_index = frame_index % self.frame_count if frame_index > 0 else 0
        return self.frames[frame_index]
