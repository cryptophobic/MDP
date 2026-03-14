from fight_env.player.tasks import FighterTask, tasks_data, TaskTimeline
from fight_env.protocols.state_protocol import StateProtocol
from fight_env.ticker import ticker


def try_transition(model: StateProtocol, candidate: FighterTask) -> bool:
    if model.timeline.expired:
        set_task(model, candidate)
        return True

    if model.task == candidate:
        return True

    current = tasks_data[model.task]
    incoming = tasks_data[candidate]

    prioritised = incoming.priority > current.priority

    if prioritised or (incoming.priority == current.priority and current.interruptible):
        set_task(model, candidate)
        return True

    return False


def set_task(model: StateProtocol, task: FighterTask):
    model.task = task
    task_data = tasks_data[task]
    model.timeline = TaskTimeline(
        start_frame_number=ticker.state,
        frame_number=ticker.state,
        duration=task_data.duration,
        events=task_data.events,
        loop=task_data.loop
    )

    # TODO: calculate real values with stats from fight_env/player/stats.py
    model.stamina_cost_enter_task -= task_data.base_stamina_cost
    model.stamina_cost_frame = task_data.base_stamina_cost_frame

def process_current_task(model: StateProtocol):
    if model.timeline.frame_number == 0:
        model.stamina -= model.stamina_cost_enter_task

    if model.timeline.expired:
        set_task(model, FighterTask.NONE)
        return

    model.stamina -= model.stamina_cost_frame
