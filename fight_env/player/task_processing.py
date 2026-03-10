from fight_env.player.tasks import FighterTask, tasks_data, TaskTimeline, TASK_UNINITIALISED
from fight_env.protocols.state_protocol import StateProtocol
from fight_env.ticker import ticker


def enter_task(model: StateProtocol, task: FighterTask):
    model.task = task
    task_data = tasks_data[task]
    model.timeline = TaskTimeline(
        start_frame_number=ticker.state,
        frame_number=TASK_UNINITIALISED,
        duration=task_data.duration,
        loop=task_data.loop
    )

    model.stamina -= task_data.base_stamina_cost
    model.stamina_cost_frame = task_data.base_stamina_cost_frame

def process_current_task(model: StateProtocol):
    if model.task == FighterTask.NONE:
        return

    if not model.timeline.expired and model.timeline.tick():
        model.stamina -= model.stamina_cost_frame
    else:
        enter_task(model, FighterTask.NONE)

