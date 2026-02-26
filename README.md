# Fighting Environment

A prototype fighting game environment with RL training capabilities. Built as a foundation for a roguelite game inspired by Dead Cells.

## What's Done

### Combat System
- State machine with actions: IDLE, ATTACK, DEFENSE, PARRY, RIPOSTE, STUN, HURT, DEAD
- Stamina-based economy: actions cost stamina, stamina depletion causes STUN
- Parry timing window: successful parry stuns the opponent, opening a riposte opportunity
- Riposte promotion: attacks against stunned opponents auto-upgrade to critical hits
- Event-driven combat resolution between two fighters

### RL Training
- Gymnasium environment wrapping the fight logic (`fight_env/gym_env.py`)
- PPO training via Stable Baselines3 (`train_fight.py`)
- Observation space: `[stamina, action, frame, opp_action, opp_frame]`
- Agent successfully discovers parry -> riposte strategy on its own (500k timesteps)
- Visual playback of trained models (`play_model.py`)
- Scripted aggressive bot as training opponent (`fight_env/bots/aggressive.py`)

### Architecture
- Shared game logic in `Fight` class, reused by both visual game and gym env
- Three-phase tick: `resolve_next_action` -> `apply_action` -> `resolve_combat`
- Sprite-based rendering via pygame (decoupled from game logic)

## Roadmap

### Phase 1: Formalize Rules
- Extract combat rules into a data-driven config (damage tables, state transitions, action properties)
- Generate mermaid state diagrams from config to visualize state machine
- Document all transition conditions and priorities

### Phase 2: Expand Combat
- Movement and positioning (approach, retreat, spacing)
- Dodge / rolling mechanics
- Heavy attacks and defense breaking
- Focusing / target tracking
- Advanced bot behaviors

### Phase 3: RL Improvements
- Curriculum training (progressively harder bots)
- Reward shaping refinement
- Self-play training

### Phase 4: Engine Migration
- Target: Godot with GDExtension (C++)
- Rider as IDE for both GDScript and C++ development
- Port formalized combat rules to C++
- Keep Python env for RL training, export models for inference in Godot

## Project Structure

```
fight_env/
  actions.py       - Action types and data (frame counts, events, costs)
  state.py         - Fighter state machine
  fight.py         - Shared game logic (resolution, riposte promotion)
  events.py        - Event and response types
  gym_env.py       - Gymnasium wrapper for RL training
  config.py        - Game constants
  logger.py        - Debug logger with filtering
  bots/
    aggressive.py  - Scripted aggressive opponent
  ui/
    render.py      - Pygame rendering
    fighter.py     - Fighter sprite display
train_fight.py     - PPO training script
play_model.py      - Visual playback of trained model
```