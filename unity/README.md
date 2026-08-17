# FightCore (Unity 6) — RL playground port

C# port of the Python `fight_env` combat core, for Unity 6 (`6000.5.3f1`).
Training stays in the Python/SB3 gym; Unity runs the trained policy for
gameplay/visualization (inference via Sentis, added in a later phase).

## Layout

```
unity/
  Assets/
    FightCore/                 engine-free combat core (no UnityEngine deps)
      Refs.cs                  enums + Event/Response/Intent value types
      Inventory.cs             weapon/shield/armour tables
      Config.cs                constants (HP, stamina limits)
      Stats.cs                 derived stats + materialize_event
      TaskData.cs              FighterTask FSM table + TaskTimeline
      ResolutionTable.cs       event-pair -> response-pair rules
      PlayerModel.cs           mutable per-fighter state + snapshot
      Processing.cs            task/intent/reactive/response pipeline
      Player.cs                per-fighter façade
      Orchestrator.cs          per-tick flow() + duel resolution
      Observation.cs           7-float obs encoder (matches gym_env._get_obs)
      FightCore.asmdef         noEngineReferences=true (enforces portability)
    Tests/EditMode/
      ParityTests.cs           replays Python fixtures, asserts frame parity
      FightCore.EditModeTests.asmdef
```

## Source of truth for correctness

The Python sim is ground truth. `../parity/dump_trajectory.py` emits fixed,
deterministic action-script trajectories to `../parity/trajectories/*.json`
(state + observation vector + responses per frame). The C# core is "correct"
iff it reproduces those frame-for-frame.

- **In Unity:** open this folder, then `Window > General > Test Runner >
  EditMode > Run All`. Requires the `com.unity.nuget.newtonsoft-json` package
  (already in `Packages/manifest.json`).
- **Headless (no Unity):** the same check runs via a small .NET project — see
  `scratchpad/parity_runner` (compiled against these exact source files). All
  three fixtures currently pass.

To regenerate fixtures after changing the Python combat rules:

```
python -m parity.dump_trajectory
```

Then re-run the Unity/headless parity check; any divergence flags a port gap.

## Design rules

- `FightCore` has **no `UnityEngine` dependency** (`noEngineReferences: true`).
  The MonoBehaviour wrapper + Sentis inference live in a *separate* assembly
  (added next phase) so the core stays deterministic and testable.
- The sim is **tick-based**, not real-time. When wrapping in a MonoBehaviour,
  drive it on a fixed logical-tick accumulator — never `Update()`/`deltaTime`.
- Stamina costs mirror the Python `set_task` raw base values; the
  stats-adjusted `calc_stamina_cost_*` path is intentionally not wired (matches
  the live Python behaviour).

## Next phases

1. ONNX export of the SB3 PPO policy; verify obs ordering/scaling vs `Observation.cs`.
2. `FightUnity` assembly: MonoBehaviour tick driver + Sentis `IWorker` inference.
3. Rendering / scene.