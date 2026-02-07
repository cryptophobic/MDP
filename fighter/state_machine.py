from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict


class States(Enum):
    ATTACK = auto()
    IDLE = auto()
    DEAD = auto()
    PARRY = auto()
    BLOCK = auto()
    RIPOSTE = auto()
    STUNNED = auto()
    HURT = auto()

@dataclass
class State:
    state: States
    frames: int
    animation_path: str

states_collection: Dict[States, State] = {
    States.ATTACK: State(States.ATTACK, 4, "Attack_1.png"),
    States.IDLE: State(States.IDLE, 0, "Fighting_Stance.png"),
    States.DEAD: State(States.DEAD, 5, "Dead.png"),
    States.PARRY: State(States.PARRY, 4, "Parry.png"),
    States.BLOCK: State(States.BLOCK, 0, "Defense.png"),
    States.RIPOSTE: State(States.RIPOSTE, 5, "Prick.png"),
    States.STUNNED: State(States.STUNNED, 4, "Idke.png"),
    States.HURT: State(States.HURT, 4, "Hurt.png")
}


class StateMachine:

    def __init__(self):
        self.current_state = None

