from typing import List

from fight_env.config import DEFAULT_HP, DEFAULT_STAMINA
from fight_env.inventory.armour import ArmourTypes
from fight_env.inventory.shields import Shields
from fight_env.inventory.weapons import Weapons
from fight_env.player.refs.events import Event, Response
from fight_env.player.processing.intent_processing import ActionType, process_intent
from fight_env.player.player_model import PlayerModel
from fight_env.player.player_snapshot import PlayerSnapshot
from fight_env.player.processing.reactive_processing import process_changes
from fight_env.player.processing.response_processing import process_response
from fight_env.player.refs.intents import Intent
from fight_env.player.stats import materialize_event, Stats
from fight_env.player.processing.task_processing import process_current_task, try_transition
from fight_env.player.refs.tasks import FighterTask


class Player:
    def __init__(self, name: str, hp: int = DEFAULT_HP, stamina: int = DEFAULT_STAMINA,):
        self._model = PlayerModel()
        stats = Stats(name, hp, stamina)
        self._model.stats = stats
        self._model.hp = stats.hp
        self._model.stamina = stats.stamina

    @property
    def is_dead(self) -> bool:
        return self._model.is_dead

    def set_shield(self, shield: Shields):
        self._model.stats.shield = shield

    def set_armour(self, armour: ArmourTypes):
        self._model.stats.armour = armour

    def set_weapon(self, weapon: Weapons):
        self._model.stats.weapon = weapon

    def tick(self):
        process_current_task(self._model)
        self._model.current_event = materialize_event(self._model.timeline.current_event, self._model.stats)
        self._model.timeline.tick()

    def request_intent(self, action: ActionType, ttl = 1) -> None:
        self._model.requested_action = Intent(action, ttl)

    def event(self) -> Event:
        return self._model.current_event

    def fallback(self) -> bool:
        return try_transition(self._model, FighterTask.FIGHTING_STANCE)

    def process_intent(self) -> bool:
        task = process_intent(self._model)
        if task != FighterTask.NONE:
            return try_transition(self._model, task)

        return False

    def process_responses(self, responses: List[Response]):
        self._model.current_responses = responses
        for response in responses:
            process_response(self._model, response)

    def reactive(self, snapshot: PlayerSnapshot) -> bool:
        task = process_changes(self._model, snapshot)
        return try_transition(self._model, task)

    def cleanup(self, fallback_resolved: bool, intent_resolved: bool, reactive_resolved: bool) -> None:
        if intent_resolved and not reactive_resolved:
            self._model.requested_action = None

        if self._model.requested_action:
            self._model.requested_action.ttl -= 1
            if self._model.requested_action.ttl <= 0:
                self._model.requested_action = None

    def make_snapshot(self) -> PlayerSnapshot:
        return PlayerSnapshot(self._model)
