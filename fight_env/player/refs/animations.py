from typing import Dict

from fight_env.animation import Animation
from fight_env.player.refs.tasks import FighterTask

animations: Dict[FighterTask, Animation] = {
    FighterTask.ATTACK_1: Animation(       name="attack_1",        sprite_file_name="Attack_1.png"),
    FighterTask.ATTACK_2: Animation(       name="attack_2",        sprite_file_name="Attack_2.png"),
    FighterTask.ATTACK_3: Animation(       name="attack_3",        sprite_file_name="Attack_3.png"),
    FighterTask.BLOW_TO_SHIELD: Animation( name="blow_to_shield",  sprite_file_name="Blow_to_shield.png"),
    FighterTask.DEAD: Animation(           name="dead",            sprite_file_name="Dead.png"),
    FighterTask.DEFENSE: Animation(        name="defense",         sprite_file_name="Defense.png"),
    FighterTask.FIGHTING_STANCE: Animation(name="fighting_stance", sprite_file_name="Fighting_Stance.png"),
    FighterTask.HURT: Animation(           name="hurt",            sprite_file_name="Hurt.png"),
    FighterTask.IDLE: Animation(           name="idle",            sprite_file_name="Idle.png"),
    FighterTask.JUMP: Animation(           name="jump",            sprite_file_name="Jump.png"),
    FighterTask.JUMP_STRIKE: Animation(    name="jump_strike",     sprite_file_name="Jump_Strike.png"),
    FighterTask.PARRY: Animation(          name="parry",           sprite_file_name="Parry.png"),
    FighterTask.POWER_PUNCH_1: Animation(  name="power_punch_1",   sprite_file_name="Power_punch_1.png"),
    FighterTask.POWER_PUNCH_2: Animation(  name="power_punch_2",   sprite_file_name="Power_punch_2.png"),
    FighterTask.RIPOSTE: Animation(        name="riposte",         sprite_file_name="Riposte.png"),
    FighterTask.ROLLING: Animation(        name="rolling",         sprite_file_name="Rolling.png"),
    FighterTask.RUN: Animation(            name="run",             sprite_file_name="Run.png"),
    FighterTask.SHIELD_STRIKE: Animation(  name="shield_strike",   sprite_file_name="Shield_Strike.png"),
    FighterTask.STUNNED: Animation(        name="stunned",         sprite_file_name="Stunned.png"),
    FighterTask.WALK: Animation(           name="walk",            sprite_file_name="Walk.png"),
}