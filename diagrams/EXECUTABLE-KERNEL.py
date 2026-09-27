#!/usr/bin/env python3
"""Regenerate every ASCII diagram in EXECUTABLE-KERNEL.md.

    python3 diagrams/EXECUTABLE-KERNEL.py [outdir]   # default /tmp/ekdiag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py EXECUTABLE-KERNEL.md <outdir>

The diagrams in EXECUTABLE-KERNEL.md are NOT verbatim transcriptions: the
pasted source had all of its art collapsed onto single lines, so each diagram
was re-derived. This script is the record of that derivation -- re-running it
and diffing against the committed document proves the diagrams still match.

Six diagrams in this source are laid out with ASCII art (`|`, `v`, `+--`,
`+--------+`) rather than box-drawing glyphs, and several early corpus
documents already do the same. They are reproduced in ASCII on purpose:
auditlib.check_ascii_substitution deliberately only fires when a block mixes
ASCII pipes into an otherwise box-drawing block, so these are in scope.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/ekdiag")
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


def chain(items, c=2, g="\u2193"):
    return dchain(items, c=c, g=g)


def ntree(node, prefix=""):
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


def ascii_flow(items, col, edges=None, labels=None):
    """ASCII-art vertical flow: `|` / `v` at `col`, labels centred on it.

    Used where the source itself used ASCII art. `edges` maps an item index to
    a side-label printed beside the `|`; `labels` maps an index to the text
    printed on the item's own row when it is not a plain label.
    """
    edges = edges or {}
    out = []
    for i, it in enumerate(items):
        out.append(row([(it, cen(len(it), col))]))
        if i == len(items) - 1:
            break
        out.append(marks([(col, "|")]) + edges.get(i, ""))
        out.append(marks([(col, "v")]))
    return out


# ---------------------------------------------------------------- I01-I04
D["I01"] = ["DOMAIN-TYPES.md"]
D["I02"] = ["SnapshotId", "KernelSnapshotId", "TaskId", "AgentId",
            "ArtifactId", "EvidenceId", "ContractId", "GateId",
            "AuthorizationId", "EventId", "", "Digest", "GitObjectId", "",
            "ArchitectureId", "SubsystemId", "ToolchainFingerprint",
            "EnvironmentFingerprint", "", "GateStatus", "VerificationStatus",
            "EvidenceStatus", "ExecutionStatus", "ProcessOutcome"]
D["I03"] = ["SnapshotId", "KernelSnapshotId"]
D["I04"] = ["KernelSnapshotId",
            " " * 4 + "identifies a Linux source snapshot",
            "SnapshotId",
            " " * 4 + "SHOULD NOT exist unless it means something",
            " " * 4 + "materially different from KernelSnapshotId"]

# ---------------------------------------------------------------- I06
D["I06"] = ["Gate", " " * 2 + NEQ + " GateStatus", " " * 2 + NEQ + " GateResult"]

# ---------------------------------------------------------------- I07-I10
S, B1, B2, B3 = 21, 8, 21, 34
D["I07"] = [
    row([("EPOCH", S)]),
    marks([(S, "|")]),
    " " * B1 + "+" + "-" * (B2 - B1 - 1) + "+" + "-" * (B3 - B2 - 1) + "+",
    marks([(B1, "|"), (B2, "|"), (B3, "|")]),
    row([("TASK", B1), ("AUTHORIZATION", B2), ("ARTIFACT", B3)]),
    marks([(B1, "|"), (B2, "|"), (B3, "|")]),
    " " * B1 + "+" + "-" * (B2 - B1 - 1) + "+" + "-" * (B3 - B2 - 1) + "+",
    marks([(S, "|")]),
    row([("EVIDENCE", S)]),
    marks([(S, "|")]),
    row([("GATES", S)]),
    marks([(S, "|")]),
    row([("CERTIFICATE", S)]),
]
D["I08"] = ["artifact.epoch == authorization.epoch",
            "artifact.epoch == task.epoch",
            "evidence.epoch == artifact.epoch",
            "gate.epoch == evidence.epoch"]
D["I09"] = ["REJECT"]
D["I10"] = ["WARNING"]

# ---------------------------------------------------------------- I11-I12
D["I11"] = ntree(("crates/", [("rfl-types/", [
    "Cargo.toml",
    ("src/", ["lib.rs", "ids.rs", "snapshot.rs", "task.rs",
              "authorization.rs", "artifact.rs", "evidence.rs",
              "contract.rs", "verification.rs", "gate.rs",
              "errors.rs"])])]))
D["I12"] = ["No LLM dependency.", "No async runtime.", "No network.",
            "No filesystem authority.", "No agent framework.",
            "No plugin system."]

# ---------------------------------------------------------------- I13-I14
D["I13"] = ntree(("crates/", ["rfl-types/", ("rfl-transition/", [
    "Cargo.toml",
    ("src/", ["lib.rs", "machine.rs", "transition.rs", "preconditions.rs",
              "authorization.rs", "scope.rs", "errors.rs"])])]))
D["I14"] = [
    "Agent",
    "  |",
    "  | TransitionRequest",
    "  v",
    "Protocol Engine",
    "  |",
    "  +-- validate epoch",
    "  +-- validate task",
    "  +-- validate authority",
    "  +-- validate capability",
    "  +-- validate scope",
    "  +-- validate preconditions",
    "  +-- validate artifact",
    "  |",
    "  v",
    "Transition",
]

# ---------------------------------------------------------------- I15-I19
D["I15"] = ["\u03b4 : (State, Request) " + ARROW + " Result"]
D["I16"] = ["Result =", " " * 4 + "Accepted(NewState, Event)",
            " " * 2 + "| Rejected(Reason)"]
D["I17"] = ['Result = "probably okay"']
D["I18"] = ['Result = "LLM believes valid"']
D["I19"] = ['Result = "majority of agents approved"']

# ---------------------------------------------------------------- I20-I23
D["I20"] = [
    "TASK", "CREATED", "   |", "   v", "ADMITTED", "   |", "   v",
    "AUTHORIZED", "   |", "   v", "EXECUTING", "   |", "   +--------+",
    "   |        |", "   v        v", "SUCCEEDED  FAILED", "   |", "   v",
    "VERIFIED", "   |", "   v", "GATED", "   |", "   v", "CERTIFIED",
]
D["I21"] = ["FAILED " + DASH * 2 + "X" + DASH * 2 + "> VERIFIED"]
D["I22"] = ["AUTHORIZED " + DASH * 2 + "X" + DASH * 2 + "> CERTIFIED"]
D["I23"] = ["EXECUTING " + DASH * 2 + "X" + DASH * 2 + "> CERTIFIED"]

# ---------------------------------------------------------------- I24-I38
D["I24"] = ["authorize(epoch=10)", "snapshot changes", "execute(epoch=10)"]
D["I25"] = ["REJECT(STALE_EPOCH)"]
D["I26"] = ["artifact.snapshot = A", "authorization.snapshot = B"]
D["I27"] = ["REJECT(SNAPSHOT_MISMATCH)"]
D["I28"] = groups([("authorized:", ["drivers/net/foo.c"]),
                   ("requested:", ["kernel/sched/core.c"])])
D["I29"] = ["REJECT(SCOPE_VIOLATION)"]
D["I30"] = ["agent produces artifact", "same authority declares:",
            " " * 4 + "artifact verified"]
D["I31"] = ["REJECT(SELF_VERIFICATION)"]
D["I32"] = ["Evidence {", " " * 4 + "claim: PASS",
            " " * 4 + "artifact: nonexistent", "}"]
D["I33"] = ["REJECT(EVIDENCE_NOT_BOUND)"]
D["I34"] = ["execute(operation_id=42)", "execute(operation_id=42)"]
D["I35"] = ["first", " " + "-> ACCEPTED", "second",
            " " + "-> REJECT(DUPLICATE_OPERATION)"]
C = 10
D["I36"] = [
    row([("events[0..N]", C)]),
    marks([(C, "|")]), marks([(C, "v")]),
    row([("replay()", C)]),
    marks([(C, "|")]), marks([(C, "v")]),
    row([("state_A", C)]),
    "",
    row([("original execution", C)]),
    marks([(C, "|")]), marks([(C, "v")]),
    row([("state_B", C)]),
]
D["I37"] = ["state_A == state_B"]
D["I38"] = ["REPLAY_FAILURE"]

# ---------------------------------------------------------------- I39-I40
D["I39"] = chain(["rfl-types", "rfl-transition", "rfl-event-ledger"], c=2)
D["I40"] = ["previous_state_hash", " " * 8 + "+ operation",
            " " * 8 + "+ resulting_state_hash"]

# ---------------------------------------------------------------- I41-I43
D["I41"] = ['"cargo test passed"']
D["I42"] = ntree(("Evidence", [("subject", ["artifact"]), "operation",
                               "command", "environment", "toolchain",
                               "input digest", "output digest",
                               "exit status", "timestamp"]))
D["I43"] = ["EvidenceRecord {", " " * 4 + "subject: ArtifactId,",
            " " * 4 + "source: ExecutionId,",
            " " * 4 + "environment: EnvironmentFingerprint,",
            " " * 4 + "toolchain: ToolchainFingerprint,",
            " " * 4 + "input_digest: Digest,",
            " " * 4 + "output_digest: Digest,",
            " " * 4 + "outcome: PASS,", "}"]

# ---------------------------------------------------------------- I44-I48
D["I44"] = ["RELEASE_ELIGIBLE"]
D["I45"] = ["acceptable upstream patch"]
D["I46"] = groups([("TechnicalCertification",
                    ["UNVERIFIED", "VERIFIED", "INVALIDATED"])])
D["I47"] = groups([("UpstreamAcceptanceState",
                    ["NOT_SUBMITTED", "UNDER_REVIEW", "REVIEWED", "ACCEPTED",
                     "REJECTED", "SUPERSEDED"])])
D["I48"] = ["VERIFIED", " " * 8 + "= UPSTREAM_ACCEPTED"]

# ---------------------------------------------------------------- I49-I50
D["I49"] = ntree(("linux/", [
    ("subsystems/", ["scheduler.yaml", "memory.yaml", "rcu.yaml",
                     "workqueue.yaml", "vfs.yaml", "block.yaml",
                     "networking.yaml", "..."]),
    "architectures/", "toolchains/", "configurations/", "verification/",
    "maintainers/"]))
D["I50"] = [
    "id: scheduler",
    "family: core",
    "source_paths:",
    "  - kernel/sched/",
    "semantic_domains:",
    "  - tasks",
    "  - scheduling",
    "  - locking",
    "  - cpu-topology",
    "migration_class:",
    "  - semantic_reconstruction",
    "  - unsafe_boundary",
    "  - concurrency_sensitive",
    "verification_backends:",
    "  - compile",
    "  - kunit",
    "  - lockdep",
    "  - kasan",
    "  - kcsan",
    "  - runtime",
    "  - differential",
    "maintainer_authority:",
    "  required: true",
]

# ---------------------------------------------------------------- I51-I53
A, A1, A2, A3 = 27, 8, 27, 46
_fork = (" " * A1 + "+" + "-" * (A2 - A1 - 1) + "+"
         + "-" * (A3 - A2 - 1) + "+")
D["I51"] = [
    row([("HUMAN / MAINTAINER", A)]),
    marks([(A, "|")]),
    row([("POLICY AUTHORITY", A)]),
    marks([(A, "|")]),
    row([("RFL-AE PROTOCOL", A)]),
    marks([(A, "|")]),
    _fork,
    marks([(A1, "|"), (A2, "|"), (A3, "|")]),
    row([("RECONSTRUCTION", A1), ("DESIGN", A2), ("VERIFICATION", A3)]),
    row([("AGENTS", A1), ("AGENTS", A2), ("AGENTS", A3)]),
    marks([(A1, "|"), (A2, "|"), (A3, "|")]),
    _fork,
    marks([(A, "|")]),
    row([("ARTIFACT STORE", A)]),
    marks([(A, "|")]),
    row([("EVIDENCE LEDGER", A)]),
    marks([(A, "|")]),
    row([("GATE ENGINE", A)]),
    marks([(A, "|")]),
    row([("TECHNICAL CERTIFICATE", A)]),
    marks([(A, "|")]),
    row([("UPSTREAM REVIEW STATE", A)]),
]
D["I52"] = ["BAD:", "LLM", " |", " v", "code", " |", " v", "tests", " |",
            " v", '"verified"']
D["I53"] = ["GOOD:", "LLM", " |", " | proposal", " v", "RFL-AE", " |",
            " | authorized operation", " v", "artifact", " |", " v",
            "independent execution", " |", " v", "evidence", " |", " v",
            "gate engine", " |", " v", "certificate"]

# ---------------------------------------------------------------- I54-I56
D["I54"] = ["1 protocol engine", "1 event ledger", "1 evidence engine",
            "1 gate engine", "0 autonomous mutation agents"]
D["I55"] = ["determinism", "replay", "authorization", "scope",
            "epoch isolation", "evidence binding", "gate semantics"]
D["I56"] = ["Agent-1: C semantic reconstruction", "Agent-2: Rust design",
            "Agent-3: implementation", "Agent-4: verification",
            "Agent-5: adversarial review"]

# ---------------------------------------------------------------- I57-I58
_phases = [
    ("PHASE 0", "Freeze", ["DOMAIN-TYPES.md", "GateStatus", "SnapshotId",
                           "authority vocabulary"]),
    ("PHASE 1", "rfl-types", ["canonical Rust domain model"]),
    ("PHASE 2", "rfl-transition", ["deterministic state machine"]),
    ("PHASE 3", "rfl-event-ledger", ["append-only events",
                                     "deterministic replay"]),
    ("PHASE 4", "rfl-evidence", ["execution/evidence binding"]),
    ("PHASE 5", "rfl-gates", ["PASS/FAIL/BLOCKED/INVALIDATED"]),
    ("PHASE 6", "conformance", ["adversarial negative suite"]),
    ("PHASE 7", "CI", ["authoritative execution"]),
    ("PHASE 8", "Linux manifests",
     ["subsystem/config/arch/toolchain model"]),
    ("PHASE 9", "agents", ["proposal-only first"]),
    ("PHASE 10", "controlled execution", ["capability-granted mutation"]),
    ("PHASE 11", "kernel reconstruction", ["subsystem by subsystem"]),
]
D["I57"] = [l for tag, name, kids in _phases
            for l in [f"{tag.ljust(8)} " + DASH + " " + name]
            + [" " * 10 + k for k in kids]]
D["I58"] = [
    "[ ] all referenced domain types defined",
    "[ ] no undefined GateStatus",
    "[ ] no undefined SnapshotId",
    "[ ] transition relation executable",
    "[ ] illegal transitions rejected",
    "[ ] authorization is epoch-bound",
    "[ ] artifacts are epoch-bound",
    "[ ] scope enforcement executable",
    "[ ] duplicate operations rejected",
    "[ ] replay deterministic",
    "[ ] evidence bound to execution",
    "[ ] self-verification rejected",
    "[ ] gate state machine executable",
    "[ ] negative tests exist",
    "[ ] CI executes the authoritative suite",
    "[ ] execution evidence is persisted",
    "[ ] release certificate derives from evidence",
]

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
