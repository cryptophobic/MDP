"""A grid visualizer for the FrozenLake domain, in pyRDDLGym's own format.

``RDDLEnv.set_visualizer`` takes a *class*, not an instance -- it calls
``viz(model, **viz_kwargs)`` itself -- and expects ``render(state)`` to hand
back a PIL image, which it then blits into a pygame window.  The state arrives
as the grounded fluent dict, ``{'at___c0_0': True, ...}``.
"""

from __future__ import annotations

import re

from PIL import Image, ImageDraw
from pyRDDLGym.core.visualizer.viz import BaseViz

_CELL_KEY = re.compile(r"^at___c(\d+)_(\d+)$")

ICE = (222, 241, 252)
ICE_EDGE = (150, 190, 215)
HOLE = (25, 42, 62)
GOAL = (108, 196, 128)
START = (196, 214, 232)
AGENT = (222, 96, 70)
ARROW = (70, 90, 110)
TEXT = (30, 45, 60)

#: Arrow tip offsets per action, as a fraction of the cell size.
ARROWS = {"move_north": (0, -1), "move_south": (0, 1), "move_east": (1, 0), "move_west": (-1, 0)}


class FrozenLakeViz(BaseViz):
    """Draws the map, the agent, and -- when given -- the greedy policy."""

    def __init__(self, model, rows=None, cell=90, policy=None, caption=""):
        self.model = model
        self.rows = rows or []
        self.cell = cell
        #: ``{(row, col): action_name}``; drawn as arrows under the agent.
        self.policy = policy or {}
        self.caption = caption

    @staticmethod
    def agent_cell(state: dict) -> tuple[int, int] | None:
        for key, value in state.items():
            if value:
                m = _CELL_KEY.match(key)
                if m:
                    return int(m.group(1)), int(m.group(2))
        return None

    def render(self, state) -> Image.Image:
        height, width = len(self.rows), len(self.rows[0])
        size, pad = self.cell, 14
        bar = 34 if self.caption else 0
        image = Image.new("RGB", (width * size + 2 * pad, height * size + 2 * pad + bar), (245, 249, 252))
        draw = ImageDraw.Draw(image)

        for r in range(height):
            for c in range(width):
                x0, y0 = pad + c * size, pad + bar + r * size
                x1, y1 = x0 + size, y0 + size
                char = self.rows[r][c]
                fill = {"H": HOLE, "G": GOAL, "S": START}.get(char, ICE)
                draw.rectangle([x0, y0, x1, y1], fill=fill, outline=ICE_EDGE, width=2)

                action = self.policy.get((r, c))
                if action and char not in "HG":
                    dx, dy = ARROWS[action]
                    cx, cy = x0 + size / 2, y0 + size / 2
                    reach = size * 0.26
                    draw.line([cx - dx * reach, cy - dy * reach, cx + dx * reach, cy + dy * reach],
                              fill=ARROW, width=3)
                    tip = (cx + dx * reach, cy + dy * reach)
                    wing = size * 0.10
                    draw.polygon([tip,
                                  (tip[0] - dx * wing + dy * wing, tip[1] - dy * wing + dx * wing),
                                  (tip[0] - dx * wing - dy * wing, tip[1] - dy * wing - dx * wing)],
                                 fill=ARROW)

                if char == "G":
                    draw.text((x0 + size / 2 - 12, y0 + 6), "GOAL", fill=(20, 60, 35))

        here = self.agent_cell(state)
        if here is not None:
            r, c = here
            cx, cy = pad + c * size + size / 2, pad + bar + r * size + size / 2
            rad = size * 0.22
            draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=AGENT,
                         outline=(255, 255, 255), width=3)

        if self.caption:
            draw.text((pad, 10), self.caption, fill=TEXT)
        return image
