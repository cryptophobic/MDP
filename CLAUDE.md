# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Two things in one tree:

1. **A 2D melee-duel environment + RL training pipeline** (`fight_env/`, `train_fight.py`), ported to Unity 6 (`unity/`) with a verified Python↔C# parity harness (`parity/`).
2. **The source material for a Ukrainian-language diploma thesis** (`docs/anotation.md`, `docs/vstup.md`, `docs/rl-in-industry.md`, `docs/bellman-q-learning.md`). Prose there is in Ukrainian and is written for an academic examiner, not for developers.

The research question driving the code: which training-configuration factors (algorithm, reward shaping, observation composition, opponent type) make an agent discover non-trivial tactics — specifically the emergent `parry → riposte` pattern.

## Commands

There is no `requirements.txt` and no packaging config — dependencies live in `.venv` (Python 3.14, gymnasium 1.2.3, stable_baselines3 2.7.1, torch 2.10, pygame-ce, onnx/onnxruntime). Use `.venv/bin/python` or activate the venv.

```bash
python -m fight_env.main        # play the pygame game (human vs scripted bot)
python train_fight.py           # PPO 500k steps -> fight_ppo.zip, then 50 eval episodes
python play_model.py            # visual playback of the trained policy
python export_onnx.py           # fight_ppo.zip -> fight_ppo.onnx (+ 3000-sample argmax validation)
python -m parity.dump_trajectory  # regenerate golden trajectories in parity/trajectories/
```

**Tests.** There is no pytest suite. The only correctness harness is the parity check:
Unity Editor → `Window > General > Test Runner > EditMode > Run All`. Each `parity/trajectories/*.json` fixture is one test case (`ParityTests.Replays_Fixture_Frame_For_Frame`), so running a single test = selecting one fixture in the Test Runner. The headless `scratchpad/parity_runner` referenced in `unity/README.md` and `docs/UNITY_MIGRATION.md` no longer exists on disk.

Unity version is pinned to `6000.5.3f1`.

## Architecture

### The tick pipeline is the contract

`Orchestrator.flow()` (`fight_env/orchestrator/orchestrator.py`) defines one logical frame, and its **ordering is mirrored exactly in C# `Orchestrator.Flow()`**. Changing the order breaks parity:

1. `make_snapshot()` on both fighters (pre-tick state, used later by reactive processing)
2. `tick()` on both — advances the task timeline and materializes the frame's raw event into a stat-adjusted `Event`
3. `DuelOrchestrator.resolve()` — the only place where fighters interact
4. `fallback()` → `process_intent()` → `reactive()` on both, each returning whether it won a transition
5. `cleanup()` — intent TTL bookkeeping

The `need = True` branch in `flow()` is a placeholder for a future distance check.

### Symmetric double resolution

`DuelOrchestrator.resolve()` calls `_resolve_duelists(e1, e2)` **and** `_resolve_duelists(e2, e1)`. Each fighter therefore ends the frame with **two** responses: `[own_action_outcome, outcome_of_being_targeted]`. This is why `gym_env.step` reads both `f1_res` and `f1_res2` when computing reward.

Lookup order inside `_resolve_duelists` is: exact `(e1.type, e2.type)` key first, then `(e1.type, Events.ANY)` fallback; within a key, the first `Rule` whose `when` predicate holds wins. New rules must respect this precedence — an `ANY` entry silently shadows nothing, but a mis-ordered specific rule does.

### Layered state machine

- `fight_env/player/refs/tasks.py` — `FighterTask` enum + the `tasks_data` table. **This table is the FSM spec**: duration, loop, per-frame `events`, priorities, stamina costs, interruptibility.
- `task_processing.try_transition` arbitrates: an expired timeline always yields; otherwise higher `priority` wins; on a tie, `start_priority` decides but **only at `frame_number == 0`**; failing that, `interruptible` on the current task lets the candidate through.
- Three transition sources compete each frame — `fallback` (→ FIGHTING_STANCE), `process_intent` (agent/bot request), `reactive` (`reactive_processing.process_changes`: dead → hurt → stunned → stance recovery). All go through the same `try_transition`.

### Riposte promotion — the tactic the research is about

An opponent in `STUNNED` emits `Events.STUNNED`, which the resolution table turns into `HAS_RIPOSTE_WINDOW_OPEN` for the *other* fighter. `intent_processing._resolve_attack` then silently upgrades an `ATTACK` intent into `FighterTask.RIPOSTE` (critical damage) while that response is present. Nothing tells the agent this exists — it must be discovered from reward.

### Stamina economy

Enter-cost + per-frame cost, drained in `process_current_task`. `stamina <= 0` → `STUNNED` via reactive processing. `STAMINA_BOTTOM_LIMIT = -4` allows going negative. `HAS_BEEN_PARRIED` uses the `INSTANT_STUN = 9999` sentinel in `response_processing`, which drains straight to the bottom limit — that is what makes parry → stun → riposte a real punish window.

### Deliberate gap: stats-adjusted stamina costs are not wired

`stats.calc_stamina_cost_enter_task` / `calc_stamina_cost_frame` exist but are **unused**. `task_processing.set_task` assigns raw `base_stamina_cost*` from `tasks_data` (see the `TODO` there). The C# port mirrors this deliberately. Wiring them up changes combat numerics — it requires regenerating fixtures and re-running parity, and it invalidates the frozen `fight_ppo` policy.

## The Python↔C# parity contract

This is the most important invariant in the repo. **Python is ground truth**; `unity/Assets/FightCore/` is correct iff it reproduces the fixtures frame-for-frame.

- `FightCore.asmdef` sets `noEngineReferences: true`. Keep it engine-free — MonoBehaviour and inference live in the separate `FightUnity` assembly.
- **Enum integer values must match exactly** across languages (`FighterTask`, `Events`, `Responses`, `ActionType`). Fixtures serialize them as ints.
- The observation vector is **not normalized**, by design: the trained model is frozen and was fit on raw ranges, so `Observation.cs` must reproduce `gym_env._get_obs` exactly. Normalizing requires retraining.
- The observation encoder is currently **duplicated in four places** — `gym_env._get_obs`, `parity/dump_trajectory._observation`, `play_model.get_obs`, and `unity/Assets/FightCore/Observation.cs`. They drift silently (this already caused one wrong-HP bug in playback), and only the first, second and fourth are covered by parity fixtures. Change all four together.
- Bots call `random.random()` and are therefore kept **out** of the core and out of fixtures — `dump_trajectory.py` drives both fighters with fixed action scripts instead.
- The C# core must never use `Time.deltaTime`. `FightDemo` drives it on a fixed 120 ms tick accumulator (`FRAME_DURATION` in `fight_env/config.py`).

**Any change to combat rules, `tasks_data`, `resolution_table`, or the observation encoder requires:** `python -m parity.dump_trajectory`, then re-run the Unity EditMode tests. A divergence is a port gap, not a flaky test.

The three fixtures deliberately cover the branches that matter: `attack_vs_idle` (plain hit), `attack_vs_block` (block vs defense-break threshold), `parry_then_riposte` (the full punish chain).

## Inference path

`train_fight.py` (SB3 PPO) → `export_onnx.py` → `fight_ppo.onnx` → Unity Inference Engine (`SentisPolicy.cs`) → the same verified `FightCore`.

- The ONNX graph outputs **action logits** `[1,4]`; argmax happens in C#. Opset 15.
- The Unity package is **`com.unity.ai.inference`** (namespace `Unity.InferenceEngine`), *not* `com.unity.sentis`. Custom asmdefs do not inherit auto-referenced packages, so `FightUnity.asmdef` references it explicitly.
- ML-Agents was evaluated and rejected — see `docs/UNITY_MIGRATION.md`, whose "As-Built" section supersedes the plan below its divider.

## Stale content to be aware of

- **`README.md` is out of date.** It describes a `fight_env/state/` + `fight.py` layout that no longer exists (the real layout is `player/` + `orchestrator/` + `inventory/`), states a 5-float observation space (it is 7), and its roadmap targets Godot — the actual engine work is Unity 6.
- Root `main.py`, `train.py`, `train_sb3*.py`, `train_frozenlake.py` are standalone gridworld/CartPole learning exercises unrelated to the fight environment. Do not confuse root `main.py` with `fight_env/main.py`.