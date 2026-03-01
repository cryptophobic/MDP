from fight_env.actions import ActionType, states, ActionData
from fight_env.events import Event, Responses, Events

def _resolve_priority(candidate_action: ActionType, current_action: ActionType):
    if candidate_action == ActionType.NONE:
        return current_action

    current_action_data = states[current_action]
    candidate_action_data = states[candidate_action]

    if candidate_action_data.interrupt_priority > current_action_data.interrupt_priority:
        return candidate_action

    if candidate_action_data.interrupt_priority == current_action_data.interrupt_priority and current_action_data.interruptible:
        return candidate_action

    return current_action


class State:
    def __init__(self, name: str, hp: int = 30, stamina: int = 20, init_action: ActionType=ActionType.IDLE):
        self.global_frame_number: int = 0
        self.action_start_frame: int = 0
        self.name: str = name
        self.max_hp: int = hp
        self.hp: int = self.max_hp
        self.hp_candidate: int = hp
        self.max_stamina: int = stamina
        self.is_dead = False
        self.stamina_restore_value: int = 1
        self.stamina: int = self.max_stamina
        self.stamina_candidate: int = self.stamina
        self.current_action: ActionType = init_action
        self.current_action_frame: int = 0
        self.requested_action: ActionType = ActionType.NONE
        self.action_candidate: ActionType = ActionType.NONE

    def set_action_candidate(self, action_candidate: ActionType) -> None:
        if self.action_candidate == action_candidate:
            return

        if self.action_candidate == ActionType.NONE:
            self.action_candidate = action_candidate
            return

        action_data = states[action_candidate]

        if self.action_candidate in action_data.alternatives:
            self.action_candidate = action_candidate
            return

        self.action_candidate = _resolve_priority(action_candidate, self.action_candidate)

    def request_alternative(self, action: ActionType) -> None:
        self.process_derived_action(states[action])

    def request_action(self, action: ActionType) -> None:
        if states[action].requestable:
            self.requested_action = action

    def is_current_action_expired(self) -> bool:
        if self.current_action == ActionType.STUNNED:
            return self.stamina_candidate >= self.max_stamina // 2

        return not states[self.current_action].loop and self.current_action_frame >= states[self.current_action].frame_count


    def _apply_action_candidate(self):
        current_action_expired = self.is_current_action_expired()
        action = self.action_candidate
        self.action_candidate = ActionType.NONE
        if action == ActionType.NONE:
            return

        if not current_action_expired:
            action = _resolve_priority(action, self.current_action)
            if action == self.current_action:
                return

        self.stamina_candidate -= states[action].stamina_cost
        self.current_action = action
        self.current_action_frame = 0
        self.action_start_frame = self.global_frame_number

    def process_response(self, response: Responses) -> None:
        # if response != Responses.NONE:
        #     logger.info(f"{response}", {self.name})
        match response:
            case Responses.DEAD:
                self.is_dead = True
            case Responses.HAS_BEEN_BLOCKED:
                self.stamina_candidate = self.stamina_candidate - 4
            case Responses.HAS_BLOCKED:
                self.stamina_candidate = self.stamina_candidate - 4
            case Responses.HAS_BEEN_PARRIED:
                # critical hit
                self.stamina_candidate = -4
            case Responses.HAS_BEEN_RIPOSTED:
                self.hp_candidate = max(self.hp_candidate - 5, 0)
            case Responses.HAS_PARRIED:
                # congratulations
                pass
            case Responses.HAS_BEEN_ATTACKED:
                self.hp_candidate = max(self.hp_candidate - 1, 0)
            case Responses.HAS_ATTACKED:
                pass
            case Responses.NONE:
                pass

    def get_current_action(self) -> ActionData:
        return states[self.current_action]

    # TODO: review several events at one fram logic
    def get_current_events(self) -> Event:
        current_action = self.get_current_action()
        current_event = current_action.frame_events.get(self.current_action_frame, ())
        return current_event[0] if current_event and current_event[0].type != Events.NONE else Event(Events.NONE)

    def _process_reactive_actions(self):
        if self.hp_candidate <= 0:
            self.action_candidate = ActionType.DEAD
            return

    def resolve_next_action(self) -> None:
        if self.is_dead:
            return

        action_data = self.get_current_action()

        self.stamina_candidate -= (action_data.stamina_cost_frame - self.stamina_restore_value)
        self.stamina_candidate = min(self.stamina_candidate, self.max_stamina)

        self.process_reactive_action()
        self.process_player_action()

    def apply_action(self) -> None:
        self.hp = self.hp_candidate
        self.stamina = self.stamina_candidate

        self.current_action_frame += 1
        action_data = self.get_current_action()
        if action_data.loop and self.current_action_frame >= states[self.current_action].frame_count:
            self.current_action_frame = 0

        self.global_frame_number += 1
        self._apply_action_candidate()

    def process_derived_action(self, requested_action: ActionData) -> None:
        if self.action_candidate not in requested_action.alternatives:
            return

        self.set_action_candidate(requested_action.action_type)

    def process_reactive_action(self) -> None:
        if self.hp_candidate <= 0:
            self.set_action_candidate(ActionType.DEAD)
        elif self.hp_candidate < self.hp:
            self.set_action_candidate(ActionType.HURT)
        elif self.stamina_candidate <= 0:
            self.set_action_candidate(ActionType.STUNNED)
        elif self.is_current_action_expired():
            self.set_action_candidate(ActionType.IDLE)

    def process_player_action(self) -> None:
        is_action_requested = self.requested_action != ActionType.NONE
        if not is_action_requested:
            return

        requested_action = self.requested_action
        self.requested_action = ActionType.NONE

        self.set_action_candidate(requested_action)
