from fight_env.config import STAMINA_BOTTOM_LIMIT
from fight_env.player.refs.events import Response, Responses
from fight_env.player.player_model import PlayerModel
from fight_env.player.stats import Stats

INSTANT_STUN = 9999


def process_response(state: PlayerModel, response: Response) -> None:
    if response.type == Responses.DEAD:
        state.is_dead = True
        return

    stamina_cost = _stamina_cost_on_response(state.stats, response)
    if stamina_cost == INSTANT_STUN:
        stamina_cost = state.stamina - STAMINA_BOTTOM_LIMIT

    state.stamina -= stamina_cost
    hp_cost = _hp_cost_on_response(state.stats, response)
    state.hp = max(state.hp - hp_cost, 0)

def _stamina_cost_on_response(stats: Stats, response: Response):
    match response.type:
        case Responses.HAS_BLOCKED:
            return stats.shield.weight + 2 * response.value - stats.shield.defense
        case Responses.HAS_BEEN_BLOCKED:
            return stats.weapon.weight + response.value
        case Responses.HAS_BEEN_PARRIED:
            return INSTANT_STUN

    return 0

def _hp_cost_on_response(stats: Stats, response: Response):
    match response.type:
        case Responses.HAS_BEEN_ATTACKED:
            return response.value - stats.armour.defense

    return 0
