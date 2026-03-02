from typing import Dict

from fight_env.animation import Animation
from fight_env.player.states import FighterState

animations: Dict[FighterState, Animation] = {
    FighterState.STUNNED: Animation(    name="stun",    sprite_file_name="Wounded.png"),
    FighterState.IDLE: Animation(       name="stance",  sprite_file_name="Fighting_Stance.png"),
    FighterState.ATTACK_1: Animation(   name="attack",  sprite_file_name="Attack_1.png"),
    FighterState.PARRY: Animation(      name="parry",   sprite_file_name="Parry.png"),
    FighterState.HURT: Animation(       name="hurt",    sprite_file_name="Hurt.png"),
    FighterState.RIPOSTE: Animation(    name="riposte", sprite_file_name="Prick.png"),
    FighterState.DEFENSE: Animation(    name="defense", sprite_file_name="Defense.png"),
    FighterState.DEAD: Animation(       name="dead",    sprite_file_name="Dead.png")
}
