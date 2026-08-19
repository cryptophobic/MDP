"""Engine-style debug overlay for the pygame view.

Draws, per fighter, the state an inspector in Unity/UE would show: the current
task and where inside its timeline we are, which event fires on which frame,
what the resolution stage answered, and the pending intent.

This is a presentation layer only. It reads `Player._model` directly instead of
going through `PlayerSnapshot`, because the snapshot deliberately carries only
what `reactive_processing` needs -- and the snapshot is mirrored in the C# port,
so growing it for debug purposes would ripple into the parity contract.
Nothing here is imported by the combat core.
"""

from typing import List, Optional, Sequence, Tuple

import pygame

from fight_env.player.player import Player
from fight_env.player.refs.events import Event, Events, Responses
from fight_env.player.refs.tasks import FighterTask, tasks_data

Line = Tuple[str, Tuple[int, int, int]]

# palette ---------------------------------------------------------------------
LABEL = (120, 130, 145)
VALUE = (215, 220, 230)
DIM = (85, 92, 105)
ACCENT = (255, 190, 70)

TASK_COLORS = {
    FighterTask.NONE: (110, 115, 125),
    FighterTask.FIGHTING_STANCE: (120, 200, 130),
    FighterTask.ATTACK_1: (240, 150, 70),
    FighterTask.RIPOSTE: (255, 110, 190),
    FighterTask.DEFENSE: (90, 160, 240),
    FighterTask.PARRY: (80, 225, 225),
    FighterTask.STUNNED: (235, 75, 75),
    FighterTask.HURT: (235, 200, 80),
    FighterTask.DEAD: (130, 130, 130),
}

# one glyph per event, so a whole timeline fits on a line
EVENT_GLYPHS = {
    Events.ATTACK_STARTED: "S",
    Events.ATTACK: "A",
    Events.CRITICAL_ATTACK: "C",
    Events.BLOCK: "B",
    Events.PARRY: "P",
    Events.STUNNED: "Z",
    Events.DEAD: "X",
}
EMPTY_CELL = "."


def _event_text(event: Optional[Event]) -> str:
    # PlayerModel.current_event defaults to a list, not an Event -- guard for the
    # frames before the first tick.
    if not isinstance(event, Event) or event.type == Events.NONE:
        return "-"
    if event.value:
        return f"{event.type.name} ({event.value})"
    return event.type.name


def _timeline(task: FighterTask, offset: int) -> Tuple[str, str]:
    """Return the `[S . A .]` strip and the caret line pointing at `offset`."""
    data = tasks_data.get(task)
    duration = data.duration if data else 0
    if duration <= 0:
        return "[-]", ""

    cells = [EVENT_GLYPHS.get(data.events.get(i, Events.NONE), EMPTY_CELL)
             for i in range(duration)]
    strip = "[" + " ".join(cells) + "]"
    caret = ""
    if 0 <= offset < duration:
        caret = " " * (1 + offset * 2) + "^"
    return strip, caret


class DebugHUD:
    """Renders one fighter's live state as a block of monospace lines."""

    LINE_HEIGHT = 15
    PAD = 6

    def __init__(self, size: int = 13):
        name = pygame.font.match_font("consolas,dejavusansmono,couriernew,monospace")
        self.font = pygame.font.Font(name, size) if name else pygame.font.Font(None, size + 3)

    # ------------------------------------------------------------------ build
    def lines(self, player: Player, title: str) -> List[Line]:
        model = player._model
        stats = model.stats
        task = model.task
        data = tasks_data.get(task)
        duration = data.duration if data else 0
        offset = model.timeline.frame_offset

        task_color = TASK_COLORS.get(task, VALUE)
        strip, caret = _timeline(task, offset)

        out: List[Line] = [
            (title.upper(), ACCENT),
            (f"TASK     {task.name}", task_color),
            (f"         prio {data.priority if data else 0}"
             f"{'  interruptible' if data and data.interruptible else ''}"
             f"{'  loop' if data and data.loop else ''}", DIM),
            (f"FRAME    {offset}/{duration}", VALUE),
            (f"         {strip}", task_color),
        ]
        if caret:
            out.append((f"         {caret}", ACCENT))

        # The caret sits on the frame the NEXT tick will process -- `frame_offset`
        # is post-tick, and is exactly the value fed to the observation vector.
        # Everything below belongs to the tick that has just finished.
        out.append(("--- resolved this tick ---", DIM))

        event_text = _event_text(model.current_event)
        out.append((f"EVENT    {event_text}", ACCENT if event_text != "-" else DIM))

        responses = model.current_responses or []
        shown = [r for r in responses if r.type != Responses.NONE]
        if shown:
            for i, r in enumerate(shown):
                label = "RESP     " if i == 0 else "         "
                text = f"{r.type.name}({r.value})" if r.value else r.type.name
                out.append((label + text, VALUE))
        else:
            out.append(("RESP     -", DIM))

        intent = model.requested_action
        out.append((f"INTENT   {intent.action.name}  ttl {intent.ttl}" if intent
                    else "INTENT   -", VALUE if intent else DIM))

        out.append((f"HP       {model.hp}/{stats.max_hp}", VALUE))
        out.append((f"STAMINA  {model.stamina}/{stats.max_stamina}", VALUE))

        if any(r.type == Responses.HAS_RIPOSTE_WINDOW_OPEN for r in responses):
            out.append((">> RIPOSTE WINDOW OPEN", (255, 110, 190)))
        if model.is_dead:
            out.append((">> DEAD", (235, 75, 75)))

        return out

    # ------------------------------------------------------------------- draw
    def draw(self, screen: pygame.Surface, player: Player, title: str,
             x: int, y: int, align_right: bool = False) -> None:
        """Blit the block. `x` is the left edge, or the right edge if align_right.

        The whole block is aligned as a unit -- aligning each line separately
        would slide the timeline caret out from under its strip.
        """
        surfaces = [self.font.render(text, True, color)
                    for text, color in self.lines(player, title)]
        self._blit_block(screen, surfaces, x, y, align_right)

    def draw_lines(self, screen: pygame.Surface, lines: Sequence[Line],
                   x: int, y: int, align_right: bool = False) -> None:
        surfaces = [self.font.render(text, True, color) for text, color in lines]
        self._blit_block(screen, surfaces, x, y, align_right)

    def _blit_block(self, screen: pygame.Surface, surfaces: List[pygame.Surface],
                    x: int, y: int, align_right: bool) -> None:
        if not surfaces:
            return
        width = max(s.get_width() for s in surfaces)
        left = x - width if align_right else x
        for i, surface in enumerate(surfaces):
            screen.blit(surface, (left, y + i * self.LINE_HEIGHT))
