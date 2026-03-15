from fight_env.player.player_model import PlayerModel
from fight_env.player.player_snapshot import PlayerSnapshot
from fight_env.player.refs.tasks import FighterTask


def process_changes(current_state: PlayerModel, last_snapshot: PlayerSnapshot) -> FighterTask:
    if current_state.hp <= 0:
        return FighterTask.DEAD
    elif current_state.hp < last_snapshot.hp:
        return FighterTask.HURT
    elif current_state.stamina <= 0:
        return FighterTask.STUNNED
    elif current_state.task == FighterTask.NONE:
        return FighterTask.FIGHTING_STANCE
    elif last_snapshot.task == FighterTask.STUNNED:
        return FighterTask.FIGHTING_STANCE if current_state.stamina >= current_state.stats.max_stamina // 2 else FighterTask.STUNNED

    return FighterTask.NONE
