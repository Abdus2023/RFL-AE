#!/usr/bin/env python3
"""Regenerate every ASCII diagram in RFL-GATES.md.

    python3 diagrams/RFL-GATES.py [outdir]    # default /tmp/rgdiag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py RFL-GATES.md <outdir>

The diagrams in RFL-GATES.md are NOT verbatim transcriptions: the pasted
source had all of its art collapsed onto single lines, so each diagram was
re-derived. This script is the record of that derivation -- re-running it and
diffing against the committed document proves the diagrams still match.

Collapse rule used throughout: a run of N spaces inside a collapsed block is a
line break followed by N-1 leading spaces; an extra space between two
unindented lines is a blank line. Runs that are clearly intra-line alignment
(the `∧   ` column in §905, the status column in §912) are kept as spacing.
Single-space word runs were broken into lines by meaning where they are lists
or stacked premises (§900, §901, §907, §908, §916, §922, §924).

Glyph note. Box-drawing art stays box-drawing; `↓` / `→` / `≠` / `⇒` / `⇏` /
`∧` / `∈` chains stay as they are. No block mixes an ASCII `|` with box glyphs.

Normalisations (all geometric, no content change):
  * §909 gate DAG: the source's spines (6, 17, merge 11) sat about one column
    left of the labels hung on them, and SourceIdentity could not be centred
    on 6 at all. The spines move to 7 / 18 / merge 12 -- the fork and merge
    keep the source's dash counts (10; 4 + 5) -- and every label is centred
    on its spine.
  * §920 protocol kernel: HUMAN, RFL-TYPES and RFL-TRANSITION were one or two
    columns off the spine at 19 that every other label sits on; all are now
    centred on 19. The two leaf labels are centred on the fork's legs
    (10 and 28), which the source kept at 10 and 28.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/rgdiag")
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
NEQ = "\u2260"                   # ≠
IMPL = "\u21d2"                  # ⇒
NIMPL = "\u21cf"                 # ⇏
AND = "\u2227"                   # ∧
ELEM = "\u2208"                  # ∈


def one(s):
    return [s]


def dchain(items, c):
    """Items at column 0 joined by a ↓ on column c."""
    out = [items[0]]
    for it in items[1:]:
        out += [" " * c + DWN, it]
    return out


def kids(items, col):
    return [" " * col + (BR if i == len(items) - 1 else TR) + DASH * 2 + " " + s
            for i, s in enumerate(items)]


def rule(head, tails, glyph, indent=4):
    """`head` then one indented `glyph tail` line per tail."""
    return [head] + [" " * indent + glyph + " " + t for t in tails]


def groups(items, indent=4):
    out = []
    for i, (h, vals) in enumerate(items):
        if i:
            out.append("")
        out += [h] + [" " * indent + v for v in vals]
    return out


def indented(head, items, indent=4):
    return [head] + [" " * indent + v for v in items]


# ================================================================ §894
D["P01"] = (["crates/rfl-gates/"] + kids(["Cargo.toml", "src/"], 0)
            + kids(["lib.rs", "gate.rs", "predicate.rs", "evaluation.rs",
                    "dependency.rs", "certification.rs", "invalidation.rs",
                    "tests/"], 4)
            + kids(["gate_status.rs", "predicates.rs", "dependencies.rs",
                    "certification.rs", "adversarial.rs"], 8))
D["P02"] = dchain(["rfl-types", "rfl-transition", "rfl-ledger",
                   "rfl-evidence", "rfl-gates"], c=4)

# ================================================================ §895
D["P03"] = dchain(["KUnit", "EvidenceRecord"], c=3)
D["P04"] = ["EvidenceRecord", "   + Contract", "   + Policy", "   " + DWN,
            "GateResult"]
D["P05"] = one(f"Test {NEQ} Gate")

# ================================================================ §897
D["P06"] = groups([("Gate", ["= requirement"]),
                   ("GateResult", ["= evaluation of requirement"])])

# ================================================================ §898
D["P07"] = groups([("PASS", ["predicate evaluated true"]),
                   ("FAIL", ["predicate evaluated false"]),
                   ("BLOCKED", ["predicate cannot validly be evaluated"]),
                   ("NOT_APPLICABLE", ["requirement is outside declared scope"]),
                   ("INVALIDATED", ["prior result no longer applies"])])
D["P08"] = groups([("KUnit ran and failed", [ARROW + " FAIL"]),
                   ("KUnit required but infrastructure unavailable",
                    [ARROW + " BLOCKED"])])

# ================================================================ §900
D["P09"] = ["Build unknown", "KUnit unknown", "therefore maybe pass"]

# ================================================================ §901
D["P10"] = one("true / false")
D["P11"] = one("true / false / unknown")
D["P12"] = ["PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE", "INVALIDATED"]
D["P13"] = one("FAIL")
D["P14"] = one("BLOCKED")

# ================================================================ §903
D["P15"] = one('"I think the remaining tests are low risk."')
D["P16"] = groups([("Agent:", ["proposes interpretation"]),
                   ("Gate evaluator:", ["evaluates declared predicate"])])

# ================================================================ §904
D["P17"] = one("Optional gate = FAIL")
D["P18"] = one("Required gate = FAIL")
D["P19"] = one("Required gate = BLOCKED")

# ================================================================ §905
# ∧ on column 4, every conjunct starting on column 8 (as EpochValid does).
D["P20"] = (["RELEASE_ELIGIBLE(A, E)", "    :=", "        EpochValid"]
            + ["    " + AND + "   " + t for t in (
                "ScopeValid", "SourceIdentityValid", "ArtifactValid",
                "ContractsSatisfied", "RequiredEvidenceComplete",
                "RequiredVerificationSatisfied", "RequiredGatesPass",
                "DependenciesValid", "NoCriticalConflict", "ReplayValid",
                "ProvenanceValid")])

# ================================================================ §906
D["P21"] = one("RequiredGate = Fail")
D["P22"] = one("RequiredGate = Blocked")
D["P23"] = rule("insufficient evidence", ["not certified"], ARROW)

# ================================================================ §907
D["P24"] = dchain(["MigrationUnit A", "MigrationUnit B", "MigrationUnit C"],
                  c=4)
D["P25"] = ["B", "C"]

# ================================================================ §908
D["P26"] = groups([("Gate G1:", ["PASS"]), ("later:", []),
                   ("Evidence E:", ["INVALIDATED"]), ("therefore:", []),
                   ("G1:", ["INVALIDATED"])])
D["P27"] = one("G1 never passed")
D["P28"] = ["G1 passed", "then", "G1 became invalidated"]

# ================================================================ §909
L, R = 7, 18
M = (L + R) // 2
assert M == 12
D["P29"] = [row([("SourceIdentity", L)]),
            marks([(L, VERT)]),
            " " * L + TR + DASH * (R - L - 1) + CORNER_TR,
            marks([(L, DOWN), (R, DOWN)]),
            row([("Artifact", L), ("Contracts", R)]),
            marks([(L, VERT), (R, VERT)]),
            " " * L + CORNER_BL + DASH * (M - L - 1) + TEE_D
            + DASH * (R - M - 1) + CORNER_BR,
            marks([(M, DOWN)]),
            row([("Verification", M)]),
            marks([(M, VERT)]), marks([(M, DOWN)]),
            row([("EvidenceComplete", M)]),
            marks([(M, VERT)]), marks([(M, DOWN)]),
            row([("ReleaseGate", M)])]
assert D["P29"][2].count(DASH) == 10
D["P30"] = one("cycle detection")
D["P31"] = one(f"G1 {ARROW} G2 {ARROW} G3 {ARROW} G1")

# ================================================================ §910
D["P32"] = dchain(["dependency gates", "source/artifact gates",
                   "contract gates", "verification gates", "release gates"],
                  c=6)
D["P33"] = one("Release = FAIL")
# Source geometry kept: each └ sits two columns right of its parent's text.
D["P34"] = ["Release"] + [" " * (2 + 6 * i) + BR + DASH * 2 + " " + s
                          for i, s in enumerate(("Verification", "Contract C17",
                                                 "DifferentialEvidence",
                                                 "BLOCKED"))]

# ================================================================ §912
D["P35"] = ["CertificationState", "    = derived from", "    gate results",
            "    + verification", "    + dependencies", "    + epoch",
            "    + evidence"]
D["P36"] = (["CERTIFICATION BLOCKED", "", "Required:"]
            + ["  " + k.ljust(21) + v for k, v in (
                ("SourceIdentity", "PASS"), ("ContractVerification", "PASS"),
                ("Build", "PASS"), ("KUnit", "PASS"), ("ABI", "BLOCKED"),
                ("Differential", "PASS"), ("DependencyIntegrity", "PASS"))])
D["P37"] = one("ready = false")

# ================================================================ §913
D["P38"] = one(f"Unverified {ARROW} Verified")
D["P39"] = one(f"Verified {ARROW} Invalidated")

# ================================================================ §914
# Source spacing kept (the second `=` is one column left of the first, as
# in the source).
D["P40"] = ["TechnicalCertification = Verified",
            "UpstreamAcceptance    = UnderReview"]
D["P41"] = ["TechnicalCertification = Verified",
            "UpstreamAcceptance    = Rejected"]

# ================================================================ §915
D["P42"] = dchain(["Certificate", "derived view over",
                   "ledger + evidence + verification + gates"], c=4)

# ================================================================ §916
D["P43"] = ["E17", "E19", "E22", "G4", "G7"]
D["P44"] = dchain(["E19", "invalidate dependent verification",
                   "invalidate dependent gate", "invalidate C42"], c=1)

# ================================================================ §917
D["P45"] = dchain(["Certificate", "Gate", "Verification", "Evidence",
                   "Execution", "Artifact", "Source"], c=4)
D["P46"] = dchain(["dependent derived claims", "potentially invalid"], c=8)

# ================================================================ §918
D["P47"] = ["CriticalDependencyState", "    " + ELEM + " {", "    Resolved,",
            "    Invalidated,", "    Unknown,", "    Conflicting", "}"]
D["P48"] = groups([(s, [ARROW + " no certification"])
                   for s in ("Unknown", "Conflicting", "Invalidated")])
D["P49"] = one("Resolved")

# ================================================================ §919
D["P50"] = indented("SemanticConflict", [
    "Ownership", "Lifetime", "Locking", "RCU", "ControlFlow", "ABI",
    "Configuration", "Architecture", "..."])
D["P51"] = one("NoCriticalConflicts = FAIL/BLOCKED")
D["P52"] = one("Two analyses disagree about lock protection")
D["P53"] = one("BLOCKED")
D["P54"] = one("Formal verification proves the generated code violates "
               "lock invariant")
D["P55"] = one("FAIL")

# ================================================================ §920
S, FL, FR = 19, 10, 28
D["P56"] = [row([("HUMAN", S)])]
for _lab in ("AUTHORIZATION", "RFL-TYPES", "RFL-TRANSITION", "RFL-LEDGER",
             "RFL-EVIDENCE", "VERIFICATION", "RFL-GATES"):
    D["P56"] += [marks([(S, VERT)]), marks([(S, DOWN)]), row([(_lab, S)])]
D["P56"] += [marks([(S, VERT)]),
             " " * FL + CORNER_TL + DASH * (S - FL - 1) + TEE_U
             + DASH * (FR - S - 1) + CORNER_TR,
             marks([(FL, VERT), (FR, VERT)]),
             marks([(FL, DOWN), (FR, DOWN)]),
             row([("TECHNICAL CERT.", FL), ("UPSTREAM STATE", FR)])]
assert D["P56"][-4].count(DASH) == 16

# ================================================================ §921
D["P57"] = dchain(["ONE C SUBSYSTEM", "ONE MigrationUnit", "SOURCE IDENTITY",
                   "KSIR", "3\u201310 CONTRACTS", "RUST DESIGN IR",
                   "RUST ARTIFACT", "BUILD", "TEST", "EVIDENCE",
                   "VERIFICATION", "GATES", "CERTIFICATE"], c=6)

# ================================================================ §922
D["P58"] = ["RCU-heavy core", "scheduler", "VFS internals", "MM",
            "architecture-specific assembly"]

# ================================================================ §923
D["P59"] = (["crates/"] + kids(["rfl-types/", "rfl-transition/", "rfl-ledger/",
                                "rfl-evidence/", "rfl-gates/", "rfl-ksir/"], 0)
            + ["", "migration/"] + kids(["example/"], 0)
            + kids(["source/", "observations/", "ksir/", "contracts/",
                    "design/", "rust/", "verification/", "evidence/",
                    "gates/", "certificate/"], 4))

# ================================================================ §924
# `AND ` is four columns wide, so the first conjunct sits on column 4 and the
# rest line up with it after their `AND`.
D["P60"] = (["CERTIFIED(A,E)", "    " + IMPL, "", "    source_identity_valid"]
            + ["AND " + t for t in (
                "epoch_valid", "migration_closure_known",
                "critical_semantics_resolved", "contracts_defined",
                "contracts_verified", "artifact_bound",
                "required_evidence_complete", "required_gates_pass",
                "dependencies_valid", "replay_valid", "provenance_valid")])
D["P61"] = rule("CERTIFIED(A,E)", ["upstream_accepted"], NIMPL)

# ================================================================ §925
D["P62"] = dchain(["RFL-TYPES", "RFL-TRANSITION", "RFL-LEDGER",
                   "RFL-EVIDENCE", "RFL-GATES", "MIGRATION UNIT", "KSIR",
                   "CONTRACTS", "RUST DESIGN IR", "RUST"], c=4)

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
