"""Exact Backward Induction solver for Papua New Guinea (Bihainim Angkol).

Solves the finite-horizon Markov Decision Process (24 steps, 6048 states)
using the exact transition operator from lagoon._advance and exports main.py.
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure local task directory is on sys.path to import lagoon.py directly
TASK_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK_DIR))

import lagoon


def solve_mdp():
    ACTIONS = lagoon.ACTIONS
    GRID = lagoon.GRID
    BITE_CHANCE = lagoon.BITE_CHANCE
    TIDE_CHANCE = lagoon.TIDE_CHANCE
    HOLD_CAPACITY = lagoon.HOLD_CAPACITY
    STEPS_PER_DAY = lagoon.STEPS_PER_DAY

    water_cells = [
        (r, c)
        for r in range(lagoon.ROWS)
        for c in range(lagoon.COLS)
        if lagoon.is_water(r, c)
    ]

    def get_transitions(r: int, c: int, h: int, a: str):
        """Returns all stochastic transitions (prob, nr, nc, nh, landed)

        Uses lagoon._advance directly, ensuring exact fidelity to environment rules.
        """
        p_bite = (
            BITE_CHANCE.get(GRID[r][c], 0.0)
            if (a == "FISH" and h < HOLD_CAPACITY)
            else 0.0
        )
        p_tide = TIDE_CHANCE

        outcomes = []
        for bite, pb in [(True, p_bite), (False, 1.0 - p_bite)]:
            if pb == 0.0:
                continue
            for tide, pt in [(True, p_tide), (False, 1.0 - p_tide)]:
                if pt == 0.0:
                    continue
                nr, nc, nh, landed = lagoon._advance(r, c, h, a, bite, tide)
                outcomes.append((pb * pt, nr, nc, nh, landed))
        return outcomes

    V = [{} for _ in range(STEPS_PER_DAY + 1)]
    policy = {}

    for r, c in water_cells:
        for h in range(HOLD_CAPACITY + 1):
            V[0][(r, c, h)] = 0.0

    for t in range(1, STEPS_PER_DAY + 1):
        for r, c in water_cells:
            for h in range(HOLD_CAPACITY + 1):
                best_q = -1e9
                best_a = None
                for a in ACTIONS:
                    q = 0.0
                    for prob, nr, nc, nh, landed in get_transitions(r, c, h, a):
                        q += prob * (landed + V[t - 1][(nr, nc, nh)])
                    if q > best_q:
                        best_q = q
                        best_a = a
                V[t][(r, c, h)] = best_q
                policy[(r, c, h, t)] = best_a

    return policy, V


def main():
    policy, V = solve_mdp()
    print(f"Optimal V(start, 24) = {V[lagoon.STEPS_PER_DAY][(*lagoon.START, 0)]:.4f}")
    out_path = TASK_DIR / "main.py"
    lagoon.export_main(policy, str(out_path))
    print(f"Exported self-contained policy to {out_path}")

    # Ensure train-input.csv exists for local testing
    input_path = TASK_DIR / "train-input.csv"
    if not input_path.exists():
        with open(input_path, "w") as f:
            f.write(
                "row,col,hold,steps_left\n"
                + "\n".join(",".join(map(str, s)) for s in lagoon.all_states())
                + "\n"
            )
        print(f"Generated test input at {input_path}")


if __name__ == "__main__":
    main()
