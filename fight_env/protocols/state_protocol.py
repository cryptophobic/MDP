from typing import Protocol, runtime_checkable

from fight_env.player.tasks import FighterTask


@runtime_checkable
class StateProtocol(Protocol):
    task: FighterTask
    stamina: int
    hp: int
