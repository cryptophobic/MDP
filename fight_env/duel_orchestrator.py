from fight_env import duel_resolver
from fight_env.player.player import Player


class DuelOrchestrator:
    def __init__(self, fighter1: Player, fighter2: Player):
        self.fighter1 = fighter1
        self.fighter2 = fighter2

    def flow(self):
        snapshot1 = self.fighter1.make_snapshot()
        snapshot2 = self.fighter2.make_snapshot()

        self.fighter1.tick()
        self.fighter2.tick()

        f1_responses, f2_responses = duel_resolver.resolve_duelists(self.fighter1.event(), self.fighter2.event())

        self.fighter1.process_responses(f1_responses)
        self.fighter2.process_responses(f2_responses)

        f1_fallback_resolved = self.fighter1.fallback()
        f2_fallback_resolved = self.fighter2.fallback()

        f1_intent_resolved = self.fighter1.process_intent()
        f2_intent_resolved = self.fighter2.process_intent()

        f1_reactive_resolved = self.fighter1.reactive(snapshot1)
        f2_reactive_resolved = self.fighter2.reactive(snapshot2)

        self.fighter1.cleanup(f1_fallback_resolved, f1_intent_resolved, f1_reactive_resolved)
        self.fighter2.cleanup(f2_fallback_resolved, f2_intent_resolved, f2_reactive_resolved)

        return f1_responses, f2_responses
