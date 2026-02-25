import time
import numpy as np
from typing import Optional, Tuple

from gymnasium import spaces
from stable_baselines3 import DQN

from main import ABCAvoidBEnv, Rewards


class ABCAvoidBBoxEnv(ABCAvoidBEnv):
    """Wraps ABCAvoidBEnv with Box observation space for SB3 compatibility."""

    def __init__(self, rewards: Rewards = Rewards(), render_mode: Optional[str] = None):
        super().__init__(rewards=rewards, render_mode=render_mode)
        self.observation_space = spaces.Box(
            low=0,
            high=max(self.n_rows, self.n_cols) - 1,
            shape=(2,),
            dtype=np.float32,
        )

    def _to_obs(self, pos: Tuple[int, int]) -> np.ndarray:
        return np.array(pos, dtype=np.float32)


# Train
env = ABCAvoidBBoxEnv()
model = DQN(
    "MlpPolicy",
    env,
    learning_rate=1e-3,
    buffer_size=10_000,
    learning_starts=500,
    batch_size=64,
    gamma=0.95,
    exploration_fraction=0.3,
    exploration_final_eps=0.05,
    verbose=1,
)
model.learn(total_timesteps=20_000)

# Run trained agent
action_names = ["UP", "RIGHT", "DOWN", "LEFT"]
env_vis = ABCAvoidBBoxEnv(render_mode="ansi")
s, _ = env_vis.reset()
print("\n--- Running trained agent ---")
print(env_vis.render())

done = False
step = 0
while not done:
    a, _ = model.predict(s, deterministic=True)
    s, r, terminated, truncated, _ = env_vis.step(int(a))
    done = terminated or truncated
    step += 1
    time.sleep(0.02)
    print(f"\nStep {step}: {action_names[int(a)]}, reward={r}")
    print(env_vis.render())