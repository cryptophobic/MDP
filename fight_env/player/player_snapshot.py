from fight_env.player.tasks import FighterTask
from fight_env.protocols.state_protocol import StateProtocol


class PlayerSnapshot(StateProtocol):
    hp: int
    stamina: int
    task: FighterTask
