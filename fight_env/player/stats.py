from fight_env.inventory.armour import Armour, armour_types, ArmourTypes
from fight_env.inventory.shields import Shield, shields, Shields
from fight_env.inventory.weapons import Weapon, weapons, Weapons
from functools import wraps

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

    def damage_value(self) -> int:
        return self.weapon.base_damage

    def critical_damage_value(self) -> int:
        return self.weapon.critical_damage
