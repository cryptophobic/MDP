from typing import List

from fight_env.player.events import Event, Response, Events
from fight_env.player.processing.intent_processing import ActionType, Intent
from fight_env.player.player_model import PlayerModel
from fight_env.player.player_snapshot import PlayerSnapshot
from fight_env.player.processing.response_processing import process_response
from fight_env.player.stats import materialize_event
from fight_env.player.processing.task_processing import process_current_task, try_transition
from fight_env.player.tasks import FighterTask
from fight_env.protocols.state_protocol import StateProtocol


class Player:
    def __init__(self, name: str):
        self._model = PlayerModel()

    def tick(self):
        process_current_task(self._model)
        self._model.current_event = Event(Events.NONE)
        self._model.current_event = materialize_event(self._model.timeline.current_event, self._model.stats)
        self._model.timeline.tick()

    def request_intent(self, action: ActionType, ttl = 1) -> None:
        self._model.requested_action = Intent(action, ttl)

    def event(self) -> Event:
        return self._model.current_event

    def fallback(self):
        try_transition(self._model, FighterTask.IDLE)

    def process_intent(self):
        if self._model.requested_action and self._model.requested_action.ttl >= 0:
            process_current_task(self._model)
        pass

    def process_responses(self, responses: List[Response]):
        self._model.current_responses = responses
        for response in responses:
            process_response(self._model, response)

    def reactive(self, snapshot: StateProtocol):
        pass

    def make_snapshot(self) -> StateProtocol:
        return PlayerSnapshot(self._model)
