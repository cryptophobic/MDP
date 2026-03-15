import pygame
import sys
from fight_env.config import FRAME_DURATION, RESOURCES_DIR, FRAME_SIZE

COLS = 5
ROWS = 4
PADDING = 10
LABEL_HEIGHT = 16
CELL = FRAME_SIZE + PADDING
WIDTH = COLS * CELL + PADDING
HEIGHT = ROWS * (CELL + LABEL_HEIGHT) + PADDING

SPRITES = [
    "Attack_1", "Attack_2", "Attack_3", "Blow_to_shield", "Dead",
    "Defense", "Fighting_Stance", "Hurt", "Idle", "Jump",
    "Jump_Strike", "Parry", "Power_punch_1", "Power_punch_2", "Riposte",
    "Rolling", "Run", "Shield_Strike", "Stunned", "Walk",
]


def load_animations():
    anims = []
    for name in SPRITES:
        path = RESOURCES_DIR / f"{name}.png"
        sheet = pygame.image.load(str(path)).convert_alpha()
        count = sheet.get_width() // FRAME_SIZE
        frames = [sheet.subsurface((i * FRAME_SIZE, 0, FRAME_SIZE, FRAME_SIZE)) for i in range(count)]
        anims.append((name, frames))
    return anims


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Animation Preview")
    font = pygame.font.SysFont("monospace", 12)
    clock = pygame.time.Clock()

    anims = load_animations()
    frame_counter = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()

        screen.fill((30, 30, 30))

        for idx, (name, frames) in enumerate(anims):
            col = idx % COLS
            row = idx // COLS
            x = PADDING + col * CELL
            y = PADDING + row * (CELL + LABEL_HEIGHT)

            frame_idx = frame_counter % len(frames)
            screen.blit(frames[frame_idx], (x, y))

            label = font.render(name, True, (200, 200, 200))
            screen.blit(label, (x, y + FRAME_SIZE + 2))

        pygame.display.flip()
        clock.tick(1000 / FRAME_DURATION)
        frame_counter += 1


if __name__ == "__main__":
    main()