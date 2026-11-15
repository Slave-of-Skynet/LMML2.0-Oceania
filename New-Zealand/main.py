"""The Braided River Run — optimal route finder for task_new_zealand.

Solves the valley map using Dijkstra's algorithm over (row, col, bridge_mask, time % P)
and writes the optimal action sequence to solution.txt.
"""

from __future__ import annotations

import heapq
import os
from pathlib import Path
import sys

import environment


def solve(map_path: str) -> tuple[int, str]:
    valley = environment.load_map(map_path)
    bridge_list = sorted(valley.bridges)
    bridge_to_bit = {b: 1 << i for i, b in enumerate(bridge_list)}

    init_bridge_mask = 0
    for b in valley.initial_open:
        init_bridge_mask |= bridge_to_bit[b]

    winch_toggle = {}
    for w, targets in valley.winches.items():
        mask = 0
        for t in targets:
            mask |= bridge_to_bit[t]
        winch_toggle[w] = mask

    start_r, start_c = valley.start
    goal_r, goal_c = valley.goal
    period = valley.tide_period
    low = valley.tide_low

    best = {}
    parent = {}
    start_key = (start_r, start_c, init_bridge_mask, 0)
    best[start_key] = 0
    pq = [(0, start_r, start_c, init_bridge_mask, 0)]

    goal_key = None
    goal_time = None

    while pq:
        t, r, c, bmask, t_mod = heapq.heappop(pq)
        state_key = (r, c, bmask, t_mod)
        if best.get(state_key, float("inf")) < t:
            continue
        if (r, c) == (goal_r, goal_c):
            goal_key = state_key
            goal_time = t
            break

        for act, (dr, dc) in environment.ACTIONS.items():
            nr, nc = r + dr, c + dc
            if not valley.in_bounds(nr, nc):
                continue
            symbol = valley.cell(nr, nc)
            if symbol in (environment.WALL, environment.WATER):
                continue
            dur = valley.duration(r, c, nr, nc)
            nt = t + dur
            if symbol == environment.FORD and not (nt % period < low):
                continue
            if environment.is_bridge(symbol) and not (bmask & bridge_to_bit[symbol]):
                continue
            nbmask = bmask
            if (nr, nc) != (r, c) and environment.is_winch(symbol):
                nbmask ^= winch_toggle[symbol]
            nt_mod = nt % period
            n_state_key = (nr, nc, nbmask, nt_mod)
            if nt < best.get(n_state_key, float("inf")):
                best[n_state_key] = nt
                parent[n_state_key] = (state_key, act)
                heapq.heappush(pq, (nt, nr, nc, nbmask, nt_mod))

    if goal_key is None:
        raise RuntimeError("No route to goal found")

    curr = goal_key
    actions = []
    while curr in parent:
        curr, act = parent[curr]
        actions.append(act)
    actions.reverse()
    route = "".join(actions)
    return goal_time, route


def main():
    if len(sys.argv) > 1:
        map_path = sys.argv[1]
    elif os.path.exists("test-input.txt"):
        map_path = "test-input.txt"
    elif os.path.exists("train-input.txt"):
        map_path = "train-input.txt"
    else:
        raise FileNotFoundError("Could not find test-input.txt or train-input.txt")

    minutes, route = solve(map_path)
    out_path = Path("solution.txt")
    out_path.write_text(route + "\n", encoding="utf-8")
    print(f"Solved {map_path}: {minutes} minutes ({len(route)} actions), written to {out_path}")


if __name__ == "__main__":
    main()
