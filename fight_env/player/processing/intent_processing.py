from typing import Dict, Callable

from fight_env.player.refs.events import Responses
from fight_env.player.player_model import PlayerModel
from fight_env.player.refs.intents import ActionType, intent_task_mapping
from fight_env.player.refs.tasks import FighterTask

IntentTaskMap = Dict[ActionType, Callable[[PlayerModel], FighterTask]]

def _resolve_attack(model) -> FighterTask:
    if any(r.type == Responses.HAS_RIPOSTE_WINDOW_OPEN for r in model.current_responses):
        return FighterTask.RIPOSTE
    return FighterTask.ATTACK_1

def process_intent(model: PlayerModel) -> FighterTask:
    action = model.requested_action.action if model.requested_action else ActionType.NONE
    task = intent_task_mapping[action]
    if task == FighterTask.ATTACK_1:
        task = _resolve_attack(model)

    return task
