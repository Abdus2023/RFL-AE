#!/usr/bin/env python3
"""Regenerate every ASCII diagram in FIRST-MIGRATION.md by column arithmetic.

    python3 diagrams/MU-000001.py [outdir]     # default /tmp/mu1diag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py FIRST-MIGRATION.md <outdir>

The diagrams in FIRST-MIGRATION.md are NOT verbatim transcriptions: the pasted
source had all of its ASCII art collapsed onto single lines, so each diagram
was re-derived. This script is the record of that derivation -- re-running it
and diffing against the committed document proves the diagrams still match.

Nothing here is hand-typed ASCII. Every glyph position comes from geo.py
arithmetic or from an explicit column constant derived structurally (box
widths, shared spine columns), never from counting runs of spaces by eye.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/mu1diag")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import (VERT, DOWN, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
                 TEE_D, TEE_U, CROSS, HORIZ, cen, row, marks, bar, box,
                 dchain, align)  # noqa: E402

D = {}
BR, TR = "\u2514", "\u251c"      # └ ├
DR = "\u2524"                    # ┤
DL = "\u251c"                    # ├


def chain(items, c=2, g="\u2193"):
    """Vertical chain joined by `g` at column c."""
    return dchain(items, c=c, g=g)


def chain_iv(items, c=2):
    """Vertical chain joined by a VERT row then a DOWN row at column c."""
    out = [items[0]]
    for it in items[1:]:
        out += [marks([(c, VERT)]), marks([(c, DOWN)]), it]
    return out


def tree(root, kids, sep=False):
    """Flat `├──`/`└──` tree. `sep` inserts a bare spine row before each kid."""
    out = [root]
    for i, k in enumerate(kids):
        if sep and i:
            out.append(marks([(0, VERT)]))
        out.append((TR if i < len(kids) - 1 else BR) + HORIZ * 2 + " " + k)
    return out


def ntree(node, prefix=""):
    """Nested tree. node = (label, [child nodes]); a child may be a bare str."""
    label, kids = node
    out = [prefix + label]
    for i, k in enumerate(kids):
        last = i == len(kids) - 1
        conn = BR if last else TR
        if isinstance(k, str):
            out.append(prefix + conn + HORIZ * 2 + " " + k)
        else:
            out.append(prefix + conn + HORIZ * 2 + " " + k[0])
            out += ntree(("", k[1]), prefix + (" " * 4 if last else VERT + "   "))[1:]
    return out


def kv(pairs, gap=5):
    """Aligned `ID      description` rows."""
    w = max(len(a) for a, _ in pairs)
    return [a.ljust(w) + " " * gap + b for a, b in pairs]


def record(name, fields, indent=4):
    """`NAME` followed by indented `field = value` rows."""
    return [name] + [" " * indent + f for f in fields]


# ---------------------------------------------------------------- E01-E03
D["E01"] = ["RFL-AE-LAB-001", "MU-000001"]

D["E02"] = ntree(("C source", [
    "one object type", "one allocation path", "one initialization path",
    "one refcount/lifetime rule", "one synchronized mutation",
    "one callback", "one destruction path", "one C/Rust boundary"]))

D["E03"] = ["RCU + workqueues + IRQ + DMA + VFS"]

# ---------------------------------------------------------------- E04-E05
D["E04"] = ntree(("fixtures/lab001/", [
    ("include/", ["lab_object.h"]),
    ("c/", ["lab_object.c"]),
    ("rust/", ["lib.rs"]),
    ("tests/", ["lifecycle.c", "differential.rs"]),
    ("expected/", ["ksir.json", "contract.json", "obligations.json"]),
]))

D["E05"] = chain(["allocation", "initialization", "publication", "get()",
                  "callback registration", "mutation under lock", "callback",
                  "put()", "destruction"], c=4)

# ---------------------------------------------------------------- E06
D["E06"] = ["refcount", "ownership", "callback lifetime", "container_of",
            "intrusive embedding", "workqueue context", "locking",
            "destruction"]

# ---------------------------------------------------------------- E07-E08
D["E07"] = kv([
    ("OBJ-001", "type = lab_object"),
    ("OWN-001", "refs protects object lifetime"),
    ("OWN-002", "lab_get acquires reference"),
    ("OWN-003", "lab_put releases reference"),
    ("OWN-004", "zero reference permits destruction"),
    ("LOCK-001", "lock protects value"),
    ("CTX-001", "lab_work executes in deferred process context"),
    ("CALL-001", "schedule_work \u2192 lab_work"),
    ("LIFE-001", "callback requires object to remain alive"),
    ("INTR-001", "work_struct embedded in lab_object"),
    ("ABI-001", "C callback receives work_struct-compatible pointer"),
])

D["E08"] = ["KSIR fact", "    \u2260", "contract"]

# ---------------------------------------------------------------- E09-E12
D["E09"] = kv([("UNKNOWN-001", "exact architecture-independent layout")])
D["E10"] = kv([("UNKNOWN-002", "indirect callback reachability")])
D["E11"] = chain(["unsupported analysis", "UNKNOWN"], c=8)
D["E12"] = chain(["unsupported analysis", "assumed safe"], c=8)

# ---------------------------------------------------------------- E13-E14
d = ["KSIR", marks([(1, VERT)]), marks([(1, DOWN)]), "Contract compiler",
     marks([(1, VERT)])]
for k in ["ownership", "lifetime", "locking", "context", "callback", "ABI",
          "destruction"]:
    d.append(marks([(1, BR if k == "destruction" else TR)]) + HORIZ * 2 + " " + k)
D["E13"] = d

D["E14"] = tree("contract/MU-000001/", ["contract.json", "invariants.json",
                                         "temporal.json", "unknowns.json",
                                         "conflicts.json"])

# ---------------------------------------------------------------- E15
D["E15"] = ["C-001", "Subject:", "    lab_object", "Precondition:",
            "    object initialized", "Invariant:",
            "    refs > 0 while object is accessible", "Postcondition:",
            "    lab_get increments refs", "Invariant:",
            "    value mutation occurs while lock held", "Temporal:",
            "    callback object remains valid until callback completion",
            "Postcondition:",
            "    final reference release permits destruction", "Context:",
            "    lab_work may execute in deferred process context"]

# ---------------------------------------------------------------- E16
# Contract graph: three branches at C-14, C, C+14 (13 dashes each side of ┼).
C = 23
B = (C - 14, C, C + 14)
d = []
d.append(row([("lab_object", C)]))
d.append(marks([(C, VERT)]))
d.append(bar([(B[0], CORNER_TL), (C, CROSS), (B[2], CORNER_TR)]))
d.append(marks([(b, DOWN) for b in B]))
d.append(row([("lifetime", B[0]), ("value", B[1]), ("callback", B[2])]))
d.append(marks([(b, VERT) for b in B]))
d.append(marks([(b, DOWN) for b in B]))
d.append(row([("refcount", B[0]), ("lock", B[1]), ("workqueue", B[2])]))
d.append(marks([(b, VERT) for b in B]))
d.append(bar([(B[0], CORNER_BL), (C, CROSS), (B[2], CORNER_BR)]))
d.append(marks([(C, DOWN)]))
d.append(row([("invariants", C)]))
D["E16"] = d

# ---------------------------------------------------------------- E17-E19
D["E17"] = chain(["Contract", "Rust Design IR"], c=4)
# The design block in the source mixes a C name + arrow with a Rust struct.
# No rust block anywhere in the corpus contains an arrow, so it is split:
# E65 is the text arrow, the struct is fenced as pure rust in the document.
D["E65"] = ["lab_object", " " * 4 + "\u2193"]

D["E19"] = ["Arc<LabObject>"]

# ---------------------------------------------------------------- E18
D["E18"] = ["C refcount", " " * 4 + "\u2193", "Rust ownership model",
            "lab_get()", " " * 4 + "\u2193", "acquire reference",
            "lab_put()", " " * 4 + "\u2193", "release reference",
            "zero", " " * 4 + "\u2193", "destruction"]

# ---------------------------------------------------------------- E20-E23
D["E20"] = chain(["spin_lock", "mutation", "spin_unlock"], c=4)
D["E21"] = ["SpinLock<State>"]
D["E22"] = ["D-LOCK-001 all mutable accesses represented",
            "D-LOCK-002 no bypass path",
            "D-LOCK-003 locking semantics preserve source behavior",
            "D-LOCK-004 callback context permits primitive",
            "D-LOCK-005 IRQ/preemption semantics preserved"]
D["E23"] = ["DESIGN \u2260 AUTHORIZED_FOR_IMPLEMENTATION"]

# ---------------------------------------------------------------- E24-E25
D["E24"] = chain(["registration", "callback reachability", "object lifetime",
                  "cancellation/quiescence", "final release"], c=4)
D["E25"] = ["fn callback()"]

# ---------------------------------------------------------------- E26
D["E26"] = [
    "UO-001 C pointer \u2192 Rust reference", "Required:",
    "    pointer valid", "    aligned", "    initialized",
    "    object alive", "    correct provenance", "",
    "UO-002 container_of equivalent", "Required:",
    "    embedded field belongs to containing object",
    "    offset/layout exact", "    address remains stable", "",
    "UO-003 FFI callback", "Required:", "    ABI compatible",
    "    calling convention compatible", "    lifetime valid",
    "    context valid",
]

# ---------------------------------------------------------------- E27
D["E27"] = ["Contract", "+ Design", "+ Unsafe Obligations", " " * 8 + "\u2193",
            "Verification Compiler", " " * 8 + "\u2193", "Verification IR"]

# ---------------------------------------------------------------- E28-E30
d = ["OBLIGATION", marks([(4, VERT)])]
for k in ["static check", "compile check", "runtime test",
          "differential test", "adversarial test"]:
    d.append(marks([(4, BR if k == "adversarial test" else TR)])
             + HORIZ * 2 + " " + k)
D["E28"] = d

D["E29"] = ["normal mutation", "concurrent mutation", "callback mutation",
            "lock bypass attempt"]
D["E30"] = ["normal callback", "callback + release race", "cancel + release",
            "duplicate release", "callback after teardown"]

# ---------------------------------------------------------------- E31-E32
D["E31"] = tree("fixtures/lab001/negative/", [
    "missing_ref.rs", "double_put.rs", "use_after_free.rs", "lock_bypass.rs",
    "wrong_layout.rs", "wrong_callback_context.rs",
    "ffi_lifetime_violation.rs"])

D["E32"] = align([("correct implementation", "\u2193 obligations satisfied"),
                  ("incorrect implementation",
                   "\u2193 at least one obligation fails")], gap=4)

# ---------------------------------------------------------------- E33-E34
D["E33"] = chain(["AUTHORIZED_FOR_TESTING", "ExecutionRequest",
                  "capability validation", "isolated worktree",
                  "exact command", "executor", "ExecutionReceipt"], c=8)
D["E34"] = ["rustc", "argv = [...]", "cwd = ...", "environment = ...",
            "toolchain = ..."]

# ---------------------------------------------------------------- E35-E37
D["E35"] = chain(["test", "stdout/stderr", "artifact", "receipt",
                  "observation", "evidence"], c=1)
D["E36"] = record("EV-001", ["subject = UO-002", "receipt = R-014",
                             "artifact = A-031", "snapshot = S-001",
                             "variant = V-001", "status = OBSERVED"])
D["E37"] = ["UO-002 VERIFIED"]

# ---------------------------------------------------------------- E38
D["E38"] = ["VerificationObligation + Evidence + Oracle"]

# ---------------------------------------------------------------- E39-E40
D["E39"] = ["LAB001-GATE = ALL(", "    snapshot_valid,",
            "    contract_reconciled,", "    design_reconciled,",
            "    no_critical_unknown,", "    no_critical_conflict,",
            "    implementation_exists,",
            "    all_required_obligations_verified,", "    ABI_verified,",
            "    lifetime_verified,", "    concurrency_verified,",
            "    negative_tests_detected,",
            "    independent_verification_completed", ")"]
D["E40"] = ["PASS", "FAIL", "BLOCKED"]

# ---------------------------------------------------------------- E41
# Independent-verification topology. Spine at 20; fork at 11 / 29 (8 dashes).
S = 20
FL, FR = 11, 29
d = []
for t in ("DESIGN AGENT", "IMPLEMENTER", "ARTIFACT"):
    d.append(row([(t, S)]))
    d.append(marks([(S, VERT)]))
    d.append(marks([(S, DOWN)]))
d.append(bar([(FL, CORNER_TL), (S, TEE_U), (FR, CORNER_TR)]))
d.append(marks([(FL, DOWN), (FR, DOWN)]))
d.append(row([("CONTRACT REVIEW", FL), ("VERIFICATION", FR)]))
d.append(marks([(FL, VERT), (FR, VERT)]))
d.append(bar([(FL, CORNER_BL), (S, TEE_D), (FR, CORNER_BR)]))
d.append(marks([(S, DOWN)]))
d.append(row([("ADVERSARIAL QA", S)]))
d.append(marks([(S, VERT)]))
d.append(marks([(S, DOWN)]))
d.append(row([("GATE", S)]))
D["E41"] = d

# ---------------------------------------------------------------- E42-E49
D["E42"] = ["ImplementationAgent", " " * 8 + VERT,
            " " * 8 + BR + HORIZ * 2 + " SubmitVerification"]
D["E43"] = ["ProtocolError::Authorization"]
D["E44"] = ["Scheduler", " " * 4 + VERT,
            " " * 4 + BR + HORIZ * 2 + " AuthorizeRelease"]
D["E45"] = ["ProtocolError::Authorization"]
D["E46"] = ["Agent", " " * 4 + VERT,
            " " * 4 + BR + HORIZ * 2 + " submit stale verification"]
D["E47"] = ["ProtocolError::StaleEpoch"]
D["E48"] = ["Agent", " " * 4 + VERT,
            " " * 4 + BR + HORIZ * 2 + " verification using invalidated evidence"]
D["E49"] = ["GateStatus::Blocked"]

# ---------------------------------------------------------------- E50-E51
D["E50"] = ["MU-000001", " " * 7 + VERT, " " * 7 + DOWN, "MigrationCertificate"]
D["E51"] = chain_iv(["S-001", "KSIR-001", "CONTRACT-001", "DESIGN-001",
                     "IMPLEMENTATION-001", "EXECUTION-001", "EVIDENCE-001",
                     "VERIFICATION-001", "GATE-001", "CERTIFICATE-001"], c=1)

# ---------------------------------------------------------------- E52-E54
D["E52"] = ["missing contract", "missing design", "missing implementation",
            "missing verification", "missing evidence", "invalid receipt",
            "invalidated evidence", "critical unknown", "critical conflict",
            "stale snapshot", "variant mismatch", "failed gate"]
D["E53"] = ["Certificate",
            "    implies all declared certificate prerequisites exist"]
D["E54"] = ["Certificate",
            "    implies the migrated code is universally correct"]

# ---------------------------------------------------------------- E55
D["E55"] = [
    "migration/MU-000001/",
    TR + HORIZ * 2 + " manifest.json",
    marks([(0, VERT)]),
    TR + HORIZ * 2 + " snapshot.json",
    TR + HORIZ * 2 + " variant.json",
    TR + HORIZ * 2 + " scope.json",
    marks([(0, VERT)]),
    TR + HORIZ * 2 + " ksir/",
    VERT + "   " + TR + HORIZ * 2 + " facts.json",
    VERT + "   " + TR + HORIZ * 2 + " unknowns.json",
    VERT + "   " + BR + HORIZ * 2 + " conflicts.json",
    marks([(0, VERT)]),
    TR + HORIZ * 2 + " contract/",
    VERT + "   " + TR + HORIZ * 2 + " contract.json",
    VERT + "   " + TR + HORIZ * 2 + " invariants.json",
    VERT + "   " + BR + HORIZ * 2 + " obligations.json",
    marks([(0, VERT)]),
    TR + HORIZ * 2 + " design/",
    VERT + "   " + TR + HORIZ * 2 + " design.json",
    VERT + "   " + TR + HORIZ * 2 + " mappings.json",
    VERT + "   " + BR + HORIZ * 2 + " unsafe-obligations.json",
    marks([(0, VERT)]),
    TR + HORIZ * 2 + " implementation/",
    VERT + "   " + TR + HORIZ * 2 + " commit.json",
    VERT + "   " + BR + HORIZ * 2 + " artifacts/",
    marks([(0, VERT)]),
    TR + HORIZ * 2 + " verification/",
    VERT + "   " + TR + HORIZ * 2 + " plan.json",
    VERT + "   " + TR + HORIZ * 2 + " results.json",
    VERT + "   " + TR + HORIZ * 2 + " oracle-results.json",
    VERT + "   " + BR + HORIZ * 2 + " counterexamples/",
    marks([(0, VERT)]),
    TR + HORIZ * 2 + " execution/",
    VERT + "   " + BR + HORIZ * 2 + " receipts/",
    marks([(0, VERT)]),
    TR + HORIZ * 2 + " evidence/",
    VERT + "   " + TR + HORIZ * 2 + " records/",
    VERT + "   " + BR + HORIZ * 2 + " dependencies.json",
    marks([(0, VERT)]),
    TR + HORIZ * 2 + " gates/",
    VERT + "   " + BR + HORIZ * 2 + " results.json",
    marks([(0, VERT)]),
    BR + HORIZ * 2 + " certificate/",
    "    " + BR + HORIZ * 2 + " migration-certificate.json",
]

# ---------------------------------------------------------------- E56-E57
D["E56"] = chain(["DISCOVERED", "MAPPED", "CONTRACTED", "DESIGNED",
                  "AUTHORIZED_FOR_IMPLEMENTATION", "IMPLEMENTED",
                  "AUTHORIZED_FOR_TESTING", "VERIFIED",
                  "ADVERSARIALLY_VERIFIED", "AUTHORIZED_FOR_REVIEW",
                  "RELEASE_ELIGIBLE", "RELEASED"], c=1)
D["E57"] = chain(["NOT_PRESENT", "OBSERVED", "BOUND", "RECONCILED",
                  "VERIFICATION_INPUT", "VERIFIED"], c=1)

# ---------------------------------------------------------------- E58
D["E58"] = ["number of agents", "number of prompts",
            "lines of generated Rust", "tokens consumed"]

# ---------------------------------------------------------------- E59-E60
D["E59"] = ["MU-000001"]
D["E60"] = chain([
    "What source snapshot was migrated?",
    "What semantic facts were reconstructed?",
    "What remains unknown?",
    "What contract was derived?",
    "What Rust design was authorized?",
    "What implementation was produced?",
    "What exact commands executed?",
    "What actually happened?",
    "What evidence supports each observation?",
    "Which obligations were verified?",
    "Which gates passed?",
    "Who had authority for each transition?",
    "What exact scope does the certificate cover?",
], c=8)
D["E61"] = ['"the agent said so"']

# ---------------------------------------------------------------- E62-E63
d = ["MU-000001", " " * 6 + VERT, " " * 6 + DOWN, "MU-000002",
     " " * 6 + VERT,
     " " * 6 + TR + HORIZ * 2 + " independent migration",
     " " * 6 + VERT, " " * 6 + DOWN, "MU-000003", " " * 6 + VERT,
     " " * 6 + TR + HORIZ * 2 + " shared semantic dependency",
     " " * 6 + DOWN, "MU-000004"]
D["E62"] = d

D["E63"] = chain(["10 units", "100 units", "1000 units", "subsystem",
                  "cross-subsystem migration"], c=1)

# ---------------------------------------------------------------- E64
D["E64"] = ntree(("RFL-AE-M0", [
    "Protocol kernel executable", "Event sourcing deterministic",
    "Authorization enforced", "Evidence ledger connected",
    "Verification IR connected", "Gate engine connected",
    "MU-000001 end-to-end"]))

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
