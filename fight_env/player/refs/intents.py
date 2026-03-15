from dataclasses import dataclass
from enum import IntEnum
from typing import Dict

from fight_env.player.refs.tasks import FighterTask


class ActionType(IntEnum):
    NONE = 0
    ATTACK = 1
    BLOCK = 2
    PARRY = 3

@dataclass
class Intent:
    action: ActionType
    ttl: int = 0
    resolved: bool = False

IntentTaskMap = Dict[ActionType, FighterTask]

intent_task_mapping: IntentTaskMap = {
    ActionType.NONE: FighterTask.NONE,
    ActionType.ATTACK: FighterTask.ATTACK_1,
    ActionType.BLOCK: FighterTask.DEFENSE,
    ActionType.PARRY: FighterTask.PARRY,
}
