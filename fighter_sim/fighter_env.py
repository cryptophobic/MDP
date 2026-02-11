import pygame
from enum import Enum, auto

from fighter_sim.fighter import Fighter


class ActionType(Enum):
    STANCE = auto()
    ATTACK = auto()

class FightingGame:
    def __init__(self, width: int = 800, height: int = 400, scale: int = 3):
        pygame.init()
        self.width = width
        self.height = height
        self.scale = scale
        self.frame_size = 128

        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Fighting Environment")
        self.clock = pygame.time.Clock()
        self.running = True

        # Load animations
        self.load_animations()

        # Create fighters
        self.player = Fighter(150, height - self.frame_size * scale, facing_right=True)
        self.bot = Fighter(width - 150 - self.frame_size * scale, height - self.frame_size * scale, facing_right=False)

        for fighter in [self.player, self.bot]:
            fighter.add_animation(ActionType.STANCE, self.stance_anim)
            fighter.add_animation(ActionType.ATTACK, self.attack_anim)

        # Colors
        self.bg_color = (40, 44, 52)
        self.ground_color = (60, 65, 75)

    def load_animations(self):
        """Load sprite sheets and create animations."""
        stance_sheet = pygame.image.load("resources/Animations/Fighting_Stance.png").convert_alpha()
        attack_sheet = pygame.image.load("resources/Animations/Attack_1.png").convert_alpha()

        # Determine frame counts from sheet width
        stance_frames = stance_sheet.get_width() // self.frame_size
        attack_frames = attack_sheet.get_width() // self.frame_size

        self.stance_anim = Animation(
            name="stance",
            sprite_sheet=stance_sheet,
            frame_count=stance_frames,
            frame_size=self.frame_size,
            loop=True,
            interruptible=True,
            frame_duration=120
        )

        self.attack_anim = Animation(
            name="attack",
            sprite_sheet=attack_sheet,
            frame_count=attack_frames,
            frame_size=self.frame_size,
            loop=False,
            interruptible=False,
            frame_duration=80
        )

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.player.request_action(ActionType.ATTACK)
                # Bot attack for testing (press B)
                elif event.key == pygame.K_b:
                    self.bot.request_action(ActionType.ATTACK)

    def update(self, dt: int):
        self.player.update(dt)
        self.bot.update(dt)

    def draw(self):
        self.screen.fill(self.bg_color)

        # Draw ground
        ground_y = self.height - 50
        pygame.draw.rect(self.screen, self.ground_color, (0, ground_y, self.width, 50))

        # Draw fighters
        for fighter in [self.player, self.bot]:
            frame = fighter.get_current_frame()
            if frame:
                scaled = pygame.transform.scale(frame,
                    (self.frame_size * self.scale, self.frame_size * self.scale))
                self.screen.blit(scaled, (fighter.x, fighter.y))

        # Draw HUD
        font = pygame.font.Font(None, 24)
        player_state = f"Player: {self.player.current_action.name} frame {self.player.current_frame}"
        bot_state = f"Bot: {self.bot.current_action.name} frame {self.bot.current_frame}"

        player_text = font.render(player_state, True, (200, 200, 200))
        bot_text = font.render(bot_state, True, (200, 200, 200))
        controls_text = font.render("SPACE: Attack | B: Bot Attack | ESC: Quit", True, (150, 150, 150))

        self.screen.blit(player_text, (10, 10))
        self.screen.blit(bot_text, (self.width - bot_text.get_width() - 10, 10))
        self.screen.blit(controls_text, (self.width // 2 - controls_text.get_width() // 2, 10))

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60)  # 60 FPS, returns ms since last call
            self.handle_input()
            self.update(dt)
            self.draw()

        pygame.quit()


if __name__ == "__main__":
    game = FightingGame()
    game.run()