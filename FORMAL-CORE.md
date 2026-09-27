# RFL-AE — Formal Core

**Sections 81–107** — schemas, state transitions, evidence rules, and benchmark contracts.

> Continues the numbering of [ARCHITECTURE.md](ARCHITECTURE.md) (§1–§51) and
> [SPECIFICATION.md](SPECIFICATION.md) (§52–§80).

Before building more agents, freeze the **formal core**: define the schemas, state transitions,
evidence rules, and benchmark contracts. Otherwise the agent architecture will drift.

## Contents

| Part | Sections |
| --- | --- |
| [I. Core representation](#81-ksir-v01) | 81–84 |
| [II. Evidence](#85-evidence-model) | 85–88 |
| [III. Benchmark suite](#89-20-initial-competency-benchmarks) | 89–94 |
| [IV. Tools & authority](#95-tool-contracts) | 95–99 |
| [V. Migration protocol](#100-canonical-migration-manifest) | 100–102 |
| [VI. Qualification & lab](#103-kernel-subsystem-qualification) | 103–107 |

<details>
<summary><strong>Full section index</strong></summary>

81. KSIR v0.1
82. Core Rust Domain Types
83. Evidence-Carrying Values
84. Status Algebra
85. Evidence Model
86. Evidence Provenance
87. Claim Graph
88. Snapshot-Scoped Truth
89. 20 Initial Competency Benchmarks (C01–C10)
90. Rust-Specific Benchmarks (R01–R05)
91. Verification Benchmarks (V01–V05)
92. Benchmark Output Contract
93. Anti-Hallucination Benchmark
94. Contradiction Benchmark
95. Tool Contracts
96. Tool Authority Levels
97. Agent Tool Policy
98. Agent Separation
99. Worktree Isolation
100. Canonical Migration Manifest
101. Canonical Commit Protocol
102. Freeze Boundary
103. Kernel Subsystem Qualification
104. Qualification Rule
105. The First Real Lab
106. Success Criteria
107. The Actual Long-Term Architecture

</details>

---

# I. Core representation

## 81. KSIR v0.1

KSIR is deliberately smaller than the eventual model.

```text
KSIR v0.1
 │
 ├── Snapshot
 ├── Symbol
 ├── Type
 ├── Field
 ├── Function
 ├── Object
 ├── Resource
 ├── Lock
 ├── AtomicAccess
 ├── RCURegion
 ├── ExecutionContext
 ├── Allocation
 ├── ABI
 ├── Invariant
 ├── Contract
 └── EvidenceRef
```

The key rule:

> **KSIR is descriptive. Agents may derive hypotheses from KSIR. Agents may not silently
> mutate observed facts into truth.**

---

## 82. Core Rust Domain Types

Conceptually:

```rust
pub struct KernelSnapshot {
    pub id: SnapshotId,
    pub repository: RepositoryRef,
    pub commit: CommitId,
    pub architecture: Architecture,
    pub config: ArtifactDigest,
    pub toolchain: ToolchainFingerprint,
}

pub struct Symbol {
    pub id: SymbolId,
    pub name: String,
    pub kind: SymbolKind,
    pub location: SourceLocation,
}

pub struct Function {
    pub symbol: SymbolId,
    pub signature: FunctionSignature,
    pub context: ContextContract,
    pub effects: Effects,
}

pub struct Object {
    pub id: ObjectId,
    pub type_id: TypeId,
    pub lifetime: LifetimeModel,
    pub ownership: OwnershipModel,
}

pub struct Invariant {
    pub id: InvariantId,
    pub statement: String,
    pub status: VerificationStatus,
    pub evidence: Vec<EvidenceRef>,
}
```

But avoid prematurely implementing the complete semantic model as Rust structs.

> **First define the wire schema.**

---

## 83. Evidence-Carrying Values

A powerful pattern is:

```rust
pub struct Observed<T> {
    pub value: T,
    pub evidence: EvidenceRef,
}

pub struct Derived<T> {
    pub value: T,
    pub derivation: DerivationId,
    pub evidence: Vec<EvidenceRef>,
}

pub struct Hypothesis<T> {
    pub value: T,
    pub basis: Vec<EvidenceRef>,
    pub unresolved: Vec<Unknown>,
}
```

Then the architecture itself discourages:

```rust
let ownership = guessed_ownership();
```

being treated as equivalent to:

```rust
let ownership = observed_ownership();
```

This is exactly the kind of type-level discipline the AI system needs.

---

## 84. Status Algebra

Use **two separate dimensions**.

### Epistemic status

```text
UNKNOWN
OBSERVED
DERIVED
HYPOTHESIS
```

### Verification status

```text
UNVERIFIED
PROVISIONAL
PARTIALLY_VERIFIED
VERIFIED
BLOCKED
```

> **Do not collapse them.**

For example, these are all meaningful states:

| Epistemic | Verification |
| --- | --- |
| Observed | Unverified |
| Derived | Partially Verified |
| Hypothesis | Provisional |
| Observed | Verified |

---

# II. Evidence

## 85. Evidence Model

An evidence item should have:

```yaml
evidence:
  id: E-000001

  snapshot:
    kernel_commit: ...
    config_digest: ...
    architecture: ...

  source:
    kind: source
    path: kernel/foo.c
    range: 120-181

  observation:
    ...

  collector:
    tool: clang-analysis
    version: ...

  execution:
    required: false

  digest:
    algorithm: sha256
    value: ...

  status:
    OBSERVED
```

An execution result adds:

```yaml
execution:
  command: ...
  environment: ...
  exit_code: 0
  stdout_digest: ...
  stderr_digest: ...
  artifact_digest: ...
```

This enforces:

> **Execution claims require execution evidence.**

---

## 86. Evidence Provenance

Every derived claim should form a DAG:

```text
                  SOURCE
                     │
            ┌────────┴────────┐
            ▼                 ▼
      AST evidence      Git evidence
            │                 │
            └────────┬────────┘
                     ▼
               derived claim
                     │
            ┌────────┴────────┐
            ▼                 ▼
    runtime evidence    test evidence
            │                 │
            └────────┬────────┘
                     ▼
              verified claim
```

Therefore:

```text
Claim → Evidence → Artifact → Snapshot
```

must be traversable in **both directions**.

---

## 87. Claim Graph

The evidence system should expose:

```text
CLAIM
 │
 ├── supported_by
 ├── contradicted_by
 ├── derived_from
 ├── depends_on
 ├── verified_by
 └── invalidated_by
```

This allows historical changes to invalidate old conclusions. For example:

```text
commit A
    │
    ▼
 INV-001
    │
    ▼
Rust design D
```

Then:

```text
commit B
    │
    └── changes locking semantics
              │
              ▼
     INV-001 invalidated
              │
              ▼
       design D stale
```

This is essential for a continuously evolving kernel.

---

## 88. Snapshot-Scoped Truth

A statement should never simply be:

```text
foo requires lock X
```

It should be:

```text
At Linux snapshot S:
  foo requires lock X
```

because the kernel changes.

Therefore:

```text
Invariant
   │
   ├── valid_from
   ├── valid_until
   └── superseded_by
```

becomes useful.

---

# III. Benchmark suite

## 89. 20 Initial Competency Benchmarks

The first benchmark suite — **C01–C10** here, plus **R01–R05** (§90) and **V01–V05** (§91),
for 20 total.

### C01 — Pointer Classification

Input:

```c
struct foo *p;
```

Determine whether usage establishes:

```text
owned  borrowed  shared  nullable
RCU-protected  lock-protected  opaque
```

Expected output includes uncertainty.

### C02 — `container_of`

Given an intrusive structure:

```c
struct foo {
    int x;
    struct list_head node;
};
```

recover the containing-object relationship and identify lifetime assumptions.

### C03 — Refcount Lifecycle

Given:

```c
refcount_inc()
refcount_dec_and_test()
```

recover:

```text
creation  acquisition  release  destruction
```

and identify paths missing a reference.

### C04 — Lock Protection

Given a function cluster, determine:

```text
field → protecting lock
```

including fields protected only on particular paths.

### C05 — Lock Ordering

Construct:

```text
Lock A → Lock B
Lock B → Lock C
```

and detect:

```text
C → A
```

as a potential cycle requiring investigation.

### C06 — Context Safety

Determine whether `function A` can call `function B`, given:

```text
A = atomic context
B = may sleep
```

Expected:

```text
BLOCKED
```

### C07 — GFP Semantics

Infer whether allocation flags are compatible with execution context.

### C08 — RCU Lifetime

Recover:

```text
publish  read  replace  retire  free
```

for an RCU-protected object.

### C09 — Atomic Ordering

Given:

```c
smp_store_release(&x, value);
y = smp_load_acquire(&x);
```

identify the ordering contract and distinguish it from ordinary Rust ownership.

### C10 — Waitqueue / Wakeup

Recover:

```text
condition  wait  state transition  wake  ordering
```

and identify lost-wakeup risks.

---

## 90. Rust-Specific Benchmarks

### R01 — Ownership Translation

Given a C pointer graph, produce a Rust ownership design **without writing implementation
code**.

### R02 — Lifetime Translation

Given:

```text
object A contains callback B
B may execute after A's caller returns
```

design the lifetime model.

### R03 — Unsafe Boundary

Given an unsafe operation, enumerate all safety obligations.

### R04 — FFI Contract

Translate a C ABI into a Rust FFI contract including:

```text
layout  nullability  ownership  threading  context  error semantics
```

### R05 — Intrusive Data Structure

Design a Rust representation preserving Linux intrusive-list semantics.

---

## 91. Verification Benchmarks

### V01 — Differential Test Design

Given C and Rust implementations, design an observable equivalence test.

### V02 — Race Construction

Given two concurrent paths, produce a schedule that would expose an ordering defect if one
exists.

### V03 — UAF Detection

Construct the minimal lifecycle scenario exposing premature reclamation.

### V04 — ABI Verification

Compare:

```text
sizeof  alignof  offset  calling convention  symbol
```

between C and Rust.

### V05 — Evidence Audit

Given:

```text
claim  test output  commit  agent statement
```

determine which parts are actually supported.

> This is a crucial benchmark.

---

## 92. Benchmark Output Contract

Every benchmark should produce structured output.

```yaml
benchmark_result:
  benchmark_id: C04

  answer:
    ...

  status:
    VERIFIED

  evidence:
    - E-0001
    - E-0002

  uncertainty:
    - ...

  counterexamples:
    - ...

  required_followup:
    - ...
```

Not merely:

```text
8/10
```

---

## 93. Anti-Hallucination Benchmark

Introduce explicit tests where the correct answer is:

```text
UNKNOWN
```

Example:

```text
Question: Who owns foo?

Available evidence:
- foo_alloc()
- foo_get()
- foo_put()
- three callbacks
- incomplete call graph
```

Correct response:

```text
OWNERSHIP = PROVISIONAL
```

Incorrect:

```text
OWNER = caller
```

The benchmark should penalize **unsupported certainty**, not merely wrong answers.

---

## 94. Contradiction Benchmark

Give agents:

```text
Source:
    spin_lock protects state

History:
    lock removed in commit X

Current code:
    READ_ONCE(state)

Runtime:
    concurrent access observed
```

Expected:

```text
CONFLICT DETECTED
```

not:

```text
pick the most plausible explanation
```

---

# IV. Tools & authority

## 95. Tool Contracts

Agents should interact with deterministic tools.

Example:

```text
inspect_symbol    find_references    expand_macro
build_call_graph  build_dataflow     inspect_layout
inspect_btf       inspect_dwarf      git_history
git_blame         run_kunit          run_kselftest
run_kasan         run_kcsan          run_lockdep
run_qemu          compare_abi        record_evidence
```

Each tool should have:

```text
input schema
output schema
authority level
side effects
reproducibility requirements
evidence production behavior
```

---

## 96. Tool Authority Levels

Not all tools have the same epistemic authority.

| Level | Authority |
| --- | --- |
| T0 | text search |
| T1 | parser |
| T2 | static analysis |
| T3 | compiler |
| T4 | runtime observation |
| T5 | controlled experiment |
| T6 | independent verification |

For example, `grep` can establish:

> the string occurs.

It cannot establish:

> the field is always protected by this lock.

This distinction should be encoded into the evidence engine.

---

## 97. Agent Tool Policy

A reasoning agent should be forced through a progression:

```text
QUESTION
   ↓
CHEAPEST ADEQUATE EVIDENCE
   ↓
INSUFFICIENT?
   ↓
MORE POWERFUL OBSERVATION
   ↓
EXPERIMENT
   ↓
INDEPENDENT VERIFICATION
```

Example:

```text
"Does foo always execute with lock X?"
         │
         ▼
static call/access analysis
         │
         ├── sufficient → DERIVED
         │
         └── insufficient
                   │
                   ▼
             runtime trace
                   │
                   ▼
               VERIFIED
```

This prevents expensive experiments from being used unnecessarily while also preventing weak
evidence from being overclaimed.

---

## 98. Agent Separation

Use at least four authority classes:

```text
DISCOVERY
   │
   └── may observe

DESIGN
   │
   └── may propose

IMPLEMENTATION
   │
   └── may modify worktree

VERIFICATION
   │
   └── may certify evidence
```

And:

```text
IMPLEMENTATION agent
       ✗ cannot mark its own artifact VERIFIED
```

The evidence engine itself should be deterministic wherever possible.

---

## 99. Worktree Isolation

Every implementation attempt should happen in an isolated worktree:

```text
kernel.git
   │
   ├── baseline/
   ├── agent-A/
   ├── agent-B/
   └── verifier/
```

The verifier receives:

```text
baseline SHA
candidate SHA
migration manifest
verification plan
```

rather than trusting conversational claims.

---

# V. Migration protocol

## 100. Canonical Migration Manifest

The unit of work should have a canonical manifest:

```yaml
migration_unit:
  id: MU-000001

  snapshot:
    commit: ...

  scope:
    subsystem: ...
    files:
      - ...

  symbols:
    - ...

  contracts:
    - ...

  invariants:
    - ...

  ownership:
    status: ...

  concurrency:
    status: ...

  abi:
    status: ...

  rust_design:
    artifact: ...

  implementation:
    commit: ...

  verification:
    required:
      - build
      - kunit
      - kasan
      - kcsan
      - differential

  release:
    status: BLOCKED
```

The manifest becomes the **transaction record**.

---

## 101. Canonical Commit Protocol

For each migration:

```text
DISCOVERY COMMIT
        ↓
  CONTRACT COMMIT
        ↓
   DESIGN COMMIT
        ↓
IMPLEMENTATION COMMIT
        ↓
    TEST COMMIT
        ↓
VERIFICATION RECORD
        ↓
   RELEASE TAG
```

These don't necessarily all have to be separate Git commits in the eventual implementation,
but they should be separate **logical artifacts**.

That makes rollback and audit straightforward.

---

## 102. Freeze Boundary

Before implementation:

```text
MIGRATION FREEZE
```

captures:

```text
Linux SHA
config
architecture
toolchain
generated files
dependencies
contract version
benchmark version
```

Then:

```text
Rust implementation
```

is evaluated against exactly that baseline.

If Linux changes:

```text
OLD MIGRATION
     │
     ▼
   STALE
     │
     ▼
REBASE ANALYSIS
```

not silently treated as current.

---

# VI. Qualification & lab

## 103. Kernel Subsystem Qualification

Now we can formalize subsystem-specific QA.

### `LOCK-QA`

```text
LQ-01 spinlock
LQ-02 mutex
LQ-03 rwlock
LQ-04 lock nesting
LQ-05 lockdep
LQ-06 IRQ locking
LQ-07 PREEMPT_RT implications
```

### `RCU-QA`

```text
RQ-01 read-side lifetime
RQ-02 publication
RQ-03 grace period
RQ-04 callback
RQ-05 reclamation
RQ-06 ordering
RQ-07 preemption
RQ-08 RT interactions
```

### `MM-QA`

```text
MQ-01 page lifetime
MQ-02 refcount
MQ-03 VMA
MQ-04 page tables
MQ-05 allocation context
MQ-06 reclaim
MQ-07 TLB
MQ-08 NUMA
MQ-09 architecture
```

### `SCHED-QA`

```text
SQ-01 task lifecycle
SQ-02 runqueue
SQ-03 wakeup
SQ-04 sleep
SQ-05 preemption
SQ-06 CPU migration
SQ-07 context switch
SQ-08 scheduler classes
```

---

## 104. Qualification Rule

A subsystem cannot be considered migration-ready merely because the model passes source
comprehension.

For example, `RCU migration authority` requires:

| Competency | Required status |
| --- | --- |
| C semantics | VERIFIED |
| ownership | VERIFIED |
| concurrency | VERIFIED |
| memory ordering | VERIFIED |
| execution context | VERIFIED |
| Rust design | VERIFIED |
| FFI | VERIFIED |
| verification | VERIFIED |
| adversarial | VERIFIED |

If:

```text
memory ordering = PROVISIONAL
```

then:

```text
RCU migration authority = BLOCKED
```

> This is where the system becomes materially different from ordinary coding agents.

---

## 105. The First Real Lab

Now define:

```text
RFL-AE-LAB-001
```

as a **small, isolated kernel migration exercise**.

Requirements:

```text
must include:
    C object
    ownership
    reference counting
    intrusive structure
    locking
    callback
    one FFI boundary
    unit tests
    concurrency test
    deliberate failure case
```

The lab isn't intended to rewrite an important production subsystem.

Its purpose is to test the **entire RFL-AE pipeline**:

```text
index
 → KSIR
 → contract
 → ownership
 → concurrency
 → Rust design
 → implementation
 → verification
 → evidence
 → migration certificate
```

---

## 106. Success Criteria

RFL-AE-LAB-001 succeeds only if the system can answer:

1. What does the C code do?
2. What are its invariants?
3. Who owns each object?
4. What protects each shared state?
5. Which contexts may execute each function?
6. What can sleep?
7. What can be freed and when?
8. What ABI must remain stable?
9. What unsafe operations are required?
10. What evidence supports every answer?
11. What does the Rust design preserve?
12. How was equivalence tested?
13. What remains unknown?
14. Can the migration be reproduced?
15. Can the migration be independently audited?

If any answer is unsupported:

```text
OPEN
```

or:

```text
BLOCKED
```

---

## 107. The Actual Long-Term Architecture

At this point the project becomes:

```text
                       RFL-AE
                          │
        ┌─────────────────┼──────────────────┐
        │                 │                  │
 KERNEL OBSERVER   SEMANTIC MODEL      EXECUTION LAB
        │                 │                  │
        ▼                 ▼                  ▼
   source/git      KSIR/invariants      QEMU/tests
  AST/BTF/DWARF       ownership         sanitizers
 runtime traces      concurrency       differential
        │                 │                  │
        └─────────────────┼──────────────────┘
                          ▼
                  MIGRATION ENGINE
                          │
               ┌──────────┼──────────┐
               ▼          ▼          ▼
            DESIGN      CODE     EVIDENCE
               │          │          │
               └──────────┼──────────┘
                          ▼
                    RELEASE GATE
```

And there is one architectural principle to freeze now:

> ### **The LLM is a reasoning component inside RFL-AE, not the source of truth.**

The source of truth is the combination of:

```text
versioned kernel snapshot
+ observed artifacts
+ formalized contracts
+ explicit hypotheses
+ executed verification
+ immutable evidence
```

---

## Next step

That gives us the foundation for the next stage: **the actual agent protocol and state
machine** — including message schemas, task admission, capability authorization, quarantine,
replay, evidence recording, and the mechanism by which 10–100 specialized agents can work on
the same kernel migration without turning the system into an uncontrolled multi-agent
conversation.
