from fight_env.actions import ActionType, available_actions, ActionData
from fight_env.events import Event, Responses, Events
from fight_env.logger import logger


class State:
    def __init__(self, name: str, hp: int = 6, stamina: int = 4, init_action: ActionType=ActionType.IDLE):
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
        self.current_event: Event = Event(Events.NONE)
        self.requested_action: ActionType = ActionType.NONE
        self.action_candidate: ActionType = ActionType.NONE
        self.riposte_window: int = 0
        self.parried: bool = False

    def request_action(self, action: ActionType) -> None:
        self.requested_action = action

    def _set_action(self, action: ActionType):
        self.stamina -= available_actions[action].stamina_cost
        self.current_action = action
        self.current_action_frame = 0

    def process_response(self, response: Responses) -> None:
        match response:
            case Responses.DEAD:
                self.is_dead = True
            case Responses.HAS_BEEN_BLOCKED:
                self.stamina_candidate = self.stamina_candidate - 2
            case Responses.HAS_BLOCKED:
                self.stamina_candidate = self.stamina_candidate - 1
            case Responses.HAS_BEEN_PARRIED:
                # critical hit
                self.parried = True
            case Responses.HAS_BEEN_RIPOSTED:
                self.hp_candidate = max(self.hp_candidate - 4, 0)
            case Responses.HAS_PARRIED:
                self.riposte_window = 4
                pass
            case Responses.HAS_BEEN_ATTACKED:
                self.hp_candidate = max(self.hp_candidate - 1, 0)
            case Responses.HAS_ATTACKED:
                pass
            case Responses.NONE:
                pass

    def get_current_action(self) -> ActionData:
        return available_actions[self.current_action]

    # TODO: review several events at one fram logic
    def get_current_events(self) -> Event:
        current_event = self.current_event
        self.current_event = Event(Events.NONE)
        return current_event

    def finalise_last_step(self) -> None:
        if self.is_dead:
            return

    def resolve_next_action(self) -> None:
        if self.is_dead:
            return

        action_data = self.get_current_action()

        # analyze difference
        self.stamina = self.stamina_candidate

        self.stamina -= (action_data.stamina_cost_frame - self.stamina_restore_value)
        self.stamina = min(self.stamina, self.max_stamina)

        hurt = self.hp_candidate < self.hp
        self.hp = self.hp_candidate

        self.current_action_frame += 1
        self.riposte_window = max(self.riposte_window - 1, 0)

        requested_action = self.requested_action
        if requested_action == ActionType.ATTACK_1 and self.riposte_window > 0:
            requested_action = ActionType.RIPOSTE

        self.requested_action = ActionType.NONE
        self.action_candidate = ActionType.NONE

        if self.current_action == ActionType.DEAD:
            return

        if self.hp <= 0:
            self.action_candidate = ActionType.DEAD
            return

        if hurt:
            self.action_candidate = ActionType.HURT
            return

        if self.parried:
            self.parried = False
            self.action_candidate = ActionType.PARRIED
            return

        if self.stamina <= 0:
            self.action_candidate = ActionType.STUN if self.current_action != ActionType.STUN else ActionType.NONE
            return

        if self.current_action_frame >= action_data.frame_count:
            if action_data.loop:
                self.action_candidate = self.current_action
            else:
                self.action_candidate = ActionType.IDLE

        if requested_action != ActionType.NONE:
            is_action_expired = self.current_action_frame >= action_data.frame_count and not action_data.loop
            if action_data.interruptible or is_action_expired:
                self.action_candidate = requested_action

    def apply_action(self) -> None:
        if self.action_candidate != ActionType.NONE:
            if self.action_candidate != self.current_action:
                logger.info(f"Current action: {self.action_candidate}", {self.name})
            self._set_action(self.action_candidate)

        self.action_candidate = ActionType.NONE

        # TODO: workaround
        current_action = self.get_current_action()
        current_event = current_action.frame_events.get(self.current_action_frame, ())
        self.current_event = current_event[0] if current_event and current_event[0].type != Events.NONE else self.current_event
