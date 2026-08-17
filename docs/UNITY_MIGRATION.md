# Unity Migration — As-Built Status (2026-07-26)

> This section reflects what is **actually built and running**. The original
> plan (which assumed ML-Agents) is preserved below the divider — its guiding
> **two-layer principle** was followed faithfully; the training-stack decision
> and a few not-yet-built pieces changed. Read this section first.

## Decision change: ML-Agents → Path B (Python trains, Unity infers)

We did **not** adopt Unity ML-Agents. Instead: **training stays in the existing
Python/SB3 PPO pipeline**; Unity runs the trained policy for play/visualization
via the **Unity Inference Engine** (formerly Sentis) over an exported ONNX model.
Rationale: a working `fight_ppo.zip` already existed, Python iteration is fast,
and reproducing the deterministic tick core in C# is required for *inference*
anyway — so ML-Agents' engine-bound training loop bought nothing.

## The whole pipeline in one line

`train_fight.py` (SB3 PPO) → `export_onnx.py` → `fight_ppo.onnx` → Unity
Inference Engine → **the same verified `FightCore`** → `FighterView` draws it.
Nothing behavioural lives in Unity that wasn't in the Python project.

## What's done (all verified)

| Milestone | Status | Where / proof |
|---|---|---|
| Combat core port (engine-free C#) | ✅ | `unity/Assets/FightCore/` (`noEngineReferences: true`) |
| **Parity** vs Python, frame-for-frame | ✅ | `parity/dump_trajectory.py` golden traces → `Assets/Tests/EditMode/ParityTests.cs` (+ headless `scratchpad/parity_runner`). All fixtures pass, incl. obs vector |
| Render layer (2D sprites + HUD) | ✅ | `unity/Assets/FightUnity/FightDemo.cs`, `FighterView.cs`; art sliced via `Editor/ArtSetup.cs` |
| ONNX export of trained policy | ✅ | `export_onnx.py` — validated 3000/3000 argmax vs `model.predict` (torch + onnxruntime) |
| In-engine inference | ✅ | `SentisPolicy.cs` + `FightDemo.AgentUsesPolicy`; trained agent fights autonomously |

## As-built file map (vs the plan's proposed structure)

| Plan proposed | Actually built | Note |
|---|---|---|
| `Assets/Combat/Core/` | `Assets/FightCore/` | Engine-free asmdef, same intent |
| `Combat/Presentation/` | `Assets/FightUnity/` | View + fixed-tick driver |
| `Combat/MLAgents/` | — replaced by `SentisPolicy.cs` + `export_onnx.py` | No ML-Agents |
| `Data/` ScriptableObjects | `TaskData.cs` / `Inventory.cs` (hardcoded C# tables) | Authoring-convenience layer **deferred**; tables mirror Python 1:1 |
| golden-trace parity harness | `parity/` + EditMode `ParityTests` | Built exactly as the plan urged |

## Plan items that held vs changed

**Held (as written):** two-layer authority split; engine-free core asmdef; exact
enum integer values; symmetric double-resolve + per-fighter response processing;
`(a,b)`→`(a,ANY)` first-match resolver order; seeded `System.Random` bots kept
*out* of the core (`FightUnity/AggressiveBot.cs`); `Orchestrator.Flow()` ==
`DuelSim.Step()` tick ordering; **no `Time.deltaTime` in the core** — `FightDemo`
uses a fixed 120 ms accumulator.

**Changed / deferred:** no ML-Agents `Agent`/`DuelManager`; **observations are
NOT normalized** — we reuse the already-trained model, so `Observation.cs` must
reproduce the exact raw ranges `gym_env._get_obs` trained on (normalizing now
would break the frozen policy; revisit only if retraining); ScriptableObject
authoring not yet built.

## Package gotcha (important)

The inference package is **`com.unity.ai.inference`** (Package Manager → Add by
name), NOT `com.unity.sentis`. Assembly + namespace are `Unity.InferenceEngine`.
Because `FightUnity` is a **custom asmdef**, it does **not** inherit
`autoReferenced` packages — `Unity.InferenceEngine` had to be added explicitly to
`FightUnity.asmdef` references (same as UGUI would). Same lesson: any package API
used from a custom asmdef needs an explicit reference.

---

# Unity Migration Plan — Dueling Env + ML-Agents

> ⚠️ **Original plan below — superseded in part.** Kept for its architecture
> rationale (two-layer principle, concept mapping, tick ordering, gotchas), which
> still applies. The ML-Agents training path was **not** taken — see the
> As-Built section above.

Decisions locked in:
- **Training stack:** Unity ML-Agents (train with `mlagents-learn`, PPO/SAC; ONNX inference in-engine at play time).
- **Combat resolution:** Port the central `resolution_table` to a deterministic C# resolver. Unity is used for authoring, presentation, and the training harness — **not** as the combat-logic authority.

---

## 0. Guiding principle: two layers

The single most important architectural rule for this migration:

| Layer | Authority | Runs headless / fast | Built from |
|-------|-----------|----------------------|------------|
| **Logic core** (combat sim) | Yes — source of truth | Yes, deterministic | Plain C# structs/classes, no `MonoBehaviour`, no Animator |
| **Presentation** (animation, VFX, UI) | No — mirrors the core | Skipped during training | `MonoBehaviour`, `Animator`, real Animation Events |

Your combat tick must produce identical results whether or not anything is rendered. That means **the frame-indexed event table stays the authority** (`ATTACK_1` emits `ATTACK` at frame offset 2). The Unity Animator only *reacts* to core state to look right for a human. Coupling combat to `Animator` playback = non-deterministic training. Don't.

The "Unity events are convenient" win you're after is delivered by **ScriptableObject task definitions** (inspector-editable timelines) + C# `event`/`Action` callbacks in the presentation layer — not by making the Animator authoritative.

---

## 1. Concept mapping (Python → C#/Unity)

| Python (`fight_env/`) | Unity/C# target | Notes |
|---|---|---|
| `player/refs/events.py` `Events`/`Responses` enums | C# `enum Events`, `enum Responses` | 1:1 copy. |
| `resolution_table` + `Rule(when, emit)` | `CombatResolver` class with a `Dictionary<(Events,Events), List<Rule>>` | Port `when`/`emit` lambdas to `Func<Event,Event,bool>` / `Func<Event,Event,(Response,Response)>`. Keep the `(A, ANY)` fallback lookup. |
| `player/refs/tasks.py` `tasks_data` (`TaskData`) | `TaskDefinition : ScriptableObject` | One asset per task. `events` dict → serialized list of `(frameOffset, Events)`. **This is your authoring-convenience layer.** |
| `TaskTimeline` (frame_number, duration, loop, frame_offset, current_event) | plain C# `struct/class TaskTimeline` | Pure logic, no Unity types. |
| `player/refs/intents.py` `ActionType` + `intent_task_mapping` | `enum ActionType` + `CombatResolver`/agent action decode | `ActionType` == ML-Agents discrete action branch. |
| `player/player_model.py` `PlayerModel` | plain C# class `FighterState` | Mutable per-fighter state. No `MonoBehaviour`. |
| `player/player.py` `Player` (tick/fallback/process_intent/reactive/cleanup) | `Fighter` (plain C#) | Methods port almost verbatim. |
| `player/processing/*.py` (task/intent/reactive/response) | `Processing/*.cs` static classes | Straight port; these are pure functions over `FighterState`. |
| `orchestrator/orchestrator.py` `Orchestrator.flow()` | `DuelSim.Step()` (plain C#) | The deterministic tick. **Reused by both training and play.** |
| `orchestrator/duel_orchestrator.py` `DuelOrchestrator.resolve()` | folded into `CombatResolver` / `DuelSim` | Symmetric double-resolve (`resolve(a,b)` and `resolve(b,a)`) stays. |
| `player/stats.py`, `inventory/*` | `Stats`, `Weapon`/`Shield`/`Armour` (ScriptableObjects or structs) | Lazy-recalc pattern → simple recompute or cached props. |
| `bots/*.py` (Aggressive, etc.) | `IPolicy` C# impls (scripted opponents) | Keep for curriculum / self-play baseline opponents. |
| `ticker.py` | drop | Replaced by `DuelSim` step counter. |
| `gym_env.py` `FightEnv` | `FighterAgent : Agent` (ML-Agents) + `DuelManager : MonoBehaviour` | Observations, action decode, reward, episode termination move here. |
| `main.py` / `ui/`, `animation.py` (pygame) | Unity scene + Animator + `DuelManager` | Presentation only. |

---

## 2. Target Unity project structure

```
Assets/
  Combat/
    Core/                 # NO UnityEngine dependency — pure C#, unit-testable
      Enums.cs            # Events, Responses, ActionType, FighterTask
      Event.cs, Response.cs
      TaskTimeline.cs
      FighterState.cs
      Fighter.cs
      CombatResolver.cs   # port of resolution_table
      DuelSim.cs          # port of Orchestrator.flow() -> Step()
      Processing/
        TaskProcessing.cs
        IntentProcessing.cs
        ReactiveProcessing.cs
        ResponseProcessing.cs
      Policies/
        IPolicy.cs, AggressivePolicy.cs, ...
    Data/                 # ScriptableObjects (authoring / "Unity events")
      TaskDefinition.cs   # duration, loop, priority, stamina, frame->Events list
      WeaponData.cs, ShieldData.cs, ArmourData.cs
      Tasks/*.asset       # ATTACK_1.asset, PARRY.asset, ...
    MLAgents/
      FighterAgent.cs     # Agent: CollectObservations, OnActionReceived, reward
      DuelManager.cs      # owns DuelSim, drives ticks, EndEpisode
    Presentation/         # visual only, skipped headless
      FighterView.cs      # reads FighterState -> drives Animator
      AnimationBindings   # real AnimationClip events for SFX/VFX
  Tests/
    CombatCoreTests.cs    # EditMode tests -> parity vs Python golden traces
```

Rule of thumb: anything in `Core/` must compile without `using UnityEngine;`. Enforce it with an asmdef that has no Unity reference — this guarantees the sim stays engine-independent and testable.

---

## 3. The combat tick (heart of the port)

`Orchestrator.flow()` becomes `DuelSim.Step()`. Preserve the exact ordering — it encodes your game feel:

```
Step(actionA, actionB):
  1. snapshotA = A.MakeSnapshot();  snapshotB = B.MakeSnapshot()
  2. A.SetIntent(actionA);          B.SetIntent(actionB)   // from agents/policies
  3. A.Tick();                      B.Tick()               // process_current_task, materialize event, timeline.tick
  4. (aRes, bRes) = CombatResolver.Resolve(A.Event, B.Event)   // symmetric double-resolve + process_responses
  5. A.Fallback();  A.ProcessIntent();  A.Reactive(snapshotA)  // same for B
  6. A.Cleanup(...); B.Cleanup(...)
  7. return (aRes, bRes)
```

Everything in steps 1–6 already exists in Python and ports mechanically. The only genuinely new code is the ML-Agents wrapper and the ScriptableObject loading.

### ML-Agents driving model (determinism-critical)

- `DuelManager` owns one `DuelSim`, `FighterAgent A`, `FighterAgent B`.
- Disable automatic stepping tied to physics. Drive the sim yourself so one **combat tick == one decision step**, independent of render frame rate:
  - Each combat tick: `A.RequestDecision(); B.RequestDecision();` → ML-Agents calls `CollectObservations` then `OnActionReceived` (which just stashes the chosen `ActionType`).
  - `DuelManager` then calls `sim.Step(actionA, actionB)`, computes rewards, calls `AddReward`, and `EndEpisode()` on death/timeout.
- Do **not** read time via `Time.deltaTime` in the core. The tick is logical, not wall-clock. This lets you crank `--time-scale` and run `--no-graphics` for fast training, and keeps runs reproducible.

---

## 4. Observations, actions, rewards (from `gym_env.py`)

- **Action space:** `Discrete(4)` → ML-Agents discrete branch of size 4 `[NONE, ATTACK, BLOCK, PARRY]` (`AGENT_ACTIONS`). Later consider action masking (e.g. mask ATTACK when stamina too low).
- **Observations (7 floats):** `[my_hp, my_stamina, my_task_idx, my_frame_offset, opp_hp, opp_task_idx, opp_frame_offset]` — same as `_get_obs`. In `CollectObservations`, **normalize** (divide hp by max_hp, etc.); ML-Agents PPO trains much better on ~[0,1]/[-1,1] inputs than your current raw ranges.
- **Reward:** port the `step()` reward logic verbatim (attack hit 0.3/1.0, parry 0.5, being hit −0.3/−1.0, win +5, death −5). Keep it in `DuelManager`/`FighterAgent` so it stays version-controlled next to the sim.
- **Self-play:** ML-Agents supports symmetric self-play natively (both agents share a Behavior Name; opponent snapshots managed by the trainer). Start with your `AggressivePolicy` as a fixed opponent, then switch on self-play in the trainer YAML.

---

## 5. Phased execution plan

**Phase 1 — Core port, no Unity engine (highest value, lowest risk).**
- Port `Core/` + `Data/` (as plain C# first; SO wrappers later). Enums, `Event/Response`, `TaskTimeline`, `FighterState`, `Fighter`, `Processing/*`, `CombatResolver`, `DuelSim`, `Stats`, inventory, `AggressivePolicy`.
- **Parity harness:** add a Python script that runs N seeded duels (both sides scripted policies) and dumps a golden trace (per tick: both tasks, hp, stamina, events, responses). Replay the same seed/policy in a C# EditMode test and assert identical traces. This is your safety net for the entire migration — build it early.
- Exit criterion: C# and Python produce byte-identical traces for a suite of seeded matchups.

**Phase 2 — ScriptableObject authoring layer.**
- Convert `tasks_data` and inventory tables to `.asset` files (`TaskDefinition`, `WeaponData`, ...). `DuelSim` reads from these instead of hardcoded data. Verify Phase-1 parity still holds.

**Phase 3 — ML-Agents integration.**
- `FighterAgent` + `DuelManager`. Wire observations/actions/rewards. Train vs `AggressivePolicy` with `mlagents-learn` (PPO). Confirm learning curve; sanity-check against whatever your current Python-trained agent achieves.

**Phase 4 — Self-play + curriculum.**
- Enable ML-Agents self-play; add scripted opponents (defensive/random ports) as curriculum stages. Export best policy to ONNX.

**Phase 5 — Presentation.**
- `FighterView` reads `FighterState` each tick and drives the `Animator`. Real Animation Events used only for SFX/VFX. This is the layer where "Unity events are convenient" pays off — but it stays cosmetic.

---

## 6. Gotchas / decisions to watch

- **Frame timing authority:** already covered — keep it in the event table, not the Animator. (#1 mistake to avoid.)
- **Enum values:** keep the exact integer values (`Events`, `Responses`, `FighterTask`, `ActionType`) so golden traces and any serialized data line up across languages.
- **Symmetric resolution:** `DuelOrchestrator` resolves both `(a,b)` and `(b,a)` and each fighter processes *its own* responses. Preserve exactly — it's why parry/block feel mutual.
- **`ANY` fallback lookup order:** resolver tries `(a.type, b.type)` then `(a.type, ANY)`. Keep order and first-match-wins semantics.
- **Randomness:** Python bots use `random.random()`. For reproducible C# parity tests, inject a seeded RNG (`System.Random`) into policies — don't use `UnityEngine.Random` in `Core/`.
- **Stamina/`INSTANT_STUN` edge cases** (`response_processing.py`): port carefully; these clamp against `STAMINA_BOTTOM_LIMIT`.
- **`max_steps` truncation** vs termination: ML-Agents `MaxStep` on the Agent handles truncation; deaths call `EndEpisode`.
- **Normalization:** raw observation ranges hurt PPO; normalize in `CollectObservations`.

---

## 7. What to reuse vs rewrite

- **Port ~verbatim (pure logic):** all `Processing/*`, `CombatResolver`, `DuelSim`, `TaskTimeline`, `FighterState`, `Stats`, bots.
- **Restructure:** `tasks_data`/inventory → ScriptableObjects.
- **Replace:** `gym_env.py` → ML-Agents `Agent`/`DuelManager`; pygame `ui/`+`animation.py` → Unity presentation; `ticker.py` → sim step counter.
- **Keep in Python:** the training driver is still Python (`mlagents-learn`) — so your RL familiarity carries over. Optionally keep the Python sim alive purely as the parity oracle.