from fight_env.player.player_model import PlayerModel
from fight_env.player.refs.tasks import FighterTask


class PlayerSnapshot:
    hp: int
    stamina: int
    max_hp: int
    max_stamina: int
    task: FighterTask
    frame_offset: int
    name: str

    def __init__(self, model: PlayerModel):
        self.hp = model.hp
        self.max_hp = model.stats.max_hp
        self.stamina = model.stamina
        self.max_stamina = model.stats.max_stamina
        self.task = model.task
        self.name = model.stats.name
        self.frame_offset = model.timeline.frame_offset
