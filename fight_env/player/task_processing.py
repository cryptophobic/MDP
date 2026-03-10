from fight_env.player.tasks import FighterTask, tasks_data, TaskTimeline, TASK_UNINITIALISED
from fight_env.protocols.state_protocol import StateProtocol
from fight_env.ticker import ticker


class TaskProcessing:

    @classmethod
    def choose_task(cls, model: StateProtocol, taskset: set[FighterTask]):
        pass

    @classmethod
    def set_task(cls, model: StateProtocol, task: FighterTask):
        model.task = task
        task_data = tasks_data[task]
        model.timeline = TaskTimeline(
            start_frame_number=ticker.state,
            frame_number=ticker.state,
            duration=task_data.duration,
            loop=task_data.loop
        )

        model.stamina -= task_data.base_stamina_cost
        model.stamina_cost_frame = task_data.base_stamina_cost_frame

    @classmethod
    def process_current_task(cls, model: StateProtocol):
        if ticker.state == cls._processed:
            return

        if model.task == FighterTask.NONE:
            pass
        elif not model.timeline.expired and model.timeline.tick():
            model.stamina -= model.stamina_cost_frame
        else:
            cls.set_task(model, FighterTask.NONE)

        cls._processed = ticker.state

