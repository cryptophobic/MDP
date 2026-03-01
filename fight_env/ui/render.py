import pygame

from fight_env.actions import ActionType
from fight_env.animation import FRAME_SIZE
from fight_env.logger import logger
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

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.running = False

        # if keys[pygame.K_i]:
        #     self.bot.state.request_action(ActionType.ATTACK_1)
        # if keys[pygame.K_o]:
        #     self.bot.state.request_action(ActionType.DEFENSE)
        # if keys[pygame.K_p]:
        #     self.bot.state.request_action(ActionType.PARRY)
        if keys[pygame.K_q]:
            self.player.state.request_action(ActionType.ATTACK_1)
        if keys[pygame.K_w]:
            self.player.state.request_action(ActionType.DEFENSE)
        if keys[pygame.K_e]:
            self.player.state.request_action(ActionType.PARRY)

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
        font = pygame.font.Font(None, 18)
        # player_state = f"Player: {self.player.state.get_current_action().animation.name} frame {self.player.state.current_action_frame}"
        # bot_state = f"Bot: {self.bot.state.get_current_action().animation.name} frame {self.bot.state.current_action_frame}"

        # player_text = font.render(player_state, True, (200, 200, 200))
        # bot_text = font.render(bot_state, True, (200, 200, 200))
        # controls_text = font.render("SPACE: Attack | B: Bot Attack | ESC: Quit", True, (150, 150, 150))
        logs = logger.get(limit=50, tags={self.bot.state.name, self.player.state.name})
        lines = [log.body for log in logs if self.player.state.name in log.tags]
        last_10 = lines[-14:]  # take last 10 entries
        player_text = font.render("\r\n".join(last_10), True, (200, 200, 200))

        lines = [log.body for log in logs if self.bot.state.name in log.tags]
        last_10 = lines[-14:]  # take last 10 entries
        bot_text = font.render("\r\n".join(last_10), True, (200, 200, 200))

        # Health and stamina bars
        bar_w = 150
        bar_h = 10
        bar_y_hp = 10
        bar_y_st = 24

        for fighter, x in [(self.player, 10), (self.bot, self.width - bar_w - 10)]:
            s = fighter.state
            hp_ratio = max(s.hp / s.max_hp, 0)
            st_ratio = max(s.stamina / s.max_stamina, 0)

            # HP bar: dark bg + red fill
            pygame.draw.rect(self.screen, (60, 20, 20), (x, bar_y_hp, bar_w, bar_h))
            pygame.draw.rect(self.screen, (200, 40, 40), (x, bar_y_hp, int(bar_w * hp_ratio), bar_h))

            # Stamina bar: dark bg + green fill
            pygame.draw.rect(self.screen, (20, 60, 20), (x, bar_y_st, bar_w, bar_h))
            pygame.draw.rect(self.screen, (40, 200, 40), (x, bar_y_st, int(bar_w * st_ratio), bar_h))

        self.screen.blit(player_text, (10, 40))
        self.screen.blit(bot_text, (self.width - bot_text.get_width() - 10, 40))
        # self.screen.blit(controls_text, (self.width // 2 - controls_text.get_width() // 2, 10))

        pygame.display.flip()

