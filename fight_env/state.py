from fight_env.actions import ActionType, available_actions, ActionData
from fight_env.events import Event, Responses, Events
from fight_env.logger import logger


class State:
    def __init__(self, name: str, hp: int = 30, stamina: int = 20, init_action: ActionType=ActionType.IDLE):
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

    def request_action(self, action: ActionType) -> None:
        self.requested_action = action

    def _set_action(self, action: ActionType):
        self.stamina_candidate -= available_actions[action].stamina_cost
        self.current_action = action
        self.current_action_frame = 0

    def process_response(self, response: Responses) -> None:
        if response != Responses.NONE:
            logger.info(f"{response}", {self.name})
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
        return available_actions[self.current_action]

    # TODO: review several events at one fram logic
    def get_current_events(self) -> Event:
        current_action = self.get_current_action()
        current_event = current_action.frame_events.get(self.current_action_frame, ())
        return current_event[0] if current_event and current_event[0].type != Events.NONE else Event(Events.NONE)

    def resolve_next_action(self) -> None:
        if self.is_dead:
            return

        action_data = self.get_current_action()

        # analyze difference
        self.stamina = self.stamina_candidate

        self.stamina -= (action_data.stamina_cost_frame - self.stamina_restore_value)
        self.stamina = min(self.stamina, self.max_stamina)
        self.stamina_candidate = self.stamina

        hurt = self.hp_candidate < self.hp
        self.hp = self.hp_candidate
        self.hp_candidate = self.hp

        self.current_action_frame += 1

        requested_action = self.requested_action
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

        if self.stamina <= 0:
            if self.current_action != ActionType.STUN or self.current_action_frame >= action_data.frame_count:
                self.action_candidate = ActionType.STUN
            return

        if self.current_action == ActionType.STUN:
            stunning_expired = self.current_action == ActionType.STUN and self.stamina >= self.max_stamina // 2
            if stunning_expired:
                self.action_candidate = ActionType.IDLE
            elif self.current_action_frame >= action_data.frame_count:
                self.action_candidate = ActionType.STUN
                return

        elif self.current_action_frame >= action_data.frame_count:
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
            if self.action_candidate != ActionType.IDLE and self.action_candidate != self.current_action:
                logger.info(f"{self.action_candidate}", {self.name})

            self._set_action(self.action_candidate)

        self.action_candidate = ActionType.NONE
