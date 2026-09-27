#!/usr/bin/env python3
"""Regenerate every ASCII diagram in KSIR-SLICE.md by column arithmetic.

    python3 diagrams/KSIR-SLICE.py [outdir]     # default /tmp/ksir2diag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py KSIR-SLICE.md <outdir>

The diagrams in KSIR-SLICE.md are NOT verbatim transcriptions: the pasted
source had all of its ASCII art collapsed onto single lines, so each diagram
was re-derived. This script is the record of that derivation -- re-running it
and diffing against the committed document proves the diagrams still match.

Nothing here is hand-typed ASCII. Every glyph position comes from geo.py
arithmetic or from an explicit column constant derived structurally (fork
spans, shared spine columns), never from counting runs of spaces by eye.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/ksir2diag")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import (VERT, DOWN, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
                 TEE_D, TEE_U, HORIZ, row, marks, bar, dchain)  # noqa: E402

D = {}
BR, TR = "\u2514", "\u251c"      # └ ├
ARROW = "\u2192"                 # →


def chain(items, c=2, g="\u2193"):
    return dchain(items, c=c, g=g)


def chain_iv(items, c=2):
    out = [items[0]]
    for it in items[1:]:
        out += [marks([(c, VERT)]), marks([(c, DOWN)]), it]
    return out


def ntree(node, prefix=""):
    """Nested tree. node = (label, [children]); a child may be a bare str."""
    label, kids = node
    out = [prefix + label]
    for i, k in enumerate(kids):
        last = i == len(kids) - 1
        conn = BR if last else TR
        if isinstance(k, str):
            out.append(prefix + conn + HORIZ * 2 + " " + k)
        else:
            out.append(prefix + conn + HORIZ * 2 + " " + k[0])
            out += ntree(("", k[1]),
                         prefix + (" " * 4 if last else VERT + "   "))[1:]
    return out


def groups(items, indent=4):
    """`name` followed by indented lines; groups run together with no blanks."""
    out = []
    for name, lines in items:
        out.append(name)
        out += [" " * indent + l for l in lines]
    return out


def arrows(items, c=1):
    """Chain where each continuation is prefixed by `→` at column c."""
    return [items[0]] + [" " * c + ARROW + " " + it for it in items[1:]]


# ---------------------------------------------------------------- G01
D["G01"] = chain(["rfl-types", "rfl-ksir", "rfl-analysis-types",
                  "rfl-analysis-compiler", "lab001", "KSIR artifact"], c=3)

# ---------------------------------------------------------------- G02
D["G02"] = ntree(("RFL-AE/", [
    ("crates/", ["rfl-types/", "rfl-ksir/", "rfl-analysis-types/",
                 "rfl-analysis-compiler/"]),
    ("fixtures/", [("lab001/", [
        ("include/", ["lab_object.h"]),
        ("c/", ["lab_object.c"]),
        ("expected/", ["structural-ksir.json"]),
        "negative/"])]),
    ("tests/", [("ksir/", ["deterministic.rs", "provenance.rs", "unknown.rs",
                           "conflict.rs", "snapshot.rs"])]),
]))

# ---------------------------------------------------------------- G03
D["G03"] = [
    "rfl-types",
    "    = universal identity / digest / snapshot primitives",
    "rfl-ksir",
    "    = semantic representation",
    "rfl-analysis-types",
    "    = observations produced by analyzers",
    "rfl-analysis-compiler",
    "    = one concrete observation producer",
]

# ---------------------------------------------------------------- G04-G07
D["G04"] = ['"lab_object"']
D["G05"] = ["sha256:...", "sha3-256:...", "blake3:..."]
D["G06"] = ["Linux 6.x"]
D["G07"] = ["same version label \u2260 same source tree"]

# ---------------------------------------------------------------- G08-G09
D["G08"] = ["snapshot = fixture tree digest",
            "architecture = host architecture",
            "config = fixture configuration digest",
            "toolchain = exact compiler identity"]
D["G09"] = [f"Variant A {ARROW} x86_64 + CONFIG_X=y",
            f"Variant B {ARROW} arm64 + CONFIG_X=n"]

# ---------------------------------------------------------------- G10-G11
D["G10"] = ["field.value = protected"]
D["G11"] = ["from where?", "using which backend?", "against which snapshot?",
            "from which execution?"]

# ---------------------------------------------------------------- G12-G13
D["G12"] = ["Ownership = RefCounted", "Aliasing  = MutableShared",
            "Lifetime  = Unknown"]
D["G13"] = ["Arc<T>"]

# ---------------------------------------------------------------- G14-G15
D["G14"] = chain(["ALLOCATED", "INITIALIZED", "PUBLISHED", "REFERENCED",
                  "QUIESCING", "RECLAIMABLE", "FREED"], c=4)
D["G15"] = chain(["lab_object.lock", "SpinLock", "protects",
                  "lab_object.value"], c=4)

# ---------------------------------------------------------------- G16
D["G16"] = ["0 observations", " " * 4 + ARROW + " InsufficientEvidence",
            "1 observation", " " * 4 + ARROW + " resolved provisional fact",
            "N identical observations", " " * 4 + ARROW + " Consistent",
            "N different observations", " " * 4 + ARROW + " Conflicted"]

# ---------------------------------------------------------------- G17-G19
# The source labels the first edge: `│ authorized execution` beside the spine.
_d = ["Protocol", marks([(3, VERT)]),
      marks([(3, VERT)]) + " authorized execution", marks([(3, DOWN)])]
for _t in ["Execution Runtime", "Compiler Backend", "ObservationBundle",
           "KSIR Reconciler"]:
    _d.append(_t)
    if _t != "KSIR Reconciler":
        _d += [marks([(3, VERT)]), marks([(3, DOWN)])]
D["G17"] = _d
D["G18"] = ["state.migration = Verified"]
D["G19"] = ["observations", "unknowns", "execution references", "artifacts"]

# ---------------------------------------------------------------- G20-G21
D["G20"] = ["A001 declarations", "A002 definitions", "A003 function calls",
            "A004 struct fields", "A005 basic field accesses",
            "A006 function-pointer/callback registration markers",
            "A007 compiler-visible layout"]

D["G21"] = groups([
    ("SUPPORTED:", ["ordinary structs", "ordinary functions", "direct calls",
                    "field declarations", "basic field accesses"]),
    ("PARTIALLY_SUPPORTED:", ["macros", "callbacks",
                              "typedef-heavy constructs"]),
    ("OPAQUE:", ["complex generated constructs", "inline assembly"]),
    ("UNKNOWN:", ["unresolved indirect calls", "unresolved ownership",
                  "unresolved lifetime"]),
])

# ---------------------------------------------------------------- G22-G24
D["G23"] = ["schedule_work()"]
D["G24"] = groups([("Ownership:", ["UNKNOWN"]), ("Lifetime:", ["UNKNOWN"]),
                   ("Callback lifetime:", ["UNKNOWN"]),
                   ("Severity:", ["CRITICAL"]), ("Migration:", ["BLOCKED"])])

# ---------------------------------------------------------------- G25-G27
D["G25"] = chain(["KSIR", "canonical serialization", "SHA-256",
                  "ksir_digest"], c=1)
D["G26"] = ["snapshot", "variant", "inputs", "tool identities",
            "algorithm revisions"]
D["G27"] = ["fresh process", "fresh filesystem", "fresh analyzer invocation",
            "same inputs", " " * 8 + "\u2193", "same semantic artifact",
            "same digest"]

# ---------------------------------------------------------------- G28-G34
D["G28"] = chain(["Snapshot A", "Observation A", "KSIR A", "Contract A"], c=1)
D["G29"] = ["Snapshot B"]
D["G30"] = ["KSIR-A = SUPERSEDED", "Contract-A = STALE", "Design-A = STALE",
            "Verification-A = STALE",
            "Certificate-A = INVALIDATED / SUPERSEDED"]
D["G31"] = ["KSIR-GATE-001"]
D["G32"] = ["1. snapshot bound", "2. variant bound",
            "3. execution receipt bound", "4. every fact has provenance",
            "5. unsupported constructs preserved", "6. conflicts explicit",
            "7. critical unknowns explicit", "8. deterministic serialization",
            "9. analyzer failure cannot produce VERIFIED",
            "10. stale snapshot cannot produce current KSIR"]
D["G33"] = ["PASS", "FAIL", "BLOCKED"]
D["G34"] = ["87% semantic confidence"]

# ---------------------------------------------------------------- G35
# The trust pipeline. Top spine 17; fork1 (4 dashes/side) to 12 and 22;
# Reconcile (col 12) then forks with 5 dashes/side to 6 and 18.
S = 17
L1, R1 = S - 5, S + 5
L2, R2 = L1 - 6, L1 + 6
d = []
for t in ("TRUSTED", "Snapshot / Variant", "Authorized Execution",
          "Observation"):
    d.append(row([(t, S)]))
    d.append(marks([(S, VERT)]))
    d.append(marks([(S, DOWN)]))
d.pop()                                    # drop the DOWN: the fork follows
d.append(bar([(L1, CORNER_TL), (S, TEE_U), (R1, CORNER_TR)]))
d.append(marks([(L1, DOWN), (R1, DOWN)]))
d.append(row([("Evidence", L1), ("Unknown", R1)]))
d.append(marks([(L1, VERT), (R1, VERT)]))
d.append(marks([(L1, DOWN), (R1, DOWN)]))
d.append(row([("Reconcile", L1), ("Blocker", R1)]))
d.append(marks([(L1, VERT)]))
d.append(bar([(L2, CORNER_TL), (L1, TEE_U), (R2, CORNER_TR)]))
d.append(marks([(L2, DOWN), (R2, DOWN)]))
d.append(row([("Semantic", L2), ("Conflict", R2)]))
d.append(row([("Fact", L2)]))
d.append(marks([(L2, VERT)]))
d.append(marks([(L2, DOWN)]))
d.append(row([("KSIR", L2)]))
D["G35"] = d

# ---------------------------------------------------------------- G36
D["G36"] = arrows(["fixture", "BuildManifest",
                   "authorized compiler execution", "ExecutionReceipt",
                   "ObservationBundle", "reconciliation", "KSIR",
                   "deterministic digest", "KSIR-GATE-001"], c=1)

# ---------------------------------------------------------------- G37
D["G37"] = [
    '{',
    '  "observation_id": "...",',
    '  "snapshot": "...",',
    '  "variant": "...",',
    '  "subject": "...",',
    '  "fact_kind": "FunctionCall",',
    '  "value": {',
    '    "caller": "lab_schedule",',
    '    "target": "schedule_work"',
    '  },',
    '  "backend": {',
    '    "name": "compiler-frontend",',
    '    "version": "...",',
    '    "algorithm_revision": "..."',
    '  },',
    '  "epistemic": "Observed",',
    '  "execution_receipt": "...",',
    '  "digest": "sha256:..."',
    '}',
]

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
