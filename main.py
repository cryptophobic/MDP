from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

import gymnasium as gym
from gymnasium import spaces
import numpy as np


# Grid layout (2 rows x 2 cols):
# (0,0) = A (start)
# (0,1) = B (bad terminal)
# (1,0) = C (goal terminal)
# (1,1) = C (goal terminal)  <- C spans the whole bottom row like in your sketch

A = (0, 0)
B = {(0, 1), (1, 1), (2, 1), (3, 2), (2, 3), (1, 3)}
# C_CELLS = {(0, 2), (2, 0)}
C_CELLS = {(2, 2)}

UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3


@dataclass
class Rewards:
    step: float = -0.01   # tiny step cost to prefer faster solutions
    goal: float = +1.0    # reaching C
    bad: float = -1.0     # stepping into B


class ABCAvoidBEnv(gym.Env):
    """
    Minimal Gymnasium env:
    - Discrete state: 0..3 representing which of the 4 grid cells you're in.
    - Discrete actions: 4 (UP, RIGHT, DOWN, LEFT)
    - Terminal: reaching B (bad) or any C cell (goal)
    """

    metadata = {"render_modes": ["ansi"], "render_fps": 4}

    def __init__(self, rewards: Rewards = Rewards(), render_mode: Optional[str] = None):
        super().__init__()
        self.rewards = rewards
        self.render_mode = render_mode

        self.n_rows = 5
        self.n_cols = 5

        # 4 cells -> 4 discrete observations
        self.observation_space = spaces.Discrete(self.n_rows * self.n_cols)
        self.action_space = spaces.Discrete(4)

        self._pos: Tuple[int, int] = A

    def _to_obs(self, pos: Tuple[int, int]) -> int:
        row, column = pos
        return row * self.n_cols + column

    def _clamp(self, row: int, column: int) -> Tuple[int, int]:
        row = int(np.clip(row, 0, self.n_rows - 1))
        column = int(np.clip(column, 0, self.n_cols - 1))
        return (row, column)

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None):
        super().reset(seed=seed)
        self._pos = A
        obs = self._to_obs(self._pos)
        info = {}
        return obs, info

    def step(self, action: int):
        row, column = self._pos

        if action == UP:
            row -= 1
        elif action == RIGHT:
            column += 1
        elif action == DOWN:
            row += 1
        elif action == LEFT:
            column -= 1
        else:
            raise ValueError(f"Invalid action: {action}")

        self._pos = self._clamp(row, column)

        terminated = False
        truncated = False

        # default step reward
        reward = self.rewards.step

        if self._pos in B:
            terminated = True
            reward = self.rewards.bad
        elif self._pos in C_CELLS:
            terminated = True
            reward = self.rewards.goal

        obs = self._to_obs(self._pos)
        info = {}

        return obs, reward, terminated, truncated, info

    def render(self):
        if self.render_mode != "ansi":
            return None

        grid = [['A' for _ in range(self.n_rows)] for _ in range(self.n_cols)]
        for pos in B:
            grid[pos[0]][pos[1]] = "B"
        for pos in C_CELLS:
            grid[pos[0]][pos[1]] = "C"

        pr, pc = self._pos
        # Mark agent position
        grid[pr][pc] = f"[{grid[pr][pc]}]"

        lines = []
        line = []
        for i in range(self.n_rows):
            line.append("+---")
        line.append("+")
        divider = "".join(line)

        lines.append(divider)
        for i in range(self.n_rows):
            line = []
            for j in range(self.n_cols):
                line.append(f"{grid[i][j]:^3}")
            lines.append(f"|{"|".join(line)}|")
            lines.append(divider)
        return "\n".join(lines)


# --- Quick smoke test ---
if __name__ == "__main__":
    env = ABCAvoidBEnv(render_mode="ansi")
    obs, info = env.reset(seed=0)
    print("RESET:\n", env.render())

    # Try DOWN from A -> should hit C and terminate with +1
    obs, reward, terminated, truncated, info = env.step(DOWN)
    print("\nAFTER DOWN:")
    print(env.render())
    print("reward=", reward, "terminated=", terminated)
