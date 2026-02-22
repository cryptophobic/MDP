from fight_env.actions import ActionType, available_actions, ActionData
from fight_env.events import Event, Responses, Events

class State:
    def __init__(self, name: str, hp: int = 10, stamina: int = 4, init_action: ActionType=ActionType.IDLE):
        self.name: str = name
        self.max_hp: int = hp
        self.hp: int = self.max_hp
        self.max_stamina: int = stamina
        self.is_dead = False
        self.stamina_restore_value: int = 1
        self.stamina: int = self.max_stamina
        self.current_action: ActionType = init_action
        self.current_action_frame: int = 0
        self.current_event: Event = Event(Events.NONE)

    def request_action(self, action: ActionType) -> bool:
        if self.is_dead:
            return False

        action_data = available_actions[self.current_action]
        if action_data.interruptible and self.stamina >= available_actions[action].stamina_cost:
            self.current_action = action
            self.current_action_frame = 0
            self.stamina -= available_actions[action].stamina_cost
            return True

        return False

    def process_response(self, response: Responses) -> None:
        match response:
            case Responses.HAS_BEEN_BLOCKED:
                self.stamina = self.stamina - 2
            case Responses.HAS_BLOCKED:
                self.stamina = self.stamina - 1
            case Responses.HAS_BEEN_PARRIED:
                # critical hit
                self.hp = max(self.hp - 4, 0)
            case Responses.HAS_PARRIED:
                pass
            case Responses.HAS_BEEN_ATTACKED:
                self.hp = max(self.hp - 1, 0)
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

    def next_frame(self) -> int:
        action_data = self.get_current_action()
        self.current_action_frame += 1

        self.stamina -= (action_data.stamina_cost_frame - self.stamina_restore_value)


        if self.current_action == ActionType.DEAD:
            if self.current_action_frame >= action_data.frame_count - 1:

                self.is_dead = True

        if self.stamina < 0:
            self.current_action = ActionType.STUN
            action_data = self.get_current_action()

            self.stamina = -6

        if self.current_action == ActionType.STUN:
            if self.stamina > 0:
                self.current_action = ActionType.IDLE
                self.current_action_frame = 0
            else:
                self.current_action_frame = self.current_action_frame % action_data.frame_count

        elif self.current_action_frame >= action_data.frame_count:
            if not action_data.loop:
                self.current_action = ActionType.IDLE
            self.current_action_frame = 0

        self.stamina = min(self.stamina, self.max_stamina)

        if self.hp == 0 and self.current_action != ActionType.DEAD:
            self.current_action = ActionType.DEAD
            self.current_action_frame = 0

        current_action = self.get_current_action()
        current_event = current_action.frame_events.get(self.current_action_frame, ())
        self.current_event = current_event[0] if current_event and current_event[0].type != Events.NONE else self.current_event

        return self.current_action_frame
