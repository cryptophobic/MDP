from stable_baselines3 import PPO

# CartPole-v1: balance a pole on a cart
# Observation: [cart_pos, cart_velocity, pole_angle, pole_angular_velocity] — 4 continuous floats
# Actions: 0 (push left), 1 (push right) — discrete
# Reward: +1 per step the pole stays upright
# Terminates: pole falls (angle > 12°) or cart leaves bounds
# Solved: average reward >= 475 over 100 episodes (max 500 steps)

env_id = "CartPole-v1"

model = PPO(
    "MlpPolicy",
    env_id,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    verbose=1,
)
model.learn(total_timesteps=100_000)

# Evaluate
import gymnasium as gym

env = gym.make(env_id, render_mode="human")
total_rewards = []
for episode in range(20):
    s, _ = env.reset()
    done = False
    episode_reward = 0
    while not done:
        a, _ = model.predict(s, deterministic=True)
        s, r, terminated, truncated, _ = env.step(int(a))
        done = terminated or truncated
        episode_reward += r
    total_rewards.append(episode_reward)
    print(f"Episode {episode + 1}: reward={episode_reward:.0f}")

print(f"\nMean reward over 20 episodes: {sum(total_rewards) / len(total_rewards):.1f}")
print("(Solved = 475+)")