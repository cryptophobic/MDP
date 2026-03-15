from typing import Dict

from fight_env.animation import Animation
from fight_env.player.refs.tasks import FighterTask

animations: Dict[FighterTask, Animation] = {
    FighterTask.STUNNED: Animation(    name="stun",    sprite_file_name="Wounded.png"),
    FighterTask.IDLE: Animation(       name="stance",  sprite_file_name="Fighting_Stance.png"),
    FighterTask.ATTACK_1: Animation(   name="attack",  sprite_file_name="Attack_1.png"),
    FighterTask.PARRY: Animation(      name="parry",   sprite_file_name="Parry.png"),
    FighterTask.HURT: Animation(       name="hurt",    sprite_file_name="Hurt.png"),
    FighterTask.RIPOSTE: Animation(    name="riposte", sprite_file_name="Prick.png"),
    FighterTask.DEFENSE: Animation(    name="defense", sprite_file_name="Defense.png"),
    FighterTask.DEAD: Animation(       name="dead",    sprite_file_name="Dead.png")
}
