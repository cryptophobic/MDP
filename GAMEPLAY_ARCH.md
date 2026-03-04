### start_new_frame (player scope)
 - frame_number++
 - apply stamina_cost_state to stamina_next if state_just_started
 - apply stamina_cost_frame to stamina_next

### events_processing (fight scope)
 - apply rules ATTACK vs BLOCK, ATTACK vs NONE etc, ATTACK vs STUNNED
 - Don't want overcomplicate here. But currently have no idea how to make it elegant. Upgrade to RIPOSTE 
So if attack has already been started we want to replace it here silently, assumming there wouldn't be some extra events on frame=0
So common sense tells me ATTACK to RIPOSTE upgrade should be happened in user_input_processing 

### events_resolution_response_processing (player scope)
 - adjust hp_next, stamina_next as possible effect of incoming events
 - Maybe it is time to introduce combos. e.g. certain successfully response opens short window (several frames) for something. e.g. RIPOSTE
so currently stunned state configured the way it informs every frame about it
```python
#file: fight_env/player/states.py
    FighterState.STUNNED: StateData(
        state_type=FighterState.STUNNED,
        priority=50,
        base_stamina_cost_frame=-BASE_STAMINA_RESTORE_VALUE_PER_TICK,
        duration=0,
        loop=True,
        events={0: (Events.STUNNED,)},
    ),
```
 - And in resolution table we could config something like this
```python
#file: fight_env/player/events.py
    (Events.STUNNED, Events.ANY): [
        Rule(
            when=lambda a, b: True,
            emit=lambda a, b: (resolution(Responses.NONE), resolution(Responses.HAS_RIPOSTE_WINDOW_OPEN)),
        )
    ],
```

### process_reactive_states (player scope)
 - set state_candidate as possible effect of incoming events (stunned, hurt, dead, combo)
 - set state_candidate as possible effect of stamina, hp updates (e.g. stun -> idle if stunned and stamina_next is above threshold)

### user_input_processing (player scope)
 - resolve user_intent to user_state_candidate. This resolving should take into account HAS_RIPOSTE_WINDOW_OPEN
 - set state_candidate from user_state_candidate

### timeline_processing (player scope)
 - check state expiring
 - calculate timeline_state_candidate if expired
 - set state_candidate from timeline_state_candidate

### finalise_frame (player scope)
 - resolve candidates according to prio (every state has prio DEAD above the HURT, HURT above the STUN, STUN the same as user_states etc...)
 - IMPORTANT: frame_number of new state is set to -1 (uninitialised). So state becomes active at the beginning of ther loop
 - set hp=hp_next
 - set stamina=stamina_next
 - set state=state_candidate


## Claude's suggestion

  Gaps / corrections                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
  1. Event emission is implicit but needs a step. After start_new_frame ticks the timeline, the fight loop needs to read each player's current events. Your StateData.events dict keyed by frame_number handles this, but it needs an explicit method. It's the bridge between phase 1 and 2.                                                                                                                                                                                           
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
  2. Response accumulation. Phase 2 (fight scope) can produce multiple responses per player per frame — your current Fight.resolve_combat already does this (f1_res + f1_res2). The combo resolver in phase 5 needs access to all of them. So process_responses should accumulate into a list that the combo resolver reads, not just apply hp/stamina and forget.                                                                                                                    

  3. Intent-to-state default mapping. ActionType.ATTACK → FighterState.ATTACK_1, ActionType.BLOCK → FighterState.DEFENSE, etc. The combo resolver upgrades this, but you need the base mapping too. Without it phase 5 has no way to go from user intent to state candidate.

  4. Candidate collection strategy. Phases 4, 5, 6 all produce candidates. I'd suggest appending to a candidates: list[FighterState] rather than doing inline priority resolution. Phase 7 picks the highest priority from the list. Simpler to debug than the old _set_action_candidate chain — you can inspect exactly what each phase proposed.

  5. The STUNNED → RIPOSTE flow works end-to-end without fight-scope hacks. Just confirming: STUNNED loops frame 0 → emits Events.STUNNED every frame → resolution table gives opponent HAS_RIPOSTE_WINDOW_OPEN → combo resolver upgrades ATTACK → RIPOSTE. The old request_alternative() in Fight disappears. Clean.

  Proposed file structure
```
  fight_env/player/
  ├── actions.py            # ActionType enum + intent-to-state default mapping
  ├── intent.py             # Intent dataclass (action + TTL for input buffering)
  ├── states.py             # FighterState, StateData, StateTimeline, states_data
  ├── events.py             # Events, Responses, Event, Response, Rule, resolution_table
  ├── reactive.py           # reactive_rules list: (condition, FighterState)
  ├── combos.py             # ComboResolver: response window buffer + upgrade rules
  ├── player_model.py       # PlayerModel: pure data, no logic
  ├── player.py             # Player: thin pipeline coordinator
  └── animations.py         # FighterState → Animation

  fight_env/
  ├── fight.py              # Fight: game loop orchestrator, event resolution
```

  Role of each file

  player_model.py — Pure data bag. No methods beyond trivial accessors. This is how you prevent the god object:
```python
  @dataclass
  class PlayerModel:
      state: FighterState
      timeline: StateTimeline
      hp: int
      hp_next: int
      stamina: int
      stamina_next: int
      candidates: list[FighterState]       # phases 4,5,6 append here
      frame_responses: list[Response]       # phase 3 accumulates here
```
  player.py — Thin coordinator. Owns a PlayerModel + ComboResolver. Each pipeline method is 5-10 lines because heavy logic lives in the rule modules:

```python
  class Player:
      model: PlayerModel
      combo: ComboResolver

      def start_new_frame(self)          # tick timeline, apply stamina costs
      def get_current_events(self)       # read StateData.events[frame_number]
      def process_responses(self, rs)    # apply hp/stamina, feed combo buffer
      def process_reactive(self)         # iterate reactive_rules → append candidates
      def process_intent(self, intent)   # combo.resolve(intent) → append candidate
      def process_timeline(self)         # check expiration → append candidate
      def finalise(self)                 # pick highest-prio candidate, commit state/hp/stamina
```

  reactive.py — Data-driven rules, no class needed:

```python
  reactive_rules: list[tuple[Callable[[PlayerModel], bool], FighterState]] = [
      (lambda m: m.hp_next <= 0,              FighterState.DEAD),
      (lambda m: m.hp_next < m.hp,            FighterState.HURT),
      (lambda m: m.stamina_next <= 0,         FighterState.STUNNED),
      (lambda m: m.state == FighterState.STUNNED
             and m.stamina_next >= threshold,  FighterState.IDLE),
  ]
```
  combos.py — Tracks response history with TTLs, upgrades intents:

```python
  @dataclass
  class ComboRule:
      trigger: Responses          # what must be in the buffer
      intent: ActionType          # what user is trying to do
      result: FighterState        # what it becomes
      window: int                 # TTL in frames

  combo_rules = [
      ComboRule(Responses.HAS_RIPOSTE_WINDOW_OPEN, ActionType.ATTACK, FighterState.RIPOSTE, window=1),
      ComboRule(Responses.HAS_ATTACKED, ActionType.ATTACK, FighterState.ATTACK_2, window=2),
  ]

  class ComboResolver:
      buffer: list[WindowEntry]

      def feed(self, responses: list[Response])      # add new, tick TTLs, prune expired
      def resolve(self, intent: ActionType) -> FighterState  # check rules, fallback to default map
```

  fight.py — The only place that sees both players:

```python
  class Fight:
      def step(self):
          for p in players: p.start_new_frame()

          events = [p.get_current_events() for p in players]
          # resolve events pairwise → responses

          for p, resps in zip(players, resolved):
              p.process_responses(resps)
              p.process_reactive()
              p.process_intent(intents[p])
              p.process_timeline()
              p.finalise()
```
  Why this prevents the god object

  The logic that used to live in State is now spread across data declarations (states_data, reactive_rules, combo_rules, resolution_table) and Player is just a dispatcher that calls them in order. Adding a new mechanic means adding a rule to the right table, not touching Player.
