from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict


class Weapons(Enum):
    NONE = auto()
    GLADIUS = auto()
    ZWEIHANDER = auto()

@dataclass(frozen=True)
class Weapon:
    name: str
    base_damage: int = 1
    critical_damage: int = 3
    weight: int = 0


weapons: Dict[Weapons, Weapon] = {
    Weapons.NONE: Weapon(
        name="Punch",
    ),
    Weapons.GLADIUS: Weapon(
        name="Gladius",
        base_damage=2,
        critical_damage=8,
        weight=1,
    ),
    Weapons.ZWEIHANDER: Weapon(
        name="Zweihänder",
        base_damage=3,
        critical_damage=9,
        weight=2,
    )
}