from fight_env.player.player_model import PlayerModel


class Player:
    def __init__(self):
        self._model = PlayerModel()

    def start_new_frame(self):
        self._model.apply_state_next()
