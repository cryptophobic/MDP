from dataclasses import dataclass

from fight_env.player.actions import ActionType


@dataclass(frozen=True)
class Intent:
    action: ActionType
    ttl: int = 0
