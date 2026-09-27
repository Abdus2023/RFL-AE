#!/usr/bin/env python3
"""Regenerate every ASCII diagram in RFL-LEDGER.md.

    python3 diagrams/RFL-LEDGER.py [outdir]    # default /tmp/rldiag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py RFL-LEDGER.md <outdir>

The diagrams in RFL-LEDGER.md are NOT verbatim transcriptions: the pasted
source had all of its art collapsed onto single lines, so each diagram was
re-derived. This script is the record of that derivation -- re-running it and
diffing against the committed document proves the diagrams still match.

Glyph note. Box-drawing art stays box-drawing; the two fork diagrams (§855,
§856) arrive as ASCII `/ \\` and stay that way; `↓` / `→` / `←` / `≠` chains
stay as they are. No block mixes an ASCII `|` with box glyphs.

Normalisations (all geometric, no content change):
  * §856 branch fork: the two branch labels were symmetric about column 18
    while the fork is symmetric about 17; the labels now sit about 17.
  * §864 security boundary: the source's `EVENT VALIDATOR` row was one column
    wider than its box (17 vs 16 inner columns). All three boxes are widened
    to 17 so every row has the same padding; that puts the ┬ on column 16,
    where the source's upper spine already was, and the lower spine (15 in
    the source) now continues on 16. Labels are centred on it.
  * §865 evidence pipeline: labels centred on the box's ┬ at column 19, which
    is also the source's spine column.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/rldiag")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import (VERT, DOWN, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
                 TEE_D, HORIZ, row, marks)  # noqa: E402

D = {}
BR, TR = "\u2514", "\u251c"      # └ ├
DASH = HORIZ                     # ─
DWN = "\u2193"                   # ↓
ARROW = "\u2192"                 # →
LARROW = "\u2190"                # ←
NEQ = "\u2260"                   # ≠


def one(s):
    return [s]


def dchain(items, c):
    out = [items[0]]
    for it in items[1:]:
        out += [" " * c + DWN, it]
    return out


def bchain(items, c):
    out = [items[0]]
    for it in items[1:]:
        out += [marks([(c, VERT)]), marks([(c, DOWN)]), it]
    return out


def kids(items, col):
    return [" " * col + (BR if i == len(items) - 1 else TR) + DASH * 2 + " " + s
            for i, s in enumerate(items)]


def rule(head, glyph, tail, indent=4):
    return [head, " " * indent + glyph + " " + tail]


def groups(items, indent=4):
    out = []
    for i, (h, vals) in enumerate(items):
        if i:
            out.append("")
        out += [h] + [" " * indent + v for v in vals]
    return out


def spine_box(left, inner, lines, pad=1):
    """Box at column `left` with `inner` columns; bottom ┬ at its centre."""
    s = left + 1 + inner // 2
    return ([" " * left + CORNER_TL + DASH * inner + CORNER_TR]
            + [" " * left + VERT + (" " * pad + l).ljust(inner) + VERT
               for l in lines]
            + [" " * left + CORNER_BL + DASH * (s - left - 1) + TEE_D
               + DASH * (left + inner - s) + CORNER_BR]), s


# ================================================================ §843
D["P01"] = (["crates/rfl-ledger/"] + kids(["Cargo.toml", "src/"], 0)
            + kids(["lib.rs", "ledger.rs", "event.rs", "digest.rs",
                    "append.rs", "replay.rs", "validation.rs", "fork.rs",
                    "tests/"], 4)
            + kids(["append.rs", "replay.rs", "tamper.rs", "ordering.rs",
                    "duplicate.rs", "fork.rs"], 8))
D["P02"] = bchain(["rfl-types", "rfl-transition", "rfl-ledger"], c=6)
D["P03"] = one("EVENT INTEGRITY + ORDER + APPEND + REPLAY + HISTORY VALIDATION")

# ================================================================ §844
D["P04"] = rule("EventId", NEQ, "EventDigest")

# ================================================================ §845
D["P05"] = dchain(["EventCore", "canonical encoding", "Digest",
                   "Event { ..., event_digest }"], c=4)
D["P06"] = one("event_digest = H(canonical(EventCore))")

# ================================================================ §846
D["P07"] = []
for _n, _prev in enumerate(["None", "E0", "E1"]):
    if _n:
        D["P07"] += [marks([(7, VERT)]), marks([(7, DOWN)])]
    D["P07"] += [f"E{_n}", " " + VERT] + kids(
        [f"sequence = {_n}", f"previous_event = {_prev}",
         f"digest = D{_n}"], 1)
D["P08"] = one("E[n].previous_event == E[n-1].id")
D["P09"] = one("E[n].previous_state == E[n-1].resulting_state")
D["P10"] = one("history linkage + state linkage")

# ================================================================ §847
D["P11"] = one("E17.resulting_state")
D["P12"] = one("E18.previous_event")
D["P13"] = one("E18.previous_state != modified(E17.resulting_state)")
D["P14"] = one("E18.previous_event")
D["P15"] = one("event_digest + previous_event + previous_state")

# ================================================================ §848
D["P16"] = ["MemoryLedger", "FileLedger", "GitLedger", "DatabaseLedger",
            "ContentAddressedLedger", "RemoteLedger"]

# ================================================================ §849
D["P17"] = dchain(["Transition relation", "valid Event", "validated ledger",
                   "replay", "authoritative state"], c=7)
D["P18"] = one("database says Certified")
D["P19"] = ["ledger replay", " " * 4 + ARROW + " state",
            " " * 4 + ARROW + " Certified"]

# ================================================================ §850
D["P20"] = [f"{i}. {s}" for i, s in enumerate([
    "validate event digest", "validate sequence", "validate previous_event",
    "validate previous_state", "validate transition", "apply transition",
    "compare resulting state", "continue"], start=1)]
D["P21"] = one("event.resulting_state")

# ================================================================ §851
D["P22"] = ["replay(E0...En)", " " * 7 + "== authoritative_state"]
D["P23"] = one("stored resulting_state != recomputed resulting_state")
D["P24"] = one("ReplayConflict")

# ================================================================ §852
D["P25"] = ["current wall clock", "randomness", "LLM output", "network state",
            "filesystem discovery", "environment variables", "CPU timing",
            "thread scheduling"]
D["P26"] = ["same State + same Request + same authoritative context",
            " " * 8 + DWN, "same Result"]

# ================================================================ §853
D["P27"] = one("now >= expires_at")
D["P28"] = one("now > event.authorization.expires_at")

# ================================================================ §854
D["P29"] = rule("TransitionContext", LARROW, "current authoritative state")
D["P30"] = rule("TransitionContext", LARROW, "event-bound historical context")

# ================================================================ §855
# Source geometry kept exactly: fork symmetric about column 14, and the two
# labels (9..12, 16..19) are symmetric about 14 as well.
D["P31"] = [row([("E10", 14)]),
            marks([(12, "/"), (16, "\\")]),
            marks([(11, "/"), (17, "\\")]),
            " " * 9 + "E11A" + "   " + "E11B"]
D["P32"] = one("previous_event = E10")
D["P33"] = one("ForkDetected")

# ================================================================ §856
D["P34"] = ["Agent A: E50 " + ARROW + " artifact A", "",
            "Agent B: E50 " + ARROW + " artifact B"]
# Fork symmetric about 17 (source); labels 8..15 and 19..26, also about 17.
D["P35"] = [row([("E50", 17)]),
            marks([(14, "/"), (20, "\\")]),
            marks([(13, "/"), (21, "\\")]),
            " " * 8 + "branch A" + "   " + "branch B"]

# ================================================================ §857
D["P36"] = ["History"] + kids(["branch A " + ARROW + " E73",
                               "branch B " + ARROW + " E71"], 1)

# ================================================================ §858
D["P37"] = (dchain(["old event", "immutable"], c=3) + [""]
            + dchain(["new event", "new history"], c=3))
D["P38"] = dchain(["E31", "CorrectionRequested", "E32"], c=1)

# ================================================================ §859
D["P39"] = ["Correction", "Invalidation", "Supersession", "Revocation"]
D["P40"] = ["E20: VerificationPassed", "E21: EvidenceInvalidated",
            "E22: VerificationInvalidated"]
D["P41"] = one('"E20 happened"')
D["P42"] = one('"artifact is currently verified"')
D["P43"] = one("history")
D["P44"] = one("current canonical state")

# ================================================================ §860
D["P45"] = dchain(["modify Core(E)", "Digest(E) changes",
                   "chain validation fails"], c=5)

# ================================================================ §861
D["P46"] = dchain(["Genesis", "E0", "E1", "..."], c=3)

# ================================================================ §862
D["P47"] = one("STRUCTURAL_VALID")
D["P48"] = one("SEMANTIC_VALID")
D["P49"] = one("REPLAY_VALID")
D["P50"] = groups([("Structural:", ["hashes correct", "sequence correct",
                                    "links correct"]),
                   ("Semantic:", ["transitions allowed"]),
                   ("Replay:", ["reconstructed state matches"])])
D["P51"] = ["Structural = PASS", "Semantic    = FAIL", "Replay      = BLOCKED"]

# ================================================================ §863
D["P52"] = ["E7.operation:", " " * 4 + "Execute " + ARROW + " Verify"]
D["P53"] = one("DigestMismatch")
D["P54"] = one("StateChainMismatch")
D["P55"] = one("HistoryLinkMismatch")
D["P56"] = one("E7, E8, E6")
D["P57"] = one("SequenceViolation")
D["P58"] = one("DuplicateEvent")
D["P59"] = one("ReplayConflict")
D["P60"] = ["E10 " + ARROW + " E11A", "E10 " + ARROW + " E11B"]
D["P61"] = one("ForkDetected")
D["P62"] = one("Certified")
D["P63"] = one("ReplayConflict")
D["P64"] = one("Replay succeeds")

# ================================================================ §864
_b1, S1 = spine_box(7, 17, ["TRANSITION", "ENGINE"])
_b2, _s2 = spine_box(7, 17, ["EVENT VALIDATOR"])
_b3, _s3 = spine_box(7, 17, ["APPEND-ONLY", "LEDGER"])
assert S1 == _s2 == _s3 == 16
D["P65"] = ([row([("REQUEST", S1)]), marks([(S1, VERT)]), marks([(S1, DOWN)])]
            + _b1
            + [marks([(S1, VERT)]), row([("accepted event", S1)]),
               marks([(S1, VERT)]), marks([(S1, DOWN)])]
            + _b2 + [marks([(S1, VERT)]), marks([(S1, DOWN)])]
            + _b3
            + [marks([(S1, VERT)]), marks([(S1, DOWN)]),
               row([("REPLAY ENGINE", S1)]),
               marks([(S1, VERT)]), marks([(S1, DOWN)]),
               row([("RECONSTRUCTED STATE", S1)])])
D["P66"] = (rule("trace", "=", "narrative") + [""]
            + rule("ledger", "=", "executable history"))

# ================================================================ §865
_eb, S2 = spine_box(10, 17, ["rfl-evidence", "", "artifact", "input",
                             "command", "environment", "toolchain", "output",
                             "outcome"])
assert S2 == 19
D["P67"] = [row([("PROTOCOL", S2)])]
for _lab in ("OperationRequest", "Transition", "Event", "Execution",
             "External observation"):
    D["P67"] += [marks([(S2, VERT)]), marks([(S2, DOWN)]), row([(_lab, S2)])]
D["P67"] += [marks([(S2, VERT)]), marks([(S2, DOWN)])] + _eb
for _lab in ("Verification", "Gates"):
    D["P67"] += [marks([(S2, VERT)]), marks([(S2, DOWN)]), row([(_lab, S2)])]
D["P68"] = ["OBSERVATION", " " * 5 + NEQ + " EVIDENCE RECORD",
            " " * 5 + NEQ + " VERIFICATION", " " * 5 + NEQ + " CERTIFICATION"]

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
