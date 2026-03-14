from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Callable

from fight_env.player.tasks import FighterTask
from fight_env.protocols.state_protocol import StateProtocol


class ActionType(IntEnum):
    NONE = 0
    ATTACK = 1
    BLOCK = 2
    PARRY = 3

@dataclass(frozen=True)
class Intent:
    action: ActionType
    ttl: int = 0

IntentTaskMap = Dict[ActionType, Callable[[StateProtocol], FighterTask]]

intent_task_mapping: IntentTaskMap = {
    ActionType.NONE: lambda model: FighterTask.NONE,
}

def process_intent(model: StateProtocol, intent: Intent) -> FighterTask:
    pass