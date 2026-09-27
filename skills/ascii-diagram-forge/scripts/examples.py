#!/usr/bin/env python3
"""examples.py — runnable demo + self-test for geo.py.

    python3 examples.py

Prints one worked example per helper, then asserts the invariants that matter.
Every pattern here is lifted from a diagram that actually shipped in the corpus,
so this file doubles as the reference for "how we draw these".
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import (align, bar, box, boxfix, cen, colbox, dchain, flow, hjoin,
                 marks, padc, row, tree, CORNER_BL, CORNER_BR, CORNER_TL,
                 CORNER_TR, CROSS, DOWN, HORIZ, TEE_D, TEE_U, VERT)

failures = []


def show(title, lines):
    print(f"--- {title} " + "-" * max(0, 58 - len(title)))
    print("\n".join(lines))
    print()


def check(label, cond):
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")
    if not cond:
        failures.append(label)


# ---------------------------------------------------------------- 1. spine + box
def ex_spine():
    C = 25
    out = [row([("Migration Unit", C)]), marks([(C, VERT)])]
    L, R = 14, 36
    out.append(bar([(L, CORNER_TL), (C, TEE_U), (R, CORNER_TR)]))
    out.append(marks([(L, DOWN), (R, DOWN)]))
    out.append(row([("Implementation", L), ("Contract Review", R)]))
    out.append(marks([(L, VERT), (R, VERT)]))
    out.append(marks([(L, DOWN), (R, DOWN)]))
    out.append(row([("Rust artifact", L), ("Contract artifact", R)]))
    out.append(marks([(L, VERT), (R, VERT)]))
    out.append(bar([(L, CORNER_BL), (C, TEE_D), (R, CORNER_BR)]))
    out += flow(C)
    out.append(row([("Independent Verifier", C)]))
    return out


# ---------------------------------------------------------------- 2. three-way fan
def ex_fan():
    C = 32
    A, B = 15, 49
    out = [row([("Orchestration IR", C)]), marks([(C, VERT)])]
    out.append(bar([(A, CORNER_TL), (C, CROSS), (B, CORNER_TR)]))
    out.append(marks([(A, DOWN), (C, DOWN), (B, DOWN)]))
    out.append(row([("Dependency", A), ("Capability", C), ("Policy", B)]))
    out.append(row([("State", A), ("Matching", C), ("Rules", B)]))
    out.append(marks([(A, VERT), (C, VERT), (B, VERT)]))
    out.append(bar([(A, CORNER_BL), (C, CROSS), (B, CORNER_BR)]))
    out += flow(C)
    out.append(row([("Deterministic Scheduler", C)]))
    return out


# ---------------------------------------------------------------- 3. tree
def ex_tree():
    crates = [("rfl-scheduler", ["readiness.rs", "selection.rs", "dispatch.rs"]),
              ("rfl-leases", ["migration.rs", "expiry.rs"])]
    out = ["crates/"]
    for ci, (crate, files) in enumerate(crates):
        last = ci == len(crates) - 1
        out.append(("\u2514\u2500\u2500 " if last else "\u251c\u2500\u2500 ") + crate + "/")
        p = "    " if last else "\u2502   "
        for fi, f in enumerate(files):
            out.append(p + ("\u2514\u2500\u2500 " if fi == len(files) - 1
                            else "\u251c\u2500\u2500 ") + f)
    return out


# ---------------------------------------------------------------- 4. branch off a chain
def ex_branch():
    out = []
    steps = ["REQUESTED", "VALIDATING", "EXECUTING", "CAPTURING"]
    for i, n in enumerate(steps):
        out.append(n)
        if n == "EXECUTING":
            out.append("    " + VERT)
            for j, b in enumerate(["timeout", "resource violation", "process failure"]):
                out.append("    " + ("\u2514\u2500\u2500 " if j == 2 else "\u251c\u2500\u2500 ") + b)
        if i < len(steps) - 1:
            out += ["    " + VERT, "    " + DOWN]
    return out


# ---------------------------------------------------------------- 5. boxes + gutter
def ex_boxes():
    C = 35
    out = boxfix(["Linux Snapshot"], C, 20)
    out += flow(C)
    out += boxfix(["Semantic Reconstruction"], C, 24)
    out.append(marks([(C, DOWN)]))
    out.append(row([("KSIR", C), ("WHAT EXISTS?", 58)]))
    return out


# ---------------------------------------------------------------- 6. aligned table
def ex_align():
    return align([("E001", "UnitDiscovered      MU-001"),
                  ("E007", "ImplementationCompleted  MU-001"),
                  ("...", "")], 2)


# ---------------------------------------------------------------- 7. side by side
def ex_colbox():
    return colbox([["Gate A"], ["Gate B", "second line"]], [15, 45])


print("=" * 62)
print("geo.py — worked examples (each shipped in the RFL-AE corpus)")
print("=" * 62)
print()
show("spine + fork (ORCHESTRATION multi-agent topology)", ex_spine())
show("three-way fan (ORCHESTRATION architecture)", ex_fan())
show("crate tree (ORCHESTRATION crate architecture)", ex_tree())
show("branch off a chain (EXECUTION lifecycle)", ex_branch())
show("forced-gutter boxes (ORCHESTRATION complete system)", ex_boxes())
show("two-column alignment (scheduler event log)", ex_align())
show("colbox side-by-side", ex_colbox())
show("dchain vertical chain", dchain(["AUTHORIZED REQUEST", "EXACT EXECUTION",
                                      "IMMUTABLE RECEIPT"], 2))
show("tree() helper", tree("MU-001", ["requires contract from MU-004",
                                      "shares ABI with MU-007"]))

print("=" * 62)
print("self-test")
print("=" * 62)

check("cen centres odd width exactly", cen("abcde", 10) == 8)
check("cen on even width lands one left (by design)", cen("abcd", 10) == 8)

# overlap must raise -- this is the defect that produced 'acceptquarantine'
try:
    row([("accept", 3), ("quarantine", 5)])
    check("row() raises on overlap", False)
except ValueError as e:
    check("row() raises on overlap", "OVERLAP" in str(e))

try:
    row([("a very long label", 2)])
    check("row() raises on negative start", False)
except ValueError as e:
    check("row() raises on negative start", "negative" in str(e))

try:
    hjoin([(10, "abcdefghij"), (5, "x")])
    check("hjoin() raises on overlap", False)
except ValueError:
    check("hjoin() raises on overlap", True)

# box geometry: right border is bw-1 from left, and boxfix gutter is G+1
rows, left, right = box(["Linux Snapshot"], 35)
check("box left/right match border glyphs",
      len(rows[0]) > right and rows[0][left] == CORNER_TL and rows[0][right] == CORNER_TR)
check("box content rows span exactly left..right",
      all(len(r.rstrip()) == right + 1 for r in rows))

fx = boxfix(["Linux Snapshot"], 35, 20)
fx_left = len(fx[0]) - len(fx[0].lstrip())
fx_right = len(fx[0].rstrip()) - 1
G = 20
check(f"boxfix right border at G+3 from its left (got {fx_right - fx_left}, want {G + 3})",
      fx_right - fx_left == G + 3)

check("no ASCII pipe in box borders", all("|" not in r for r in rows))
check("dchain length is 2n-1", len(dchain(["a", "b", "c"])) == 5)
check("tree gives root+spine+kids", len(tree("R", ["a", "b"])) == 4)
check("padc pads to width", all(len(padc(s, 12)) == 12 for s in ("a", "abcd", "abcdefghij")))

print()
if failures:
    print(f"{len(failures)} FAILED: {failures}")
    sys.exit(1)
print("all self-tests passed")
