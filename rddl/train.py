"""PPO training on the RDDL model instead of fight_env.

Same hyperparameters and same evaluation loop as `train_fight.py`; only the
environment differs. The combat rules come from `rddl/duel_domain.rddl`, the
opponent is the unmodified `fight_env/bots/aggressive.py`, and the reward
coefficients live in `rddl/duel_instance.rddl` so reward shaping can be varied
without touching any Python.

Run:  python -m rddl.train
"""

from stable_baselines3 import PPO

from rddl.train_env import RDDLFightEnv

TOTAL_TIMESTEPS = 500_000
EPISODES = 50
OUT = "fight_ppo_rddl"


def main() -> None:
    env = RDDLFightEnv(max_steps=500)

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
    model.learn(total_timesteps=TOTAL_TIMESTEPS)
    model.save(OUT)
    print(f"saved {OUT}.zip")

    wins = losses = 0
    for episode in range(EPISODES):
        obs, _ = env.reset()
        done = False
        episode_reward = 0.0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = env.step(int(action))
            done = terminated or truncated
            episode_reward += reward

        won = env.opponent_is_dead
        lost = env.agent_is_dead
        wins += won
        losses += lost
        result = "WIN" if won else "LOSS" if lost else "DRAW"
        print(f"Episode {episode + 1}: {result} (reward={episode_reward:.1f})")

    print(f"\nResults over {EPISODES} episodes:")
    print(f"  Wins:   {wins}")
    print(f"  Losses: {losses}")
    print(f"  Draws:  {EPISODES - wins - losses}")

    env.close()


if __name__ == "__main__":
    main()
