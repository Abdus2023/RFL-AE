#!/usr/bin/env python3
"""Regenerate every ASCII diagram in RFL-TRANSITION.md.

    python3 diagrams/RFL-TRANSITION.py [outdir]    # default /tmp/rxdiag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py RFL-TRANSITION.md <outdir>

The diagrams in RFL-TRANSITION.md are NOT verbatim transcriptions: the pasted
source had all of its art collapsed onto single lines, so each diagram was
re-derived. This script is the record of that derivation -- re-running it and
diffing against the committed document proves the diagrams still match.

Glyph note. Every diagram in this source arrives as box-drawing art or as a
`↓` / `→` / `⇒` chain, and stays that way. There is no ASCII `|` / `v` art in
this source at all.

Normalisations (all geometric, no content change):
  * §838 state machine: the source's chain below SUCCEEDED ran on column 30
    while the fork's right branch lands on column 29; the whole lower chain
    now continues on 29.
  * §842 TCB: the source's spine sat on column 20 with the labels off-centre;
    the spine and both labels now sit on the boxes' centre, column 21.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/rxdiag")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import (VERT, DOWN, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
                 TEE_D, TEE_U, HORIZ, row, marks)  # noqa: E402

D = {}
BR, TR = "\u2514", "\u251c"      # └ ├
DASH = HORIZ                     # ─
DWN = "\u2193"                   # ↓
ARROW = "\u2192"                 # →
IMPL = "\u21d2"                  # ⇒
UP = "\u25b2"                    # ▲


def one(s):
    return [s]


def dchain(items, c):
    out = [items[0]]
    for it in items[1:]:
        out += [" " * c + DWN, it]
    return out


def bchain(items, c):
    """Box-drawing chain: labels at column 0, │ / ▼ at column c."""
    out = [items[0]]
    for it in items[1:]:
        out += [marks([(c, VERT)]), marks([(c, DOWN)]), it]
    return out


def kids(items, col, prefix=None):
    """├── / └── children at column `col`."""
    prefix = " " * col if prefix is None else prefix
    return [prefix + (BR if i == len(items) - 1 else TR) + DASH * 2 + " " + s
            for i, s in enumerate(items)]


def rule(head, glyph, tail, indent=4):
    return [head, " " * indent + glyph + " " + tail]


def pairs(items, indent=4):
    out = []
    for i, (h, g, t) in enumerate(items):
        if i:
            out.append("")
        out += rule(h, g, t, indent)
    return out


# ================================================================ §823
D["N01"] = (["crates/rfl-transition/"]
            + kids(["Cargo.toml", "src/"], 0)
            + kids(["lib.rs", "engine.rs", "preconditions.rs",
                    "transitions.rs", "rejection.rs", "authorization.rs",
                    "replay.rs", "tests/"], 4)
            + kids(["epoch.rs", "authorization.rs", "transitions.rs",
                    "replay.rs", "adversarial.rs"], 8))
D["N02"] = dchain(["rfl-types", "rfl-transition"], c=4)

# ================================================================ §824
D["N03"] = dchain(["validate", "authorize", "check state", "check epoch",
                   "check scope", "construct next state", "construct event",
                   "commit"], c=3)
D["N04"] = dchain(["mutate", "discover violation", "try to undo"], c=2)

# ================================================================ §825
D["N05"] = ["Task T1"]
for _i, (_a, _s) in enumerate([("A1", "Failed"), ("A2", "Failed"),
                               ("A3", "Succeeded")]):
    D["N05"] += [VERT, (BR if _i == 2 else TR) + DASH * 2
                 + f" Attempt {_a} {ARROW} {_s}"]

# ================================================================ §826
D["N06"] = one("Created " + ARROW + " Certified")
D["N07"] = one("Rejected(InvalidTransition)")

# ================================================================ §827
D["N08"] = [f"check_{n}(...)" for n in (
    "task", "epoch", "snapshot", "authorization", "capability", "scope",
    "state", "dependencies", "duplicate")]

# ================================================================ §828
D["N09"] = one('"request invalid"')

# ================================================================ §829
D["N10"] = ["Authorization"] + kids(
    ["actor", "task", "epoch", "operation", "capability", "scope",
     "expiration"], 1)
D["N11"] = ["authorization.actor == request.actor",
            "authorization.task == request.task",
            "authorization.epoch == request.epoch",
            "authorization.capability permits request.operation",
            "authorization.scope contains request.target",
            "now < authorization.expires_at"]

# ================================================================ §830
D["N12"] = one("drivers/foo/bar.c")
D["N13"] = ["authorized for:", " " * 4 + "drivers/foo/", "",
            "actually modifies:", " " * 4 + "kernel/sched/"]

# ================================================================ §831
D["N14"] = ["ExecutionTarget", "BuildTarget", "TestTarget", "RepositoryTarget"]

# ================================================================ §832
D["N15"] = (["RFL protocol", marks([(6, VERT)]),
             marks([(6, VERT)]) + " typed execution request",
             marks([(6, DOWN)]), "Execution Adapter", marks([(6, VERT)])]
            + kids(["Cargo", "LLVM", "clang", "kernel build", "KUnit",
                    "kselftest", "other tools"], 6))

# ================================================================ §833
D["N16"] = one("Request R42")
D["N17"] = dchain(["RequestId", "request ledger", "already accepted?"], c=4)
D["N18"] = pairs([("same request + same content", ARROW,
                   "return recorded result"),
                  ("same request + different content", ARROW,
                   "ReplayConflict")])

# ================================================================ §834
D["N19"] = one("R42 " + ARROW + " Execute artifact A")
D["N20"] = one("R42 " + ARROW + " Execute artifact B")
D["N21"] = ["RequestDigest =", " " * 4 + "H(canonical(OperationRequest))"]
D["N22"] = one("same RequestId AND same RequestDigest")
D["N23"] = one("same RequestId AND different RequestDigest")
D["N24"] = one("ReplayConflict")

# ================================================================ §835
D["N25"] = ["Epoch E17", marks([(3, VERT)]),
           " " * 3 + TR + DASH * 2 + " analyze source",
           " " * 3 + TR + DASH * 2 + " generate Rust",
           marks([(3, VERT)]),
           " " * 3 + BR + DASH * 2 + " source repository advances",
           " " * 12 + DWN, " " * 9 + "Epoch E18"]
D["N26"] = ["Authorization(E17)", " " * 8 + "+ Request(E18)", " " * 8 + DWN,
            "EpochMismatch"]

# ================================================================ §836
D["N27"] = (dchain(["Evidence", "supports verification"], c=4)
            + ["", "NOT", ""]
            + dchain(["Evidence", "declares itself valid",
                      "authorizes certification"], c=4))

# ================================================================ §837
# The drop to Certificate hangs from the whole tree, not from one child; it
# sits at the source's column 9, separated from the tree by nothing.
D["N28"] = (["Artifact", marks([(3, VERT)])]
            + kids(["source identity", "semantic contracts",
                    "design mappings", "verification evidence",
                    "required gates", "dependency status", "epoch"], 3)
            + [marks([(9, VERT)]), marks([(9, DOWN)]),
               " " * 5 + "Certificate"])
D["N29"] = one("artifact.metadata.certified = true")

# ================================================================ §838
SL, SW = 20, 14                  # box left edge, inner width
SS = SL + 7                      # ┬ / spine = 27
FL, FR = SS - 2, SS + 2          # fork branches 25 / 29


def sbox(label_row):
    return [" " * SL + CORNER_TL + DASH * SW + CORNER_TR,
            " " * SL + VERT + label_row + VERT,
            " " * SL + CORNER_BL + DASH * (SS - SL - 1) + TEE_D
            + DASH * (SL + SW - SS) + CORNER_BR]


D["N30"] = []
for _lab, _op in [("    CREATED   ", "Admit"), ("   ADMITTED   ", "Authorize"),
                  (" AUTHORIZED   ", "Execute"), ("  EXECUTING   ", None)]:
    assert len(_lab) == SW, _lab
    D["N30"] += sbox(_lab)
    if _op:
        D["N30"] += [marks([(SS, VERT)]) + " " + _op, marks([(SS, DOWN)])]
D["N30"] += [
    " " * FL + CORNER_TL + DASH + TEE_U + DASH + CORNER_TR,
    " " * SL + "fail " + VERT + "   " + VERT + " complete",
    marks([(FL, DOWN), (FR, DOWN)]),
    " " * SL + "FAILED  SUCCEEDED",
]
for _op, _lab in [("Verify", "VERIFIED"), ("Gate", "GATED"),
                  ("Certify", "CERTIFIED")]:
    D["N30"] += [marks([(FR, VERT)]), marks([(FR, VERT)]) + " " + _op,
                 marks([(FR, DOWN)]), row([(_lab, FR)])]

# ================================================================ §839
D["N31"] = rule("Certified", IMPL, "Linux upstream accepts patch")
D["N32"] = rule("Certified", IMPL,
                "RFL-AE technical certification conditions satisfied")
D["N33"] = rule("UpstreamAcceptanceState", "=", "separate governance state")

# ================================================================ §840
D["N34"] = rule("\u00acAuthorized(request)", IMPL, "\u00acExecuting(request)")
D["N35"] = rule("request.epoch != state.epoch", IMPL, "Reject(EpochMismatch)")
D["N36"] = rule("target \u2209 authorization.scope", IMPL,
                "Reject(ScopeViolation)")
D["N37"] = rule("Evidence(subject)", IMPL, "corresponding execution exists")
D["N38"] = rule("Certified(task)", IMPL, "Verified(task)")
D["N39"] = rule("required_gate == Blocked", IMPL, "\u00acCertified")
D["N40"] = rule("replay(ledger)", "==", "authoritative_state")
D["N41"] = rule("committed_event", IMPL, "cannot be replaced by later event")

# ================================================================ §841
D["N42"] = bchain(["Transition", "Event", "Hash-chain validation",
                   "Append-only ledger", "Replay", "State reconstruction"],
                  c=5)
D["N43"] = dchain(["rfl-types", "rfl-transition", "rfl-ledger",
                   "rfl-evidence", "rfl-gates"], c=6)

# ================================================================ §842
TW = 41
TS = 1 + TW // 2                 # 21 = centre of a 43-wide box


def tbox(lines):
    return ([CORNER_TL + DASH * TW + CORNER_TR]
            + [VERT + (" " + l).ljust(TW) + VERT for l in lines]
            + [CORNER_BL + DASH * TW + CORNER_BR])


D["N44"] = ([row([("RFL-AE TCB", TS)]), ""]
            + tbox(["Canonical types", "Identity / digest semantics",
                    "Epoch semantics", "Authorization predicates",
                    "Scope predicates", "Transition relation",
                    "Event integrity", "Replay semantics", "Evidence binding",
                    "Gate algebra"])
            + [marks([(TS, UP)]), marks([(TS, VERT)]),
               row([("everything else is subordinate", TS)]),
               marks([(TS, VERT)])]
            + tbox(["LLMs", "Semantic analyzers", "Code generators",
                    "Planners", "Review agents", "Build systems",
                    "Test systems", "External tools"]))

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
