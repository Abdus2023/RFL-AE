#!/usr/bin/env python3
"""Regenerate every ASCII diagram in RFL-TYPES.md.

    python3 diagrams/RFL-TYPES.py [outdir]    # default /tmp/rtdiag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py RFL-TYPES.md <outdir>

The diagrams in RFL-TYPES.md are NOT verbatim transcriptions: the pasted
source had all of its art collapsed onto single lines, so each diagram was
re-derived. This script is the record of that derivation -- re-running it and
diffing against the committed document proves the diagrams still match.

Glyph note. Diagrams that arrive in the source as box-drawing art stay
box-drawing (the crate tree, the SourceSet / MigrationUnit trees, the attempt
tree, the hash chain and the kernel diagram); the dependency-direction diagram
arrives as ASCII `/ | \\` with `↓` heads and stays that way. `↓` chains stay
`↓`. No block mixes an ASCII `|` with box glyphs.

Normalisations (all geometric, no content change):
  * §804 dependency direction: the source's lower half was offset one column
    right of its upper half (spine 22 vs 21); both halves now mirror each
    other about column 21. The label row keeps the source's own columns.
  * §821 kernel: the spine drifted (16 above the box, 17 below) while the
    box's ┬ is at column 18; every spine and label now sits on column 18.
  * §822 transition matrix: the two lower labels were not centred on the ↓
    at column 20; both now are.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/rtdiag")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import (VERT, DOWN, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
                 TEE_D, HORIZ, row, marks)  # noqa: E402

D = {}
BR, TR = "\u2514", "\u251c"      # └ ├
DASH = HORIZ                     # ─
DWN = "\u2193"                   # ↓
NEQ = "\u2260"                   # ≠


def one(s):
    return [s]


def dchain(items, c):
    out = [items[0]]
    for it in items[1:]:
        out += [" " * c + DWN, it]
    return out


def pairs(items, indent=4, blank=True):
    """`Label:` / indented value groups, separated by blank lines."""
    out = []
    for i, (head, val) in enumerate(items):
        if i and blank:
            out.append("")
        out += [head, " " * indent + val]
    return out


# ================================================================ §804
_src = ["lib.rs", "ids.rs", "digest.rs", "epoch.rs", "status.rs", "task.rs",
        "authorization.rs", "operation.rs", "artifact.rs", "evidence.rs",
        "contract.rs", "gate.rs", "error.rs"]
# Reproduced as in the source, including `├──` on `rfl-types/` even though it
# is the only child of `crates/`.
D["M01"] = (["crates/",
             TR + DASH * 2 + " rfl-types/",
             VERT + "   " + TR + DASH * 2 + " Cargo.toml",
             VERT + "   " + BR + DASH * 2 + " src/"]
            + [VERT + "       " + (BR if i == len(_src) - 1 else TR)
               + DASH * 2 + " " + f for i, f in enumerate(_src)])

S = 21
D["M02"] = [
    row([("rfl-types", S)]),
    marks([(S - 5, "/"), (S, "|"), (S + 5, "\\")]),
    marks([(S - 6, "/"), (S, "|"), (S + 6, "\\")]),
    marks([(S - 7, DWN), (S, DWN), (S + 7, DWN)]),
    # label row at the source's own columns (5 / 20 / 28)
    " " * 5 + "rfl-transition" + "  " + "ledger" + "  " + "evidence",
    marks([(S - 7, "\\"), (S, "|"), (S + 7, "/")]),
    marks([(S - 6, "\\"), (S, "|"), (S + 6, "/")]),
    row([("gates", S)]),
]

# ================================================================ §806
D["M03"] = one("sha256:<64 lowercase hexadecimal characters>")
D["M04"] = one("sha256:0123456789abcdef...")
D["M05"] = ["Digest equality", " " * 4 + "= same algorithm AND same digest bytes"]

# ================================================================ §807
D["M06"] = ["Epoch(a) " + NEQ + " Epoch(b)", " " * 8 + DWN,
            "state/evidence/authorization cannot silently cross the boundary"]
D["M07"] = dchain(["Analyze C at snapshot A", "C changes",
                   "Generate Rust against snapshot B",
                   "reuse analysis from A", "false certification"], c=8)

# ================================================================ §808
D["M08"] = one("FAIL " + NEQ + " BLOCKED")

# ================================================================ §809
D["M09"] = pairs([("Evidence:", "Observed"), ("Verification:", "Verified"),
                  ("Gate:", "Pass")])
D["M10"] = pairs([("Evidence:", "Hypothesis"), ("Verification:", "Verified")])

# ================================================================ §810
D["M11"] = one('"run arbitrary shell command"')
D["M12"] = ["OperationKind"] + [" " * 4 + "+ " + s for s in (
    "typed Target", "Scope", "Authorization", "Epoch")]

# ================================================================ §811
D["M13"] = pairs([
    ("Capability", "= what this actor/system is capable of doing"),
    ("Authorization", "= this actor may perform this operation for this task"
                      " in this scope during this epoch")])

# ================================================================ §813
D["M14"] = ["SourceSet"] + [
    " " + (BR if i == 4 else TR) + DASH * 2 + " " + s for i, s in enumerate(
        ["repository identity", "commit/object identity", "source paths",
         "source regions", "configuration scope"])]
_mu = ["source identity", "semantic model", "contracts", "Rust design",
       "artifact"]
D["M15"] = ["MigrationUnit"]
for _i, _s in enumerate(_mu):
    D["M15"] += [" " * 7 + VERT,
                 " " * 7 + (BR if _i == len(_mu) - 1 else TR) + DASH * 2
                 + " " + _s]

# ================================================================ §814
D["M16"] = ["Maybe", "Probably", "Best effort", "LLM says okay",
            "Confidence = 0.97"]

# ================================================================ §815
D["M17"] = dchain(["Executing", "Failed", "Executing"], c=3)
_att = [("Attempt #1", "Failed"), ("Attempt #2", "Executing"),
        ("Attempt #3", "Succeeded")]
D["M18"] = ["Task"]
for _i, (_a, _st) in enumerate(_att):
    _last = _i == len(_att) - 1
    D["M18"] += [" " + VERT,
                 " " + (BR if _last else TR) + DASH * 2 + " " + _a,
                 " " + (" " if _last else VERT) + " " * 6 + BR + DASH * 2
                 + " " + _st]

# ================================================================ §816
D["M19"] = ["E0", " " + VERT, " " + VERT + " hash(E0)", " " + DWN,
            "E1", " " + VERT, " " + VERT + " hash(E1 + previous_event)",
            " " + DWN, "E2", " " + VERT, " " + DWN, "E3"]

# ================================================================ §817
D["M20"] = ["replay(authoritative_ledger)", " " * 8 + "== authoritative_state"]
D["M21"] = one('"we logged what happened"')
D["M22"] = ["E17.resulting_state", "E17.event_digest", "E18.previous_event",
            "E18.sequence"]

# ================================================================ §818
D["M23"] = ["Agent:", " " * 4 + '"I verified it."', "", " " * 8 + NEQ, "",
            "Execution infrastructure:",
            " " * 4 + '"This exact artifact was built/tested',
            " " * 5 + "under this exact environment,",
            " " * 5 + 'producing this exact result."']

# ================================================================ §819
D["M24"] = one("Generator " + NEQ + " sole verifier")
D["M25"] = dchain(["Agent A", "generates Rust", "Agent A",
                   "claims verification"], c=2)

# ================================================================ §821
D["M26"] = dchain(["rfl-types", "rfl-transition", "rfl-ledger",
                   "rfl-evidence", "rfl-gates"], c=4)

KL, KW = 8, 19            # box left edge, inner width -> ┬ at KL + 10 = 18
KS = KL + 1 + KW // 2
D["M27"] = [
    row([("UNTRUSTED AGENTS", KS)]),
    marks([(KS, VERT)]),
    marks([(KS, VERT)]) + " typed request",
    marks([(KS, DOWN)]),
    " " * KL + CORNER_TL + DASH * KW + CORNER_TR,
    " " * KL + VERT + "RFL-AE KERNEL".center(KW) + VERT,
    " " * KL + VERT + " " * KW + VERT,
] + [" " * KL + VERT + (" " + s).ljust(KW) + VERT for s in (
    "Types", "Epoch", "Authorization", "Transition", "Ledger", "Evidence",
    "Gates")] + [
    " " * KL + CORNER_BL + DASH * (KS - KL - 1) + TEE_D
    + DASH * (KL + KW - KS) + CORNER_BR,
]
for _lab in ("EXECUTION SYSTEM", "EVIDENCE", "CERTIFICATE"):
    D["M27"] += [marks([(KS, VERT)]), marks([(KS, DOWN)]), row([(_lab, KS)])]

D["M28"] = pairs([("LLM output", NEQ + " protocol state"),
                  ("LLM confidence", NEQ + " verification"),
                  ("test output", NEQ + " contract satisfaction"),
                  ("contract satisfaction", NEQ + " upstream acceptance")])

# ================================================================ §822
T = 20
D["M29"] = ["Current State \u00d7 Operation \u00d7 Preconditions",
            " " * T + DWN, row([("Accepted / Rejected", T)]),
            " " * T + DWN, row([("State + Event", T)])]

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
