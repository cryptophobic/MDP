from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict


class ArmourTypes(Enum):
    NONE = auto()
    LIGHT_ARMOUR = auto()
    HEAVY_ARMOUR = auto()

@dataclass(frozen=True)
class Armour:
    name: str
    defense: int = 0
    weight: int = 0


armour_types: Dict[ArmourTypes, Armour] = {
    ArmourTypes.NONE: Armour(
        name="Naked",
    ),
    ArmourTypes.LIGHT_ARMOUR: Armour(
        name="Light armour",
        defense=1,
        weight=1,
    ),
    ArmourTypes.HEAVY_ARMOUR: Armour(
        name="Heavy armour",
        defense=2,
        weight=2,
    )
}
