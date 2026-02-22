import pygame

from fight_env.actions import ActionType
from fight_env.animation import FRAME_SIZE
from fight_env.state import State
from fight_env.ui.fighter import Fighter


class Render:
    def __init__(self, player_state: State, bot_state: State):
        pygame.init()
        self.width = 800
        self.height = 400
        self.scale = 3

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Fighting Environment")
        self.clock = pygame.time.Clock()
        self.running = True

        # Create fighters
        self.player = Fighter(150, self.height - FRAME_SIZE * self.scale, facing_right=True)
        self.bot = Fighter(self.width - 150 - FRAME_SIZE * self.scale, self.height - FRAME_SIZE * self.scale, facing_right=False)

        self.player.set_state(player_state)
        self.bot.set_state(bot_state)

        # Colors
        self.bg_color = (40, 44, 52)
        self.ground_color = (60, 65, 75)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                match event.key:
                    case pygame.K_ESCAPE:
                        self.running = False
                    case pygame.K_i:
                        self.player.state.request_action(ActionType.ATTACK_1)
                    case pygame.K_o:
                        self.player.state.request_action(ActionType.DEFENSE)
                    case pygame.K_p:
                        self.player.state.request_action(ActionType.PARRY)
                    case pygame.K_q:
                        self.bot.state.request_action(ActionType.ATTACK_1)
                    case pygame.K_w:
                        self.bot.state.request_action(ActionType.DEFENSE)
                    case pygame.K_e:
                        self.bot.state.request_action(ActionType.PARRY)

    def update(self, dt: int):
        self.player.update(dt)
        self.bot.update(dt)

    def step(self):
        dt = self.clock.tick(60)
        self.handle_input()
        self.update(dt)
        self.draw()

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
                    (FRAME_SIZE * self.scale, FRAME_SIZE * self.scale))
                self.screen.blit(scaled, (fighter.x, fighter.y))

        # Draw HUD
        font = pygame.font.Font(None, 24)
        player_state = f"Player: {self.player.state.get_current_action().animation.name} frame {self.player.state.current_action_frame}"
        bot_state = f"Bot: {self.bot.state.get_current_action().animation.name} frame {self.bot.state.current_action_frame}"

        player_text = font.render(player_state, True, (200, 200, 200))
        bot_text = font.render(bot_state, True, (200, 200, 200))
        controls_text = font.render("SPACE: Attack | B: Bot Attack | ESC: Quit", True, (150, 150, 150))

        self.screen.blit(player_text, (10, 10))
        self.screen.blit(bot_text, (self.width - bot_text.get_width() - 10, 10))
        self.screen.blit(controls_text, (self.width // 2 - controls_text.get_width() // 2, 10))

        pygame.display.flip()

