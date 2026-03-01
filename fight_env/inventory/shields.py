from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict


class Shields(Enum):
    NONE = auto()
    BUCKLER = auto()
    WOODEN_SHIELD = auto()
    IRON_SHIELD = auto()

@dataclass(frozen=True)
class Shield:
    name: str
    defense: int = 0
    weight: int = 0


# TODO: going to expand it later with parrying, shield attacking etc abilities
shields: Dict[Shields, Shield] = {
    Shields.NONE: Shield(
        name='Bare hand',
    ),
    Shields.BUCKLER: Shield(
        name='Buckler',
        defense=1,
        weight=1,
    ),
    Shields.WOODEN_SHIELD: Shield(
        name='Wooden Shield',
        defense=1,
        weight=1,
    ),
    Shields.IRON_SHIELD: Shield(
        name='Iron Shield',
        defense=2,
        weight=2,
    )
}