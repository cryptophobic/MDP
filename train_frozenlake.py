
import argparse
import time

import gymnasium as gym
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--slippery", action="store_true", help="slippery ice (stochastic moves)")
parser.add_argument("--map", default="4x4", choices=["4x4", "8x8"])
parser.add_argument("--episodes", type=int, default=None, help="default: 5000 dry / 30000 slippery")
parser.add_argument("--render", default="human", choices=["human", "ansi"],
                    help="human = pygame window, ansi = text grid")
args = parser.parse_args()

episodes = args.episodes if args.episodes is not None else (30_000 if args.slippery else 5_000)

env = gym.make("FrozenLake-v1", map_name=args.map, is_slippery=args.slippery)
nS = env.observation_space.n
nA = env.action_space.n

Q = np.zeros((nS, nA), dtype=np.float32)

alpha = 0.1
gamma = 0.99
eps = 1.0          # start fully random...
eps_min = 0.05     # ...and decay towards mostly-greedy
eps_decay = (eps - eps_min) / (episodes * 0.8)

wins = 0
for episode in range(episodes):
    s, _ = env.reset()
    done = False
    while not done:
        if np.random.rand() < eps:
            a = env.action_space.sample()
        else:
            a = int(np.argmax(Q[s]))

        s2, r, terminated, truncated, _ = env.step(a)
        done = terminated or truncated

        current_q = Q[s, a]
        best_next_q = np.max(Q[s2])

        if terminated:
            target = float(r)
        else:
            target = float(r) + gamma * best_next_q

        # target = r + (0.0 if terminated else gamma * np.max(Q[s2]))
        td_error = target - current_q
        Q[s, a] = Q[s, a] + alpha * td_error
        s = s2

    wins += int(r > 0)
    eps = max(eps_min, eps - eps_decay)

    if (episode + 1) % max(1, episodes // 10) == 0:
        window = max(1, episodes // 10)
        print(f"episode {episode + 1:6}/{episodes}  success rate (last {window}): {wins / window:.2%}  eps={eps:.2f}")
        wins = 0

env.close()

# Show learned policy
action_names = ["LEFT", "DOWN", "RIGHT", "UP"]  # FrozenLake action order
side = int(np.sqrt(nS))
print("\nGreedy policy (best action per state):")
for row in range(side):
    cells = []
    for col in range(side):
        s = row * side + col
        cells.append("....." if Q[s].max() == 0 else f"{action_names[int(np.argmax(Q[s]))]:5}")
    print("  " + " ".join(cells))

# # Run trained agent with visualization
# print("\n--- Running trained agent ---")
env_vis = gym.make("FrozenLake-v1", map_name=args.map, is_slippery=args.slippery, render_mode=args.render)
s, _ = env_vis.reset()
if args.render == "ansi":
    print(env_vis.render())

done = False
step = 0
while not done:
    a = int(np.argmax(Q[s]))  # greedy action (no exploration)
    s, r, terminated, truncated, _ = env_vis.step(a)
    done = terminated or truncated
    step += 1
    time.sleep(0.3)
    print(f"\nStep {step}: {action_names[a]}, reward={r}")
    if args.render == "ansi":
        print(env_vis.render())

print("\nGOAL reached!" if r > 0 else "\nFell in a hole / timed out.")
time.sleep(1.0)
env_vis.close()