"""
1. End of STUNNED
2. Enter STUNNED
3. Enter HURT
4. Exit HURT
4. Enter DEAD
"""
from fight_env.player.processing import task_processing
from fight_env.player.tasks import FighterTask
from fight_env.protocols.state_protocol import StateProtocol


def process_changes(current_state: StateProtocol, last_snapshot: StateProtocol) -> None:
    if current_state.hp <= 0:
        task_processing.set_task(current_state, FighterTask.DEAD)
    elif current_state.hp < last_snapshot.hp:
        task_processing.set_task(current_state, FighterTask.HURT)
    elif current_state.stamina <= 0:
        task_processing.set_task(current_state, FighterTask.STUNNED)
    elif current_state.task == FighterTask.NONE:
        task_processing.set_task(current_state, FighterTask.IDLE)

