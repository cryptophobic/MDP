# Fight Environment Architecture

## Overview

The fight system is a frame-based combat simulation. Each frame follows a strict pipeline.
`PlayerModel` is a pure data container — all logic lives in stateless processing functions.
The outside world (renderer, gym env, bots) only sees frozen `PlayerSnapshot`s produced at the end of each frame.

## Core Types

### PlayerModel (mutable, internal)
Pure data container, no methods. Processors read/write it during a frame.

Fields:
- `stats: Stats` — equipment-derived values
- `hp: int`, `stamina: int` — current resources
- `task: FighterTask` — active task (IDLE, ATTACK_1, HURT, STUNNED, DEAD, etc.)
- `timeline: TaskTimeline` — tracks frame offset, duration, loop, expiry
- `stamina_cost_per_frame: int` — ongoing drain from current task
- `requested_task: FighterTask` — player input buffer
- `is_dead: bool`

### PlayerSnapshot (frozen, external)
Immutable output of a frame. All external consumers use this.

Fields:
- `hp`, `stamina`, `task`, `frame_offset`, `is_dead`
- `responses: tuple[Response, ...]` — combat responses received this frame

### TaskData (static definition)
Defines a task's properties: `priority`, `duration`, `loop`, `interruptible`,
`base_stamina_cost` (one-time on entry), `base_stamina_cost_frame` (per-frame drain),
`events: Dict[int, Tuple[Events]]` (what events fire at which frame offsets).

### TaskTimeline (runtime state)
Tracks progress through a task: `frame_offset`, `duration`, `loop`, `expired`.
For looped tasks, frame_offset wraps for event lookup but the raw counter does not reset,
ensuring entry cost is applied only once.

## Frame Lifecycle Pipeline

Each frame executes these phases in order:

```
Phase A — Task Resolution (uses previous frame's snapshot):

  1. tick(model)
     - If first frame of task: apply base_stamina_cost
     - Apply base_stamina_cost_frame
     - Advance timeline

  2. Fallback
     - If timeline expired -> try_transition(model, IDLE)

  3. Intent + Combo Upgrade
     - Read player input (requested_task)
     - Run combo_upgrade(intent, prev_snapshot.responses) to potentially upgrade
       (e.g. ATTACK_1 + HAS_RIPOSTE_WINDOW_OPEN -> RIPOSTE)
     - try_transition(model, upgraded_intent)

  4. Reactive
     - Compare model state against previous snapshot
     - hp <= 0 -> try_transition(DEAD)
     - hp < prev_snapshot.hp -> try_transition(HURT)
     - stamina <= 0 -> try_transition(STUNNED)

Phase B — Combat:

  5. Event Generation
     - Read current task's events at current frame_offset
     - Stats convert event type to Event with value (e.g. ATTACK -> damage from weapon)

  6. Combat Resolution
     - Resolve (event_p1, event_p2) through resolution_table
     - Produces Response pairs for each player

  7. Response Processing
     - Apply responses: modify hp, stamina based on response type and stats
     - (e.g. HAS_BEEN_ATTACKED -> hp loss, HAS_BEEN_PARRIED -> instant stun)

  8. Snapshot
     - Freeze model state + responses into PlayerSnapshot
     - This snapshot is used by next frame's Phase A and by all external consumers
```

## Task Transition — try_transition

Called multiple times per frame (fallback, intent, reactive). Does NOT apply stamina costs.
Transition succeeds if:
- Candidate priority > current task priority, OR
- Equal priority AND current task is interruptible

The last successful transition wins. Stamina costs are deferred to tick() on the next frame's
first-frame check.

```
try_transition(model, candidate_task):
    if candidate can interrupt current:
        model.task = candidate_task
        model.timeline = new TaskTimeline(...)
        return True
    return False
```

## Inter-Player Communication

Players communicate exclusively through the event/response system. No direct model inspection.

### Event Resolution Table (events.py)
Maps (my_event, opponent_event) pairs to response pairs via rules:

```
(ATTACK, ANY)   -> (HAS_ATTACKED, HAS_BEEN_ATTACKED)
(ATTACK, PARRY) -> (HAS_BEEN_PARRIED, HAS_PARRIED)      # more specific key wins
(ATTACK, BLOCK) -> conditional on attack vs defense value
(STUNNED, ANY)  -> (NONE, HAS_RIPOSTE_WINDOW_OPEN)
(DEAD, ANY)     -> (DEAD, WON)
```

### Combo Resolution Table (combos.py)
Maps (my_intent, received_response) to upgraded task via rules.
Same pattern as event resolution:

```
(ATTACK_1, HAS_RIPOSTE_WINDOW_OPEN) -> RIPOSTE
```

## Task Definitions (tasks.py)

Organized by priority tier:

- **Top level (100):** DEAD
- **System level (90):** HURT
- **System level (50):** STUNNED (loop, emits STUNNED event at frame 0)
- **User level (50):** ATTACK_1, PARRY, RIPOSTE, DEFENSE
- **Fallback (0):** IDLE (loop, interruptible), NONE

## File Structure

```
fight_env/player/
  player_model.py         # Pure data container
  player_snapshot.py      # Frozen frame output
  tasks.py                # FighterTask enum, TaskData definitions, TaskTimeline
  events.py               # Events, Responses, Event, Response, resolution_table
  stats.py                # Equipment -> derived values
  intent_processing.py    # Player input -> requested task
  combos.py               # Combo upgrade rules: (intent, response) -> upgraded task
  task_processing.py      # tick(), try_transition(), enter_task()
  reactive_processing.py  # Resource changes -> forced tasks (HURT/DEAD/STUNNED)
  response_processing.py  # Combat responses -> resource mutations
  animations.py           # Task -> Animation mapping (separate from task data)
  protocols.py            # StateProtocol if still needed

fight_env/
  fight.py                # Orchestrator: runs the pipeline, holds models + snapshots
  gym_env.py              # Gymnasium wrapper, reads snapshots
  main.py                 # Game loop with rendering, reads snapshots
```