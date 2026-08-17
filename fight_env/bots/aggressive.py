import random
from fight_env.player.player import Player
from fight_env.player.processing.intent_processing import ActionType
from fight_env.player.refs.tasks import FighterTask


class Aggressive:
    def __init__(self, player: Player, opponent: Player):
        self.player = player
        self.opponent = opponent

    def next_move(self) -> bool:
        snapshot = self.opponent.make_snapshot()

        if snapshot.task == FighterTask.ATTACK_1:
            if snapshot.frame_offset == 1:
                if random.random() > 0.3:
                    self.player.request_intent(ActionType.BLOCK)
                    return False

        if snapshot.task == FighterTask.RIPOSTE:
            if snapshot.frame_offset == 2:
                if random.random() > 0.3:
                    self.player.request_intent(ActionType.BLOCK)
                    return False

        if snapshot.task == FighterTask.STUNNED:
            if random.random() > 0.3:
                self.player.request_intent(ActionType.ATTACK)
            return False

        if snapshot.stamina >= snapshot.max_stamina // 2:
            if random.random() > 0.8:
                self.player.request_intent(ActionType.ATTACK)
            return True
