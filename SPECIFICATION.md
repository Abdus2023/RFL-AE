# RFL-AE v0.1 — System Specification

**Sections 52–80** — the engineering specification layer.

> Continues the numbering of [ARCHITECTURE.md](ARCHITECTURE.md) (§1–§51).

The critical shift is from *"agents that know kernel concepts"* to an architecture where an
agent can be given a kernel migration unit and **must produce a chain of independently
checkable artifacts**.

## Contents

| Part | Sections |
| --- | --- |
| [I. System & repository](#52-rfl-ae-v01-system-specification) | 52–53 |
| [II. Domain model & contracts](#54-core-domain-model) | 54–62 |
| [III. Safety & agent protocol](#63-safety-obligations) | 63–67 |
| [IV. Verification](#68-verification-pipeline) | 68–73 |
| [V. Qualification & capability](#74-core-subsystem-qualification) | 74–77 |
| [VI. Invariants & final architecture](#78-the-hardest-problem) | 78–80 |

<details>
<summary><strong>Full section index</strong></summary>

52. RFL-AE v0.1: System Specification
53. Repository Architecture
54. Core Domain Model
55. `KernelSnapshot`
56. KSIR
57. Unknown Is a First-Class Value
58. Contract Representation
59. Ownership Contract
60. Concurrency Contract
61. Execution-Context Contract
62. Rust Design IR
63. Safety Obligations
64. Agent Protocol
65. Agent State Machine
66. Authorization State
67. Quarantine Is Essential
68. Verification Pipeline
69. Verification Is Layered
70. Differential Oracle
71. Example Migration
72. Benchmark: Intentional Wrong Rust
73. The Agent Must Know When Not to Translate
74. Core Subsystem Qualification
75. Core Subsystem Qualification Map
76. Capability Dependency Graph
77. First Release Gate
78. The Hardest Problem
79. The Ultimate Artifact: Kernel Invariant Ledger
80. Final Architecture: Evidence-Carrying Migration

</details>

---

# I. System & repository

## 52. RFL-AE v0.1: System Specification

```text
RFL-AE — Rust-for-Linux Autonomous Engineering

Purpose:
  Assist incremental, evidence-gated migration of Linux
  kernel C subsystems/components to Rust.

Primary invariant:
  NO EVIDENCE → NO VERIFIED CLAIM

Secondary invariant:
  IMPLEMENTATION AUTHORITY ≠ VERIFICATION AUTHORITY
```

The system should initially be **advisory + gated**, not autonomous merge authority.

---

## 53. Repository Architecture

```text
rfl-ae/
│
├── README.md
├── LICENSE
├── Cargo.toml
├── rust-toolchain.toml
│
├── docs/
│   ├── architecture/
│   ├── methodology/
│   ├── subsystem-model/
│   ├── verification/
│   └── governance/
│
├── crates/
│   │
│   ├── rfl-types/
│   ├── rfl-ksir/
│   ├── rfl-c-analyzer/
│   ├── rfl-kernel-index/
│   ├── rfl-ownership/
│   ├── rfl-concurrency/
│   ├── rfl-context/
│   ├── rfl-abi/
│   ├── rfl-history/
│   ├── rfl-migration/
│   ├── rfl-verification/
│   ├── rfl-differential/
│   ├── rfl-adversarial/
│   ├── rfl-evidence/
│   └── rfl-gates/
│
├── schemas/
│   ├── ksir/
│   ├── contract/
│   ├── evidence/
│   ├── migration/
│   └── capability/
│
├── agents/
│   ├── cartographer/
│   ├── semantics/
│   ├── ownership/
│   ├── concurrency/
│   ├── rust-design/
│   ├── implementation/
│   ├── verification/
│   ├── adversarial/
│   ├── historian/
│   ├── reviewer/
│   └── evidence/
│
├── tools/
│   ├── index-kernel
│   ├── inspect-symbol
│   ├── build-ksir
│   ├── derive-contract
│   ├── derive-ownership
│   ├── derive-locks
│   ├── generate-ffi
│   ├── verify-migration
│   └── evidence-report
│
├── benchmarks/
│   ├── c-semantics/
│   ├── ownership/
│   ├── concurrency/
│   ├── abi/
│   ├── context/
│   ├── rust/
│   └── differential/
│
├── fixtures/
│   ├── minimal-kernel/
│   ├── linux-subsystems/
│   └── known-failures/
│
└── tests/
    ├── unit/
    ├── integration/
    ├── conformance/
    └── adversarial/
```

| Directory | Count |
| --- | --- |
| `crates/` | 15 |
| `schemas/` | 5 |
| `agents/` | 11 |
| `tools/` | 9 |
| `benchmarks/` | 7 |
| `fixtures/` | 3 |
| `tests/` | 4 |
| `docs/` | 5 |

---

# II. Domain model & contracts

## 54. Core Domain Model

The most important design decision is to establish a **small immutable domain model** before
adding agents.

```text
             KernelSnapshot
                    │
                    ├── SourceTree
                    ├── Config
                    ├── Toolchain
                    ├── Architecture
                    └── Commit
                    │
                    ▼
               KernelIndex
                    │
                    ▼
                  KSIR
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    Contract    Ownership  Concurrency
        │           │           │
        └───────────┼───────────┘
                    ▼
              MigrationUnit
                    │
                    ▼
            VerificationPlan
                    │
                    ▼
             EvidenceBundle
```

---

## 55. `KernelSnapshot`

Never analyze "Linux" as an unqualified moving target.

A snapshot needs:

```yaml
kernel_snapshot:
  repository: linux
  commit: <exact-sha>
  tree_hash: <digest>

  architecture:
    name: x86_64

  config:
    source: .config
    digest: <digest>

  compiler:
    cc: ...
    rustc: ...

  generated_artifacts:
    digest: ...

  analysis_tools:
    versions:
      clang: ...
      pahole: ...
      sparse: ...
```

This gives every observation a precise environment.

Without this, an evidence record such as:

```text
"foo is implemented this way in Linux"
```

is underspecified.

---

## 56. KSIR

The **Kernel Semantic Intermediate Representation** should be the canonical internal
representation.

```text
KSIR
 │
 ├── Snapshot
 ├── Symbols
 ├── Types
 ├── Functions
 ├── Fields
 ├── Objects
 ├── Resources
 ├── Locks
 ├── Atomics
 ├── RCU domains
 ├── Execution contexts
 ├── Allocation domains
 ├── ABI surfaces
 ├── Architecture constraints
 ├── Security constraints
 └── Evidence references
```

Important distinction:

```text
KSIR
  ├── OBSERVED facts
  ├── DERIVED relationships
  ├── HYPOTHESES
  └── UNKNOWN
```

> **Do not flatten these.**

---

## 57. Unknown Is a First-Class Value

The system must be able to represent:

```yaml
ownership:
  object: foo
  status: UNKNOWN
```

rather than forcing:

```yaml
ownership:
  object: foo
  owner: caller
```

The latter is a **dangerous hallucination** if the evidence doesn't establish it.

Use, where appropriate:

```text
UNKNOWN
NOT_OBSERVABLE
NOT_REACHABLE
NOT_PRESENT
NOT_APPLICABLE
```

---

## 58. Contract Representation

A kernel function contract can be modeled as:

```yaml
function_contract:
  symbol: foo_update

  inputs:
    - name: foo
      type: "*struct foo"

  preconditions:
    - "foo lifetime is valid"
    - "foo->lock is held"

  context:
    allowed:
      - PROCESS

  sleeping:
    may_sleep: true

  locking:
    requires:
      - foo->lock

  memory:
    reads:
      - foo->state
    writes:
      - foo->state

  errors:
    - EINVAL

  side_effects:
    - state_transition
```

But each field needs provenance.

```yaml
provenance:
  - claim: "foo->lock protects foo->state"
    basis:
      - source
      - lock_analysis
      - historical_commit
```

---

## 59. Ownership Contract

Represent ownership independently:

```yaml
ownership_contract:
  object: foo

  creation:
    function: foo_alloc

  owner:
    kind: reference_count
    references:
      - caller
      - worker
      - rcu_reader

  destruction:
    function: foo_free
    destruction_condition:
      - refcount_zero

  synchronization:
    mutation:
      - foo->lock
    lookup:
      - rcu_read_lock
```

This becomes the bridge to Rust.

---

## 60. Concurrency Contract

The agent should construct something resembling:

```yaml
concurrency_contract:
  object: foo

  state:
    foo->state:
      readers:
        - foo_read
        - foo_status
      writers:
        - foo_update
      protection:
        mechanism: spinlock
        lock: foo->lock

  lifecycle:
    mechanism: rcu

  ordering:
    publication:
      mechanism: smp_store_release
    consumption:
      mechanism: smp_load_acquire
```

Now the Rust designer has something substantially stronger than source text.

---

## 61. Execution-Context Contract

```yaml
context_contract:
  function: foo_worker

  callable_from:
    - PROCESS

  may_sleep: true

  may_allocate:
    GFP_KERNEL: true

  interrupt_safe: false

  preemption:
    required: enabled
```

The verifier can then check whether a proposed Rust implementation violates the contract.

---

## 62. Rust Design IR

Don't jump directly from KSIR to Rust source. Insert another representation:

```text
KSIR
 ↓
Rust Design IR
 ↓
Rust source
```

Rust Design IR contains:

```text
RustType  RustTrait  RustLifetime  RustOwnership
RustSyncPrimitive  RustFFIBoundary  UnsafeBlock  SafetyObligation
```

Example:

```yaml
rust_design:
  type: Foo

  ownership:
    model: refcounted

  synchronization:
    state:
      mechanism: spinlock

  lifetime:
    external_refs: allowed

  ffi:
    exposed: true

  unsafe:
    blocks:
      - id: UB-001
        reason: intrusive_list_recovery
        obligations:
          - valid_container_pointer
          - object_alive
          - correct_field_offset
```

---

# III. Safety & agent protocol

## 63. Safety Obligations

Every unsafe operation becomes a set of obligations.

```text
UB-001
  │
  ├── O1 pointer valid
  ├── O2 pointer aligned
  ├── O3 object initialized
  ├── O4 object alive
  ├── O5 aliasing valid
  ├── O6 synchronization valid
  └── O7 architecture assumption valid
```

Each obligation can independently become:

```text
PROVED  OBSERVED  DERIVED  PROVISIONAL  OPEN  BLOCKED
```

Therefore:

```text
unsafe block
     │
     ├── 7 obligations
     │
     ├── 6 proved
     └── 1 open
            │
            ▼
      RELEASE BLOCK
```

---

## 64. Agent Protocol

Agents should communicate through **typed artifacts**, not conversational prose.

**Bad:**

```text
"Looks like this lock protects the structure."
```

**Good:**

```yaml
artifact: concurrency_claim

subject: struct_foo
property: protected_field
field: foo->state

protection:
  mechanism: spinlock
  symbol: foo->lock

confidence: PROVISIONAL

evidence:
  - source: ...
  - access_analysis: ...

unresolved:
  - indirect_writer_17
```

This makes the multi-agent system auditable.

---

## 65. Agent State Machine

Each agent should have explicit capability state.

```text
        UNKNOWN
           │
           ▼
       ANALYZING
           │
           ▼
      HYPOTHESIS
           │
           ▼
     DEMONSTRATED
           │
           ▼
       VERIFIED
           │
           ▼
      AUTHORIZED
```

But:

```text
VERIFIED  ≠  AUTHORIZED
```

An agent can know how to perform a task without being authorized to modify the repository.

---

## 66. Authorization State

For every migration unit:

```text
           DISCOVERED
                ↓
             MAPPED
                ↓
           CONTRACTED
                ↓
            DESIGNED
                ↓
  AUTHORIZED_FOR_IMPLEMENTATION
                ↓
           IMPLEMENTED
                ↓
     AUTHORIZED_FOR_TESTING
                ↓
            VERIFIED
                ↓
      AUTHORIZED_FOR_REVIEW
                ↓
        RELEASE_ELIGIBLE
```

A failure causes:

```text
              ┌───────────┐
                 FAILURE
              └─────┬─────┘
                    ▼
               QUARANTINE
                    │
           ┌────────┴────────┐
           ▼                 ▼
       diagnosis         rollback
```

> **No silent continuation.**

---

## 67. Quarantine Is Essential

If an agent discovers:

```text
contradictory lock model
unknown lifetime
ABI mismatch
unexplained race
architecture dependency
```

the migration unit becomes:

```text
QUARANTINED
```

The system should not allow an LLM to "reason through" the contradiction and continue without
evidence.

---

# IV. Verification

## 68. Verification Pipeline

For each migration unit:

```text
                  SOURCE
                     │
                     ▼
                C baseline
                     │
            ┌────────┴────────┐
            ▼                 ▼
      static model      runtime model
            │                 │
            └────────┬────────┘
                     ▼
                   KSIR
                     │
                     ▼
                Rust design
                     │
                     ▼
                Rust build
                     │
           ┌─────────┼─────────┐
           ▼         ▼         ▼
        compile    KUnit    static
           │         │         │
           └─────────┼─────────┘
                     ▼
               dynamic tests
                     │
           ┌─────────┼─────────┐
           ▼         ▼         ▼
         KASAN     KCSAN    lockdep
           │         │         │
           └─────────┼─────────┘
                     ▼
               differential
                     │
                     ▼
                adversarial
                     │
                     ▼
                 evidence
```

---

## 69. Verification Is Layered

Don't use a single "tests passed" flag.

| Layer | Check |
| --- | --- |
| V0 | parses |
| V1 | builds |
| V2 | unit behavior |
| V3 | kernel integration |
| V4 | runtime behavior |
| V5 | concurrency |
| V6 | memory safety |
| V7 | ABI |
| V8 | differential behavior |
| V9 | adversarial |
| V10 | regression stability |

A migration can therefore say:

```text
Build:             VERIFIED
Functional:        VERIFIED
Memory:            VERIFIED
Concurrency:       PARTIALLY_VERIFIED
Differential:      PROVISIONAL
Architecture:      OPEN
```

Much more useful than:

```text
PASS
```

---

## 70. Differential Oracle

The difficult part is deciding what constitutes equivalent behavior.

Create explicit equivalence dimensions:

| Dimension | Equivalence property |
| --- | --- |
| E0 | Compile compatibility |
| E1 | ABI equivalence |
| E2 | Return/error equivalence |
| E3 | State transition equivalence |
| E4 | Resource lifecycle equivalence |
| E5 | Synchronization guarantees |
| E6 | Security properties |
| E7 | Observable I/O |
| E8 | Performance constraints |

The verification plan declares which dimensions are applicable.

---

## 71. Example Migration

Suppose the first experimental unit is:

```text
intrusive kernel list + reference-counted object
```

The C side:

```text
struct foo
 ├── refcount
 ├── state
 └── list_head
```

The system discovers:

```yaml
ownership:  refcount
mutation:   spinlock
container:  intrusive list
lifetime:   refcount
context:    process + worker
unsafe:     container recovery
```

Then Rust design:

```rust
Foo
├── RefCount
├── Lock<State>
└── IntrusiveNode
```

The actual Rust representation can then be debated by the design agent.

> The important thing is that the **semantic requirements were extracted before
> implementation**.

---

## 72. Benchmark: Intentional Wrong Rust

This should become one of the benchmark categories.

Give the model:

```rust
struct Foo {
    state: Mutex<State>,
    node: ListNode,
}
```

and ask: **Is this a valid translation?**

The correct response should not be based on surface resemblance. It must ask:

```text
Does the original lock permit sleeping?
Is it acquired in interrupt context?
Is node lifetime independent?
Is Foo reference counted?
Can the node outlive Foo?
Is list traversal RCU protected?
```

If these are unknown:

```text
RESULT = BLOCKED
```

> That is a **successful** benchmark outcome.

---

## 73. The Agent Must Know When Not to Translate

This is arguably one of the most important competencies.

Possible result:

```yaml
migration_decision:
  status: BLOCKED

  reasons:
    - unresolved_rcu_lifetime
    - architecture_specific_assembly
    - undocumented_abi
    - dynamic_callback_registration

  required_evidence:
    - runtime_trace
    - historical_analysis
    - architecture_analysis
```

A system that frequently says **BLOCKED with good evidence** is more useful than one that
always produces Rust.

---

# V. Qualification & capability

## 74. Core Subsystem Qualification

Before an agent can touch a real subsystem, it should pass a subsystem-specific qualification.

For `RCU`:

```text
RCU-QA
  must demonstrate:
    grace-period reasoning
    read-side lifetime
    callback lifecycle
    publication ordering
    reclamation
    preemption interactions
    interrupt interactions
    PREEMPT_RT differences
    memory ordering
```

For scheduler:

```text
SCHED-QA
  must demonstrate:
    runqueue invariants
    task state transitions
    locking
    preemption
    wakeup paths
    context switching
    CPU migration
    scheduler classes
```

For `mm`:

```text
MM-QA
  must demonstrate:
    page lifetime
    references
    page tables
    VMAs
    locking
    reclaim
    allocation contexts
    NUMA
    TLB interaction
    architecture constraints
```

The qualification itself becomes a benchmark.

---

## 75. Core Subsystem Qualification Map

```text
                         KERNEL
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
     CORE                MEMORY              EXECUTION
       │                    │                    │
       ▼                    ▼                    ▼
    locking              page/mm             scheduler
      RCU                 slab                  IRQ
    atomics                vm                 timers
     lists                 DMA               workqueue
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                     INFRASTRUCTURE
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                    ▼
      VFS                  NET                 BLOCK
       │                    │                    │
       ▼                    ▼                    ▼
    drivers              sockets              storage
```

The agent shouldn't qualify for the upper layers until its lower-level competency is
demonstrated.

---

## 76. Capability Dependency Graph

```text
    C semantics
         │
         ├───────────────┐
         ▼               ▼
   Kernel memory    Kernel ABI
         │               │
         ▼               ▼
     Ownership    FFI engineering
         │               │
         └───────┬───────┘
                 ▼
        Rust kernel design
                 │
         ┌───────┼───────┐
         ▼       ▼       ▼
      locking   RCU   context
         │       │       │
         └───────┼───────┘
                 ▼
         subsystem rewrite
                 │
                 ▼
           verification
                 │
                 ▼
          autonomous work
```

This gives us a concrete answer to:

> **What skills must an AI acquire before it can safely rewrite kernel code?**

---

## 77. First Release Gate

RFL-AE v0.1 should **not** claim: *autonomous Linux kernel rewriting.*

Its release claim should be much narrower:

> **RFL-AE v0.1 can construct evidence-backed semantic models of selected Linux kernel
> migration units and generate reviewable Rust migration designs under explicit uncertainty
> and verification gates.**

That is a defensible milestone.

Then:

| Version | Capability |
| --- | --- |
| v0.1 | semantic reconstruction |
| v0.2 | Rust design generation |
| v0.3 | isolated Rust implementation |
| v0.4 | differential verification |
| v0.5 | adversarial migration |
| v0.6 | multi-unit migration |
| v1.0 | bounded autonomous migration |

---

# VI. Invariants & final architecture

## 78. The Hardest Problem

The deepest technical problem isn't C parsing. It is:

> ### **Recovering distributed invariants.**

A Linux invariant may be spread across:

```text
function A
    ↓
header macro
    ↓
lock definition
    ↓
callback
    ↓
interrupt handler
    ↓
allocator
    ↓
architecture implementation
    ↓
Git commit
    ↓
KUnit test
```

No individual file contains the complete contract.

Therefore the AI needs **cross-artifact invariant synthesis**.

```text
source  docs  tests  history  runtime  architecture  ABI
                          │
                          ▼
                  Invariant Candidate
                          │
                          ▼
                 Independent Evidence
                          │
                          ▼
                      Invariant
```

That should be one of the central research problems of the project.

---

## 79. The Ultimate Artifact: Kernel Invariant Ledger

Every important invariant gets an identity:

```yaml
invariant_id: INV-RCU-00421

subject:
  subsystem: rcu
  object: foo

statement:
  "foo cannot be reclaimed until all relevant RCU readers
   have passed through a grace period."

kind:
  lifetime

status:
  VERIFIED

evidence:
  source:
    - ...
  implementation:
    - ...
  tests:
    - ...
  history:
    - ...

dependencies:
  - INV-RCU-00102
  - INV-MEM-00311

consumers:
  - MU-00123
  - MU-00491
```

Now a Rust migration can explicitly say:

```yaml
preserves_invariants:
  - INV-RCU-00421
  - INV-MEM-00311
```

This is far more powerful than a conventional test report.

---

## 80. Final Architecture: Evidence-Carrying Migration

The end state should look like:

```text
                     LINUX C
                        │
                        ▼
                SEMANTIC ANALYSIS
                        │
                        ▼
                INVARIANT LEDGER
                        │
                        ▼
                      KSIR
                        │
                        ▼
                 RUST DESIGN IR
                        │
                        ▼
               RUST IMPLEMENTATION
                        │
                        ▼
            ┌───────────┴───────────┐
            ▼                       ▼
        SAFE RUST              UNSAFE RUST
                                    │
                                    ▼
                           SAFETY OBLIGATIONS
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
             STATIC              DYNAMIC          DIFFERENTIAL
                │                   │                   │
                └───────────────────┼───────────────────┘
                                    ▼
                            ADVERSARIAL TEST
                                    │
                                    ▼
                             EVIDENCE BUNDLE
                                    │
                                    ▼
                          MIGRATION CERTIFICATE
```

The **Migration Certificate** is the final artifact:

```yaml
migration:
  id: MU-XXXXX

  source:
    linux_commit: ...

  target:
    rust_commit: ...

  scope:
    ...

  invariants:
    preserved:
      - ...
    unresolved:
      - ...

  abi:
    status: VERIFIED

  ownership:
    status: VERIFIED

  concurrency:
    status: PARTIALLY_VERIFIED

  memory_safety:
    status: VERIFIED

  differential:
    status: VERIFIED

  adversarial:
    status: VERIFIED

  known_limitations:
    - ...

  evidence:
    - ...
```

That gives us a concrete governing idea:

> **The AI does not merely produce Rust code. It produces an evidence-carrying migration
> artifact whose code, semantic model, safety obligations, tests, and provenance can be
> independently inspected.**

---

## Next step

The next logical step is to define **the actual `KSIR v0.1` schema and Rust domain types**,
followed by the **first 20 kernel competency benchmarks**.

Those two pieces will turn the architecture above into something implementable rather than
conceptual.
