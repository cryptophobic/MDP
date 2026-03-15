from fight_env.inventory.armour import Armour, armour_types, ArmourTypes
from fight_env.inventory.shields import Shield, shields, Shields
from fight_env.inventory.weapons import Weapon, weapons, Weapons
from functools import wraps

from fight_env.player.refs.events import Events, Event
from fight_env.player.refs.tasks import TaskData

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
                 name: str = "",
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

    def _update_values(self):
        self._weight = self.armour.weight + self.shield.weight + self.weapon.weight
        # self._stamina_restore_value = BASE_STAMINA_RESTORE_VALUE_PER_FRAME
        self._base_stamina_expense = self._weight // 5

    @property
    def base_stamina_expense(self) -> int:
        return self._base_stamina_expense

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

    @property
    def damage_value(self) -> int:
        return self.weapon.base_damage

    @property
    def critical_damage_value(self) -> int:
        return self.weapon.critical_damage


def materialize_event(raw_event: Events, stats: Stats) -> Event:
    value_map = {
        Events.ATTACK: (Events.ATTACK, stats.damage_value),
        Events.CRITICAL_ATTACK: (Events.ATTACK, stats.critical_damage_value),
        Events.BLOCK: (Events.BLOCK, stats.shield.defense),
    }
    mapped_vent, value = value_map.get(raw_event, (raw_event, 0))
    return Event(mapped_vent, value)


def calc_stamina_cost_enter_task(task_data: TaskData, stats: Stats) -> int:
    return task_data.base_stamina_cost + stats.base_stamina_expense if task_data else 0


def calc_stamina_cost_frame(task_data: TaskData, stats: Stats) -> int:
    return task_data.base_stamina_cost_frame + stats.base_stamina_expense if task_data else 0

