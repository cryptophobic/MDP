from typing import Optional

from fight_env.inventory.armour import Armour, armour_types, ArmourTypes
from fight_env.inventory.shields import Shield, shields, Shields
from fight_env.inventory.weapons import Weapon, weapons, Weapons
from fight_env.logger import logger
from fight_env.state.actions import ActionType, states
from functools import wraps

from fight_env.state.events import Response, Responses, Events, Event

BASE_STAMINA_RESTORE_VALUE_PER_FRAME = 1
STAMINA_BOTTOM_LIMIT = -4
INSTANT_STUN = 9999

def lazy_recalc(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self._recalc_needed:
            self._update_values()
            self._recalc_needed = False
        return method(self, *args, **kwargs)

    return wrapper

def make_dirty(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self._recalc_needed = True
        return method(self, *args, **kwargs)

    return wrapper


class Stats:
    def __init__(self,
                 name: str,
                 hp: int = 30,
                 stamina: int = 20):
        self.name: str = name
        self._base_hp: int = hp
        self._base_stamina: int = stamina
        self._hp: int = hp
        self._stamina: int = stamina

        self._armour: Armour = armour_types[ArmourTypes.NONE]
        self._shield: Shield = shields[Shields.NONE]
        self._weapon: Weapon = weapons[Weapons.NONE]

        self._recalc_needed: bool = True
        self._weight: int = 0
        self._stamina_restore_value: int = 0
        self._base_stamina_expense: int = 0

    @property
    def hp(self) -> int:
        return self._hp

    @property
    def stamina(self) -> int:
        return self._stamina

    @property
    def armour(self) -> Armour:
        return self._armour

    @armour.setter
    @make_dirty
    def armour(self, armour: ArmourTypes):
        self._armour = armour_types[armour]

    @property
    def shield(self) -> Shield:
        return self._shield

    @shield.setter
    @make_dirty
    def shield(self, shield: Shields):
        self._shield = shields[shield]

    @property
    def weapon(self) -> Weapon:
        return self._weapon

    @weapon.setter
    @make_dirty
    def weapon(self, weapon: Weapons):
        self._weapon = weapons[weapon]

    @property
    @lazy_recalc
    def stamina_restore_per_frame(self) -> int:
        return self._stamina_restore_value

    def _update_values(self):
        self._weight = self.armour.weight + self.shield.weight + self.weapon.weight
        self._stamina_restore_value = BASE_STAMINA_RESTORE_VALUE_PER_FRAME
        self._base_stamina_expense = self._weight // 5

    @property
    @lazy_recalc
    def max_stamina(self) -> int:
        return self._base_stamina - self._weight

    @property
    def max_hp(self) -> int:
        return self._base_hp

    @property
    @lazy_recalc
    def weight(self) -> int:
        return self._weight

    @lazy_recalc
    def stamina_cost_per_action(self, action: ActionType) -> int:
        action_data = states.get(action)
        return action_data.stamina_cost + self._base_stamina_expense if action_data else 0

    @lazy_recalc
    def stamina_cost_per_frame(self, action: ActionType) -> int:
        action_data = states.get(action)
        return action_data.stamina_cost_frame + self._base_stamina_expense if action_data else 0

    @lazy_recalc
    def stamina_cost_on_response(self, response: Response):
        match response.type:
            case Responses.HAS_BLOCKED:
                return self.shield.weight + 2 * response.value - self.shield.defense
            case Responses.HAS_BEEN_BLOCKED:
                return self.weapon.weight + response.value
            case Responses.HAS_BEEN_PARRIED:
                return INSTANT_STUN

        return 0

    @lazy_recalc
    def hp_cost_on_response(self, response: Response):
        match response.type:
            case Responses.HAS_BEEN_ATTACKED:
                return response.value - self._armour.defense

        return 0

    @lazy_recalc
    def get_event(self, event_type: Events) -> Optional[Event]:
        match event_type:
            case Events.ATTACK:
                return Event(event_type, self._weapon.base_damage)
            case Events.CRITICAL_ATTACK:
                return Event(Events.ATTACK, self._weapon.critical_damage)
            case Events.BLOCK:
                return Event(event_type, self._shield.defense)
            case Events.PARRY:
                return Event(event_type)
            case Events.DEAD:
                return Event(event_type)

        return Event(Events.NONE)

    def damage_value(self) -> int:
        return self.weapon.base_damage

    def critical_damage_value(self) -> int:
        return self.weapon.critical_damage
