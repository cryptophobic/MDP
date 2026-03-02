from dataclasses import dataclass

from fight_env.player.states import FighterState


@dataclass
class PlayerModel:
    hp: int
    stamina: int

    state: FighterState
    action_frame: int
    action_start_frame: int

    # “candidates” can be grouped:
    hp_next: int
    stamina_next: int

    # optional
    flags: set[Flag]          # DEAD, STUNNED etc (or derived from hp/stamina)