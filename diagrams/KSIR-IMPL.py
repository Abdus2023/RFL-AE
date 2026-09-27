#!/usr/bin/env python3
"""Regenerate every ASCII diagram in KSIR-IMPL.md by column arithmetic.

    python3 diagrams/KSIR-IMPL.py [outdir]     # default /tmp/ksir1diag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py KSIR-IMPL.md <outdir>

The diagrams in KSIR-IMPL.md are NOT verbatim transcriptions: the pasted
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

OUT = os.environ.get("DIAGDIR", "/tmp/ksir1diag")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import (VERT, DOWN, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
                 TEE_D, TEE_U, HORIZ, cen, row, marks, bar, dchain)  # noqa: E402

D = {}
BR, TR = "\u2514", "\u251c"      # └ ├
ARR = "\u25ba"                   # ►


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


def groups(items):
    """`name` followed by 4-space-indented lines; groups run together."""
    out = []
    for name, lines in items:
        out.append(name)
        out += [" " * 4 + l for l in lines]
    return out


# ---------------------------------------------------------------- F01
# C fixture -> ObservationBundle -> Reconciliation -> KSIR -> UNKNOWN/CONTRACT
# Upper half: labels left-aligned at 0, spine at 8. Lower half: centred on 12.
S = 12
d = ["C fixture", marks([(3, VERT)])]
for i, k in enumerate(["compiler observations", "source observations",
                       "CFG / call graph", "execution receipts"]):
    d.append(marks([(3, BR if i == 3 else TR)]) + HORIZ * 2 + " " + k)
d.append(marks([(S, VERT)]))
d.append(marks([(S, DOWN)]))
d.append(row([("ObservationBundle", S)]))
d.append(marks([(S, VERT)]))
d.append(marks([(S, DOWN)]))
d.append(row([("Reconciliation", S)]))
L1, R1 = S - 5, S + 5
d.append(bar([(L1, CORNER_TL), (S, TEE_U), (R1, CORNER_TR)]))
d.append(marks([(L1, VERT), (R1, VERT)]))
d.append(row([("resolved", L1), ("conflict", R1)]))
d.append(marks([(L1, VERT), (R1, VERT)]))
d.append(bar([(L1, CORNER_BL), (S, TEE_D), (R1, CORNER_BR)]))
d.append(marks([(S, DOWN)]))
d.append(row([("KSIR", S)]))
d.append(marks([(S, VERT)]))
L2, R2 = S - 6, S + 6
d.append(bar([(L2, CORNER_TL), (S, TEE_U), (R2, CORNER_TR)]))
d.append(marks([(L2, DOWN), (R2, DOWN)]))
d.append(row([("UNKNOWN", L2), ("CONTRACT", R2)]))
d.append(marks([(L2, VERT)]))
d.append(bar([(L2, CORNER_BL), (S, ARR)]) + " blocking gates")
D["F01"] = d

# ---------------------------------------------------------------- F02
D["F02"] = ntree(("crates/", [
    ("rfl-types/", [("src/", ["ids.rs", "digest.rs", "snapshot.rs",
                              "variant.rs", "provenance.rs", "status.rs"])]),
    ("rfl-ksir/", [("src/", [
        "lib.rs", "symbol.rs", "function.rs", "object.rs", "pointer.rs",
        "ownership.rs", "lifetime.rs", "concurrency.rs", "context.rs",
        "effects.rs", "callback.rs", "refcount.rs", "abi.rs",
        "architecture.rs", "config.rs", "fact.rs", "unknown.rs",
        "conflict.rs", "graph.rs"])]),
]))

# ---------------------------------------------------------------- F03-F04
D["F03"] = ['{', '  "ownership": null', '}']
D["F04"] = ['{', '  "domain": "Ownership",', '  "reason": "IndirectCallUnresolved",',
            '  "severity": "Critical"', '}']

# ---------------------------------------------------------------- F05-F07
D["F05"] = chain_iv(["Analyzer", "AnalysisObservation", "ObservationBundle",
                     "Reconciler", "SemanticFact"], c=3)
D["F06"] = ["OBSERVED"]
D["F07"] = ["VERIFIED"]

# ---------------------------------------------------------------- F08-F09
D["F08"] = ["Build Manifest"]
D["F09"] = chain(["No BuildManifest",
                  "No authoritative compiler observation",
                  "No VERIFIED semantic claim"], c=8)

# ---------------------------------------------------------------- F10-F11
D["F10"] = chain(["source", "compiler frontend", "AST/type information",
                  "function declarations", "struct declarations",
                  "field layout", "calls"], c=1)

G = [("lab_object", ["refs", "lock", "value", "work"]),
     ("lab_get", ["refcount_inc"]),
     ("lab_put", ["refcount_dec", "lab_free"]),
     ("lab_update", ["spin_lock", "value =", "spin_unlock"]),
     ("lab_schedule", ["refcount_inc", "schedule_work"]),
     ("lab_work", ["container_of", "value =", "refcount_dec"])]
d = []
for name, kids in G:
    d.append(name)
    for i, k in enumerate(kids):
        d.append("  " + (BR if i == len(kids) - 1 else TR) + HORIZ * 2 + " " + k)
D["F11"] = d

# ---------------------------------------------------------------- F12
D["F12"] = chain(["EXACT", "FINITE_SET", "CONDITIONAL_SET", "UNKNOWN"], c=2)

# ---------------------------------------------------------------- F13-F14
D["F13"] = ["registration:", "    schedule_work()", " " * 8 + "\u2193",
            "    workqueue dispatcher", " " * 8 + "\u2193", "    lab_work()"]
D["F14"] = ["lab_work:", "    context = WORKQUEUE", "    may_sleep = MAY_SLEEP"]

# ---------------------------------------------------------------- F15-F16
D["F15"] = ["Direct effects", " " * 6 + "+ Callee effects",
            " " * 6 + "+ Callback effects", " " * 6 + "+ Context effects",
            " " * 6 + "\u2193", "Effective function contract"]

D["F16"] = groups([
    ("lab_schedule", ["direct:", "    ref_acquire", "    schedule_callback"]),
    ("lab_work", ["direct:", "    lock_acquire", "    mutation",
                  "    lock_release", "    ref_release"]),
    ("lab_put", ["direct:", "    ref_release", "    possible_free"]),
])

# ---------------------------------------------------------------- F17-F20
D["F17"] = ["list_add() = ownership transfer"]
D["F18"] = chain(["allocation", "initialization", "publication",
                  "reference acquisition", "callback registration",
                  "callback completion", "reference release",
                  "destruction"], c=4)

d = ["Object", marks([(2, VERT)]),
     marks([(2, TR)]) + HORIZ * 2 + " initial owner", marks([(2, VERT)]),
     marks([(2, TR)]) + HORIZ * 2 + " refs",
     "  " + VERT + "    " + TR + HORIZ * 2 + " lab_get",
     "  " + VERT + "    " + TR + HORIZ * 2 + " lab_schedule",
     "  " + VERT + "    " + BR + HORIZ * 2 + " lab_put",
     marks([(2, VERT)]),
     marks([(2, BR)]) + HORIZ * 2 + " work callback",
     " " * 7 + VERT,
     " " * 7 + BR + HORIZ * 2 + " requires object alive"]
D["F19"] = d

D["F20"] = ["UNKNOWN:", "    Lifetime", "    severity = Critical"]

# ---------------------------------------------------------------- F21-F23
D["F21"] = ["lab_object.value", "lab_update:", "    WRITE",
            "    lock = lab_object.lock", "    PROTECTED", "lab_work:",
            "    WRITE", "    lock = ?", "    PROTECTED / UNKNOWN"]
D["F22"] = ["CONFLICT"]
D["F23"] = ["UNPROTECTED"]

# ---------------------------------------------------------------- F24-F26
D["F24"] = ["Compiler:", "    field offset = 16", "DWARF:",
            "    field offset = 16", "Rust layout probe:",
            "    field offset = 24"]
D["F25"] = ["CONFLICT"]
D["F26"] = ["field offset = 16", "confidence = 0.91"]

# ---------------------------------------------------------------- F27-F28
D["F27"] = ["AST + annotations"]
D["F28"] = ["observations", " " * 4 + "\u2193",
            "    reconciled semantic facts", "    + explicit unknowns",
            "    + explicit conflicts", "    + validity domains",
            "    + provenance"]

# ---------------------------------------------------------------- F29-F30
rules = [("UNKNOWN ownership", "+ FFI crossing"),
         ("UNKNOWN lifetime", "+ callback/async access"),
         ("UNKNOWN synchronization", "+ mutable shared state"),
         ("UNKNOWN context", "+ potentially sleeping operation"),
         ("UNKNOWN ABI", "+ exported symbol")]
d = []
for head, cond in rules:
    d += [head, " " * 4 + cond, " " * 4 + "\u2192 CRITICAL"]
D["F29"] = d

D["F30"] = ['{', '  "blockers": [', '    {', '      "domain": "Lifetime",',
            '      "subject": "lab_object",',
            '      "reason": "CallbackReachabilityUnresolved",',
            '      "severity": "Critical"', '    }', '  ]', '}']

# ---------------------------------------------------------------- F31
D["F31"] = ntree(("fixtures/lab001/", [
    ("include/", ["lab_object.h"]),
    ("c/", ["lab_object.c"]),
    ("rust/", ["lib.rs"]),
    ("tests/", ["lifecycle.c", "differential.rs"]),
    ("expected/", ["ksir.json", "contract.json", "obligations.json"]),
    ("negative/", ["missing_ref.rs", "double_put.rs", "use_after_free.rs",
                   "lock_bypass.rs", "wrong_layout.rs",
                   "wrong_callback_context.rs",
                   "ffi_lifetime_violation.rs"]),
]))

# ---------------------------------------------------------------- F32
D["F32"] = [
    "KSIR-001 Exact source snapshot is bound.",
    "KSIR-002 Exact build variant is bound.",
    "KSIR-003 Compiler invocation has an execution receipt.",
    "KSIR-004 Every canonical fact has provenance.",
    "KSIR-005 Unsupported constructs become UNKNOWN.",
    "KSIR-006 Analyzer failure cannot produce VERIFIED.",
    "KSIR-007 Unknown ownership is preserved.",
    "KSIR-008 Unknown lifetime is preserved.",
    "KSIR-009 Call graph preserves unresolved indirect calls.",
    "KSIR-010 Context propagation is deterministic.",
    "KSIR-011 Effect propagation is deterministic.",
    "KSIR-012 Conflicting observations produce CONFLICT.",
    "KSIR-013 Critical UNKNOWN produces a blocker.",
    "KSIR-014 Facts are variant-scoped.",
    "KSIR-015 Changing snapshot invalidates dependent KSIR.",
    "KSIR-016 Changing compiler identity invalidates compiler-derived evidence.",
    "KSIR-017 Changing generated headers changes the build-variant identity.",
    "KSIR-018 KSIR serialization is deterministic.",
    "KSIR-019 KSIR replay produces identical digest.",
    "KSIR-020 No LLM-generated assertion can enter canonical KSIR without provenance.",
]

# ---------------------------------------------------------------- F33
# End-to-end chain. Upper half: labels at col 0, spine at 8. After the fork the
# spine moves to 15 (the source's own merge point) and labels centre on it.
UP = 8
DN = 15
RIGHT = 23
d = []
for t in ["RFL-AE-LAB-001", "MU-000001", "exact Linux/C fixture snapshot",
          "BuildManifest", "authorized compiler execution",
          "ExecutionReceipt", "compiler observations", "ObservationBundle"]:
    d.append(t)
    d.append(marks([(UP, VERT)]))
    d.append(marks([(UP, DOWN)]))
d.pop()                                    # last DOWN belongs to the fork row
d.append(marks([(UP, TR)]) + HORIZ * 14 + "\u2510")
d.append(marks([(UP, DOWN), (RIGHT, DOWN)]))
d.append(row([("resolved", UP), ("UNKNOWN/CONFLICT", RIGHT)]))
d.append(marks([(UP, VERT), (RIGHT, VERT)]))
d.append(bar([(UP, CORNER_BL), (DN, TEE_D), (RIGHT, CORNER_BR)]))
d.append(marks([(DN, DOWN)]))
for t in ["KSIR", "Contract IR", "Rust Design IR", "Verification IR",
          "authorized execution", "Evidence", "Gates",
          "Migration Certificate"]:
    d.append(row([(t, DN)]))
    if t != "Migration Certificate":
        d.append(marks([(DN, VERT)]))
        d.append(marks([(DN, DOWN)]))
D["F33"] = d

# ---------------------------------------------------------------- F34-F35
D["F34"] = ["Which source?", "Which snapshot?", "Which configuration?",
            "Which compiler?", "Which command?", "Which observations?",
            "Which semantic facts?", "Which unknowns?", "Which conflicts?",
            "Which contract?", "Which design?", "Which implementation?",
            "Which exact tests?", "Which receipts?", "Which evidence?",
            "Which obligations were verified?",
            "Which authority performed verification?", "Which gates passed?",
            "What remains outside scope?"]
D["F35"] = ['"the agent said so"']

# ---------------------------------------------------------------- F36
kids = ["1. rfl-types", "2. rfl-ksir schema", "3. BuildManifest",
        "4. compiler execution backend", "5. ObservationBundle",
        "6. structural reconciliation", "7. context/effect reconstruction",
        "8. ownership/lifetime reconstruction",
        "9. lock/callback/refcount reconstruction",
        "10. UNKNOWN + CONFLICT extraction",
        "11. KSIR deterministic serialization", "12. KSIR QA corpus",
        "13. feed MU-000001"]
d = ["M0", marks([(0, VERT)])]
for i, k in enumerate(kids):
    d.append((BR if i == len(kids) - 1 else TR) + HORIZ * 2 + " " + k)
D["F36"] = d

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
