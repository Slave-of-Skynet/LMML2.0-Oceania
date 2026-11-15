"""Pre-registered decoder for Australia (see INVENTORY_PROTOCOL.md section 0).

Usage: python -I decode.py outputs/inventory.tsv
       python -I decode.py --bits 100010100110100   (raw bit string, secondary table only)

TSV columns: id, type, x_hint, y_hint, screenshot, competent, note, then one
behaviour column per observed generation, named like R1_G612, R2_G640.
Values: take/hit/kill = "engaged", skip/ignore/avoid = "passed".

PRIMARY scheme (frozen): order by x_hint asc (ties: listed order), bit 1 = agent
behaviour differs from `competent`, 5-bit groups, A=1..Z=26.
"""
import csv
import re
import sys
from collections import Counter

ENGAGE = {"take", "hit", "kill"}
PASS = {"skip", "ignore", "avoid"}


def norm(v):
    v = (v or "").strip().lower()
    if v in ENGAGE:
        return "E"
    if v in PASS:
        return "P"
    return None


def letters(bits, a=1):
    out = []
    for i in range(0, len(bits) - len(bits) % 5, 5):
        n = int(bits[i:i + 5], 2) - a
        out.append(chr(65 + n) if 0 <= n < 26 else "?")
    tail = len(bits) % 5
    return "".join(out) + (f" (+{tail} leftover bits)" if tail else "")


def inv(bits):
    return bits.translate(str.maketrans("01", "10"))


def variants(bits):
    rows = []
    for name, b in [("as-is", bits), ("inverted", inv(bits)),
                    ("reversed", bits[::-1]), ("rev+inv", inv(bits)[::-1])]:
        rows.append((name, b, letters(b, 1), letters(b, 0)))
    return rows


def print_variants(title, bits):
    print(f"  {title}: {len(bits)} bits")
    print(f"    {'variant':<9} {'bits':<{max(len(bits), 4)}}  A=1        A=0")
    for name, b, a1, a0 in variants(bits):
        print(f"    {name:<9} {b:<{max(len(bits), 4)}}  {a1:<10} {a0}")


def x_key(row):
    try:
        return float(row["x_hint"])
    except (TypeError, ValueError):
        return float("inf")


def main(argv):
    if len(argv) >= 2 and argv[0] == "--bits":
        print_variants("raw bits (secondary only)", argv[1])
        return 0
    if len(argv) != 1:
        print(__doc__)
        return 2
    with open(argv[0], encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    rows = sorted(enumerate(rows), key=lambda t: (x_key(t[1]), t[0]))
    rows = [r for _, r in rows]
    beh_cols = [c for c in rows[0] if re.match(r"^R\d+_", c or "")] if rows else []

    print(f"Objects: {len(rows)}  by type: {dict(Counter(r['type'] for r in rows))}")
    bad_x = [r["id"] for r in rows if x_key(r) == float("inf")]
    unclear = [r["id"] for r in rows if norm(r.get("competent")) is None]
    if bad_x:
        print(f"WARNING non-numeric x_hint (sorted last): {bad_x}")
    if unclear:
        print(f"WARNING competent unclear for ids {unclear}: primary scheme undefined until resolved")
    if len(rows) % 5:
        print(f"WARNING {len(rows)} events is not a multiple of 5")
    print("Order:", " ".join(f"{r['id']}:{r['type']}" for r in rows))
    print()

    primary = {}
    for col in beh_cols:
        beh = [norm(r.get(col)) for r in rows]
        missing = [r["id"] for r, b in zip(rows, beh) if b is None]
        if missing:
            print(f"[{col}] missing/unknown behaviour for ids {missing}; skipped")
            continue
        engaged = "".join("1" if b == "E" else "0" for b in beh)
        if not unclear:
            dev = "".join("1" if b != norm(r["competent"]) else "0" for r, b in zip(rows, beh))
            primary[col] = dev
            print(f"[{col}] PRIMARY deviation bits {dev} -> {letters(dev, 1)}")
        print_variants(f"[{col}] secondary, engaged=1", engaged)
        for t in ("coin", "qblock"):
            sub = "".join(e for r, e in zip(rows, engaged) if r["type"] == t)
            if sub:
                print(f"    only {t:<6}: {sub} -> A=1 {letters(sub, 1)} | A=0 {letters(sub, 0)}")
        print()

    if len(primary) >= 2:
        runs = {}
        for col, bits in primary.items():
            runs.setdefault(col.split("_")[0], set()).add(bits)
        stable = all(len(s) == 1 for s in runs.values())
        agree = len({next(iter(s)) for s in runs.values()}) == 1 if stable else False
        print(f"Stable within each run: {stable}; identical across runs: {agree if len(runs) >= 2 else 'not assessed (only one run)'}")
        if stable and agree and len(runs) >= 2 and not len(rows) % 5:
            word = letters(next(iter(primary.values())), 1)
            ok = "?" not in word
            print("CANDIDATE (primary, reproduced):" if ok else "No clean A-Z word:", word)
        else:
            print("No candidate: need >=2 runs agreeing, stable within run, events % 5 == 0")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
