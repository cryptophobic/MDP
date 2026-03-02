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

### Phase 1: Refactor — Stateless Combat Math
- Make `Stats` a pure data bag: equipment-derived numbers only (max_hp, max_stamina, weight, base_stamina_expense, shield_defense, armour_defense, base_damage, critical_damage, stamina_restore_per_frame)
- Extract combat formulas into stateless free functions / `combat_math` module:
  - `calc_stamina_cost(action_data, base_expense) -> int`
  - `calc_stamina_cost_per_frame(action_data, base_expense) -> int`
  - `calc_stamina_cost_on_response(response, shield, weapon) -> int`
  - `calc_hp_cost_on_response(response, armour_defense) -> int`
  - `build_event(event_type, weapon) -> Event`
- Extract combat rules into a data-driven config (damage tables, state transitions, action properties)
- Generate mermaid state diagrams from config to visualize state machine

### Phase 2: Refactor — Decompose State
- Split `State` into focused components:
  - `ActionStateMachine` — request/candidate/priority resolution/transitions
  - `ResourcePool` — hp/stamina current/candidate/apply pattern, reactive thresholds
  - `Position` / `Movement` — spatial state (prepared for Phase 3)
  - `ComboTracker` — combo chain state (prepared for Phase 3)
- `State` becomes a thin coordinator owning these components and orchestrating per-frame updates
- Each component handles its own slice: adding movement doesn't touch action logic, adding combos doesn't touch resource logic

### Phase 3: Expand Combat
- Movement and positioning (approach, retreat, spacing)
- Dodge / rolling mechanics with i-frames
- Combo chains
- Heavy attacks and defense breaking
- Expand observation space in gym_env to include position, combo state
- Advanced bot behaviors

### Phase 4: RL Improvements
- Curriculum training (progressively harder bots)
- Reward shaping refinement
- Self-play training

### Phase 5: Engine Migration
- Target: Godot with GDExtension (C++)
- Rider as IDE for both GDScript and C++ development
- Port formalized combat rules to C++
- Keep Python env for RL training, export models for inference in Godot

## Project Structure

```
fight_env/
  state/
    actions.py       - Action types and data (frame counts, events, costs)
    events.py        - Event/response types and resolution table
    state.py         - Fighter state coordinator
    stats.py         - Equipment and derived stat values (pure data)
  fight.py           - Shared game logic (tick orchestration, riposte promotion)
  gym_env.py         - Gymnasium wrapper for RL training
  config.py          - Game constants
  logger.py          - Debug logger with filtering
  bots/
    aggressive.py    - Scripted aggressive opponent
  ui/
    render.py        - Pygame rendering
    fighter.py       - Fighter sprite display
train_fight.py       - PPO training script
play_model.py        - Visual playback of trained model
```