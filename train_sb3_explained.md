# train_sb3.py — Line by Line

## Observation Space: `spaces.Box`

```python
self.observation_space = spaces.Box(
    low=0,
    high=max(self.n_rows, self.n_cols) - 1,
    shape=(2,),
    dtype=np.float32,
)
```

`spaces.Box` defines a continuous observation space — a float vector with bounds.

- **`low=0`** — minimum value for each element. Since we pass a scalar, it applies to all elements. Could also be an array like `np.array([0, 0])` for per-element bounds.
- **`high=4`** — maximum value (5x5 grid, indices 0–4). Same scalar-to-all rule. The neural net uses these bounds for input normalization internally.
- **`shape=(2,)`** — the observation is a 1D array of 2 floats: `[row, col]`. This is what the neural net receives as input at each step.
- **`dtype=np.float32`** — SB3 expects float32. Must match what `_to_obs` returns.

**Why Box instead of Discrete?** A `Discrete(25)` observation is a single integer (0–24). The neural net sees "state 12" and "state 13" as unrelated numbers — it can't learn that they're adjacent cells. With `Box(shape=(2,))`, the net sees `[2, 2]` and `[2, 3]` and can learn spatial relationships. This is critical for generalization.

**Normalization hint:** SB3 doesn't auto-normalize Box observations. Values in [0, 4] are fine, but if your fighting env has mixed scales (hp 0–6, action 0–17, frame 0–8), consider normalizing to [0, 1] or [-1, 1]. Large value differences between features make training harder for neural nets.

```python
def _to_obs(self, pos: Tuple[int, int]) -> np.ndarray:
    return np.array(pos, dtype=np.float32)
```

Overrides the parent's `_to_obs` which returned an int. Now returns `np.array([row, col], dtype=np.float32)` to match `spaces.Box`. This is called by both `reset()` and `step()` in the parent class, so the override covers everything.

## DQN Model Init

```python
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
```

### `"MlpPolicy"`

The neural network architecture. "Mlp" = Multi-Layer Perceptron (fully connected layers). Default is two hidden layers of 64 neurons each: `input(2) → 64 → 64 → output(4)`.

The network takes the observation `[row, col]` and outputs a Q-value for each of the 4 actions. The agent picks the action with the highest Q-value (same idea as your Q-table, but the "table" is approximated by a neural net).

You can customize the architecture:
```python
policy_kwargs = dict(net_arch=[128, 128])  # two layers of 128
model = DQN("MlpPolicy", env, policy_kwargs=policy_kwargs)
```

For a 5x5 grid, the default 64x64 is already overkill. For the fighting env it should be reasonable.

### `env`

The Gymnasium environment. DQN reads `env.observation_space` and `env.action_space` to configure the network's input/output dimensions.

### `learning_rate=1e-3`

Step size for the neural net optimizer (Adam). Analogous to `alpha` in your tabular Q-learning.
- Too high → training is unstable, Q-values oscillate
- Too low → training is slow, may not converge in time
- Typical range: 1e-4 to 1e-3

### `buffer_size=10_000`

**Replay buffer** size. DQN stores past transitions `(state, action, reward, next_state, done)` and samples from them randomly during training. This is a key difference from tabular Q-learning where you learn from each transition once and immediately.

Benefits of replay:
- Breaks correlation between consecutive experiences
- Reuses past experience (data efficient)
- Stabilizes training

For this small grid, 10k is plenty. For the fighting env you might want 50k–100k.

### `learning_starts=500`

Number of random steps before training begins. The agent first fills the replay buffer with random exploration, then starts learning. This ensures the network trains on diverse experiences from the start rather than the first few correlated transitions.

### `batch_size=64`

How many transitions are sampled from the replay buffer per training update. Larger batches = more stable gradients but slower updates. 32–256 is typical.

### `gamma=0.95`

Discount factor — identical to `gamma` in your tabular Q-learning. How much the agent values future rewards vs immediate ones. 0.95 means a reward 10 steps away is worth `0.95^10 ≈ 0.60` of its face value.

### `exploration_fraction=0.3`

DQN uses epsilon-greedy exploration (same as your tabular code). This controls how quickly epsilon decays:
- Starts at `exploration_initial_eps` (default 1.0 = fully random)
- Linearly decays to `exploration_final_eps` over `exploration_fraction * total_timesteps` steps
- With 20,000 timesteps and fraction 0.3: epsilon goes from 1.0 to 0.05 over the first 6,000 steps

### `exploration_final_eps=0.05`

Minimum exploration rate. After decay, the agent still takes a random action 5% of the time. Prevents the agent from getting permanently stuck in a suboptimal policy.

### `verbose=1`

Print training progress to stdout.

## Training

```python
model.learn(total_timesteps=20_000)
```

Runs 20,000 environment steps total. Each step:
1. Agent observes state, picks action (epsilon-greedy)
2. Environment returns (next_state, reward, done)
3. Transition stored in replay buffer
4. Neural net trained on a random batch from the buffer
5. If episode ends (terminated/truncated), environment resets automatically

**How this differs from your tabular loop:** Your loop ran 500 episodes. SB3 counts total steps across all episodes. If each episode averages ~5 steps, 20,000 steps ≈ 4,000 episodes.

## Inference

```python
a, _ = model.predict(s, deterministic=True)
```

- `model.predict()` returns `(action, hidden_states)`. Hidden states are None for MlpPolicy (used by recurrent policies).
- `deterministic=True` means pick the best action (no exploration). Equivalent to `np.argmax(Q[s])` in your tabular code.

## Why It Might Not Be Working Well

A few likely reasons for the agent getting stuck:

- **Too few timesteps** — 20,000 may not be enough. DQN has overhead (replay buffer warmup, target network updates) that tabular Q-learning doesn't. Try 50,000–100,000.
- **Exploration schedule** — with `exploration_fraction=0.3`, epsilon hits 0.05 at step 6,000. The agent may lock into a bad policy before exploring enough. Try `exploration_fraction=0.5` or higher.
- **Overkill for the problem** — a 5x5 grid with 4 actions is trivially solved by tabular Q-learning in 500 episodes. DQN's neural net, replay buffer, and target network add complexity that hurts more than it helps on toy problems. DQN shines when the state space is too large for a table.
- **No truncation/max steps** — if the agent wanders without hitting B or C, episodes run forever. Add a step limit: `truncated = (self.step_count > 50)` in your env's `step()`. This gives the agent negative reward signal from the step cost and prevents infinite episodes.

## What to Read Next

### SB3 Docs
- DQN: https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html
- Custom environments: https://stable-baselines3.readthedocs.io/en/master/guide/custom_env.html

### Key Concepts to Understand
- **Replay buffer** — why random sampling from past experience stabilizes training (breaks temporal correlation)
- **Target network** — DQN uses a second "frozen" copy of the Q-network to compute targets, updated periodically. Prevents the "moving target" problem. Controlled by `target_update_interval` and `tau` params.
- **Observation normalization** — for the fighting env, wrapping with `VecNormalize` or manually scaling features to [0,1] will likely be important.

### Alternative Algorithms in SB3
- **PPO** (`from stable_baselines3 import PPO`) — on-policy, simpler to tune, often works well out of the box. Good first try for the fighting env.
- **A2C** — simpler/faster PPO variant, good for quick experiments.
- **DQN** — best when you want direct comparison with Q-learning, works only with discrete actions.

### Hyperparameter Tuning
SB3 integrates with Optuna for automated tuning:
https://github.com/DLR-RM/rl-baselines3-zoo — has tuned hyperparameters for many environments as reference.