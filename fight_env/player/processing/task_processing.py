from fight_env.player.player_model import PlayerModel
from fight_env.player.refs.tasks import FighterTask, tasks_data, TaskTimeline


def try_transition(model: PlayerModel, candidate: FighterTask) -> bool:

    if model.timeline.expired:
        set_task(model, candidate)
        return True

    if model.task == candidate:
        return False

    current = tasks_data[model.task]
    incoming = tasks_data[candidate]

    prioritised = incoming.priority > current.priority

    if not prioritised and current.priority == incoming.priority:
        if model.timeline.frame_number == 0:
            prioritised = incoming.start_priority > current.start_priority

        if not prioritised and current.interruptible:
            prioritised = True

    if prioritised:
        set_task(model, candidate)
        return True

    return False


def set_task(model: PlayerModel, task: FighterTask):
    task_data = tasks_data[task]
    # is_drain = task_data.base_stamina_cost + task_data.base_stamina_cost_frame > 0
    #
    # if is_drain and model.stamina < task_data.base_stamina_cost + task_data.base_stamina_cost_frame:
    #     task = FighterTask.NONE
    #     task_data = tasks_data[task]

    model.task = task

    model.timeline = TaskTimeline(
        duration=task_data.duration,
        events=task_data.events,
        loop=task_data.loop
    )

    # TODO: calculate real values with stats from fight_env/player/stats.py
    model.stamina_cost_enter_task = task_data.base_stamina_cost
    model.stamina_cost_frame = task_data.base_stamina_cost_frame

def process_current_task(model: PlayerModel):
    if model.timeline.frame_number == 0:
        model.stamina -= model.stamina_cost_enter_task

    if model.timeline.expired:
        set_task(model, FighterTask.NONE)
        return

    model.stamina -= model.stamina_cost_frame
    model.stamina = min(model.stamina, model.stats.max_stamina)
