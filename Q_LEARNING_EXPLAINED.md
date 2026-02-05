# Q-Learning Algorithm Explained

This document explains the Q-learning implementation in `train.py`.

---

## 1. Q-Table Initialization

```python
Q = np.zeros((nS, nA), dtype=np.float32)
```

- **Q-table** is a 2D array: rows = states, columns = actions
- `nS` = number of states (9 for a 3x3 grid)
- `nA` = number of actions (4: UP, RIGHT, DOWN, LEFT)
- Initialized to zeros — the agent knows nothing initially
- `Q[s, a]` represents: "expected cumulative reward if I take action `a` in state `s` and act optimally thereafter"

---

## 2. Hyperparameters

```python
alpha = 0.2   # learning rate
gamma = 0.95  # discount factor
eps = 0.2     # exploration rate
```

### `alpha` (learning rate) = 0.2
Controls how much new information overrides old.
- `alpha = 0` — never learn (Q stays at zero)
- `alpha = 1` — completely replace old value with new target
- `alpha = 0.2` — blend: 20% new info, 80% old estimate

Higher alpha learns faster but can be unstable. Lower alpha is more stable but slower.

### `gamma` (discount factor) = 0.95
Controls how much the agent cares about future rewards.
- `gamma = 0` — only care about immediate reward (greedy)
- `gamma = 1` — future rewards are as important as immediate
- `gamma = 0.95` — future rewards matter, but slightly less than immediate

Why discount?
1. Mathematically ensures convergence (infinite sums stay finite)
2. Models uncertainty — distant future is less predictable
3. Encourages faster solutions

### `eps` (epsilon / exploration rate) = 0.2
Controls exploration vs exploitation tradeoff.
- With probability `eps` (20%) — take a **random** action (explore)
- With probability `1 - eps` (80%) — take the **best known** action (exploit)

Without exploration, the agent might never discover better paths.

---

## 3. Training Loop Structure

```python
for episode in range(500):
    s, _ = env.reset()
    done = False
    while not done:
        # ... (action selection and learning)
```

### Outer loop: Episodes
- An **episode** = one complete run from start to terminal state
- 500 episodes gives the agent 500 attempts to learn
- Each episode starts fresh at state A

### Inner loop: Steps within an episode
- Continues until `done = True` (reached goal C or bad state B)
- Each step: observe state, choose action, receive reward, update Q

---

## 4. Epsilon-Greedy Action Selection

```python
if np.random.rand() < eps:
    a = env.action_space.sample()   # random action
else:
    a = int(np.argmax(Q[s]))        # best known action
```

This is the **epsilon-greedy policy**:

| Random number | Action | Purpose |
|---------------|--------|---------|
| < 0.2 | Random | **Explore** — try new things, might find better paths |
| >= 0.2 | Best Q-value | **Exploit** — use what we've learned |

### Why not always exploit?
Early in training, Q-values are all zero (or wrong). Without exploration, the agent would:
1. Pick arbitrarily (all Q equal)
2. Maybe find a suboptimal path
3. Never try alternatives

### Why not always explore?
Random actions don't use learned knowledge. The agent would never follow its learned policy.

### `np.argmax(Q[s])`
Returns the action index with highest Q-value for state `s`.
Example: if `Q[s] = [0.1, 0.8, 0.3, 0.2]`, argmax returns `1` (RIGHT has highest value).

---

## 5. Environment Interaction

```python
s2, r, terminated, truncated, _ = env.step(a)
done = terminated or truncated
```

`env.step(a)` returns:
- `s2` — new state after taking action
- `r` — reward received (-0.01 for step, +1.0 for goal, -1.0 for bad)
- `terminated` — True if reached terminal state (C or B)
- `truncated` — True if episode cut short (time limit, not used here)
- `_` — info dict (unused)

---

## 6. The Bellman Update (Core of Q-Learning)

```python
target = r + (0.0 if done else gamma * np.max(Q[s2]))
Q[s, a] += alpha * (target - Q[s, a])
```

This is where learning happens.

### Step 1: Compute the target

```python
target = r + gamma * max(Q[s2])
```

The **Bellman equation** says the true Q-value should equal:
```
Q(s, a) = immediate_reward + discounted_future_value
        = r + gamma * max_a'(Q(s', a'))
```

- `r` — reward we just received
- `gamma * max(Q[s2])` — best possible future value from new state
- If `done`, there's no future, so future value = 0

### Step 2: Update Q toward target

```python
Q[s, a] += alpha * (target - Q[s, a])
```

This is **temporal difference (TD) learning**:

```
new_Q = old_Q + alpha * (target - old_Q)
      = old_Q + alpha * error
```

- `target - Q[s, a]` = **TD error** (how wrong our estimate was)
- If target > Q[s,a]: error is positive, Q increases
- If target < Q[s,a]: error is negative, Q decreases
- `alpha` controls step size

Equivalent formulation:
```
new_Q = (1 - alpha) * old_Q + alpha * target
      = 80% old estimate + 20% new evidence
```

---

## 7. State Transition

```python
s = s2
```

Move to the new state for the next iteration of the inner loop.

---

## Visual Summary

```
Episode loop:
  Start at A (state 0)

  Step loop:
    ┌─────────────────────────────────────────────────┐
    │  Current state: s                               │
    │                                                 │
    │  1. Choose action a (epsilon-greedy)            │
    │     - 20% random exploration                    │
    │     - 80% best Q-value exploitation             │
    │                                                 │
    │  2. Take action: s2, r = env.step(a)            │
    │                                                 │
    │  3. Compute target:                             │
    │     target = r + gamma * max(Q[s2])             │
    │                                                 │
    │  4. Update Q-table:                             │
    │     Q[s,a] += alpha * (target - Q[s,a])         │
    │                                                 │
    │  5. Move: s = s2                                │
    └─────────────────────────────────────────────────┘

  Repeat until terminal state (C or B)
```

---

## Convergence

With enough episodes, Q-values converge to **optimal values** — the true expected return for each state-action pair. The learned policy (always pick `argmax(Q[s])`) becomes optimal.

Requirements for convergence:
1. Every state-action pair visited infinitely often (epsilon > 0 ensures this)
2. Learning rate decreases over time (or is small enough)
3. MDP is finite

In practice, 500 episodes is plenty for a 3x3 grid.