from fight_env.state.actions import ActionType, states, ActionData
from fight_env.state.events import Event, Responses, Events, Response
from fight_env.state.stats import Stats, INSTANT_STUN, STAMINA_BOTTOM_LIMIT


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
        self.current_action_frame: int = 0

        self.stats: Stats = Stats(name=name, hp=hp, stamina=stamina)

        self.hp: int = self.stats.max_hp
        self.hp_candidate: int = hp
        self.is_dead = False
        self.stamina: int = self.stats.max_stamina
        self.stamina_candidate: int = self.stamina

        self.current_action: ActionType = init_action
        self.requested_action: ActionType = ActionType.NONE
        self.action_candidate: ActionType = ActionType.NONE

    def request_alternative(self, action: ActionType) -> None:
        self._process_derived_action(states[action])

    def request_action(self, action: ActionType) -> None:
        if states[action].requestable:
            self.requested_action = action

    def process_response(self, response: Response) -> None:
        if response.type == Responses.DEAD:
            self.is_dead = True
            return

        stamina_cost = self.stats.stamina_cost_on_response(response)
        if stamina_cost == INSTANT_STUN:
            stamina_cost = self.stamina_candidate - STAMINA_BOTTOM_LIMIT

        self.stamina_candidate -= stamina_cost
        hp_cost = self.stats.hp_cost_on_response(response)
        self.hp_candidate = max(self.hp_candidate - hp_cost, 0)

    def get_current_action(self) -> ActionData:
        return states[self.current_action]

    # TODO: review several events at one frame logic
    def get_current_events(self) -> Event:
        current_action = self.get_current_action()
        current_event_type = current_action.frame_events.get(self.current_action_frame, ())
        current_event_type = current_event_type[0] if current_event_type else Events.NONE

        return self.stats.get_event(current_event_type)

    def resolve_next_action(self) -> None:
        if self.is_dead:
            return

        stamina_cost = self.stats.stamina_cost_per_frame(self.current_action)
        stamina_cost -= self.stats.stamina_restore_per_frame

        self.stamina_candidate -= stamina_cost
        self.stamina_candidate = min(self.stamina_candidate, self.stats.max_stamina)

        self._process_reactive_action()
        self._process_player_action()

    def apply_action(self) -> None:
        self.hp = self.hp_candidate
        self.stamina = self.stamina_candidate

        self.current_action_frame += 1
        action_data = self.get_current_action()
        if action_data.loop and self.current_action_frame >= states[self.current_action].frame_count:
            self.current_action_frame = 0

        self.global_frame_number += 1
        self._apply_action_candidate()

    def _set_action_candidate(self, action_candidate: ActionType) -> None:
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

    def _process_derived_action(self, requested_action: ActionData) -> None:
        if self.action_candidate not in requested_action.alternatives:
            return

        self._set_action_candidate(requested_action.action_type)

    def _process_reactive_action(self) -> None:
        if self.hp_candidate <= 0:
            self._set_action_candidate(ActionType.DEAD)
        elif self.hp_candidate < self.hp:
            self._set_action_candidate(ActionType.HURT)
        elif self.stamina_candidate <= 0:
            self._set_action_candidate(ActionType.STUNNED)
        elif self._is_current_action_expired():
            self._set_action_candidate(ActionType.IDLE)

    def _process_player_action(self) -> None:
        is_action_requested = self.requested_action != ActionType.NONE
        if not is_action_requested:
            return

        requested_action = self.requested_action
        self.requested_action = ActionType.NONE
        self._set_action_candidate(requested_action)

    def _is_current_action_expired(self) -> bool:
        if self.current_action == ActionType.STUNNED:
            return self.stamina_candidate >= self.stats.max_stamina // 2

        return not states[self.current_action].loop and self.current_action_frame >= states[self.current_action].frame_count

    def _apply_action_candidate(self):
        current_action_expired = self._is_current_action_expired()
        action = self.action_candidate
        self.action_candidate = ActionType.NONE
        if action == ActionType.NONE:
            return

        if not current_action_expired:
            action = _resolve_priority(action, self.current_action)
            if action == self.current_action:
                return

        self.stamina_candidate -= self.stats.stamina_cost_per_action(action)
        self.current_action = action
        self.current_action_frame = 0
        self.action_start_frame = self.global_frame_number
