from fight_env import duel_resolver
from fight_env.player.player import Player


class DuelOrchestrator:
    def __init__(self):
        self.fighter1 = Player("fighter1")
        self.fighter2 = Player("fighter2")


    def flow(self):
        snapshot1 = self.fighter1.make_snapshot()
        snapshot2 = self.fighter2.make_snapshot()

        self.fighter1.tick()
        self.fighter2.tick()

        f1_responses, f2_responses = duel_resolver.resolve_duelists(self.fighter1.event(), self.fighter2.event())

        self.fighter1.process_responses(f1_responses)
        self.fighter2.process_responses(f2_responses)

        self.fighter1.fallback()
        self.fighter2.fallback()

        self.fighter1.process_intent()
        self.fighter2.process_intent()

        self.fighter1.reactive(snapshot1)
        self.fighter2.reactive(snapshot2)
