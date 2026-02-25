from stable_baselines3 import PPO
from fight_env.gym_env import FightEnv, AGENT_ACTIONS

env = FightEnv(max_steps=500)

model = PPO(
    "MlpPolicy",
    env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    verbose=1,
)
model.learn(total_timesteps=500_000)
model.save("fight_ppo")

# Evaluate
action_names = ["NONE", "ATTACK", "DEFENSE", "PARRY"]
total_wins = 0
total_losses = 0
episodes = 50

for episode in range(episodes):
    s, _ = env.reset()
    done = False
    episode_reward = 0
    while not done:
        a, _ = model.predict(s, deterministic=True)
        s, r, terminated, truncated, _ = env.step(int(a))
        done = terminated or truncated
        episode_reward += r

    won = env.opponent.is_dead
    lost = env.agent.is_dead
    total_wins += won
    total_losses += lost
    result = "WIN" if won else "LOSS" if lost else "DRAW"
    print(f"Episode {episode + 1}: {result} (reward={episode_reward:.1f})")

print(f"\nResults over {episodes} episodes:")
print(f"  Wins:   {total_wins}")
print(f"  Losses: {total_losses}")
print(f"  Draws:  {episodes - total_wins - total_losses}")