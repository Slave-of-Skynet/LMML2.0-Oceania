PARAMS = {"lam": 1.1, "lam_opp": 0.9001, "front_w": 0.4517, "hidden_v": 2.875, "expose": 0.4524, "fog_v": 9.3126, "fog_c": 3, "end_turns": 4, "waste": 0.7735, "topk": 9}

N = 15
NB = []
for i in range(N * N):
    r, c = divmod(i, N)
    NB.append(tuple(j for j, ok in ((i - N, r > 0), (i + N, r < N - 1), (i - 1, c > 0), (i + 1, c < N - 1)) if ok))
STARTS = (0, N * N - 1)


def reset_agent():
    pass


def options(owners, w, cost, player, energy):
    other = 1 - player
    seen = set()
    out = []
    for i, o in enumerate(owners):
        if o != player:
            continue
        for b in NB[i]:
            if b in seen:
                continue
            ob = owners[b]
            if ob == -1:
                c = cost[b]
            elif ob == other and b not in STARTS:
                c = cost[b] + 2
            else:
                continue
            seen.add(b)
            if c <= energy:
                out.append((b, c))
    return out


def evaluate(owners, w, cost, me, sc, en, my_turns, p):
    opp = 1 - me
    lam = p["lam"] if my_turns > p["end_turns"] else p["lam"] * my_turns / (p["end_turns"] + 1)
    lamo = p["lam_opp"] if my_turns > p["end_turns"] else p["lam_opp"] * my_turns / (p["end_turns"] + 1)
    val = (sc[me] - sc[opp]) + lam * en[me] - lamo * en[opp]
    front = 0.0
    expose = 0.0
    counted = set()
    for i, o in enumerate(owners):
        if o != me:
            continue
        for b in NB[i]:
            ob = owners[b]
            if ob == -3:
                if b not in counted:
                    counted.add(b)
                    front += p["hidden_v"]
            elif ob == -1:
                if b not in counted:
                    counted.add(b)
                    front += w[b] / (cost[b] + 3) * 3
            elif ob == opp and i not in STARTS:
                expose += w[i]
    scale = min(1.0, my_turns / 20.0)
    return val + scale * (p["front_w"] * front - p["expose"] * expose)


def apply(owners, sc, w, player, cell):
    o = owners[cell]
    owners[cell] = player
    sc[player] += w[cell]
    if o == 1 - player:
        sc[o] -= w[cell]
    return o


def search(owners, w, cost, sc, en, me, player, depth, my_turns, p, alpha, beta):
    if depth == 0:
        return evaluate(owners, w, cost, me, sc, en, my_turns, p), None
    opp = 1 - player
    moves = [(None, 0)] + options(owners, w, cost, player, en[player])
    k = ROOT_K if depth == DEPTH else (OPP_K if player != me else p["topk"])
    if len(moves) > k + 1:
        rest = moves[0]
        moves = sorted(moves[1:], key=lambda m: -(w[m[0]] * (2 if owners[m[0]] == opp else 1) - 1.1 * m[1]))[:k]
        moves.insert(0, rest)
    maximizing = player == me
    nt = my_turns - (1 if player == me else 0)
    best_m = None
    best = -1e18 if maximizing else 1e18
    fog = player != me and en[player] >= p["fog_c"]
    for m, c in moves + ([("fog", p["fog_c"])] if fog else []):
        e = list(en)
        if m is None:
            e[player] = min(9, e[player] + 3)
            v, _ = search(owners, w, cost, sc, e, me, opp, depth - 1, nt, p, alpha, beta)
        elif m == "fog":
            e[player] -= c
            sc[player] += p["fog_v"]
            v, _ = search(owners, w, cost, sc, e, me, opp, depth - 1, nt, p, alpha, beta)
            sc[player] -= p["fog_v"]
        else:
            e[player] -= c
            prev = apply(owners, sc, w, player, m)
            v, _ = search(owners, w, cost, sc, e, me, opp, depth - 1, nt, p, alpha, beta)
            owners[m] = prev
            sc[player] -= w[m]
            if prev == opp:
                sc[opp] += w[m]
        if maximizing:
            if v > best:
                best, best_m = v, m
            alpha = max(alpha, v)
        else:
            if v < best:
                best, best_m = v, m
            beta = min(beta, v)
        if beta <= alpha:
            break
    return best, best_m


DEPTH = 3
END_K = 3
ROOT_K = 16
OPP_K = 9
OVR = {}
END_TOPK = 7


def endsearch(owners, w, cost, sc, en, me, player, depth, p, alpha, beta, fog_left):
    if depth == 0:
        m = sc[me] - sc[1 - me]
        return (1000 if m > 0 else (-1000 if m < 0 else 0)) + m, None
    opp = 1 - player
    moves = options(owners, w, cost, player, en[player])
    caps = [x for x in moves if owners[x[0]] == opp]
    neut = sorted([x for x in moves if owners[x[0]] != opp], key=lambda m: -w[m[0]])[:END_TOPK]
    caps = sorted(caps, key=lambda m: -w[m[0]])[:END_TOPK]
    cand = caps + neut + [(None, 0)]
    if player != me and fog_left and en[player] >= p["fog_c"]:
        cand.append(("fog", p["fog_c"]))
    maximizing = player == me
    best = -1e18 if maximizing else 1e18
    best_m = None
    for m, c in cand:
        e = list(en)
        if m is None:
            e[player] = min(9, e[player] + 3)
            v, _ = endsearch(owners, w, cost, sc, e, me, opp, depth - 1, p, alpha, beta, fog_left)
        elif m == "fog":
            e[player] -= c
            sc[player] += p["fog_v"]
            v, _ = endsearch(owners, w, cost, sc, e, me, opp, depth - 1, p, alpha, beta, fog_left)
            sc[player] -= p["fog_v"]
        else:
            e[player] -= c
            prev = apply(owners, sc, w, player, m)
            v, _ = endsearch(owners, w, cost, sc, e, me, opp, depth - 1, p, alpha, beta, fog_left)
            owners[m] = prev
            sc[player] -= w[m]
            if prev == opp:
                sc[opp] += w[m]
        if maximizing:
            if v > best:
                best, best_m = v, m
            alpha = max(alpha, v)
        else:
            if v < best:
                best, best_m = v, m
            beta = min(beta, v)
        if beta <= alpha:
            break
    return best, best_m


PROFILE_PARAMS = {"0": {"lam": 1.1, "lam_opp": 0.7151, "front_w": 0.4339, "hidden_v": 3.7375, "expose": 0.4524, "fog_v": 12.0564, "fog_c": 3, "end_turns": 0, "waste": 0.4952, "topk": 9}, "1": {"lam": 1.43, "lam_opp": 0.9001, "front_w": 0.4517, "hidden_v": 2.875, "expose": 0.6174, "fog_v": 7.9157, "fog_c": 3, "end_turns": 4, "waste": 0.8895, "topk": 9}, "2": {"lam": 1.43, "lam_opp": 1.0596, "front_w": 0.5372, "hidden_v": 2.875, "expose": 0.6049, "fog_v": 5.2477, "fog_c": 2, "end_turns": 3, "waste": 0.6538, "topk": 9}}


def choose_action(state):
    p = dict(PROFILE_PARAMS.get(str(state["opponent_profile"]), PARAMS))
    for k, base in (("lam_m", "lam"), ("lamo_m", "lam_opp"), ("front_m", "front_w"), ("expose_m", "expose"), ("fog_m", "fog_v"), ("hid_m", "hidden_v")):
        if k in OVR:
            p[base] = p[base] * OVR[k]
    me = state["seat"]
    owners = list(state["owners"])
    w = [x or 0 for x in state["weights"]]
    cost = [x or 0 for x in state["costs"]]
    sc = list(state["scores"])
    en = list(state["energy"])
    my_turns = (state["actions_remaining"] + 1) // 2
    if my_turns <= END_K:
        _, m = endsearch(owners, w, cost, sc, en, me, me, state["actions_remaining"], p, -1e18, 1e18, True)
    else:
        _, m = search(owners, w, cost, sc, en, me, me, DEPTH, my_turns, p, -1e18, 1e18)
    if m not in state["legal_actions"]:
        return None
    return m
