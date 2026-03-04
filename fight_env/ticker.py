class Ticker:
    def __init__(self, initial_tick: int = 0):
        self._state = initial_tick

    def tick(self):
        self._state += 1

    def reset(self, initial_tick: int = 0):
        self._state = initial_tick

    @property
    def state(self):
        return self._state

ticker = Ticker()
