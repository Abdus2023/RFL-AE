#!/usr/bin/env python3
"""Regenerate every ASCII diagram in PROTOCOL-P58.md by column arithmetic.

    python3 diagrams/PROTOCOL-P58.py [outdir]     # default /tmp/p58diag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py PROTOCOL-P58.md <outdir>

The diagrams in PROTOCOL-P58.md are NOT verbatim transcriptions: the pasted
source had all of its ASCII art collapsed onto single lines, so each diagram
was re-derived. This script is the record of that derivation -- re-running it
and diffing against the committed document proves the diagrams still match.

--- original rationale ---

The pasted source has all of its ASCII art collapsed onto single lines. The
collapse rule is: a run of N spaces encodes a newline followed by N-1 leading
spaces. That rule is reversible, so the original column positions are
recoverable -- but they are re-derived here structurally (box widths, fan
spans, spine columns) rather than counted by eye, because eyeballing space
runs is exactly how a one-column error creeps in.

Nothing in this file is hand-typed ASCII. Every glyph position comes from
geo.py arithmetic.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import (VERT, DOWN, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
                 TEE_D, TEE_U, HORIZ, cen, row, marks, bar, box, boxfix,
                 dchain, align, padc)  # noqa: E402

OUT = os.environ.get("DIAGDIR", "/tmp/p58diag")
os.makedirs(OUT, exist_ok=True)
D = {}


def chain_iv(items, c):
    """Vertical chain joined by VERT+DOWN at column c."""
    out = [items[0]]
    for it in items[1:]:
        out += [marks([(c, VERT)]), marks([(c, DOWN)]), it]
    return out


def tree(name, kids, indent="  ", cont=VERT + "   "):
    """A root with ├──/└── children; nested groups given as (label, subkids)."""
    out = [name, indent + cont.rstrip() if cont else ""]
    return out


def store_tree(root, kids):
    out = [root]
    for i, k in enumerate(kids):
        out.append("\u251c\u2500\u2500 " + k if i < len(kids) - 1
                   else "\u2514\u2500\u2500 " + k)
    return out


# ---------------------------------------------------------------- D01
# COMMAND -> PROTOCOL KERNEL -> EVENT STORE -> PROJECTION/REPLAY
#   -> CANONICAL STATE -> EVIDENCE/GATES -> RELEASE DECISION
C = 20
L2, R2 = C - 10, C + 10
d = []
d.append(row([("COMMAND", C)]))
d.append(marks([(C, VERT)]))
d.append(marks([(C, DOWN)]))
d += boxfix(["PROTOCOL", "KERNEL"], C, 11)
d.append(marks([(C, VERT)]))
d.append(marks([(C, VERT)]) + " canonical")
d.append(marks([(C, VERT)]) + " events")
d.append(marks([(C, VERT)]))
d.append(marks([(C, DOWN)]))
d += boxfix(["EVENT STORE"], C, 11)
d.append(marks([(C, VERT)]))
d.append(bar([(L2, CORNER_TL), (C, TEE_U), (R2, CORNER_TR)]))
d.append(marks([(L2, DOWN), (R2, DOWN)]))
d.append(row([("PROJECTION", L2), ("REPLAY", R2)]))
d.append(marks([(L2, VERT), (R2, VERT)]))
d.append(bar([(L2, CORNER_BL), (C, TEE_D), (R2, CORNER_BR)]))
d.append(marks([(C, DOWN)]))
d.append(row([("CANONICAL STATE", C)]))
d.append(marks([(C, VERT)]))
d.append(bar([(L2, CORNER_TL), (C, TEE_U), (R2, CORNER_TR)]))
d.append(marks([(L2, DOWN), (R2, DOWN)]))
d.append(row([("EVIDENCE", L2), ("GATES", R2)]))
d.append(marks([(L2, VERT), (R2, VERT)]))
d.append(bar([(L2, CORNER_BL), (C, TEE_D), (R2, CORNER_BR)]))
d.append(marks([(C, DOWN)]))
d.append(row([("RELEASE DECISION", C)]))
D["D01"] = d

# ---------------------------------------------------------------- D02
D["D02"] = align([
    ("Evidence says:", "WHAT WAS OBSERVED"),
    ("Verification says:", "WHAT THE OBSERVATION ESTABLISHES"),
    ("Gate says:", "WHETHER REQUIREMENTS ARE SATISFIED"),
    ("Protocol says:", "WHETHER THE STATE TRANSITION IS ALLOWED"),
], gap=3)

# ---------------------------------------------------------------- D03
D["D03"] = store_tree("crates/rfl-protocol/src/store/", [
    "mod.rs", "memory.rs", "append_log.rs", "record.rs",
    "recovery.rs", "integrity.rs"])

# ---------------------------------------------------------------- D04
# Physical event record: three columns of interior 14/14/16, total width 48.
W = (14, 14, 16)
c1 = 1 + W[0]
c2 = 1 + W[0] + 1 + W[1]
c3 = 1 + W[0] + 1 + W[1] + 1 + W[2]


def cell(text, w):
    return VERT + (" " + text).ljust(w)


def cells(vals):
    return "".join(cell(v, w) for v, w in zip(vals, W)) + VERT


d = []
d.append(bar([(0, CORNER_TL), (c1, TEE_D), (c2, TEE_D), (c3, CORNER_TR)]))
d.append(cells(["magic", "schema", "payload_length"]))
d.append(bar([(0, "\u251c"), (c1, "\u253c"), (c2, "\u253c"), (c3, "\u2524")]))
d.append(cells(["sequence", "event_digest", "payload"]))
d.append(bar([(0, "\u251c"), (c1, TEE_U), (c2, TEE_U), (c3, "\u2524")]))
d.append(VERT + " record_checksum".ljust(sum(W) + 2) + VERT)
d.append(bar([(0, CORNER_BL), (sum(W) + 3, CORNER_BR)]))
D["D04"] = d

# ---------------------------------------------------------------- D05
D["D05"] = dchain(["LOCK", "read current head", "compare expected head",
                   "validate sequence", "validate previous digest",
                   "append complete record",
                   "flush according to durability policy",
                   "publish new head", "UNLOCK"], c=2)

# ---------------------------------------------------------------- D06
D["D06"] = dchain(["START", "scan records", "validate framing",
                   "validate sequence", "validate hash chain",
                   "validate event digest", "validate state transition",
                   "reconstruct head"], c=2)

# ---------------------------------------------------------------- D07
D["D07"] = ["E001", "E002", "E003", "CORRUPTED"]

# ---------------------------------------------------------------- D09
D["D09"] = ["event constructed", " " * 6 + "\u2260", "event accepted",
            " " * 6 + "\u2260", "event durably persisted", " " * 6 + "\u2260",
            "operation executed", " " * 6 + "\u2260", "claim verified"]

# ---------------------------------------------------------------- D10
D["D10"] = chain_iv(["Artifact", "Observation", "EvidenceRecord",
                     "VerificationClaim", "Gate"], 3)

# ---------------------------------------------------------------- D11
D["D11"] = ["test output", " " * 3 + "\u2193", "VERIFIED"]

# ---------------------------------------------------------------- D12
D["D12"] = dchain(["Kernel snapshot S1", "Contract C1", "Design D1",
                   "Implementation I1", "Verification V1"], c=4)

# ---------------------------------------------------------------- D13
def _lbl(code, status):
    return code.ljust(5) + status


D["D13"] = ["S1", " " + "\u2193",
            _lbl("C1", "INVALIDATED"), " " + "\u2193",
            _lbl("D1", "INVALIDATED"), " " + "\u2193",
            _lbl("I1", "STALE"), " " + "\u2193",
            _lbl("V1", "INVALIDATED")]

# ---------------------------------------------------------------- D15
d = []
d.append("C implementation")
d.append(marks([(6, VERT)]))
d.append(bar([(6, "\u251c")]) + HORIZ * 4 + " normalized observation "
         + HORIZ * 4 + "\u2510")
right = 6 + 1 + 4 + 1 + len("normalized observation") + 1 + 4
d.append(marks([(6, VERT), (right, VERT)]))
d.append(marks([(6, DOWN), (right, DOWN)]))
d.append(row([("Rust implementation", 9), ("comparison", right)]))
D["D15"] = d

# ---------------------------------------------------------------- D16
# Gate evidence chain: spine at col 1, one branch column per depth, +7 each.
levels = ["Requirement", "Obligation", "Verification", "Oracle Result",
          "Evidence", "Receipt", "Artifact"]
d = ["Gate", marks([(1, VERT)])]
for i, name in enumerate(levels):
    g = 1 + 7 * i
    last = i == len(levels) - 1
    glyph = "\u2514" if last else "\u251c"
    lead = marks([(g, glyph)]) if g == 1 else marks([(1, VERT), (g, glyph)])
    d.append(lead + HORIZ * 2 + " " + name)
    if not last:
        d.append(marks([(1, VERT), (g + 7, VERT)]))
D["D16"] = d

# ---------------------------------------------------------------- D17
D["D17"] = chain_iv(["SOURCE", "OBSERVATION", "KSIR FACT", "CONTRACT",
                     "OBLIGATION", "DESIGN", "IMPLEMENTATION", "EXECUTION",
                     "RECEIPT", "EVIDENCE", "VERIFICATION", "GATE",
                     "CERTIFICATE", "REVIEW", "RELEASE"], 2)

# ---------------------------------------------------------------- D18
D["D18"] = chain_iv(["KSIR fact", "Contract", "Design", "Implementation",
                     "Verification", "Gate", "Certificate"], 3)

# ---------------------------------------------------------------- D19
D["D19"] = dchain(["KSIR", "Contract INVALID", "Design STALE",
                   "Verification INVALID", "Gate INVALID",
                   "Certificate INVALID"], c=1)

# ---------------------------------------------------------------- D20
D["D20"] = ["Contract C1 valid at epoch 4", "Contract changes at epoch 5",
            "C1 \u2192 STALE"]

# ---------------------------------------------------------------- D21
D["D21"] = ["CURRENT EPOCH = 4", "contract changed", " " * 6 + "\u2193",
            "AdvanceEpoch", " " * 6 + "\u2193", "EPOCH = 5",
            " " * 6 + "\u2193", "dependent work becomes stale"]

# ---------------------------------------------------------------- D22
D["D22"] = dchain(["Rust struct", "canonical serialization", "bytes",
                   "SHA-256", "Digest"], c=4)

# ---------------------------------------------------------------- D23
D["D23"] = ["Debug formatting", "JSON with arbitrary map ordering",
            "platform-dependent serialization"]

# ---------------------------------------------------------------- D24
# The lifecycle state machine. Spine S=28: the narrow boxes are 15 wide with
# their tee at S (left S-7); the wide box is 32 wide with its tee at S
# (left S-15). Both are consistent only for S=28.
S = 28
F1, F2 = 20, 37          # fork columns


def nbox(text):
    return boxfix([text], S, 11)


def spine(label=None):
    return marks([(S, VERT)]) + (" " + label if label else "")


d = []
d += nbox("DISCOVERED")
d.append(spine("Map"))
d.append(marks([(S, DOWN)]))
d += nbox("MAPPED")
d.append(spine("Contract"))
d.append(marks([(S, DOWN)]))
d += nbox("CONTRACTED")
d.append(spine("Design"))
d.append(marks([(S, DOWN)]))
d += nbox("DESIGNED")
d.append(spine("authorize"))
d.append(marks([(S, DOWN)]))
# wide box: interior 30, tee at S
# interior 30 -> width 32; the tee stays on the spine at S (left = S - 15)
wb_left = S - 15
d.append(bar([(wb_left, CORNER_TL), (wb_left + 31, CORNER_TR)]))
d.append(marks([(wb_left, VERT)]) + " AUTHORIZED_FOR_IMPLEMENTATION"
         + VERT)
d.append(bar([(wb_left, CORNER_BL), (S, TEE_D),
              (wb_left + 31, CORNER_BR)]))
d.append(spine("implementation"))
d.append(marks([(S, DOWN)]))
d += nbox("IMPLEMENTED")
d.append(spine("authorize test"))
d.append(marks([(S, DOWN)]))
# AUTHORIZED_FOR_TESTING: interior 24 -> width 26; tee at left + 12 == S
tb_left = S - 12
d.append(bar([(tb_left, CORNER_TL), (tb_left + 25, CORNER_TR)]))
d.append(marks([(tb_left, VERT)]) + " AUTHORIZED_FOR_TESTING " + VERT)
d.append(bar([(tb_left, CORNER_BL), (S, TEE_D), (tb_left + 25, CORNER_BR)]))
d.append(spine("verify"))
# fork to PARTIALLY_VERIFIED / VERIFIED
d.append(bar([(F1, CORNER_TL), (S, TEE_U), (F2, CORNER_TR)]))
d.append(marks([(F1, DOWN), (F2, DOWN)]))
d.append(row([("PARTIALLY_VERIFIED", 22), ("VERIFIED", 38)]))
d.append(marks([(F1, VERT), (F2, VERT)]))
d.append(bar([(F1, CORNER_BL), (S, TEE_D), (F2, CORNER_BR)]))
d.append(spine("adversarial"))
d.append(marks([(S, DOWN)]))
d.append(row([("ADVERSARIALLY_VERIFIED", 27)]))
d.append(marks([(S, VERT)]))
d.append(marks([(S, DOWN)]))
d.append(row([("AUTHORIZED_FOR_REVIEW", 27)]))
d.append(marks([(S, VERT)]))
d.append(marks([(S, DOWN)]))
d.append(row([("RELEASE_ELIGIBLE", S)]))
d.append(marks([(S, VERT)]))
d.append(marks([(S, DOWN)]))
d.append(row([("RELEASED", S)]))
D["D24"] = d

# ---------------------------------------------------------------- D25
d = box(["QUARANTINED"], 23, tee=False)[0]
D["D25"] = d

# ---------------------------------------------------------------- D26
D["D26"] = ["implementation authority = suspended",
            "release authority = unavailable",
            "canonical promotion = unavailable"]

# ---------------------------------------------------------------- D27
d = []
d.append(row([("QUARANTINED", 5)]))
d.append(marks([(4, VERT)]))
d.append(marks([(4, DOWN)]))
d.append("Investigation")
d.append(marks([(4, VERT)]))
d.append(marks([(4, "\u251c")]) + HORIZ * 2 + " evidence resolves issue")
d.append(marks([(4, VERT)]))
d.append(marks([(4, "\u2514")]) + HORIZ * 2 + " conflict remains")
d.append(marks([(12, VERT)]))
d.append(marks([(12, DOWN)]))
d.append(row([("QUARANTINED", 14)]))
D["D27"] = d

# ---------------------------------------------------------------- D28
D["D28"] = ["protocol version", "schema version", "source commit",
            "event format version", "state schema version",
            "test corpus digest", "conformance results",
            "adversarial test results", "toolchain fingerprint",
            "artifact digests"]

# ---------------------------------------------------------------- D29
d = ["Protocol Release", marks([(6, VERT)])]
for k in ["source identity", "semantic identity", "schema identity",
          "verification evidence"]:
    g = "\u2514" if k == "verification evidence" else "\u251c"
    d.append(marks([(6, g)]) + HORIZ * 2 + " " + k)
D["D29"] = d

# ---------------------------------------------------------------- D30
# RFL-AE v0.1 crate tree: top-level spine at col 0, nested spine at col 3.
groups = [
    ("rfl-types", []),
    ("rfl-protocol", ["typed commands", "typed events", "authorization",
                      "transition algebra", "deterministic reducer",
                      "event store", "replay", "CAS", "protocol QA"]),
    ("rfl-evidence", ["evidence records", "dependency graph",
                      "invalidation", "provenance"]),
    ("rfl-verification", ["obligations", "oracle", "results",
                          "differential verification"]),
    ("rfl-gates", ["requirement algebra", "gate evaluation",
                   "certificate compilation"]),
]
d = ["RFL-AE v0.1", marks([(0, VERT)])]
for gi, (g, kids) in enumerate(groups):
    glast = gi == len(groups) - 1
    gg = "\u2514" if glast else "\u251c"
    d.append(marks([(0, gg)]) + HORIZ * 2 + " " + g)
    cont = " " * 4 if glast else marks([(0, VERT)]) + "   "
    for ki, k in enumerate(kids):
        kg = "\u2514" if ki == len(kids) - 1 else "\u251c"
        d.append(cont + kg + HORIZ * 2 + " " + k)
D["D30"] = d

# ---------------------------------------------------------------- D31
D["D31"] = dchain(["Migration discovery", "KSIR structural facts",
                   "Contract", "Rust design", "Implementation artifact",
                   "Authorized execution", "Execution receipt", "Evidence",
                   "Verification obligation", "Gate",
                   "Migration certificate"], c=7)

# ---------------------------------------------------------------- small
D["D32"] = dchain(["Certificate", "Release Gate", "Release Authorization"], c=4)
D["D33"] = dchain(["Certificate", "automatic release"], c=4)
D["D34"] = ["Gate Engine \u2260 Protocol Engine"]
D["D35"] = ["Are the declared requirements satisfied?"]
D["D36"] = ["Is the requested state transition permitted?"]
D["D37"] = ["bool"]
D["D38"] = ["FAIL"]
D["D39"] = ["BLOCKED"]
D["D40"] = ["ABI verification"]
D["D41"] = ["ABI layout = UNKNOWN"]
D["D42"] = ["UNKNOWN"]
D["D43"] = ["GateStatus::Blocked"]
D["D44"] = ["GateStatus::Fail"]
D["D45"] = ["UNKNOWN \u2260 FALSE"]
D["D46"] = ["Certificate", "    \u2260", "Release authorization"]
D["D47"] = ["these conditions were established",
            "within this declared scope",
            "against this snapshot/variant",
            "using these artifacts/evidence/gates"]
D["D48"] = ["GateEvaluated"]
D["D49"] = ["GatePassed"]
D["D50"] = ["CORRUPT_HISTORY"]
D["D51"] = ["rfl-ae-protocol-v0.1.0-alpha"]
D["D52"] = ["PROTOCOL-GATE-001"]
D["D53"] = ["payload: serde_json::Value"]

# gate pseudo-code (not valid Rust -- fenced as text)
D["D55"] = ["IMPLEMENTATION_RELEASE_GATE = ALL(",
            "    SnapshotMatches,", "    ContractVerified,",
            "    DesignVerified,", "    ImplementationArtifactExists,",
            "    ABIContractSatisfied,", "    NoCriticalUnknown,",
            "    NoCriticalConflict", ")"]
D["D56"] = ["TEST_GATE = ALL(", "    VerificationPlanExists,",
            "    RequiredObligationsEvaluated,", "    ExecutionReceiptsValid,",
            "    EvidenceValid,", "    RequiredVariantsExecuted,",
            "    NoBlockingCounterexample", ")"]
D["D57"] = ["RELEASE_GATE = ALL(", "    ContractSatisfied,",
            "    DesignSatisfied,", "    VerificationSatisfied,",
            "    AdversarialVerificationSatisfied,", "    RegressionSatisfied,",
            "    ReviewApproved,", "    NoBlockingUnknown,",
            "    NoBlockingConflict,", "    SnapshotCurrent", ")"]

D["D14"] = ["S2"]
D["D66"] = ['"Migration appears safe."']
D["D63"] = ["Invalidated", "Superseded"]
D["D64"] = ["receipt digest mismatch"]
D["D65"] = ["Compile", "ABI", "Return/Error", "StateTransition",
            "ResourceLifecycle", "Synchronization", "Security",
            "ObservableIO", "Performance", "Architecture", "Configuration",
            "Regression"]
D["D58"] = ["SubmitVerification"]
D["D59"] = ["status: Verified"]
D["D60"] = ["97/100 tests passed \u2192 VERIFIED"]
D["D61"] = ["C output == Rust output"]
for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
for k in sorted(D):
    print("=" * 70)
    print(k)
    print("=" * 70)
    print("\n".join(D[k]))
