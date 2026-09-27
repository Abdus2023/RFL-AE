#!/usr/bin/env python3
"""Regenerate every ASCII diagram in SEMANTIC-LAYER.md.

    python3 diagrams/SEMANTIC-LAYER.py [outdir]    # default /tmp/sldiag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py SEMANTIC-LAYER.md <outdir>

The diagrams in SEMANTIC-LAYER.md are NOT verbatim transcriptions: the pasted
source had all of its art collapsed onto single lines, so each diagram was
re-derived. This script is the record of that derivation -- re-running it and
diffing against the committed document proves the diagrams still match.

Glyph note. Diagrams that arrive in the source as box-drawing art stay
box-drawing (the preamble pipeline, the provenance graph, the agent fan-out,
the compilation pipeline, the two-evidence chain and the maturity boundary);
those that arrive as ASCII art (`|`, `v`, `+--`) stay ASCII, matching the
established corpus pattern. No block mixes an ASCII `|` with box glyphs.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/sldiag")
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
DWN = "\u2193"                   # ↓


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


def atree(node, prefix=""):
    """Same as ntree but with ASCII glyphs."""
    label, kids = node
    out = [prefix + label]
    for i, k in enumerate(kids):
        last = i == len(kids) - 1
        conn = "+--" if not last else "+--"
        if isinstance(k, str):
            out.append(prefix + conn + " " + k)
        else:
            out.append(prefix + conn + " " + k[0])
            out += atree(("", k[1]), prefix + ("    " if last else "|   "))[1:]
    return out


def groups(items, indent=4):
    out = []
    for name, lines in items:
        out.append(name)
        out += [" " * indent + l for l in lines]
    return out


def bchain(items, c=4):
    """Box-drawing vertical chain: labels at column 0, │/▼ at column c.

    Labels are NOT centred on the spine -- the source keeps them flush left
    and runs the spine down beside them, which is also the only layout that
    works when a label is wider than twice the spine column.
    """
    out = [items[0]]
    for it in items[1:]:
        out += [marks([(c, VERT)]), marks([(c, DOWN)]), it]
    return out


def achain(items, c=4):
    """ASCII vertical chain with | / v at column c, labels at column 0."""
    out = [items[0]]
    for it in items[1:]:
        out += [marks([(c, "|")]), marks([(c, "v")]), it]
    return out


def alist(root, kids, col=4):
    out = [root]
    for k in kids:
        out.append(" " * col + "+-- " + k)
    return out


def one(s):
    return [s]


# ---------------------------------------------------------------- K01
D["K01"] = bchain(["C source", "Observed program facts",
                   "Semantic Reconstruction", "Kernel Semantic IR (KSIR)",
                   "Contracts", "Rust Design IR", "Rust implementation",
                   "Independent verification"], c=10)

# ---------------------------------------------------------------- K02-K06
D["K03"] = one('"What is the Rust equivalent?"')
D["K04"] = one("What does foo mean?")
D["K05"] = bchain(["C Artifact", "Observable Facts",
                   "Control/Data/Concurrency Analysis", "Semantic Claims",
                   "Contracts", "Rust Design"], c=4)
D["K06"] = [
    "C semantics",
    " " * 7 + "|",
    " " * 7 + "+--------------------+",
    " " * 7 + "|                    |",
    " " * 7 + "v                    v",
    # "Semantic Contract" is flush left; "Evidence" sits under the right `v`.
    "Semantic Contract".ljust(24) + "Evidence",
    " " * 7 + "|",
    " " * 7 + "v",
    "Rust Design",
]

# ---------------------------------------------------------------- K07
D["K07"] = ntree(("crates/", [("rfl-ksir/", [("src/", [
    "lib.rs", "function.rs", "type.rs", "memory.rs", "concurrency.rs",
    "control.rs", "abi.rs", "lifecycle.rs", "provenance.rs"])])]))

# ---------------------------------------------------------------- K08-K10
D["K08"] = one("evidence")
D["K09"] = groups([("Invariant:", ['"lock L protects field x"']),
                   ("Evidence:", ["source locations", "call graph",
                                  "lock annotations", "runtime observations",
                                  "static analysis"])])
D["K10"] = one('"lock L protects x"')

# ---------------------------------------------------------------- K11-K15
D["K11"] = groups([("Observed:", ["function A calls spin_lock(&L)"])])
D["K12"] = groups([("Derived:",
                    ["execution of A enters a region protected by L"])])
D["K13"] = groups([("Hypothesis:", ["all accesses to field x require L"])])
D["K14"] = groups([("Verified:",
                    ["the invariant has sufficient independent evidence"])])
D["K15"] = ["OBSERVED", " " * 4 + NEQ + " DERIVED",
            " " * 4 + NEQ + " HYPOTHESIS", " " * 4 + NEQ + " VERIFIED"]

# ---------------------------------------------------------------- K16
P = 17
D["K16"] = [
    row([("SOURCE", P)]),
    marks([(P, VERT)]), marks([(P, DOWN)]),
    row([("OBSERVATION", P)]),
    marks([(P, VERT)]),
    " " * 11 + CORNER_TL + DASH * 5 + TEE_U + DASH * 5 + CORNER_TR,
    marks([(11, DOWN), (23, DOWN)]),
    row([("DERIVATION", 11), ("DERIVATION", 23)]),
    marks([(11, VERT), (23, VERT)]),
    " " * 11 + CORNER_BL + DASH * 5 + TEE_D + DASH * 5 + CORNER_BR,
    marks([(P, DOWN)]),
    row([("CLAIM", P)]),
    marks([(P, VERT)]), marks([(P, DOWN)]),
    row([("CONTRACT", P)]),
    marks([(P, VERT)]), marks([(P, DOWN)]),
    row([("VERIFICATION", P)]),
]

# ---------------------------------------------------------------- K17-K19
D["K17"] = [f"{i}. {n}" for i, n in enumerate(
    ["Type", "Memory", "Ownership", "Lifetime", "Aliasing", "Initialization",
     "Destruction", "Concurrency", "Locking", "RCU", "Interrupt context",
     "Process context", "Allocation context", "Error behavior",
     "Control flow", "Data flow", "ABI", "Calling convention",
     "Side effects", "Global state", "CPU locality", "Preemption",
     "Atomicity", "Ordering", "Synchronization", "Configuration",
     "Architecture dependencies", "Generated code", "Macro behavior",
     "External subsystem dependencies"], start=1)]
D["K18"] = one("NOT_OBSERVED")
D["K19"] = one("false")

# ---------------------------------------------------------------- K20-K24
D["K20"] = one("foo()")
D["K21"] = one("process context")
D["K22"] = one("sleep")
D["K23"] = ["atomic context", "interrupt context"]
D["K24"] = one("Interrupt + RCU read-side + preemption constraints")

# ---------------------------------------------------------------- K25-K27
D["K25"] = one('"there is a lock here."')
D["K26"] = ntree(("Lock L", [
    ("protects:", ["field x", "field y"]),
    ("acquired:", ["function A", "function B"]),
    ("released:", ["function A", "function B"]),
    ("ordering:", ["L1 -> L2"]),
    ("context:", ["process / atomic / ..."]),
]))
D["K27"] = ["Mutex", "SpinLock", "RwLock", "raw lock abstraction", "guard",
            "atomic", "RCU primitive"]

# ---------------------------------------------------------------- K28-K31
D["K28"] = bchain(["caller allocates", "callee stores pointer",
                   "asynchronous worker consumes it", "worker releases it"],
                  c=4)
D["K29"] = one('"this pointer has transferred ownership."')
D["K30"] = bchain(["Object O  CREATE", "OWNED(A)", "TRANSFER", "OWNED(B)",
                   "RELEASE", "DESTROYED"], c=4)
D["K31"] = ["Box", "Arc", "Rc", "Pin", "&mut T", "&T",
            "kernel-specific ownership wrapper"]

# ---------------------------------------------------------------- K32-K33
D["K32"] = atree(("Object", ["created at A", "published at B",
                             "consumed by worker C",
                             "removed from lookup at D", "grace period E",
                             "freed at F"]))
D["K33"] = ["RCU", "refcounting", "workqueues", "timers", "callbacks",
            "interrupt handlers"]

# ---------------------------------------------------------------- K34-K36
D["K34"] = groups([("LOCK", ["protects concurrent mutation"]),
                   ("RCU", ["protects access/lifetime under"
                            " grace-period semantics"])])
D["K35"] = ["RCU read-side critical section", "RCU publication",
            "RCU replacement", "RCU retirement",
            "grace-period synchronization", "post-grace reclamation"]
D["K36"] = [f"C pointer", " " * 4 + ARROW + " Rust reference"]

# ---------------------------------------------------------------- K37-K39
D["K37"] = groups([("init(A)", ["requires:", " " * 4 + "B initialized"]),
                   ("init(C)", ["requires:", " " * 4 + "A initialized"])])
D["K38"] = bchain(["B", "A", "C"], c=0)
D["K39"] = one("C before A")

# ---------------------------------------------------------------- K40-K42
D["K40"] = bchain(["register", "publish", "operate", "quiesce", "unregister",
                   "flush", "free"], c=4)
D["K41"] = groups([("Drop(X)", ["requires:", " " * 4 + "workers stopped",
                                " " * 4 + "callbacks quiesced",
                                " " * 4 + "references released",
                                " " * 4 + "publication removed"])])
D["K42"] = achain(["C ABI", "ABI Contract", "Rust ABI Design"], c=4)

# ---------------------------------------------------------------- K43-K45
D["K43"] = groups([("CONFIG_A", ["enables X"]),
                   ("CONFIG_B", ["changes implementation Y"]),
                   ("CONFIG_A && CONFIG_B", ["activates Z"])])
D["K44"] = one("behavior proven under CONFIG_X")
D["K45"] = one("behavior proven for all configurations")

# ---------------------------------------------------------------- K46-K50
D["K46"] = ["x86", "ARM64", "RISC-V", "..."]
D["K47"] = atree(("SemanticContract", ["universal", "architecture-specific"]))
D["K48"] = one('"this operation is safe"')
D["K49"] = ["ARCH = x86_64", "CONFIG = ...", "TOOLCHAIN = ..."]
D["K50"] = ["written source", "generated source", "macro expansion",
            "compiler-generated behavior", "architecture-generated behavior"]

# ---------------------------------------------------------------- K51-K52
D["K51"] = ["Agent 1", "Agent 2", "Agent 3"]
A = 31
A1, A2, A3 = 7, 31, 55
_af = (" " * A1 + "+" + "-" * (A2 - A1 - 1) + "+" + "-" * (A3 - A2 - 1) + "+")
D["K52"] = [
    row([("Reconstruction Coordinator", A)]),
    marks([(A, "|")]),
    _af,
    marks([(A1, "|"), (A2, "|"), (A3, "|")]),
    marks([(A1, "v"), (A2, "v"), (A3, "v")]),
    row([("Control/Data", A1), ("Memory/Lifetime", A2), ("Concurrency", A3)]),
    row([("Analyzer", A1), ("Analyzer", A2), ("Analyzer", A3)]),
    marks([(A1, "|"), (A2, "|"), (A3, "|")]),
    _af,
    marks([(A, "|")]),
    marks([(A, "v")]),
    row([("ABI Analyzer", A)]),
    marks([(A, "|")]), marks([(A, "v")]),
    row([("Configuration Analyzer", A)]),
    marks([(A, "|")]), marks([(A, "v")]),
    row([("Contract Synthesizer", A)]),
]

# ---------------------------------------------------------------- K53-K61
D["K54"] = groups([("O1:", ["foo->value is written while lock is held."])])
D["K55"] = one("source = foo.c:L100-L102")
D["K56"] = groups([("D1:", ["lock(foo->lock) protects this write."])])
D["K57"] = groups([("C1:", ["writes to foo->value require foo->lock."])])
D["K58"] = ["all writes to foo->value", "all reads of foo->value",
            "all paths acquiring foo->lock", "all paths accessing foo->value"]
D["K59"] = one("foo->value++;")
D["K60"] = one("C1")
D["K61"] = one("CONFLICT")

# ---------------------------------------------------------------- K62-K63
D["K62"] = ["Conflict", " " * 4 + NEQ + " Failure"]
D["K63"] = ["unresolved critical conflict",
            " " * 8 + ARROW + " release blocked"]

# ---------------------------------------------------------------- K64-K67
D["K64"] = ["Agent A: lock protects x", "Agent B: lock protects x",
            "Agent C: lock does not protect x"]
D["K65"] = one("2 vs 1")
D["K66"] = achain(["Claims", "Evidence", "Analysis", "Verification"], c=4)
D["K67"] = one("UNKNOWN / CONFLICT")

# ---------------------------------------------------------------- K68-K70
D["K68"] = one("confidence = 0.97")
D["K69"] = ["score > 0.95", " " * 4 + ARROW + " Verified"]
D["K70"] = one("Verified")

# ---------------------------------------------------------------- K71-K72
D["K71"] = achain(["KSIR", "Contract IR", "Design IR"], c=4)
D["K72"] = one("unsafe_obligations")

# ---------------------------------------------------------------- K73-K74
D["K74"] = (["unsafe block", marks([(4, "|")]), marks([(4, "v")]),
             "UnsafeObligation", marks([(4, "|")])]
            + [" " * 4 + "+-- " + k for k in
               ("invariant 1", "invariant 2", "invariant 3")]
            + [marks([(4, "|")]), marks([(4, "v")]), "verification"])

# ---------------------------------------------------------------- K75
S = 23
B = 14
W = 19
_boxes = [
    ("Source Evidence", None),
    ("KSIR", ["control", "data", "memory", "lifetime", "ownership",
              "locking", "RCU", "context", "ABI", "config", "architecture"]),
    ("Contract Model", None),
]
K75 = [row([("LINUX C", S)]), marks([(S, VERT)]), marks([(S, DOWN)])]
for title, body in _boxes:
    K75.append(" " * B + CORNER_TL + DASH * W + CORNER_TR)
    inner = [title] + (body or [""])
    for t in inner:
        K75.append(" " * B + VERT + " " + t.ljust(W - 2) + " " + VERT)
    K75.append(" " * B + CORNER_BL + DASH * 8 + TEE_D + DASH * (W - 9)
               + CORNER_BR)
    if title == "Contract Model":
        K75.append(marks([(S, VERT)]))
        K75.append(row([("contract verified", S)]))
    K75.append(marks([(S, VERT)]))
    K75.append(marks([(S, DOWN)]))
K75.append(row([("Rust Design IR", S)]))
K75.append(marks([(S, VERT)]))
K75.append(marks([(S, DOWN)]))
K75.append(" " * B + CORNER_TL + DASH * W + CORNER_TR)
K75.append(" " * B + VERT + " Rust Generator ".ljust(W) + VERT)
K75.append(" " * B + CORNER_BL + DASH * 8 + TEE_D + DASH * (W - 9)
           + CORNER_BR)
K75.append(marks([(S, VERT)]))
K75.append(marks([(S, DOWN)]))
K75.append(row([("Rust artifact", S)]))
K75.append(marks([(S, VERT)]))
F1, F3 = 10, 36
K75.append(" " * F1 + CORNER_TL + DASH * (S - F1 - 1) + CROSS
           + DASH * (F3 - S - 1) + CORNER_TR)
K75.append(marks([(F1, VERT), (S, VERT), (F3, VERT)]))
K75.append(marks([(F1, DOWN), (S, DOWN), (F3, DOWN)]))
K75.append(row([("compile", F1), ("KUnit", S), ("runtime", F3)]))
K75.append(marks([(F1, VERT), (S, VERT), (F3, VERT)]))
K75.append(" " * F1 + CORNER_BL + DASH * (S - F1 - 1) + TEE_D
           + DASH * (F3 - S - 1) + CORNER_BR)
K75.append(marks([(S, DOWN)]))
K75.append(row([("Evidence", S)]))
K75.append(marks([(S, VERT)]))
K75.append(marks([(S, DOWN)]))
K75.append(row([("Verification", S)]))
K75.append(marks([(S, VERT)]))
K75.append(marks([(S, DOWN)]))
K75.append(row([("Gates", S)]))
K75.append(marks([(S, VERT)]))
K75.append(marks([(S, DOWN)]))
K75.append(row([("Certificate", S)]))
D["K75"] = K75

# ---------------------------------------------------------------- K76-K81
D["K76"] = ["RustArtifact", " " * 4 + "cannot become Certified"]
D["K77"] = bchain(["RustArtifact", "RustDesign", "SemanticContract", "KSIR",
                   "SourceEvidence"], c=4)
D["K78"] = bchain(["RustArtifact", "Execution", "Evidence", "Verification",
                   "Gates"], c=4)
D["K79"] = bchain(["SOURCE SEMANTICS", "KSIR", "CONTRACT", "RUST DESIGN",
                   "RUST ARTIFACT", "EXECUTION EVIDENCE", "VERIFICATION"],
                  c=17)
D["K80"] = [f"C {ARROW} Rust translation"]
D["K81"] = one("Rust compiles + tests pass")

# ---------------------------------------------------------------- K82-K84
D["K82"] = one("CERTIFIABLE(U)")
D["K83"] = [
    "source_identity_valid", "AND semantic_model_complete_for_required_domains",
    "AND no_unresolved_critical_conflicts", "AND required_contracts_verified",
    "AND design_contract_conformant", "AND unsafe_obligations_resolved",
    "AND abi_contract_satisfied", "AND configuration_scope_satisfied",
    "AND architecture_scope_satisfied", "AND execution_evidence_valid",
    "AND verification_gates_pass", "AND replay_valid",
]
D["K84"] = one("complete_for_required_domains")

# ---------------------------------------------------------------- K85-K87
D["K85"] = one("linux/subsystems/scheduler.yaml")
D["K86"] = [
    "semantic_requirements:",
    "  type: required", "  ownership: required", "  lifetime: required",
    "  locking: required", "  rcu: required",
    "  interrupt_context: required", "  preemption: required",
    "  abi: required", "  configuration: required",
    "  architecture: required", "",
    "verification_requirements:",
    "  build: required", "  kunit: required", "  runtime: required",
    "  concurrency: required", "  differential: conditional",
]
D["K87"] = one("rcu: not_applicable")

# ---------------------------------------------------------------- K88
D["K88"] = bchain(["C source", "source extraction", "KSIR", "contract",
                   "Rust Design IR", "Rust", "test", "evidence", "gate",
                   "certificate"], c=4)

# ---------------------------------------------------------------- K89
M = 24
M1, M2 = 7, 38
D["K89"] = [
    row([("RFL-AE", M)]),
    marks([(M, VERT)]),
    " " * M1 + CORNER_TL + DASH * (M - M1 - 1) + TEE_U
    + DASH * (M2 - M - 1) + CORNER_TR,
    marks([(M1, VERT), (M2, VERT)]),
    row([("PROTOCOL KERNEL", M1), ("RECONSTRUCTION ENGINE", M2)]),
    marks([(M1, VERT), (M2, VERT)]),
]
_left = ["types", "authorization", "transitions", "event ledger", "evidence",
         "verification", "gates"]
_right = ["C analysis", "KSIR", "contracts", "design IR", "Rust generation"]
# The two columns are trees side by side: the connector sits AT M1 / M2, not
# centred on it, so build the line directly instead of via row().
for i in range(max(len(_left), len(_right))):
    def _cell(items, idx):
        if idx >= len(items):
            return ""
        g = BR if idx == len(items) - 1 else TR
        return g + DASH * 2 + " " + items[idx]
    _l, _r = _cell(_left, i), _cell(_right, i)
    _line = (" " * M1 + _l) if _l else ""
    if _r:
        _line = _line.ljust(M2) + _r
    D["K89"].append(_line)

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
