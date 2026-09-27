#!/usr/bin/env python3
"""Regenerate every ASCII diagram in PROTOCOL-V01.md.

    python3 diagrams/PROTOCOL-V01.py [outdir]      # default /tmp/pv01diag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py PROTOCOL-V01.md <outdir>

The diagrams in PROTOCOL-V01.md are NOT verbatim transcriptions: the pasted
source had all of its art collapsed onto single lines, so each diagram was
re-derived. This script is the record of that derivation -- re-running it and
diffing against the committed document proves the diagrams still match.

Glyph note. The source's maintainer-authority diagram (§743) used box-drawing
characters for its two forks but ASCII `|` for its spines. That mix is exactly
what auditlib.check_ascii_substitution is written to catch -- an ASCII pipe
inside an otherwise box-drawing block is how a single wrong glyph silently
breaks a spine -- so the spines are normalised to `│` here. The ASCII `v`
arrowheads are kept, because the §718 domain-model diagram already uses that
combination and `v` is not in the rule's scope.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/pv01diag")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import (VERT, DOWN, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
                 TEE_D, TEE_U, CROSS, HORIZ, row, marks, bar,
                 dchain)  # noqa: E402

D = {}
BR, TR = "\u2514", "\u251c"      # └ ├
DASH = HORIZ                     # ─
NEQ = "\u2260"                   # ≠
ARROW = "\u2192"                 # →
def chain(items, c=2, g="\u2193"):
    return dchain(items, c=c, g=g)


def ntree(node, prefix=""):
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


def aflow(labels, col=2, items=None):
    """ASCII flow: `|` / `v` at `col` between labels at column 0."""
    out = [labels[0]]
    for l in labels[1:]:
        out += [marks([(col, "|")]), marks([(col, "v")]), l]
    return out


def alist(root, kids, col=2, arrow="+--"):
    """ASCII list: `+-- item` at `col` under a root, spine at `col`."""
    out = [root, marks([(col, "|")])]
    for k in kids:
        out.append(" " * col + arrow + " " + k)
    return out


# ---------------------------------------------------------------- J01
# The canonical domain model. Box glyphs with ASCII `v` arrowheads, as the
# source had it; verified against the box-width and orphan rules.
S = 31
B1, B2, B3 = 14, 32, 50
R1, R2 = 20, 42
J01 = []
for lbl in ("KernelSnapshot", "Epoch"):
    J01.append(" " * 20 + CORNER_TL + DASH * 22 + CORNER_TR)
    J01.append(" " * 20 + VERT + lbl.center(22) + VERT)
    J01.append(" " * 20 + CORNER_BL + DASH * 10 + TEE_D + DASH * 11 + CORNER_BR)
    if lbl == "KernelSnapshot":
        J01 += [marks([(S, VERT)]), marks([(S, "v")])]
J01.append(marks([(S, VERT)]))
_fan = (" " * B1 + CORNER_TL + DASH * (B2 - B1 - 1) + CROSS
        + DASH * (B3 - B2 - 1) + CORNER_TR)
J01.append(_fan)
J01.append(marks([(B1, VERT), (B2, VERT), (B3, VERT)]))
J01.append(marks([(B1, "v"), (B2, "v"), (B3, "v")]))
J01.append(row([("Task", B1), ("Contract", B2), ("Capability", B3)]))
J01.append(marks([(B1, VERT), (B2, VERT), (B3, VERT)]))
J01.append(" " * B1 + CORNER_BL + DASH * (B2 - B1 - 1) + CROSS
           + DASH * (B3 - B2 - 1) + CORNER_BR)
for lbl in ("Authorization", "OperationRequest", "TransitionEngine"):
    J01.append(marks([(S, "v")]))
    J01.append(row([(lbl, S)]))
    J01.append(marks([(S, VERT)]))
# The tee sits on the spine S; the two branches are R1 (Reject) and R2
# (Accept). The accept branch then continues downward on R2.
J01.append(" " * R1 + CORNER_TL + DASH * (S - R1 - 1) + TEE_U
           + DASH * (R2 - S - 1) + CORNER_TR)
J01.append(marks([(R1, VERT), (R2, VERT)]))
J01.append(row([("Reject", R1), ("Accept", R2)]))
J01.append(marks([(R1, VERT), (R2, VERT)]))
J01.append(marks([(R1, "v"), (R2, "v")]))
J01.append(row([("Reason", R1), ("Event", R2)]))
for lbl in ("Artifact/Evidence", "Gates", "Certificate"):
    J01.append(marks([(R2, VERT)]))
    J01.append(marks([(R2, "v")]))
    J01.append(row([(lbl, R2)]))
D["J01"] = J01

# ---------------------------------------------------------------- J02-J10
D["J02"] = ["String"]
D["J03"] = ["ArtifactId"]
D["J04"] = ["TaskId"]
D["J05"] = ["SnapshotId"]
D["J06"] = ["pub struct TaskId(pub Uuid);", "pub struct AgentId(pub Uuid);",
            "pub struct ArtifactId(pub Uuid);",
            "pub struct EvidenceId(pub Uuid);",
            "pub struct ContractId(pub Uuid);", "pub struct GateId(pub Uuid);",
            "pub struct AuthorizationId(pub Uuid);",
            "pub struct EventId(pub Uuid);"]
D["J07"] = ["pub struct ProtocolSnapshotId(...);"]
D["J08"] = ["KernelSnapshotId != ProtocolSnapshotId"]
D["J09"] = ["pub fn same_epoch(a: &Epoch, b: &Epoch) -> bool;"]
D["J10"] = ["same_epoch(a,b)",
            " " * 4 + "iff a.kernel       == b.kernel",
            " " * 6 + "&& a.specification == b.specification",
            " " * 6 + "&& a.protocol      == b.protocol",
            " " * 6 + "&& a.generation   == b.generation"]

# ---------------------------------------------------------------- J11-J19
D["J11"] = ["kernel/sched/"]
D["J12"] = ["kernel/sched/core.c"]
D["J13"] = ["contains(scope, target)"]
D["J14"] = ["authorized:", " " * 4 + "subsystem=scheduler",
            "requested:", " " * 4 + "kernel/sched/core.c",
            " " * 3 + "=> ACCEPT"]
D["J15"] = ["authorized:", " " * 4 + "subsystem=scheduler",
            "requested:", " " * 4 + "fs/open.c",
            " " * 3 + "=> REJECT(SCOPE_VIOLATION)"]
D["J16"] = ["what an actor is potentially allowed to do"]
D["J17"] = ["whether that actor is authorized to perform this specific"
            " operation at this epoch, on this target, within this scope."]
D["J18"] = ['"I have write capability"']
D["J19"] = ['"I may modify anything."']

# ---------------------------------------------------------------- J20-J25
D["J20"] = ["ShellCommand"]
D["J21"] = ['"Please modify scheduler code."']
D["J22"] = ["natural-language instruction"]
D["J23"] = ["maybe probably needs LLM judgment"]
D["J24"] = ["BLOCKED"]
D["J25"] = ["FAIL"]

# ---------------------------------------------------------------- J26-J33
D["J26"] = ["Created   -> Admitted", "Admitted   -> Authorized",
            "Authorized   -> Executing", "Executing   -> Succeeded",
            "  -> Failed", "Succeeded   -> Verified", "Verified   -> Gated",
            "Gated   -> Certified"]
D["J27"] = ["Created -> Certified"]
D["J28"] = ["InvalidTransition"]
D["J29"] = ["Failed -> Executing"]
D["J30"] = ["TaskAttempt"]
D["J31"] = ["Task"]
D["J32"] = ["Task", marks([(1, "|")]),
            " +-- Attempt 1 -> FAILED", marks([(1, "|")]),
            " +-- Attempt 2 -> EXECUTING", marks([(1, "|")]),
            " +-- Attempt 3 -> SUCCEEDED"]
D["J33"] = ["Task", " " * 4 + "!=", "TaskAttempt"]

# ---------------------------------------------------------------- J34-J37
D["J34"] = ["0 1 2 3 ..."]
D["J35"] = ["pub previous_event: Option<EventId>,", "pub event_digest: Digest,"]
D["J36"] = ["E0", marks([(1, "|")]), marks([(1, "v")]), "E1",
            marks([(1, "|")]), marks([(1, "v")]), "E2",
            marks([(1, "|")]), marks([(1, "v")]), "E3"]
D["J37"] = ["replay(events) == authoritative_state"]

# ---------------------------------------------------------------- J38-J40
C = 9
D["J38"] = [row([("execute(requests)", C)]), marks([(C, "|")]),
            marks([(C, "v")]), row([("events", C)]),
            row([("replay(events)", C)]), marks([(C, "|")]),
            marks([(C, "v")]), row([("state'", C)]), "",
            "state' == execution_state"]
D["J39"] = aflow(["operation", "execution authority", "raw result",
                  "EvidenceRecord"], col=4)
D["J40"] = alist("agent", ["code", '"tests passed"'], col=1, arrow="+-->")

# ---------------------------------------------------------------- J41-J50
D["J41"] = ["EvidenceOutcome::Passed"]
D["J42"] = ["Artifact::Verified"]
D["J43"] = ["Verify(Artifact, Contract, EvidenceSet)",
            " " * 8 + "-> VerificationResult"]
D["J44"] = ["one test passed", " " * 6 + "= verified"]
D["J45"] = ["SemanticContract", "SafetyContract", "ConcurrencyContract",
            "ABIContract", "BuildContract", "RuntimeContract",
            "CompatibilityContract", "PerformanceContract",
            "MigrationContract"]
D["J46"] = ["scheduler/core.c"]
D["J47"] = groups([("Semantic:", ["scheduling decisions preserved"]),
                   ("Concurrency:", ["lock ordering preserved"]),
                   ("Safety:", ["ownership/lifetime invariants preserved"]),
                   ("ABI:", ["exported interfaces preserved"]),
                   ("Runtime:",
                    ["scheduler behavior valid under test matrix"])])
D["J48"] = ["PASS  != NOT_APPLICABLE", "FAIL  != BLOCKED",
            "BLOCKED  != PASS", "INVALIDATED  != FAIL"]
D["J49"] = ["BLOCKED"]
D["J50"] = ["FAIL"]

# ---------------------------------------------------------------- J51-J54
D["J51"] = ["Certificate", " " * 4 + "=", " " * 4 + "Derive(",
            " " * 8 + "Artifact,", " " * 8 + "Contracts,",
            " " * 8 + "Evidence,", " " * 8 + "Verification,",
            " " * 8 + "Gates", " " * 4 + ")"]
D["J52"] = ['Agent says "CERTIFIED"']
D["J53"] = ["RELEASE_ELIGIBLE(a, e)"]
D["J54"] = ["epoch_valid(a,e)", "AND scope_valid(a)",
            "AND contracts_satisfied(a)", "AND verification_satisfied(a)",
            "AND all_required_gates_pass(a)", "AND no_required_gate_blocked(a)",
            "AND no_required_gate_failed(a)", "AND no_dependency_invalidated(a)",
            "AND evidence_complete(a)", "AND replay_valid(a)"]

# ---------------------------------------------------------------- J55-J58
D["J55"] = aflow(["Agent", "Proposal", "Protocol validation",
                  "OperationRequest", "Authorization", "Execution"], col=2)
D["J56"] = ["git commit", "git push", "rm", "cargo publish"]
D["J57"] = ntree(("RFL-AE/", ["ARCHITECTURE.md", "SPECIFICATION.md", "...",
                              "VERIFICATION.md", "GATES.md", "EXECUTION.md",
                              "ORCHESTRATION.md", "skills/"]))
D["J58"] = ntree(("RFL-AE/", [
    ("docs/", ["ARCHITECTURE.md", "SPECIFICATION.md", "FORMAL-CORE.md",
               "PROTOCOL.md", "RUST-CORE.md", "TRANSITIONS.md", "KSIR.md",
               "RECONSTRUCTION.md", "CONTRACTS.md", "DESIGN-IR.md",
               "VERIFICATION.md", "GATES.md", "EXECUTION.md",
               "ORCHESTRATION.md"]),
    ("crates/", ["rfl-types/", "rfl-transition/", "rfl-ledger/",
                 "rfl-evidence/", "rfl-verification/", "rfl-gates/"]),
    ("schemas/", ["epoch.schema.json", "task.schema.json",
                  "authorization.schema.json", "artifact.schema.json",
                  "evidence.schema.json", "verification.schema.json",
                  "gate.schema.json", "certificate.schema.json"]),
    ("linux/", ["subsystems/", "architectures/", "configurations/",
                "toolchains/", "verification/", "maintainers/"]),
    ("conformance/", ["positive/", "negative/", "replay/", "authorization/",
                      "adversarial/"]),
    "skills/",
    (".github/", ["workflows/"]),
]))

# ---------------------------------------------------------------- J59-J61
D["J59"] = alist("RFL-AE", ["rustc", "rustfmt", "clippy", "rustdoc/rusttest",
                            "KUnit", "kselftest", "KASAN", "KCSAN", "lockdep",
                            "build matrix", "architecture matrix",
                            "runtime/differential tests"], col=2)
D["J60"] = groups([("RFL-AE knows", ["WHAT evidence means"]),
                   ("Linux tools determine",
                    ["WHETHER the underlying test actually passed"])])

# The two-plane diagram. Spines normalised from ASCII `|` to `│`; the forks
# keep the source's box-drawing characters and the arrowheads stay ASCII `v`.
P = 20
P1, P2 = 7, 33
_pf = (" " * P1 + CORNER_TL + DASH * (P - P1 - 1) + TEE_U
       + DASH * (P2 - P - 1) + CORNER_TR)
_pb = (" " * P1 + CORNER_BL + DASH * (P - P1 - 1) + TEE_D
       + DASH * (P2 - P - 1) + CORNER_BR)
D["J61"] = [
    row([("TECHNICAL PLANE", P)]),
    marks([(P, VERT)]),
    _pf,
    marks([(P1, VERT), (P2, VERT)]),
    row([("Verification", P1), ("Gates", P2)]),
    marks([(P1, VERT), (P2, VERT)]),
    _pb,
    marks([(P, VERT)]),
    row([("Technical Certificate", P)]),
    marks([(P, VERT)]),
    marks([(P, "v")]),
    row([("REVIEW / GOVERNANCE", P)]),
    marks([(P, VERT)]),
    _pf,
    marks([(P1, VERT), (P2, VERT)]),
    # "subsystem maintainer" is 20 wide, wider than 2*P1; the source lets it
    # start left of the spine, so centre it on 11 (start col 1) rather than P1.
    row([("subsystem maintainer", 11), ("Rust maintainer", P2)]),
    marks([(P1, VERT), (P2, VERT)]),
    _pb,
    marks([(P, VERT)]),
    row([("Upstream State", P)]),
]

# ---------------------------------------------------------------- J62-J63
D["J62"] = (["C source", marks([(2, "|")]), marks([(2, "v")]),
             "C semantic evidence", marks([(2, "|")])]
            + ["  +-- " + k for k in
               ("types", "ownership", "lifetime", "aliasing", "locking",
                "interrupt context", "RCU context", "allocation context",
                "error behavior", "ABI", "initialization", "teardown",
                "concurrency")]
            + [marks([(2, "|")]), marks([(2, "v")]), "Semantic Contract",
               marks([(2, "|")]), marks([(2, "v")]), "Rust Design IR",
               marks([(2, "|")]), marks([(2, "v")]), "Rust implementation"])
D["J63"] = ["technically verified", " " * 8 + "= socially/upstream accepted"]

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
