from typing import Optional, List

from fight_env.orchestrator.duel_orchestrator import DuelOrchestrator
from fight_env.player.player import Player
from fight_env.player.refs.events import Response, Responses


class Orchestrator:
    def __init__(self, players: List[Player]):
        self.fighter1 = players[0]
        self.fighter2 = players[1]
        self.duel_orchestrator: Optional[DuelOrchestrator] = None

    def flow(self):
        snapshot1 = self.fighter1.make_snapshot()
        snapshot2 = self.fighter2.make_snapshot()

        self.fighter1.tick()
        self.fighter2.tick()

        # later distance check here
        need = True
        if need:
            self.duel_orchestrator = DuelOrchestrator(self.fighter1, self.fighter2)
            f1_responses, f2_responses = self.duel_orchestrator.resolve()
        else:
            f1_responses, f2_responses = ((Response(Responses.NONE), Response(Responses.NONE)),
                                          (Response(Responses.NONE), Response(Responses.NONE)))

        f1_fallback_resolved = self.fighter1.fallback()
        f2_fallback_resolved = self.fighter2.fallback()

        f1_intent_resolved = self.fighter1.process_intent()
        f2_intent_resolved = self.fighter2.process_intent()

        f1_reactive_resolved = self.fighter1.reactive(snapshot1)
        f2_reactive_resolved = self.fighter2.reactive(snapshot2)

        self.fighter1.cleanup(f1_fallback_resolved, f1_intent_resolved, f1_reactive_resolved)
        self.fighter2.cleanup(f2_fallback_resolved, f2_intent_resolved, f2_reactive_resolved)

        return f1_responses, f2_responses
