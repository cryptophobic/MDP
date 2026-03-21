import pygame
import sys
from fight_env.config import FRAME_DURATION, RESOURCES_DIR, FRAME_SIZE

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
BG_COLOR = (30, 30, 30)

ANIMATIONS = ["Walk", "Run"]


def load_animation(name):
    path = RESOURCES_DIR / f"{name}.png"
    sheet = pygame.image.load(str(path)).convert_alpha()
    count = sheet.get_width() // FRAME_SIZE
    frames = [sheet.subsurface((i * FRAME_SIZE, 0, FRAME_SIZE, FRAME_SIZE)) for i in range(count)]
    return frames


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Move Calibration")
    font = pygame.font.SysFont("monospace", 16)
    clock = pygame.time.Clock()

    all_anims = {name: load_animation(name) for name in ANIMATIONS}
    current_anim_idx = 0

    frame_duration = FRAME_DURATION  # ms per animation frame
    frame_duration = 50
    move_speed = 2.0  # pixels per tick
    move_speed = 4.0  # pixels per tick

    # NPC state
    x = float(FRAME_SIZE // 2)
    y = float(SCREEN_HEIGHT // 2 - FRAME_SIZE // 2)
    direction = 1  # 1 = right, -1 = left
    frame_timer = 0.0
    frame_index = 0

    # corners for patrol
    left_x = float(FRAME_SIZE // 2)
    right_x = float(SCREEN_WIDTH - FRAME_SIZE - FRAME_SIZE // 2)

    while True:
        dt = clock.tick(60)  # 60 fps, dt in ms

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    current_anim_idx = (current_anim_idx + 1) % len(ANIMATIONS)
                    frame_index = 0

        keys = pygame.key.get_pressed()
        # Frame duration: left/right
        if keys[pygame.K_LEFT]:
            frame_duration = max(10, frame_duration - 1)
        if keys[pygame.K_RIGHT]:
            frame_duration += 1
        # Move speed: up/down
        if keys[pygame.K_UP]:
            move_speed = round(move_speed + 0.05, 2)
        if keys[pygame.K_DOWN]:
            move_speed = round(max(0.05, move_speed - 0.05), 2)

        # Move NPC
        x += direction * move_speed
        if x >= right_x:
            x = right_x
            direction = -1
        elif x <= left_x:
            x = left_x
            direction = 1

        # Advance animation frame
        anim_name = ANIMATIONS[current_anim_idx]
        frames = all_anims[anim_name]
        frame_timer += dt
        if frame_timer >= frame_duration:
            frame_timer -= frame_duration
            frame_index = (frame_index + 1) % len(frames)

        # Draw
        screen.fill(BG_COLOR)

        sprite = frames[frame_index]
        if direction == -1:
            sprite = pygame.transform.flip(sprite, True, False)
        screen.blit(sprite, (int(x), int(y)))

        # HUD
        lines = [
            f"Animation: {anim_name}  (TAB to switch)",
            f"Frame duration: {frame_duration} ms  (LEFT/RIGHT)",
            f"Move speed: {move_speed:.2f} px/tick  (UP/DOWN)",
            f"Frame: {frame_index}/{len(frames)}",
        ]
        for i, line in enumerate(lines):
            label = font.render(line, True, (220, 220, 220))
            screen.blit(label, (10, 10 + i * 20))

        pygame.display.flip()


if __name__ == "__main__":
    main()