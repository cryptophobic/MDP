import numpy as np

from main import ABCAvoidBEnv

env = ABCAvoidBEnv()
nS = env.observation_space.n
nA = env.action_space.n

Q = np.zeros((nS, nA), dtype=np.float32)

alpha = 0.2
gamma = 0.95
eps = 0.2

for episode in range(500):
    s, _ = env.reset()
    done = False
    while not done:
        if np.random.rand() < eps:
            a = env.action_space.sample()
        else:
            a = int(np.argmax(Q[s]))

        s2, r, terminated, truncated, _ = env.step(a)
        done = terminated or truncated

        target = r + (0.0 if done else gamma * np.max(Q[s2]))
        Q[s, a] += alpha * (target - Q[s, a])
        s = s2

# Show learned Q-table
action_names = ["UP", "RIGHT", "DOWN", "LEFT"]
print("\nQ-table (best actions per state):")
for s in range(nS):
    best_a = int(np.argmax(Q[s]))
    print(f"  State {s}: {action_names[best_a]:5} (Q={Q[s, best_a]:.2f})")

# Run trained agent with visualization
print("\n--- Running trained agent ---")
env_vis = ABCAvoidBEnv(render_mode="ansi")
s, _ = env_vis.reset()
print(env_vis.render())

done = False
step = 0
while not done:
    a = int(np.argmax(Q[s]))  # greedy action (no exploration)
    s, r, terminated, truncated, _ = env_vis.step(a)
    done = terminated or truncated
    step += 1
    print(f"\nStep {step}: {action_names[a]}, reward={r}")
    print(env_vis.render())
