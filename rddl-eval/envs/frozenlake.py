"""Generate a FrozenLake domain as RDDL, for any rectangular map.

The domain is fixed; the map lives entirely in the ``non-fluents`` block as an
adjacency table, so a different grid is a different instance, not a different
domain.  That is the whole point of writing it this way: 3x3 and 8x8 share
one domain, and slippery ice is a number rather than a second domain.

Map characters follow Gymnasium's FrozenLake: ``S`` start, ``F`` frozen,
``H`` hole, ``G`` goal.
"""

from __future__ import annotations

MAP_3X3 = ["SFF", "FHF", "FFG"]
MAP_4X4 = ["SFFF", "FHFH", "FFFH", "HFFG"]

#: Gym's ``is_slippery=True`` moves the agent in the intended direction with
#: probability 1/3 and into each perpendicular direction with probability 1/3,
#: which is this SLIP -- the total probability of *not* going where you aimed.
GYM_SLIP = 2.0 / 3.0

#: (name, row-delta, column-delta).  Row 0 is the top row, so north decreases it.
DIRECTIONS = (
    ("NORTH", -1, 0),
    ("SOUTH", 1, 0),
    ("EAST", 0, 1),
    ("WEST", 0, -1),
)

DOMAIN = """domain frozenlake {

    requirements = {
        reward-deterministic
    };

    types {
        cell : object;
    };

    pvariables {
        NORTH(cell, cell) : { non-fluent, bool, default = false };
        SOUTH(cell, cell) : { non-fluent, bool, default = false };
        EAST(cell, cell)  : { non-fluent, bool, default = false };
        WEST(cell, cell)  : { non-fluent, bool, default = false };
        HOLE(cell)        : { non-fluent, bool, default = false };
        GOAL(cell)        : { non-fluent, bool, default = false };

        // Probability that the ice sends the agent somewhere other than where
        // it aimed, split evenly between the two perpendicular directions.
        // 0 is dry ice; 2/3 reproduces Gym's is_slippery=True exactly.
        SLIP              : { non-fluent, real, default = 0.0 };

        at(cell)          : { state-fluent, bool, default = false };

        move_north        : { action-fluent, bool, default = false };
        move_south        : { action-fluent, bool, default = false };
        move_east         : { action-fluent, bool, default = false };
        move_west         : { action-fluent, bool, default = false };

        // The two coin flips MUST live here rather than inside at'(?c): an
        // inline Bernoulli would be resampled once per cell, and the agent
        // would end up standing on none of them or two of them at once.
        // aimed -> intended direction; veer -> which of the two perpendiculars.
        aimed             : { interm-fluent, bool, level = 1 };
        veer              : { interm-fluent, bool, level = 1 };

        // Exactly one of these is true whenever an action was taken.
        go_north          : { interm-fluent, bool, level = 2 };
        go_south          : { interm-fluent, bool, level = 2 };
        go_east           : { interm-fluent, bool, level = 2 };
        go_west           : { interm-fluent, bool, level = 2 };
    };

    cpfs {
        aimed = Bernoulli(1.0 - SLIP);
        veer  = Bernoulli(0.5);

        // Aiming north or south veers east (veer) or west (~veer);
        // aiming east or west veers north (veer) or south (~veer).
        go_north = ( move_north ^ aimed )
                 | ( (move_east | move_west) ^ ~aimed ^ veer );
        go_south = ( move_south ^ aimed )
                 | ( (move_east | move_west) ^ ~aimed ^ ~veer );
        go_east  = ( move_east ^ aimed )
                 | ( (move_north | move_south) ^ ~aimed ^ veer );
        go_west  = ( move_west ^ aimed )
                 | ( (move_north | move_south) ^ ~aimed ^ ~veer );

        at'(?c) =
            if ( exists_{?f : cell} [ at(?f) ^ (HOLE(?f) | GOAL(?f)) ] )
            then at(?c)
            else (
                  ( go_north ^ exists_{?f : cell} [ at(?f) ^ NORTH(?f, ?c) ] )
                | ( go_south ^ exists_{?f : cell} [ at(?f) ^ SOUTH(?f, ?c) ] )
                | ( go_east  ^ exists_{?f : cell} [ at(?f) ^ EAST(?f, ?c) ] )
                | ( go_west  ^ exists_{?f : cell} [ at(?f) ^ WEST(?f, ?c) ] )
                | ( at(?c) ^ (
                        ( go_north ^ ~exists_{?t : cell} [ NORTH(?c, ?t) ] )
                      | ( go_south ^ ~exists_{?t : cell} [ SOUTH(?c, ?t) ] )
                      | ( go_east  ^ ~exists_{?t : cell} [ EAST(?c, ?t) ] )
                      | ( go_west  ^ ~exists_{?t : cell} [ WEST(?c, ?t) ] )
                      | ( ~go_north ^ ~go_south ^ ~go_east ^ ~go_west )
                    ) )
            );
    };

    // The prime is required: pyRDDLGym evaluates `reward` against the state
    // *before* the transition, and termination fires on the same step, so an
    // unprimed `at` would score 0 on the very step that reaches the goal.
    // (Lint rule 7 bans primes on a CPF right-hand side; the reward is not a CPF.)
    reward = if ( exists_{?c : cell} [ at'(?c) ^ GOAL(?c) ] ) then 1.0 else 0.0;

    state-invariants {
        forall_{?c : cell} [ at(?c) => at(?c) ];
    };

    action-preconditions {
        (if (move_north) then 1 else 0) + (if (move_south) then 1 else 0)
      + (if (move_east) then 1 else 0) + (if (move_west) then 1 else 0) <= 1;
    };

    termination {
        exists_{?c : cell} [ at(?c) ^ (HOLE(?c) | GOAL(?c)) ];
    };
}
"""


def cell_name(row: int, col: int) -> str:
    return f"c{row}_{col}"


def build(rows: list[str], horizon: int = 50, discount: float = 1.0,
          slip: float = 0.0) -> str:
    """Domain + non-fluents + instance for *rows*, as one three-block file.

    *slip* is the probability of not moving in the intended direction; pass
    :data:`GYM_SLIP` to match ``gym.make(..., is_slippery=True)``.
    """
    height, width = len(rows), len(rows[0])
    if any(len(r) != width for r in rows):
        raise ValueError("every map row must have the same width")
    if not 0.0 <= slip <= 1.0:
        raise ValueError(f"slip must be a probability, got {slip}")

    cells = [cell_name(r, c) for r in range(height) for c in range(width)]

    edges: list[str] = []
    for name, d_row, d_col in DIRECTIONS:
        for r in range(height):
            for c in range(width):
                nr, nc = r + d_row, c + d_col
                if 0 <= nr < height and 0 <= nc < width:
                    edges.append(f"        {name}({cell_name(r, c)}, {cell_name(nr, nc)}) = true;")

    holes = [f"        HOLE({cell_name(r, c)}) = true;"
             for r in range(height) for c in range(width) if rows[r][c] == "H"]
    goals = [f"        GOAL({cell_name(r, c)}) = true;"
             for r in range(height) for c in range(width) if rows[r][c] == "G"]
    ice = [f"        SLIP = {slip:.6f};"] if slip > 0 else []

    starts = [cell_name(r, c)
              for r in range(height) for c in range(width) if rows[r][c] == "S"]
    if len(starts) != 1:
        raise ValueError(f"map needs exactly one S, found {len(starts)}")

    non_fluents = "\n".join(
        ["non-fluents frozenlake_nf {", "    domain = frozenlake;", "",
         "    objects {", "        cell : { " + ", ".join(cells) + " };", "    };", "",
         "    non-fluents {"] + edges + [""] + holes + goals + ice + ["    };", "}"]
    )

    instance = "\n".join([
        "instance frozenlake_inst {",
        "    domain = frozenlake;",
        "    non-fluents = frozenlake_nf;",
        "",
        "    init-state {",
        f"        at({starts[0]}) = true;",
        "    };",
        "",
        "    max-nondef-actions = 1;",
        f"    horizon = {horizon};",
        f"    discount = {discount};",
        "}",
    ])

    return DOMAIN + "\n" + non_fluents + "\n\n" + instance + "\n"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default="3x3", choices=["3x3", "4x4"])
    parser.add_argument("--slippery", action="store_true", help="slippery ice (Gym's 1/3 split)")
    parser.add_argument("--out", default="envs/frozenlake3x3.rddl")
    args = parser.parse_args()

    rows = MAP_3X3 if args.map == "3x3" else MAP_4X4
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(build(rows, slip=GYM_SLIP if args.slippery else 0.0))
    print(f"wrote {args.out}")
