# RFL-AE — Kernel Contract Reconstruction

**Sections 292–320** — the layer that defines what the Rust implementation is required to
preserve.

> Continues the numbering of [ARCHITECTURE.md](ARCHITECTURE.md) (§1–§51),
> [SPECIFICATION.md](SPECIFICATION.md) (§52–§80), [FORMAL-CORE.md](FORMAL-CORE.md)
> (§81–§107), [PROTOCOL.md](PROTOCOL.md) (§109–§135), [RUST-CORE.md](RUST-CORE.md)
> (§136–§172), [TRANSITIONS.md](TRANSITIONS.md) (§173–§203), [KSIR.md](KSIR.md)
> (§204–§250), and [RECONSTRUCTION.md](RECONSTRUCTION.md) (§251–§291). §108 does not exist
> in the source.
>
> **Note on derived material:** the source's "Contract Categories" grid (§299) and the
> `G-CONTRACT-001`…`G-CONTRACT-008` gate list (§313) are rendered as markdown tables; the
> collapsed ASCII figures are redrawn in `text` fences from computed column layouts. No
> content was added beyond that.

## Contents

| Part | Sections | |
| --- | --- | --- |
| [I. The contract model](#292-contract-reconstruction-model) | 292–299 |
| [II. Contract dimensions](#300-temporal-contracts) | 300–308 |
| [III. Verification and refinement](#309-contract-differential-testing) | 309–313 |
| [IV. Contract compiler and adversarial review](#314-contract-compiler) | 314–318 |
| [V. Proof chain and the next layer](#319-end-to-end-proof-chain) | 319–320 |

---

The next layer is where the system stops merely describing C semantics and starts defining
**what the Rust implementation is required to preserve**.

The distinction must remain strict:

```text
KSIR        = What we have reconstructed about the existing kernel
Contract    = What must remain true after migration
Rust Design = One proposed way to satisfy that contract
```

Therefore:

```text
C source
    ↓
observations
    ↓
KSIR
    ↓
CONTRACT
    ↓
Rust Design IR
    ↓
Rust
```

A Rust type is never itself evidence that a contract has been preserved.

---

## 292. Contract Reconstruction Model

Define a kernel contract as:

```rust
struct KernelContract {
    contract_id: ContractId,

    snapshot: KernelSnapshotId,
    validity: ValidityDomain,

    subject: SubjectId,

    preconditions: Vec<Condition>,
    postconditions: Vec<Condition>,

    invariants: Vec<Invariant>,
    ownership: OwnershipContract,
    lifetime: LifetimeContract,
    concurrency: ConcurrencyContract,
    context: ExecutionContextContract,

    effects: EffectContract,

    callbacks: CallbackContract,

    abi: AbiContract,

    architecture: ArchitectureContract,

    security: SecurityContract,

    error_behavior: ErrorContract,

    temporal: Vec<TemporalContract>,

    evidence: EvidenceSet,

    unknowns: Vec<UnknownId>,
    conflicts: Vec<ConflictId>,

    status: ContractStatus,
}
```

The contract is **snapshot-bound** and **variant-bound**.

It is not an eternal description of Linux.

---

## 293. Contract Status

Do not use a single confidence score.

Use explicit states:

```text
DRAFT
    ↓
EVIDENCE_BOUND
    ↓
RECONCILED
    ↓
PARTIALLY_VERIFIED
    ↓
VERIFIED
```

With blocking states:

```text
CONFLICTED
BLOCKED
INVALIDATED
SUPERSEDED
```

A contract can also be partially verified dimension-by-dimension.

For example:

```text
Ownership      VERIFIED
Lifetime       PARTIALLY_VERIFIED
Locking        VERIFIED
Context        VERIFIED
ABI            UNVERIFIED
RCU            BLOCKED
```

Overall migration eligibility is then determined by gate rules rather than an aggregate
score.

---

## 294. Preconditions

A precondition describes what must be true before an operation is valid.

Examples:

```text
P1:
    caller holds lock L
P2:
    object reference is alive
P3:
    execution context permits sleeping
P4:
    pointer belongs to kernel address space
P5:
    DMA mapping is active
P6:
    RCU read-side critical section is active
```

These become explicit semantic objects:

```rust
struct Precondition {
    id: ConditionId,
    predicate: Predicate,
    scope: Scope,
    evidence: EvidenceSet,
}
```

---

## 295. Postconditions

Postconditions describe what the operation guarantees.

Examples:

```text
foo_get():
    reference count increased

foo_put():
    reference released

list_add():
    node becomes reachable from list

device_remove():
    device no longer published

timer_cancel():
    callback cannot execute after required quiescence

work_cancel_sync():
    required callback quiescence established
```

Again, the system must distinguish:

```text
OBSERVED
DERIVED
HYPOTHESIS
```

from:

```text
VERIFIED
```

---

## 296. Invariants

The contract layer should transform low-level facts into explicit invariants.

Example:

```text
I-001
Subject:
    struct foo::state
Invariant:
    mutable access requires protection by foo->lock
Scope:
    CONFIG_FOO=y
Evidence:
    O17, O19, O31
Status:
    PARTIALLY_VERIFIED
```

Another:

```text
I-002
Subject:
    struct foo
Invariant:
    object remains alive while an RCU reader can dereference it
Status:
    VERIFIED
```

These invariant IDs become the bridge between C and Rust.

---

## 297. Invariant Preservation

For every Rust design element:

```text
RustDesignElement
```

the system should require:

```text
preserves:
    I-001
    I-002
    I-007

introduces obligations:
    U-003
    U-004
```

Example:

```rust
struct Foo {
    state: SpinLock<State>,
}
```

does not automatically prove:

```text
I-001 preserved
```

The system needs an explicit mapping:

```text
C:
    foo->lock protects foo->state
Rust:
    Foo::state is accessed through SpinLock
Mapping:
    C protection invariant → Rust synchronization invariant
```

Then verification can test the mapping.

---

## 298. Contract Normal Form

To make contracts machine-comparable, normalize them.

Conceptually:

```text
Contract Normal Form

subject
scope
condition
operation
required_state
effect
result_state
temporal_relation
evidence
```

Example:

```text
subject:
    foo
operation:
    foo_put
condition:
    refcount > 0
required_state:
    object alive
effect:
    decrement reference
result:
    if count == 0 → destruction
temporal:
    destruction occurs only after final reference release
```

This allows the same contract to be represented independently of C or Rust syntax.

---

## 299. Contract Categories

The system should generate contracts across distinct dimensions.

| Domain | Contract question |
| --- | --- |
| Ownership | Who owns this resource? |
| Lifetime | When does it remain valid? |
| Aliasing | Who may access it simultaneously? |
| Locking | What protects mutable state? |
| Atomics | What ordering is required? |
| RCU | What grace-period guarantee exists? |
| Context | Where may this function execute? |
| Sleepability | May this path block? |
| Allocation | Which allocation constraints apply? |
| Callback | Who invokes this function and when? |
| DMA | When is device access valid? |
| MMIO | What access/order constraints apply? |
| ABI | What binary representation is required? |
| Architecture | What assumptions are architecture-specific? |
| Errors | Which failures and rollback rules exist? |
| Security | Which privilege/trust boundaries apply? |
| Temporal | What must happen before/after what? |

This is the **contract surface** of a migration unit.

---

## 300. Temporal Contracts

Ordinary pre/postconditions are insufficient for kernel code.

Consider:

```text
register callback
     ↓
callback may execute
     ↓
cancel
     ↓
wait for quiescence
     ↓
free callback object
```

The essential property is temporal:

```text
FREE(object)
    occurs after
CALLBACK_QUIESCENT
```

Represent:

```rust
struct TemporalContract {
    before: Event,
    after: Event,
    relation: TemporalRelation,
}
```

Relations:

```text
Before
After
During
Until
UntilGracePeriod
UntilCompletion
Eventually
NeverAfter
```

This becomes extremely important for workqueues, timers, RCU, deferred freeing and
asynchronous drivers.

---

## 301. Concurrency Contracts

Concurrency should become a formal contract rather than comments.

Example:

```text
C-17
Object:
    foo
State:
    foo->state
Protection:
    foo->lock
Readers:
    foo_read()
Writers:
    foo_update()
Required:
    writer holds foo->lock
Allowed:
    readers hold foo->lock
```

For atomics:

```text
A-03
Variable:
    foo->state
Operation:
    atomic_cmpxchg
Ordering:
    acquire/release
Synchronization role:
    publication
```

The Rust design must explicitly preserve the synchronization role, not merely translate the
operation to an `Atomic*` type.

---

## 302. Context Contracts

A function contract should contain:

```text
CallableContexts
RequiredContext
MaySleep
MayAllocate
AllowedAllocationModes
IRQState
PreemptionRequirements
RCURequirements
```

Example:

```text
foo_update()
callable:
    PROCESS
may_sleep:
    true
allocation:
    GFP_KERNEL
requires:
    no spinlock held
```

Another:

```text
foo_irq()
callable:
    HARDIRQ
may_sleep:
    false
allocation:
    GFP_ATOMIC only
requires:
    IRQ-safe synchronization
```

The Rust API design can then encode or enforce these restrictions where practical.

---

## 303. API Contract Generation

One of the strongest uses of the contract layer is generating candidate Rust APIs.

Suppose KSIR says:

```text
foo->state
    mutable
    protected_by = foo->lock
```

The contract becomes:

```text
MutableStateAccess:
    requires lock ownership
```

Rust Design IR can then consider:

```rust
struct Foo {
    state: SpinLock<State>,
}
```

with:

```rust
impl Foo {
    fn update(&self, ...) {
        let mut state = self.state.lock();
        ...
    }
}
```

The important architectural rule:

```text
Contract → permits/prohibits design choices
```

rather than:

```text
LLM → invents API → analyzer tries to justify it
```

---

## 304. Rust Design Alternatives

A contract should permit multiple valid designs.

Example:

```text
Contract:
    mutable access serialized by lock L
```

Possible designs:

```text
D1:
    SpinLock<T>
D2:
    Mutex<T>
D3:
    RwLock<T>
D4:
    Atomic<T>
D5:
    per-CPU ownership
D6:
    actor-like serialized execution
```

The design agent proposes candidates.

The contract verifier determines:

```text
preserves invariants?
preserves context restrictions?
preserves ordering?
preserves ABI?
preserves lifetime?
```

There is no need for the system to declare one representation universally "best".

---

## 305. Design Obligation

Every design choice should generate obligations.

```text
Design:
    Arc<Foo>

Obligations:
    O1:
        all ownership transfers correspond to refcount acquisition

    O2:
        final release corresponds to C destruction

    O3:
        no C path depends on intrusive layout

    O4:
        callback lifetime remains valid

    O5:
        RCU semantics are not accidentally replaced by reference counting
```

This prevents the classic migration error:

```text
C refcount
    ↓
Rust Arc
    ↓
"equivalent"
```

without demonstrating the required semantics.

---

## 306. Unsafe Boundary Generation

The contract engine should explicitly enumerate unsafe operations.

Example:

```c
foo = container_of(node, struct foo, node)
```

Rust design:

```text
container_of equivalent
```

generates:

```text
UnsafeObligation U-42
must establish:
    node belongs to Foo::node
    containing object is alive
    offset is correct
    pointer alignment valid
    provenance valid
    no conflicting mutable alias
```

Then:

```rust
unsafe {
    ...
}
```

is not accepted merely because the compiler accepts it.

The unsafe block is a **proof obligation carrier**.

---

## 307. Unsafe Budget

The migration system should track unsafe structurally.

```text
MigrationUnit
├── unsafe_blocks
├── unsafe_functions
├── FFI boundaries
├── raw pointer operations
├── architecture intrinsics
└── unresolved unsafe obligations
```

Example:

```text
UnsafeSummary
blocks:
    17
fully justified:
    12
partially justified:
    3
unresolved:
    2
status:
    BLOCKED
```

No aggregate "95% safe" metric.

A single unresolved critical lifetime obligation can block the unit.

---

## 308. Contract-to-Test Generation

Contracts should generate verification requirements.

Example:

```text
Invariant:
    object remains alive until final reference release
```

generates:

```text
Test:
    acquire reference
    remove publication
    release publication reference
    continue using acquired reference
    release final reference
    verify destruction occurs once
```

For locking:

```text
Invariant:
    field mutation requires lock L
```

generate:

```text
Test:
    concurrent writer/writer
    writer/reader
    unlocked access negative case
```

For RCU:

```text
Invariant:
    reclamation occurs only after grace period
```

generate:

```text
reader active
remove object
attempt reclamation
verify object remains valid
complete grace period
verify reclamation
```

The exact tests depend on the subsystem and available instrumentation.

---

## 309. Contract Differential Testing

The C implementation becomes the behavioral reference **only for behavior that has actually
been characterized**.

For a migration pair:

```text
C implementation
      │
      ├── input I
      ▼
  observation OC

Rust implementation
      │
      ├── input I
      ▼
  observation OR
```

Then compare:

```text
OC ↔ OR
```

across contract dimensions:

```text
return
error state
resource lifetime
synchronization
observable I/O
security behavior
ABI
```

Not every internal representation must match.

The requirement is:

```text
preserve specified contract
```

not:

```text
produce identical implementation
```

---

## 310. Contract Refinement

The migration should be treated as refinement.

```text
C semantic behavior
        │
        ▼
Kernel Contract
        │
        ▼
Rust Design
        │
        ▼
Rust Implementation
```

Each arrow requires evidence.

Formally:

```text
C ⊨ Contract
```

means the reconstructed contract is supported by evidence about C.

Then:

```text
Rust ⊨ Contract
```

means the Rust implementation satisfies the same contract.

Therefore the migration argument becomes:

```text
C satisfies Contract
+
Rust satisfies Contract
───────────────────────
Contract preserved
```

subject to the contract's scope and completeness.

This is substantially stronger than source-to-source equivalence.

---

## 311. Contract Completeness

A dangerous failure mode is proving a contract that is too weak.

Example:

```text
Contract:
    foo() returns 0 on success.
```

Rust does the same.

Technically:

```text
PASS
```

But perhaps the C function also guarantees:

```text
lock state
reference ownership
callback registration
memory ordering
device state
```

Therefore contract completeness must be checked.

Introduce:

```text
ContractCoverage
```

across:

```text
ownership
lifetime
concurrency
context
effects
callbacks
ABI
errors
security
temporal behavior
```

Example:

```text
Contract Coverage
ownership      COMPLETE
lifetime       COMPLETE
locking        COMPLETE
context        COMPLETE
callbacks      PARTIAL
ABI            COMPLETE
security       UNKNOWN
```

The contract cannot become "verified" merely because its currently modeled pieces pass.

---

## 312. Semantic Coverage vs Test Coverage

These are different.

```text
Test coverage:
    92%

Semantic coverage:
    61%
```

could legitimately occur.

Test coverage asks:

> ### **How much code executed?**

Semantic coverage asks:

> ### **How much of the relevant kernel contract has been reconstructed?**

A migration should require both appropriate test evidence and adequate semantic coverage.

---

## 313. Contract Completeness Gate

A release gate could require:

| ID | Requirement |
| --- | --- |
| G-CONTRACT-001 | No critical contract domain UNKNOWN |
| G-CONTRACT-002 | No unresolved critical conflicts |
| G-CONTRACT-003 | All exported ABI contracts reconstructed |
| G-CONTRACT-004 | All asynchronous lifetime contracts reconstructed |
| G-CONTRACT-005 | All mutable shared-state protection contracts reconstructed |
| G-CONTRACT-006 | All unsafe obligations resolved |
| G-CONTRACT-007 | Configuration scope explicitly recorded |
| G-CONTRACT-008 | Architecture assumptions explicitly recorded |

Only then:

```text
AUTHORIZED_FOR_IMPLEMENTATION
```

or later:

```text
RELEASE_ELIGIBLE
```

depending on which gate is being applied.

---

## 314. Contract Compiler

This suggests a new component:

```text
rfl-contract/
```

Architecture:

```text
KSIR
 │
 ├── ownership facts
 ├── lifetime facts
 ├── concurrency facts
 ├── context facts
 ├── effects
 ├── callbacks
 ├── ABI
 └── architecture
        │
        ▼
Contract Compiler
        │
        ├── Preconditions
        ├── Postconditions
        ├── Invariants
        ├── Temporal obligations
        ├── Safety obligations
        ├── Differential obligations
        └── Verification requirements
        │
        ▼
Kernel Contract
```

Potential crate layout:

```text
crates/
├── rfl-contract-types/
├── rfl-contract-normalize/
├── rfl-contract-infer/
├── rfl-contract-coverage/
├── rfl-contract-diff/
├── rfl-contract-verify/
└── rfl-contract-gates/
```

---

## 315. Agent Boundary

The contract compiler should itself be mostly deterministic.

LLMs can assist with:

```text
candidate invariant extraction
semantic interpretation
counterexample generation
candidate Rust designs
test generation
documentation
```

But the authoritative contract pipeline remains:

```text
KSIR facts
    ↓
deterministic contract rules
    ↓
contract artifact
```

The LLM can propose:

```text
Hypothesis H17:
    list membership constitutes ownership transfer
```

but cannot silently transform that into:

```text
OwnershipContract = TRANSFERRED
```

without evidence.

---

## 316. Contract Review Agent

A dedicated adversarial agent should attack the contract itself.

Its task is not:

```text
"Does the Rust code look good?"
```

but:

```text
"What important C behavior is missing from this contract?"
```

It should search for:

```text
unmodeled side effects
unmodeled callbacks
hidden ownership transfers
implicit locking
conditional behavior
architecture branches
error paths
rollback paths
deferred execution
publication races
lifetime extensions
security boundaries
ABI assumptions
```

Output:

```text
ContractGap
├── missing invariant
├── missing precondition
├── missing temporal relation
├── missing effect
├── missing configuration scope
└── evidence
```

This is a critical anti-completeness-theater mechanism.

---

## 317. Contract Counterexample Engine

The next powerful capability is to generate **counterexamples to proposed contracts**.

Suppose:

```text
Contract:
    object may be freed immediately after list removal
```

The counterexample engine searches:

```text
list removal
     ↓
RCU reader?
     ↓
callback?
     ↓
refcount?
     ↓
other pointer?
```

If it finds:

```text
reader can retain pointer after removal
```

then:

```text
CONTRACT REJECTED
```

with evidence:

```text
CEX-17
reader path:
    A → B → C
object:
    foo
removal:
    D
reclamation:
    E
ordering:
    E may occur before C completes
```

This turns contract review into an adversarial search problem.

---

## 318. Migration Unit Contract Package

A migration unit should eventually contain:

```text
migration/
└── MU-004821/
    ├── scope.json
    ├── snapshot.json
    ├── variant.json
    ├── ksir.json
    ├── contract.json
    ├── obligations.json
    ├── unknowns.json
    ├── conflicts.json
    ├── design.json
    ├── implementation.json
    ├── verification.json
    └── evidence/
```

This package is independently inspectable.

A reviewer should be able to start from:

```text
Rust line
```

and trace backward:

```text
Rust line
 ↓
design element
 ↓
contract obligation
 ↓
invariant
 ↓
KSIR fact
 ↓
observation
 ↓
source/build variant
```

That is the desired evidence chain.

---

## 319. End-to-End Proof Chain

The architecture is now:

```text
SOURCE
  │
  ▼
BUILD VARIANT
  │
  ▼
OBSERVATION
  │
  ▼
RECONCILED FACT
  │
  ▼
KSIR
  │
  ▼
INVARIANT
  │
  ▼
KERNEL CONTRACT
  │
  ▼
RUST DESIGN
  │
  ▼
SAFETY OBLIGATION
  │
  ▼
RUST IMPLEMENTATION
  │
  ▼
VERIFICATION
  │
  ▼
DIFFERENTIAL VERIFICATION
  │
  ▼
ADVERSARIAL VERIFICATION
  │
  ▼
EVIDENCE BUNDLE
  │
  ▼
MIGRATION CERTIFICATE
```

Every arrow is a potential failure boundary.

That is exactly where the system should spend engineering effort.

---

## 320. The Next Layer

With semantic reconstruction and contract reconstruction defined, the remaining major
problem is now:

> ### **How does RFL-AE construct a Rust representation that preserves those contracts without simply reproducing the C architecture?**

That requires the **Rust Design IR** to become formal enough to compare candidate designs
before implementation.

The next layer should therefore define:

```text
Rust Design IR
├── type mapping
├── ownership mapping
├── lifetime mapping
├── synchronization mapping
├── context/API mapping
├── callback mapping
├── FFI boundaries
├── representation invariants
├── unsafe obligations
├── architecture abstractions
├── error mapping
├── initialization/teardown
└── contract-preservation proof obligations
```

The critical transition will be:

```text
Kernel Contract
             │
             ▼
Candidate Rust Designs
             │
             ├── Design A
             ├── Design B
             ├── Design C
             └── rejected designs
                    │
                    ▼
     Contract Checker
             │
             ▼
 IMPLEMENTATION_AUTHORIZED
```

This is where the architecture becomes capable of handling the hardest question in the
project:

> ### **When should the system preserve a C mechanism, when should it replace that mechanism with a Rust-native abstraction, and how can it prove that the replacement preserves the kernel contract?**
