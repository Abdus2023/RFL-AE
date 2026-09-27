#!/usr/bin/env python3
"""Regenerate every ASCII diagram in KSIR-ANALYZER.md by column arithmetic.

    python3 diagrams/KSIR-ANALYZER.py [outdir]     # default /tmp/ksir3diag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py KSIR-ANALYZER.md <outdir>

The diagrams in KSIR-ANALYZER.md are NOT verbatim transcriptions: the pasted
source had its ASCII art collapsed onto single lines, so each diagram was
re-derived. This script is the record of that derivation -- re-running it and
diffing against the committed document proves the diagrams still match.

Two diagrams arrived already laid out (the §1 analyzer-boundary boxes and the
§19 gate flow). The gate flow is structurally consistent and is reproduced
unchanged. The analyzer-boundary boxes had one interior row one column short
of the other nine, which trips the corpus's box-width rule, so the box is
re-emitted here with the padding computed rather than typed.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/ksir3diag")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import (VERT, DOWN, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
                 TEE_D, TEE_U, HORIZ, cen, row, marks, bar, dchain)  # noqa: E402

D = {}
BR, TR = "\u2514", "\u251c"      # └ ├
DASH = HORIZ                     # ─
NEQ = "\u2260"                   # ≠
ARROW = "\u2192"                 # →
DOWNARROW = "\u2193"             # ↓


def chain(items, c=1, g="\u2193"):
    return dchain(items, c=c, g=g)


def chain_iv(items, c=2):
    out = [items[0]]
    for it in items[1:]:
        out += [marks([(c, VERT)]), marks([(c, DOWN)]), it]
    return out


def ntree(node, prefix="", arrow=False):
    """Nested tree. node = (label, [children]); a child may be a bare str."""
    label, kids = node
    out = [prefix + label]
    for i, k in enumerate(kids):
        last = i == len(kids) - 1
        conn = BR if last else TR
        if isinstance(k, str):
            out.append(prefix + conn + DASH * 2 + " " + k)
        else:
            out.append(prefix + conn + DASH * 2 + " " + k[0])
            out += ntree(("", k[1]),
                         prefix + (" " * 4 if last else VERT + "   "))[1:]
    return out


def groups(items, indent=4):
    out = []
    for name, lines in items:
        out.append(name)
        out += [" " * indent + l for l in lines]
    return out


def box(width, interior):
    """Box with an explicit display width; interior rows are padded."""
    out = [CORNER_TL + DASH * (width - 2) + CORNER_TR]
    for t in interior:
        out.append(VERT + t.ljust(width - 2) + VERT)
    return out


def boxbottom(width, tee_col):
    """Bottom border carrying a ┬ at tee_col."""
    return (CORNER_BL + DASH * tee_col + TEE_D
            + DASH * (width - 3 - tee_col) + CORNER_BR)


# ---------------------------------------------------------------- H01
# Two boxes on a shared spine at column 29. Re-emitted because the source's
# `authorization / snapshot / scope / capability / epoch` row was 62 columns
# where the other nine box rows are 63.
W, SP = 63, 29
TEE = SP - 1          # boxbottom puts TEE_D at tee_col+1, so this lands on SP
h = []
h += box(W, [" " * 20 + "RFL-AE Protocol" + " " * 26,
             "",
             " authorization / snapshot / scope / capability / epoch"])
h.append(boxbottom(W, TEE))
h.append(marks([(SP, VERT)]))
h.append(marks([(SP, DOWN)]))
h.append(row([("Execution Runtime", SP)]))
h.append(marks([(SP, VERT)]))
h.append(row([("exact command + receipt", SP)]))
h.append(marks([(SP, VERT)]))
h.append(marks([(SP, DOWN)]))
h += box(W, [" " * 17 + "rfl-analysis-compiler" + " " * 23,
             "",
             " source " + ARROW + " compiler frontend " + ARROW
             + " normalized observations"])
h.append(boxbottom(W, TEE))
h.append(marks([(SP, VERT)]))
h.append(marks([(SP, DOWN)]))
h.append(row([("ObservationBundle", SP)]))
h.append(marks([(SP, VERT)]))
h.append(marks([(SP, DOWN)]))
h.append(row([("Reconciliation", SP)]))
h.append(marks([(SP, VERT)]))
h.append(marks([(SP, DOWN)]))
h.append(row([("KSIR v0.1", SP)]))
D["H01"] = h

# ---------------------------------------------------------------- H02-H03
D["H02"] = chain(["KSIR fact", "Observation", "AnalysisArtifact",
                  "ExecutionReceipt"], c=1)
D["H03"] = chain(["KSIR fact", '"compiler said so"'], c=1)

# ---------------------------------------------------------------- H04-H05
D["H04"] = chain_iv(["clang / GCC / sparse / ...", "CompilerObservation",
                     "NormalizedObservation", "KSIR"], c=9)
D["H05"] = ["compiler-frontend", "version: X.Y.Z", "executable: sha256:...",
            "schema: compiler-observation/0.1", "algorithm: clang-structural-v1"]

# ---------------------------------------------------------------- H06-H08
D["H06"] = ntree(("BuildManifest", ["source tree", "generated headers",
                                    "compiler", "flags", "include paths",
                                    "environment"]))
D["H06"] += [marks([(14, VERT)]), marks([(14, DOWN)]),
             row([("CommandSpec", 8)])]
D["H07"] = ["cc -I fixtures/lab001/include -c fixtures/lab001/c/lab_object.c"
            " -o ..."]
D["H08"] = ['"compiled successfully"']

# ---------------------------------------------------------------- H09-H11
D["H10"] = ["lab_alloc", "lab_get", "lab_put", "lab_update", "lab_schedule",
            "lab_work"]
D["H11"] = ntree(("fixtures/lab001/include/",
                  [("linux/", ["refcount.h", "spinlock.h", "workqueue.h"]),
                   "lab_object.h"]))

# ---------------------------------------------------------------- H12
# The expected structural graph. Blocks are kept at column 0 with sub-items at
# column 4; the source's inter-block spacing was ambiguous.
D["H12"] = (
    ntree(("STRUCT lab_object", ["refs : refcount_t", "lock : spinlock_t",
                                 "value : int", "work : work_struct"]))
    + [""] + [f"FUNCTION {n}" for n in D["H10"]] + ["", "CALL GRAPH"]
    + ["lab_alloc", " " * 4 + BR + DASH * 2 + " allocation",
       "lab_get", " " * 4 + BR + DASH * 2 + " refcount_inc",
       "lab_put", " " * 4 + TR + DASH * 2 + " refcount_dec",
       " " * 4 + BR + DASH * 2 + " lab_free",
       "lab_update", " " * 4 + TR + DASH * 2 + " spin_lock",
       " " * 4 + TR + DASH * 2 + " value WRITE",
       " " * 4 + BR + DASH * 2 + " spin_unlock",
       "lab_schedule", " " * 4 + TR + DASH * 2 + " refcount_inc",
       " " * 4 + BR + DASH * 2 + " schedule_work",
       "lab_work", " " * 4 + TR + DASH * 2 + " container_of",
       " " * 4 + TR + DASH * 2 + " value ACCESS",
       " " * 4 + BR + DASH * 2 + " refcount_dec"])

# ---------------------------------------------------------------- H13-H16
D["H13"] = ["OBSERVED", " " * 4 + f"lab_schedule {ARROW} schedule_work"]
D["H14"] = ["DERIVED",
            " " * 4 + "lab_schedule establishes callback reachability"]
D["H15"] = ["UNKNOWN", " " * 4 + "callback lifetime guarantee"]
D["H16"] = chain(["source observation", "semantic derivation",
                  "remaining uncertainty"], c=1)

# ---------------------------------------------------------------- H17-H22
D["H17"] = [f"A {ARROW} B"]
D["H18"] = ["B has effect E"]
D["H19"] = ["A has effect E"]
D["H20"] = ["OBS-001:", " " * 4 + "lab_update calls spin_lock",
            "OBS-002:", " " * 4 + "spin_lock acquires SpinLock",
            "DER-001:", " " * 4 + "lab_update acquires SpinLock"]
D["H21"] = ["CALL-EFFECT-PROPAGATION-001"]
D["H22"] = ["CALL-EFFECT-PROPAGATION-002"]

# ---------------------------------------------------------------- H23-H29
D["H23"] = ["schedule_work(&obj->work)", ARROW, "callback registration"]
D["H24"] = ["callback = lab_work", "registration = lab_schedule",
            "dispatcher = UNKNOWN"]
D["H25"] = chain(["schedule_work", "callback registration", "lab_work"], c=1)
D["H26"] = [f"schedule_work {ARROW} WORKQUEUE"]
D["H27"] = ["lab_work:", " " * 4 + "reachable_context = WORKQUEUE"]
D["H28"] = ["callback registration + dispatcher context = callback context"]
D["H29"] = ["lab_work.context = UNKNOWN"]

# ---------------------------------------------------------------- H30-H33
D["H30"] = [f"refcount_inc(obj)", " " * 4 + ARROW
            + " evidence of reference acquisition"]
D["H31"] = [f"refcount_dec(obj)", " " * 4 + ARROW
            + " evidence of reference release"]
D["H32"] = [f"refcount_inc {ARROW} ownership"]
D["H33"] = ntree(("RefcountFact", ["counter", "acquire operations",
                                   "release operations", "zero transition",
                                   "destruction relation"]))

# ---------------------------------------------------------------- H34-H38
D["H34"] = ["schedule_work(obj)"]
D["H35"] = ["put(obj)"]
D["H36"] = ["Does callback registration itself retain obj?"]
D["H37"] = ["UNKNOWN:", " " * 4 + "callback lifetime"]
D["H38"] = ["Migration blocked:",
            " " * 4 + "callback lifetime is unresolved."]

# ---------------------------------------------------------------- H39
D["H39"] = [
    '{',
    '  "schema": "rfl-ksir/0.1",',
    '  "snapshot": "sha256:...",',
    '  "variant": "variant:...",',
    '  "functions": [',
    '    "lab_alloc",',
    '    "lab_get",',
    '    "lab_put",',
    '    "lab_update",',
    '    "lab_schedule",',
    '    "lab_work"',
    '  ],',
    '  "objects": [',
    '    "lab_object"',
    '  ],',
    '  "calls": [',
    '    ["lab_get", "refcount_inc"],',
    '    ["lab_put", "refcount_dec"],',
    '    ["lab_update", "spin_lock"],',
    '    ["lab_update", "spin_unlock"],',
    '    ["lab_schedule", "schedule_work"]',
    '  ],',
    '  "callbacks": [',
    '    {',
    '      "registration": "lab_schedule",',
    '      "callback": "lab_work",',
    '      "dispatcher": "UNKNOWN"',
    '    }',
    '  ],',
    '  "unknowns": [',
    '    {',
    '      "domain": "CallbackReachability",',
    '      "reason": "ExternalDefinitionUnavailable"',
    '    }',
    '  ]',
    '}',
]

# ---------------------------------------------------------------- H40-H45
D["H40"] = ["KSIR = empty", "status = VERIFIED"]
D["H41"] = ["AnalysisStatus:", " " * 4 + "FAILED",
            "KSIR:", " " * 4 + "unavailable / partial",
            "Evidence:", " " * 4 + "execution receipt exists",
            "Verification:", " " * 4 + "BLOCKED"]
D["H42"] = [f"execution failure {NEQ} semantic false {NEQ} verification failure"]
D["H43"] = ["backend-A:", " " * 4 + "sizeof(lab_object) = 32",
            "backend-B:", " " * 4 + "sizeof(lab_object) = 40"]
D["H44"] = ["CONFLICT"]
D["H45"] = ["critical conflict = true", "KSIR gate = BLOCKED"]

# ---------------------------------------------------------------- H46-H49
D["H46"] = ["Request:", " " * 4 + "snapshot A",
            "Execution:", " " * 4 + "source tree B"]
D["H47"] = ["SnapshotMismatch"]
D["H48"] = ["Request:", " " * 4 + "Variant A",
            "Compiler execution:", " " * 4 + "Variant B"]
D["H49"] = ["VariantMismatch"]

# ---------------------------------------------------------------- H50
# Reproduced unchanged: spine 22, fork `/ \` at 15/25, branch spines 13/28,
# then a second spine at 13 forking to 8/18.
D["H50"] = [
    row([("MU-000001", 17)]),
    marks([(22, VERT)]), marks([(22, DOWN)]),
    row([("protocol authorization", 14)]),
    marks([(22, VERT)]), marks([(22, DOWN)]),
    row([("BuildManifest", 15)]),
    marks([(22, VERT)]), marks([(22, DOWN)]),
    row([("compiler execution", 13)]),
    marks([(22, VERT)]), marks([(22, DOWN)]),
    row([("receipt R-001", 15)]),
    marks([(22, VERT)]), marks([(22, DOWN)]),
    row([("observations O-*", 13)]),
    marks([(22, VERT)]), marks([(22, DOWN)]),
    row([("reconciler", 15)]),
    row([("/", 15), ("\\", 25)]),
    row([("resolved", 10), ("conflict", 25)]),
    marks([(13, VERT), (28, VERT)]),
    marks([(13, DOWN), (28, DOWN)]),
    row([("KSIR", 11), ("quarantine", 26)]),
    marks([(13, VERT)]), marks([(13, DOWN)]),
    row([("KSIR-GATE-001", 8)]),
    marks([(13, VERT)]),
    bar([(8, CORNER_TL), (13, TEE_U), (18, CORNER_TR)]),
    marks([(8, DOWN), (18, DOWN)]),
    row([("PASS", 6), ("BLOCKED", 16)]),
]

# ---------------------------------------------------------------- H51-H53
D["H51"] = ntree(("KSIR", ["refcount observations", "lock observations",
                           "callback observations", "field accesses",
                           "lifetime unknown"]))
D["H51"] += [marks([(10, VERT)]), marks([(10, DOWN)]), row([("Contract", 6)])]
D["H52"] = [
    "C001: object must be initialized before publication",
    "C002: value mutation requires the established lock",
    "C003: reference acquisition must precede asynchronous use",
    "C004: final reference release permits destruction",
    "C005: callback must not access object after destruction",
    "C006: callback execution context must satisfy its operations",
]
D["H53"] = ["C005 = BLOCKED"]

# ---------------------------------------------------------------- H54
_now = ["rfl-analysis-types", "compiler backend", "normalized observations",
        "structural reconciler", "KSIR serializer", "KSIR-GATE-001"]
# the source interleaves a spine row between every item of this first block
_d = ["NOW", marks([(1, VERT)])]
for _i, _it in enumerate(_now):
    _d.append((" " + BR if _i == len(_now) - 1 else " " + TR)
              + DASH * 2 + " " + _it)
    if _i != len(_now) - 1:
        _d.append(marks([(1, VERT)]))
for _tail, _kids in (("THEN", ["context propagation", "effect propagation",
                               "callback graph", "refcount analysis",
                               "lifetime reconstruction",
                               "lock/access analysis"]),
                     ("THEN", ["Contract IR generation", "obligations",
                               "first Rust Design IR"])):
    _d += [marks([(8, VERT)]), marks([(8, DOWN)]), _tail, marks([(1, VERT)])]
    for _i, _it in enumerate(_kids):
        _d.append((" " + BR if _i == len(_kids) - 1 else " " + TR)
                  + DASH * 2 + " " + _it)
_d += [marks([(8, VERT)]), marks([(8, DOWN)]), "MU-000001",
       marks([(8, VERT)]), marks([(8, DOWN)]),
       f"full evidence {ARROW} verification {ARROW} gate {ARROW} certificate"]
D["H54"] = _d

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
