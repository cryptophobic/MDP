import pygame

from fight_env.player.player import Player
from fight_env.animation import FRAME_SIZE
from fight_env.player.processing.intent_processing import ActionType
from fight_env.ui.debug_hud import DebugHUD
from fight_env.ui.fighter import Fighter


class Render:
    def __init__(self, player_state: Player, bot_state: Player):
        pygame.init()
        self.width = 800
        self.height = 400
        self.scale = 1

        self.player_state = player_state
        self.bot_state = bot_state

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Fighting Environment")
        self.clock = pygame.time.Clock()
        self.running = True

        # Create fighters
        self.player = Fighter((self.width // 2) - (FRAME_SIZE // 2), self.height - FRAME_SIZE * self.scale, facing_right=True)
        self.bot = Fighter((self.width // 2) - (FRAME_SIZE // 4), self.height - FRAME_SIZE * self.scale, facing_right=False)

        # Colors
        self.bg_color = (40, 44, 52)
        self.ground_color = (60, 65, 75)

        # Debug overlay (F1 toggles, engine style)
        self.hud = DebugHUD()
        self.show_debug = True
        self.tick_count = 0

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                self.show_debug = not self.show_debug

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.running = False

        if keys[pygame.K_i]:
            self.bot_state.request_intent(ActionType.ATTACK)
        if keys[pygame.K_o]:
            self.bot_state.request_intent(ActionType.BLOCK)
        if keys[pygame.K_p]:
            self.bot_state.request_intent(ActionType.PARRY)
        if keys[pygame.K_q]:
            self.player_state.request_intent(ActionType.ATTACK)
        if keys[pygame.K_w]:
            self.player_state.request_intent(ActionType.BLOCK)
        if keys[pygame.K_e]:
            self.player_state.request_intent(ActionType.PARRY)

    def draw(self):
        self.tick_count += 1
        self.screen.fill(self.bg_color)

        self.player.set_state(self.player_state.make_snapshot())
        self.bot.set_state(self.bot_state.make_snapshot())

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

        # Debug overlay, directly under the bars
        if self.show_debug:
            hud_y = bar_y_st + bar_h + 8
            self.hud.draw(self.screen, self.player_state, self.player_state._model.stats.name,
                          10, hud_y)
            self.hud.draw(self.screen, self.bot_state, self.bot_state._model.stats.name,
                          self.width - 10, hud_y, align_right=True)
            self.hud.draw_lines(
                self.screen,
                [(f"tick {self.tick_count}", (85, 92, 105)),
                 ("F1 debug  ESC quit", (85, 92, 105))],
                self.width // 2 - 60, hud_y)

        pygame.display.flip()

