#!/usr/bin/env python3
"""Regenerate every ASCII diagram in PROOF-CARRYING.md.

    python3 diagrams/PROOF-CARRYING.py [outdir]    # default /tmp/pcdiag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py PROOF-CARRYING.md <outdir>

The diagrams in PROOF-CARRYING.md are NOT verbatim transcriptions: the pasted
source had all of its art collapsed onto single lines, so each diagram was
re-derived. This script is the record of that derivation -- re-running it and
diffing against the committed document proves the diagrams still match.

Glyph note. Diagrams that arrive in the source as box-drawing art stay
box-drawing (the foo() call tree, the trust boundary, the certificate chain
and the final architecture); those that arrive as ASCII art (`|`, `v`, `+--`,
`\\`, `/`) stay ASCII, matching the established corpus pattern. `↓` chains stay
`↓`. No block mixes an ASCII `|` with box glyphs.

Two source rows were normalised, both by one column:
  * §796 (trust boundary): the `scope enforcement` row was one column wider
    than every other row of its box (45 vs 44 inner columns).
  * §802 (final architecture): the `Epoch ─ Authorization ─ ...` row was one
    column narrower than its box (56 vs 57 inner columns).
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/pcdiag")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import (VERT, DOWN, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
                 TEE_D, HORIZ, row, marks)  # noqa: E402

D = {}
BR, TR = "\u2514", "\u251c"      # └ ├
DASH = HORIZ                     # ─
ARROW = "\u2192"                 # →
DWN = "\u2193"                   # ↓
DBL, DBLX = "\u2550", "\u256a"   # ═ ╪


def one(s):
    return [s]


def groups(items, indent=4):
    out = []
    for name, lines in items:
        out.append(name)
        out += [" " * indent + l for l in lines]
    return out


def achain(items, c=4, notes=None):
    """ASCII vertical chain: labels at column 0, `|` / `v` at column c.

    `notes` maps an item index i (>0) to a label written beside the `|` that
    leads INTO item i, e.g. `| mapping`.
    """
    notes = notes or {}
    out = [items[0]]
    for i, it in enumerate(items[1:], start=1):
        out.append(marks([(c, "|")]))
        if i in notes:
            out.append(marks([(c, "|")]) + " " + notes[i])
        out += [marks([(c, "v")]), it]
    return out


def dchain(items, c=4):
    """`↓` chain: labels at column 0, arrow at column c."""
    out = [items[0]]
    for it in items[1:]:
        out += [" " * c + DWN, it]
    return out


def ascii_tree_block(root, blocks, c):
    """root, then for each block: `|`, `+-- kid`..., optionally `|` `v` next.

    blocks = [(kids, next_label_or_None)].
    """
    out = [root]
    for kids, nxt in blocks:
        out.append(marks([(c, "|")]))
        out += [" " * c + "+-- " + k for k in kids]
        if nxt is not None:
            out += [marks([(c, "|")]), marks([(c, "v")]), nxt]
    return out


def and_list(first, rest):
    return [first] + ["AND " + r for r in rest]


# ================================================================ §775
D["L01"] = one("MigrationUnit")
D["L02"] = ["scheduler/", " " * 4 + "migration-unit:",
            " " * 8 + "sched_entity_lifecycle"]
D["L03"] = ["net/", " " * 4 + "migration-unit:", " " * 8 + "napi_poll_path"]
D["L04"] = ["1..N C functions", "1..N C types", "1..N macros",
            "1..N data structures", "required call-graph neighborhood",
            "required synchronization context"]

# ================================================================ §776
D["L05"] = [
    "foo()",
    " " + TR + DASH * 2 + " bar()",
    " " + VERT + "    " + BR + DASH * 2 + " alloc()",
    " " + TR + DASH * 2 + " schedule_work()",
    " " + BR + DASH * 2 + " put_ref()",
]
D["L06"] = ["bar()", "allocation context", "worker lifetime",
            "reference counting"]
D["L07"] = one("foo()")
D["L08"] = ascii_tree_block("MigrationUnit", [(
    ["foo()", "bar()", "object lifetime", "worker", "reference contract"],
    None)], c=4)

# ================================================================ §777
D["L09"] = one("Closure(U)")
# Fan U -> type / caller / callback at 6 / 14 / 22; caller -> lock and
# callback -> worker; lock and worker converge on lifetime with the source's
# 7 / 5 / 3 gaps between the diagonals.
U1, U2, U3 = 6, 14, 22
D["L10"] = [
    row([("U", U2)]),
    marks([(U2, "|")]),
    " " * U1 + "+" + "-" * (U2 - U1 - 1) + "+" + "-" * (U3 - U2 - 1) + "+",
    marks([(U1, "|"), (U2, "|"), (U3, "|")]),
    marks([(U1, "v"), (U2, "v"), (U3, "v")]),
    # `callback` starts at column 19 as in the source (centred on 23, not on
    # the U3 connector) so it keeps two spaces of clearance from `caller`.
    row([("type", U1), ("caller", U2), ("callback", U3 + 1)]),
    marks([(U2, "|"), (U3, "|")]),
    marks([(U2, "v"), (U3, "v")]),
    row([("lock", U2), ("worker", U3)]),
    marks([(U2, "\\"), (U3, "/")]),
    marks([(U2 + 1, "\\"), (U3 - 1, "/")]),
    marks([(U2 + 2, "v"), (U3 - 2, "v")]),
    row([("lifetime", (U2 + U3) // 2)]),
]
D["L11"] = one("Complete(U)")
D["L12"] = one("all files in U were translated")
D["L13"] = one("all required semantic dependencies have been accounted for.")

# ================================================================ §778
D["L14"] = ["unexamined dependency", " " * 8 + DWN,
            "implicitly assumed correct"]
D["L15"] = ["unexamined dependency", " " * 8 + DWN, "UNKNOWN", " " * 8 + DWN,
            "gate decides whether UNKNOWN is tolerable"]
D["L16"] = ["UNKNOWN", " " * 4 + ARROW + " BLOCKED"]
D["L17"] = ["UNKNOWN", " " * 4 + ARROW + " PASS"]

# ================================================================ §779
C1, C2, C3 = 17, 26, 35
_cfan = " " * C1 + "+" + "-" * (C2 - C1 - 1) + "+" + "-" * (C3 - C2 - 1) + "+"
D["L18"] = [
    row([("MigrationUnit", C2)]),
    marks([(C2, "|")]),
    _cfan,
    marks([(C1, "|"), (C2, "|"), (C3, "|")]),
    marks([(C1, "v"), (C2, "v"), (C3, "v")]),
    # Source label columns: Type-C 14, Lock-C 24, Lifetime-C 33 -- centring
    # Lifetime-C on the C3 connector would leave one space after Lock-C.
    row([("Type-C", C1), ("Lock-C", C2 + 1), ("Lifetime-C", C3 + 3)]),
    marks([(C1, "|"), (C2, "|"), (C3, "|")]),
    _cfan,
    marks([(C2, "|")]),
    marks([(C2, "v")]),
    row([("Semantic Contract", C2)]),
    marks([(C2, "|")]),
    marks([(C2, "v")]),
    row([("Rust Design", C2)]),
]
D["L19"] = achain(["LifetimeContract", "ReferenceContract", "CallbackContract",
                   "WorkerContract"], c=7)

# ================================================================ §780
D["L20"] = ["ContractId =", " " * 4 + "H("] + [
    " " * 8 + f for f in ("epoch,", "subject,", "kind,",
                          "canonical_statement,", "dependencies")] + [
    " " * 4 + ")"]

# ================================================================ §781
D["L21"] = one('"foo probably owns bar"')
D["L22"] = one('"this function seems safe under the lock"')

# ================================================================ §782
D["L23"] = groups([("C Contract:", ["object X is reference-counted"])])
D["L24"] = groups([("Rust Design:", ["representation = RefCounted<X>"])])
D["L25"] = achain(["C semantic contract", "Rust design decision"], c=7,
                  notes={1: "mapping"})

# ================================================================ §783
D["L26"] = ["&T", "&mut T", "Box<T>", "Arc<T>", "Pin<Box<T>>",
            "UnsafeCell<T>", "Atomic<T>", "raw pointer", "kernel wrapper"]
D["L27"] = one("ownership contract + lifetime contract + concurrency contract")
D["L28"] = one("because the model thought it looked right.")

# ================================================================ §784
D["L29"] = (["DesignDecision", marks([(6, "|")]), marks([(6, "v")]),
             "UnsafeObligation", marks([(6, "|")])]
            + [" " * 6 + "+-- required invariant " + x for x in "ABC"])

# ================================================================ §785
D["L30"] = one("Verified")
D["L31"] = one("Certified")

# ================================================================ §786
D["L32"] = achain(["GenerationRecord", "Human modification", "Final artifact"],
                  c=7)

# ================================================================ §787
D["L33"] = one("AI-generated source = final source")
D["L34"] = achain(["GeneratedArtifact", "ModifiedArtifact"], c=7,
                  notes={1: "human edit"})
D["L35"] = achain(["C source", "KSIR", "Design", "AI-generated Rust",
                   "Human-modified Rust", "Verified artifact"], c=3)

# ================================================================ §788
D["L36"] = achain(["C implementation", " " * 5 + "result C"], c=7,
                  notes={1: "test input I"})
D["L37"] = achain(["Rust implementation", " " * 5 + "result R"], c=7,
                  notes={1: "same test input I"})
D["L38"] = one("Compare(result_C, result_R)")
D["L39"] = one("exact equality")
D["L40"] = one("observational equivalence")

# ================================================================ §789
D["L41"] = one("C and Rust behave identically on 100 tests")
D["L42"] = one("C and Rust are equivalent for all inputs.")
D["L43"] = ["DifferentialTest", " " * 4 + "= Evidence"]
D["L44"] = ["DifferentialTest",
            " " * 4 + "= Proof of universal semantic equivalence"]

# ================================================================ §791
D["L45"] = one("CERTIFIED")
D["L46"] = one("UNKNOWN")
D["L47"] = one("BLOCKED")

# ================================================================ §792
D["L48"] = one("95% code coverage")
D["L49"] = one("RCU lifetime semantics")
D["L50"] = ["CodeCoverage", "PathCoverage", "ContractCoverage",
            "EvidenceCoverage", "ConfigurationCoverage",
            "ArchitectureCoverage", "ConcurrencyCoverage"]

# ================================================================ §793
D["L51"] = one("MIGRATION_READY(U)")
D["L52"] = and_list("source identity valid", [
    "dependency closure known", "required semantic domains analyzed",
    "critical conflicts resolved", "contracts extracted",
    "contracts sufficiently evidenced", "design authority granted"])
D["L53"] = one("MIGRATION_READY")
D["L54"] = one("Rust design generation")
D["L55"] = one("repository mutation")

# ================================================================ §794
D["L56"] = ["DESIGN_AUTHORIZED", "IMPLEMENTATION_AUTHORIZED",
            "EXECUTION_AUTHORIZED", "RELEASE_AUTHORIZED"]
D["L57"] = groups([("Agent may:", ["generate Rust"])])
D["L58"] = one("modify repository")
D["L59"] = one("run privileged commands")
D["L60"] = one("publish patch")
D["L61"] = dchain(["Observe", "Analyze", "Propose", "Design", "Generate",
                   "Modify", "Execute", "Verify", "Release"], c=3)

# ================================================================ §795
D["L62"] = one("ALLOW(op)")
D["L63"] = and_list("actor_has_capability", [
    "authorization_exists", "authorization_epoch == current_epoch",
    "operation_within_scope", "task_allows_operation", "preconditions_hold"])

# ================================================================ §796
# Box inner width 44 (46 with borders), spine / ┬ / ▼ / ╪ at column 22; the
# double rule is 47 wide as in the source. Labels are centred on the spine.
TB_W, TB_S = 44, 22


def tb_box(lines, top_entry, bottom_exit, pad=2):
    top = (CORNER_TL + DASH * (TB_S - 1) + DOWN + DASH * (TB_W - TB_S)
           + CORNER_TR) if top_entry else CORNER_TL + DASH * TB_W + CORNER_TR
    bot = (CORNER_BL + DASH * (TB_S - 1) + TEE_D + DASH * (TB_W - TB_S)
           + CORNER_BR) if bottom_exit else CORNER_BL + DASH * TB_W + CORNER_BR
    body = [VERT + (" " * pad + l).ljust(TB_W) + VERT for l in lines]
    return [top] + body + [bot]


def tb_crossing(label, rule_label):
    return [marks([(TB_S, VERT)]), row([(label, TB_S)]),
            marks([(TB_S, VERT)]),
            DBL * TB_S + DBLX + DBL * (47 - TB_S - 1),
            marks([(TB_S, VERT)]), row([(rule_label, TB_S)]),
            marks([(TB_S, VERT)])]


D["L64"] = (
    [row([("UNTRUSTED / PROBABILISTIC", TB_S)])]
    + tb_box(["", "LLM agents", "planners", "semantic analyzers",
              "code generators", "review agents", ""], False, True)
    + tb_crossing("typed requests", "TRUSTED PROTOCOL")
    + tb_box(["", "type validation", "epoch validation", "authorization",
              "scope enforcement", "transitions", "event ledger",
              "evidence binding", "gate evaluation",
              "certificate derivation", ""], True, True)
    + tb_crossing("external evidence", "EXECUTION SYSTEMS")
    + tb_box(["Linux build/test/toolchain infrastructure"], True, False,
             pad=1)
)
D["L65"] = one("typed state + deterministic rules + authorized execution"
               " + authenticated evidence")

# ================================================================ §797
D["L66"] = ["C-ControlFlow", "C-DataFlow", "C-Memory", "C-Lifetime",
            "C-Locking", "C-RCU", "C-Context", "C-ABI", "C-Config",
            "C-Architecture"]
D["L67"] = ["ContractSynthesizer", "ConflictResolver", "RustDesigner",
            "UnsafeReviewer"]
D["L68"] = ["StaticVerifier", "BuildVerifier", "KUnitVerifier",
            "RuntimeVerifier", "DifferentialVerifier", "ConcurrencyVerifier",
            "ABIVerifier"]
D["L69"] = ["EvidenceAuditor", "GateAuditor", "ProvenanceAuditor"]

# ================================================================ §798
D["L70"] = (groups([("LifetimeAgent:", ["ownership transfers at A"])]) + [""]
            + groups([("ConcurrencyAgent:", ["ownership remains with B"])])
            + [""]
            + groups([("RCUAgent:", ["object cannot be freed at A"])]))
D["L71"] = ascii_tree_block("Conflict", [
    (["claim A", "claim B", "claim C"], "Evidence acquisition"),
    (["source analysis", "call graph", "runtime instrumentation",
      "maintainer knowledge"], "Resolution"),
], c=3)
D["L72"] = one("OPEN / BLOCKED")

# ================================================================ §799
D["L73"] = one('"Can an LLM translate this C function?"')
D["L74"] = ["Given C migration unit U:", ""] + [
    f"{i}. {s}" for i, s in enumerate([
        "identify source closure", "reconstruct semantics",
        "extract contracts", "identify conflicts", "produce Rust design",
        "enumerate unsafe obligations", "generate Rust",
        "execute verification", "collect evidence", "produce certificate"],
        start=1)]
D["L75"] = ["SemanticRecall", "ContractPrecision", "ConflictDetectionRate",
            "UnsafeObligationRecall", "DesignConformance", "BuildSuccess",
            "TestConformance", "DifferentialConformance",
            "EvidenceCompleteness", "ReplayDeterminism",
            "FalseCertificationRate"]

# ================================================================ §800
D["L76"] = one("FALSE_CERTIFICATION_RATE")
D["L77"] = one("CODE_GENERATION_SUCCESS")
D["L78"] = one("wrong Rust + no certificate")
D["L79"] = one("wrong Rust + valid-looking certificate")
D["L80"] = dchain(["UNCERTAIN", "BLOCKED"], c=3)
D["L81"] = dchain(["UNCERTAIN", "PASS"], c=3)

# ================================================================ §801
_cert = [
    ("Epoch", []),
    ("MigrationUnit", ["C source digest", "source closure"]),
    ("KSIR", ["observations", "derivations", "invariants"]),
    ("Contracts", ["ownership", "lifetime", "concurrency", "ABI",
                   "configuration"]),
    ("Rust Design", ["mappings", "unsafe obligations"]),
    ("Artifact", ["Rust digest"]),
    ("Generation Provenance", []),
    ("Execution Evidence", []),
    ("Verification Results", []),
    ("Gate Results", []),
    ("Replay Verification", []),
]
D["L82"] = ["CERTIFICATE"]
for _i, (_name, _kids) in enumerate(_cert):
    _last = _i == len(_cert) - 1
    D["L82"].append(VERT)
    D["L82"].append((BR if _last else TR) + DASH * 2 + " " + _name)
    for _j, _k in enumerate(_kids):
        _g = BR if _j == len(_kids) - 1 else TR
        D["L82"].append(VERT + "   " + _g + DASH * 2 + " " + _k)
D["L83"] = ["CertificateDigest =", " " * 4 + "H(canonical_certificate)"]

# ================================================================ §802
# Box inner width 57 (59 with borders), ┬ at column 27 as in the source. The
# source's upper spine drifted to column 31 and its lower labels were not
# centred on the ┬; here every spine and label sits on column 27.
FA_W, FA_S = 57, 27
_chain = ["MIGRATION UNIT", "SOURCE EVIDENCE", "KSIR", "SEMANTIC CONTRACTS",
          "RUST DESIGN IR", "RUST ARTIFACT", "EXECUTION SYSTEMS", "EVIDENCE",
          "VERIFICATION", "GATES", "CERTIFICATE", "UPSTREAM REVIEW STATE"]
D["L84"] = [
    row([("HUMAN AUTHORITY", FA_S)]),
    marks([(FA_S, VERT)]), marks([(FA_S, DOWN)]),
    row([("POLICY / SCOPE", FA_S)]),
    marks([(FA_S, VERT)]), marks([(FA_S, DOWN)]),
    CORNER_TL + DASH * FA_W + CORNER_TR,
    VERT + (" " * 20 + "RFL-AE PROTOCOL").ljust(FA_W) + VERT,
    VERT + " " * FA_W + VERT,
    VERT + ("  Epoch " + DASH + " Authorization " + DASH + " Transition "
            + DASH + " Ledger " + DASH + " Gates").ljust(FA_W) + VERT,
    CORNER_BL + DASH * (FA_S - 1) + TEE_D + DASH * (FA_W - FA_S) + CORNER_BR,
]
for _lab in _chain:
    D["L84"] += [marks([(FA_S, VERT)]), marks([(FA_S, DOWN)]),
                 row([(_lab, FA_S)])]
D["L85"] = dchain(["AI proposes", "protocol authorizes",
                   "execution produces evidence",
                   "independent verification evaluates",
                   "gates derive status", "certificate records result"], c=4)
D["L86"] = dchain(["AI proposes", "AI verifies", "AI certifies"], c=4)

# ================================================================ §803
D["L87"] = ["rfl-types"] + [" " * 3 + "+ " + s for s in (
    "rfl-transition", "rfl-ledger", "rfl-evidence", "rfl-gates",
    "one MigrationUnit", "18 adversarial conformance tests")]

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
