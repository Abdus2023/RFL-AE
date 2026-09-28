#!/usr/bin/env python3
"""Regenerate every ASCII diagram in RFL-TRANSITION-V01.md.

    python3 diagrams/RFL-TRANSITION-V01.py [outdir]    # default /tmp/rtrdiag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py RFL-TRANSITION-V01.md <outdir>

The diagrams in RFL-TRANSITION-V01.md are NOT verbatim transcriptions: the
pasted source had all of its art collapsed onto single lines, so each diagram
was re-derived. This script is the record of that derivation -- re-running it
and diffing against the committed document proves the diagrams still match.

Collapse rule used throughout: a run of N spaces inside a collapsed block is a
line break followed by N-1 leading spaces; an extra space between two
unindented lines is a blank line. Runs that are clearly intra-line alignment
(the `∧   ` column in §955, the name column in §958, `│     └──` in §959, the
`=` column in §960) are kept as spacing. Single-space word runs were broken
into lines where they are lists (§947, §950, §952, §954, §964, §965, §967);
in §963 each `↓ δ` stays on its arrow line because δ labels the step.

Glyph note. Box-drawing art stays box-drawing; `↓` / `→` / `►` / `≠` / `⇒` /
`∧` / `∀` chains stay as they are. No block mixes an ASCII `|` with box glyphs
(the `|` in §950 is the source's own alternation bar in a text-only block).

Normalisations (all geometric, no content change):
  * §968 authority boundary: the spine (the box's ┬ and every arrow) is on
    column 20 in the source, but `HUMAN / POLICY`, `OperationRequest`,
    `Accepted` and `EventProposal` were one to four columns off it; all
    labels are now centred on 20. The box's width and contents are the
    source's.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/rtrdiag")
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
HEAD = "\u25ba"                  # ►
NEQ = "\u2260"                   # ≠
IMPL = "\u21d2"                  # ⇒
AND = "\u2227"                   # ∧
FORALL = "\u2200"                # ∀
DELTA = "\u03b4"                 # δ


def one(s):
    return [s]


def dchain(items, c):
    """Items at column 0 joined by a ↓ on column c."""
    out = [items[0]]
    for it in items[1:]:
        out += [" " * c + DWN, it]
    return out


def lchain(items, c):
    """Items at column 0 joined by │ / │ label / ▼ on column c.
    `items` alternates node, label, node, ...; a label of None means none."""
    out = [items[0]]
    for i in range(1, len(items), 2):
        lab, nxt = items[i], items[i + 1]
        out.append(marks([(c, VERT)]))
        if lab is not None:
            out.append(" " * c + VERT + " " + lab)
        out += [marks([(c, DOWN)]), nxt]
    return out


def kids(items, col):
    return [" " * col + (BR if i == len(items) - 1 else TR) + DASH * 2 + " " + s
            for i, s in enumerate(items)]


def groups(items, indent=4):
    out = []
    for i, (h, vals) in enumerate(items):
        if i:
            out.append("")
        out += [h] + [" " * indent + v for v in vals]
    return out


def indented(head, items, indent=4):
    return [head] + [" " * indent + v for v in items]


# ================================================================ §947
D["P01"] = (["crates/rfl-transition/"] + kids(["Cargo.toml", "src/"], 0)
            + kids(["lib.rs", "engine.rs", "state.rs", "context.rs",
                    "preconditions.rs", "transitions.rs", "rejection.rs",
                    "authorization.rs", "replay.rs", "tests/"], 4)
            + kids(["admission.rs", "authorization.rs", "execution.rs",
                    "verification.rs", "certification.rs", "epoch.rs",
                    "replay.rs", "adversarial.rs"], 8))
D["P02"] = ["rfl-transition", marks([(6, VERT)])] + kids(["rfl-types"], 6)
D["P03"] = [f"rfl-transition {ARROW} {t}"
            for t in ("rfl-ledger", "rfl-evidence", "rfl-gates")]

# ================================================================ §949
D["P04"] = groups([("State", ["= authoritative protocol state"]),
                   ("Context", ["= supplied evaluation context"])])

# ================================================================ §950
D["P05"] = [f"{DELTA} : (State, OperationRequest, TransitionContext)",
            " " * 6 + ARROW, " " * 4 + "TransitionResult"]
D["P06"] = ["TransitionResult", "    =", "      Accepted(EventProposal)",
            "    |", "      Rejected(Rejection)"]
D["P07"] = one(f"{DELTA}(S, R, C) = X")
D["P08"] = one("context.observed_time")

# ================================================================ §951
D["P09"] = dchain(["TransitionEngine", "EventProposal", "Ledger validation",
                   "append", "authoritative history"], c=6)

# ================================================================ §952
D["P10"] = dchain(["REQUEST", "Transition accepted",
                   "authorization to perform operation", "actual executor",
                   "execution result"], c=2)
D["P11"] = one('"The protocol permits this execution."')
D["P12"] = one('"The command ran successfully."')
D["P13"] = [f"{a} {NEQ} {b}" for a, b in (
    ("Accepted", "Executed"), ("Executed", "Succeeded"),
    ("Succeeded", "Verified"), ("Verified", "Certified"))]

# ================================================================ §954
D["P14"] = [f"P{i:02d} {s}" for i, s in enumerate([
    "request identity", "task existence", "epoch", "snapshot",
    "specification", "protocol", "authorization existence",
    "authorization epoch", "authorization actor", "authorization task",
    "capability", "operation compatibility", "scope", "expiry", "revocation",
    "task state", "dependency state", "duplicate/replay",
    "operation-specific preconditions"], start=1)]
assert len(D["P14"]) == 19
D["P15"] = one("EpochMismatch")
D["P16"] = one("ScopeViolation")

# ================================================================ §955
# `:=` on column 1; AuthorizationExists and every conjunct after `∧   ` on 5.
D["P17"] = (["AUTHORIZED(R,S,C)", " :=", "     AuthorizationExists"]
            + [" " + AND + "   " + t for t in (
                "EpochMatches", "ActorMatches", "TaskMatches",
                "CapabilityExists", "OperationAllowed", "ScopeSatisfied",
                "NotExpired", "NotRevoked")])
D["P18"] = one("Authorization exists")
D["P19"] = one("Capability exists")
D["P20"] = one("Agent possesses capability")

# ================================================================ §956
D["P21"] = groups([("Capability", ["=", "what an actor may potentially perform"]),
                   ("Authorization", ["=", "permission to perform one operation",
                                      "for one task", "in one epoch",
                                      "within one scope"])])
D["P22"] = one("Capability(Execute, /drivers/foo)")
D["P23"] = one("Execute(Task-42, /drivers/foo)")

# ================================================================ §957
D["P24"] = one("requested_scope \u2286 authorized_scope")
D["P25"] = one("authorized_scope \u2286 requested_scope")
D["P26"] = ["Authorized:", "", "drivers/foo/**"]
D["P27"] = one("drivers/foo/bar.c")
D["P28"] = one("drivers/bar/baz.c")
D["P29"] = one("drivers/foo/** + drivers/bar/**")

# ================================================================ §958
# Source geometry kept: spine on 3; both branch arrowheads on column 30.
_c = 3
D["P30"] = lchain(["Created", "Admit", "Admitted", "Authorize", "Authorized",
                   "Execute", "Executing"], _c)
D["P30"] += [" " * _c + TR + DASH * 8 + " Complete " + DASH * 8 + HEAD
             + " Succeeded",
             marks([(_c, VERT)]),
             " " * _c + BR + DASH * 8 + " Fail " + DASH * 12 + HEAD + " Failed",
             ""]
assert D["P30"][-4].index(HEAD) == D["P30"][-2].index(HEAD) == 30
D["P30"] += lchain(["Succeeded", "Verify", "Verified", "Gate", "Gated",
                    "Certify", "Certified"], _c)
D["P31"] = ([f"{'Created'.ljust(13)}{ARROW} {op}"
             for op in ("Execute", "Verify", "Certify")] + [""]
            + [f"{s.ljust(13)}{ARROW} {op}" for s, op in (
                ("Admitted", "Execute"), ("Authorized", "Verify"),
                ("Executing", "Certify"), ("Succeeded", "Certify"),
                ("Failed", "Verify"), ("Verified", "Execute"),
                ("Gated", "Execute"), ("Certified", "anything"))])

# ================================================================ §959
# Source geometry kept: attempt outcomes hang on column 6.
D["P32"] = ["Task T"]
for _n, _last in ((0, False), (1, False), (2, True)):
    D["P32"] += [VERT, (BR if _last else TR) + DASH * 2 + f" Attempt A{_n}",
                 (" " if _last else VERT) + " " * 5 + BR + DASH * 2 + " "
                 + ("Succeeded" if _last else "Failed")]
D["P33"] = one("A0.state = Executing")
D["P34"] = one("A1")
D["P35"] = one("attempt sequence is historical evidence")

# ================================================================ §960
D["P36"] = one("RequestDigest = Digest(CanonicalEncode(OperationRequest))")
D["P37"] = one("(RequestId, RequestDigest)")
D["P38"] = one(f"{ARROW} return recorded result")
D["P39"] = one(f"{ARROW} ReplayConflict")
D["P40"] = ["RequestId = R1", "first meaning  = Execute(foo)",
            "second meaning = Execute(bar)"]

# ================================================================ §961
D["P41"] = dchain(["artifact generator", "verification authority"], c=7)
D["P42"] = dchain(["artifact generator", '"verify myself"'], c=7)

# ================================================================ §962
D["P43"] = (["generic transition engine", marks([(10, VERT)])]
            + kids(["generic authorization", "generic epoch", "generic scope",
                    "operation policy"], 10))
D["P44"] = one("Execute")

# ================================================================ §963
D["P45"] = indented("stored_state", ["+", "stored_events", "=",
                                     '"probably valid"'])
D["P46"] = ["Genesis", "   " + DWN, "Event 1", "   " + DWN + " " + DELTA,
            "State 1", "   " + DWN, "Event 2", "   " + DWN + " " + DELTA,
            "State 2", "   " + DWN, "..."]
D["P47"] = one("replay(E\u2080...E\u2099) = S\u2099")
D["P48"] = one("stored resulting_state == digest(replay-derived state)")
D["P49"] = one("ReplayDivergence")

# ================================================================ §964
D["P50"] = ["09:00 authorization active", "09:05 Execute accepted",
            "09:10 authorization expires"]
D["P51"] = ["Event"] + kids(["event timestamp",
                             "authorization snapshot/reference", "epoch",
                             "transition inputs"], 1)
D["P52"] = one(f"current validity {NEQ} historical validity")

# ================================================================ §965
D["P53"] = ["E0: authorization active", "E1: Execute accepted",
            "E2: authorization revoked"]
D["P54"] = ["E1 = valid historical transition",
            "E2 = valid revocation transition"]
D["P55"] = one("E1 = invalid because authorization is currently revoked")

# ================================================================ §966
D["P56"] = one(f"request.epoch != state.epoch {IMPL} reject")
D["P57"] = one(f"\u00acAUTHORIZED(request) {IMPL} reject")
D["P58"] = one(f"requested_scope \u2284 authorized_scope {IMPL} reject")
D["P59"] = one(f"(state, operation) \u2209 TransitionTable {IMPL} reject")
D["P60"] = one(f"apply(S,R,C) = Reject {IMPL} S' = S")
D["P61"] = one(f"{DELTA}(S,R,C) = X {IMPL} repeated {DELTA}(S,R,C) = X")
D["P62"] = one(f"same RequestId + same RequestDigest {IMPL} same historical "
               "result")
D["P63"] = one(f"same RequestId + different RequestDigest {IMPL} "
               "ReplayConflict")
D["P64"] = one("past valid transition")
D["P65"] = one("Verified")
D["P66"] = one("Certified")

# ================================================================ §967
D["P67"] = indented(f"{FORALL} R:", ["epoch mismatch", f"{IMPL} never Accepted"])
D["P68"] = indented(f"{FORALL} R:", ["unauthorized scope",
                                     f"{IMPL} never Accepted"])
D["P69"] = indented(f"{FORALL} S,R,C:", ["rejected transition",
                                         f"{IMPL} state unchanged"])
D["P70"] = indented(f"{FORALL} valid histories H:",
                    ["replay(H) == recorded_final_state"])
D["P71"] = ["event digest", "previous event", "state digest", "sequence",
            "request digest"]

# ================================================================ §968
S, LEFT, INNER = 20, 8, 23
assert LEFT + 1 + INNER // 2 == S
_box = ([" " * LEFT + CORNER_TL + DASH * INNER + CORNER_TR]
        + [" " * LEFT + VERT + l.ljust(INNER) + VERT for l in (
            "   rfl-transition", "", " epoch", " authorization", " capability",
            " scope", " state", " dependencies", " transition table")]
        + [" " * LEFT + CORNER_BL + DASH * (S - LEFT - 1) + TEE_D
           + DASH * (LEFT + INNER - S) + CORNER_BR])
D["P72"] = [row([("HUMAN / POLICY", S)]), marks([(S, VERT)]),
            marks([(S, DOWN)]), row([("OperationRequest", S)]),
            marks([(S, VERT)]), marks([(S, DOWN)])]
D["P72"] += _box + [marks([(S, VERT)]), row([("Accepted", S)]),
                    marks([(S, VERT)]), marks([(S, DOWN)])]
for _lab in ("EventProposal", "rfl-ledger"):
    D["P72"] += [row([(_lab, S)]), marks([(S, VERT)]), marks([(S, DOWN)])]
D["P72"] += [row([("authoritative", S)]), row([("history", S)])]

# ================================================================ §969
D["P73"] = lchain(["rfl-types", None, "rfl-transition", None, "rfl-ledger"],
                  3)
D["P73"] += ([marks([(3, VERT)])]
             + kids(["append", "hash-chain validation", "replay",
                     "fork detection", "tamper tests"], 3))
D["P73"] += lchain(["", None, "rfl-evidence", None, "rfl-gates"], 3)[1:]
D["P74"] = one("What exactly makes a historical event authoritative, and how "
               "do we prove that replay of that history reconstructs the same "
               "protocol state without trusting the stored state itself?")

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
