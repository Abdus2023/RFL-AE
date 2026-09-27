# RFL-AE — Rust Design IR

**Sections 321–356** — the decision boundary between recovered kernel semantics and generated
Rust.

> Continues the numbering of [ARCHITECTURE.md](ARCHITECTURE.md) (§1–§51),
> [SPECIFICATION.md](SPECIFICATION.md) (§52–§80), [FORMAL-CORE.md](FORMAL-CORE.md)
> (§81–§107), [PROTOCOL.md](PROTOCOL.md) (§109–§135), [RUST-CORE.md](RUST-CORE.md)
> (§136–§172), [TRANSITIONS.md](TRANSITIONS.md) (§173–§203), [KSIR.md](KSIR.md)
> (§204–§250), [RECONSTRUCTION.md](RECONSTRUCTION.md) (§251–§291), and
> [CONTRACTS.md](CONTRACTS.md) (§292–§320). §108 does not exist in the source.
>
> **Note on derived material:** the collapsed ASCII figures are redrawn in `text` fences from
> computed column layouts. No content was added beyond that. The §353 heading keeps the
> source's `→`; it is not used as a link target.

## Contents

| Part | Sections | |
| --- | --- | --- |
| [I. Design IR foundations](#321-rust-design-ir-root) | 321–328 |
| [II. Synchronization, context, enforcement](#329-pinning-obligation) | 329–336 |
| [III. Boundaries, architecture, errors](#337-ffi-boundary) | 337–344 |
| [IV. Callbacks, search, gates](#345-callback-design) | 345–351 |
| [V. Obligations and the pipeline](#352-generated-safety-obligations) | 352–356 |

---

The Rust Design IR should be the **decision boundary between recovered kernel semantics and
generated Rust**.

It must prevent this failure:

```text
C source
  ↓
LLM translation
  ↓
Rust source
  ↓
"looks idiomatic"
```

The correct pipeline is:

```text
Kernel Contract
      ↓
Design Space
      ↓
Candidate Rust Design
      ↓
Contract Preservation Analysis
      ↓
Unsafe Obligation Extraction
      ↓
ABI / Context / Concurrency Checks
      ↓
AUTHORIZED_FOR_IMPLEMENTATION
      ↓
Rust implementation
```

The design IR is therefore not an AST and not a Rust code generator.

It is a **semantic design specification**.

---

## 321. Rust Design IR Root

Conceptually:

```rust
struct RustDesign {
    design_id: DesignId,

    snapshot: KernelSnapshotId,
    variant: BuildVariantId,

    migration_unit: MigrationUnitId,

    source_contract: ContractId,

    types: Vec<RustType>,
    traits: Vec<RustTrait>,
    lifetimes: Vec<RustLifetime>,

    ownership: Vec<OwnershipMapping>,
    concurrency: Vec<ConcurrencyMapping>,
    context: Vec<ContextMapping>,

    callbacks: Vec<CallbackMapping>,

    ffi_boundaries: Vec<FFIBoundary>,

    initialization: InitializationModel,
    teardown: TeardownModel,

    errors: ErrorMapping,

    architecture: ArchitectureMapping,

    unsafe_obligations: Vec<UnsafeObligation>,

    preservation_claims: Vec<PreservationClaim>,

    rejected_alternatives: Vec<RejectedDesign>,

    evidence: EvidenceSet,

    status: DesignStatus,
}
```

The important field is:

```text
source_contract
```

Every design must declare:

> ### **Which contract am I attempting to preserve?**

---

## 322. Design Is Not Implementation

A design may say:

```text
Foo:
    ownership = Arc-like shared ownership
```

without saying:

```rust
struct Foo {
    ...
}
```

This allows architectural alternatives to be evaluated before code exists.

For example:

```text
Design A:
    intrusive reference counting
Design B:
    Arc<T>
Design C:
    explicit lifetime + borrowed references
Design D:
    subsystem-owned arena
```

The contract checker can eliminate designs before implementation effort is spent.

---

## 323. Representation Mapping

Every important C semantic object needs a mapping.

```text
C Semantic Object
         ↓
Rust Design Element
```

Example:

```text
C:
    struct foo
Rust:
    struct Foo
```

But the mapping must include more than naming:

```text
C layout
C ownership
C lifetime
C synchronization
C callbacks
C ABI
       ↓
Rust representation
```

Thus:

```rust
struct TypeMapping {
    source_type: TypeId,
    target_type: RustTypeId,

    layout_relation: LayoutRelation,
    ownership_relation: OwnershipRelation,
    lifetime_relation: LifetimeRelation,
    alias_relation: AliasRelation,

    preserved_invariants: Vec<InvariantId>,
    obligations: Vec<ObligationId>,
}
```

---

## 324. Rust Type Taxonomy

The design IR should distinguish several kinds of Rust types.

```text
RustType
├── Struct
├── Enum
├── Union
├── Newtype
├── Alias
├── Primitive
├── Pointer
├── Reference
├── Slice
├── TraitObject
├── FunctionPointer
├── FFIType
├── OpaqueType
└── ArchitectureSpecific
```

And semantic roles:

```text
SemanticRole
├── OwnedResource
├── BorrowedView
├── SharedResource
├── RefCountedResource
├── RcuResource
├── LockedState
├── AtomicState
├── DeviceResource
├── DmaBuffer
├── MmioRegion
├── Callback
├── Token
├── Handle
└── OpaqueKernelObject
```

This allows:

```rust
struct Foo
```

to be distinguished from:

```text
Foo = shared concurrently accessed kernel object
```

---

## 325. Ownership Mapping

The central question is:

```text
C ownership semantics
        ↓
Rust ownership semantics
```

Possible mappings:

```text
C Owned         → Box<T>
C Borrowed      → &T / &mut T
C Refcounted    → Arc<T> / custom refcount
C RCU-protected → RCU-specific abstraction
C PerCPU        → per-CPU abstraction
C Device-owned  → device-lifetime token
C DMA-owned     → DMA buffer abstraction
C Opaque        → Opaque<T>
```

These are **candidate mappings**, not automatic translations.

The design checker must validate whether the proposed Rust abstraction actually preserves the
C semantics.

---

## 326. Ownership Transfer Events

A Rust type alone cannot represent every ownership transfer.

The IR therefore needs:

```rust
struct OwnershipMapping {
    source: OwnershipContractId,
    target: RustOwnershipModel,

    acquire_mapping: Vec<OperationMapping>,
    release_mapping: Vec<OperationMapping>,
    transfer_mapping: Vec<OperationMapping>,

    destruction_mapping: Option<OperationMapping>,

    obligations: Vec<ObligationId>,
}
```

Example:

```text
C:
    foo_get()
        → increment refcount
Rust:
    Foo::clone_handle()
        → increment shared ownership

C:
    foo_put()
        → decrement
Rust:
    Drop<FooHandle>
        → decrement
```

The design must prove that the event correspondence is correct.

---

## 327. Lifetime Design

Rust lifetime parameters are only one possible representation.

The IR needs a richer model:

```text
RustLifetime
├── lexical
├── ownership-derived
├── token-derived
├── scoped
├── reference-counted
├── RCU-scoped
├── callback-scoped
├── device-scoped
└── static
```

Example:

```text
C:
    object valid while device exists
Rust design:
    Device<'a> → Object<'a>
```

Another:

```text
C:
    object survives independently through refcount
Rust:
    OwnedHandle<Foo>
```

Another:

```text
C:
    pointer valid only during RCU read-side section
Rust:
    RcuGuard<'a, Foo>
```

The system should prefer the **smallest abstraction that faithfully represents the contract**,
not the most sophisticated Rust type.

---

## 328. Self-Referential Structures

Kernel code frequently contains structures whose addresses or embedded members participate in
intrusive relationships.

The design IR needs explicit:

```text
SelfReference
IntrusiveMembership
ContainerOfRelation
PinnedAddressRequirement
```

Example:

```text
Foo
├── list_node
└── data
```

where:

```text
list_node → containing Foo
```

The design checker asks:

```text
Does Foo require stable address?
Can Foo move?
Can list_node outlive Foo?
Who removes list_node?
```

If the answer requires stable address:

```rust
Pin<Foo>
```

may become a candidate.

But again:

```text
self-reference ≠ automatically Pin
```

The actual address-stability contract must be established first.

---

## 329. Pinning Obligation

A proposed pinned design should carry:

```text
P-001
Requirement:
    object address remains stable from publication until removal.
Evidence:
    intrusive pointer relationship
    callback stores address
    asynchronous invocation
Design:
    Pin<Foo>
Verification:
    no move after publication
```

If the system cannot establish the address-stability requirement:

```rust
Pin<Foo>
```

should not be introduced merely because the C structure "looks self-referential".

---

## 330. Synchronization Mapping

C:

```c
spin_lock(&foo->lock)
...
spin_unlock(&foo->lock)
```

does not necessarily map directly to one Rust primitive.

The design IR records:

```rust
ConcurrencyMapping {
    source_lock: LockId,
    target_primitive: RustSyncPrimitive,

    protected_state: Vec<RustFieldId>,

    acquisition_mapping,
    release_mapping,

    irq_behavior,
    preemption_behavior,

    ordering_obligations,
}
```

Candidate:

```rust
SpinLock<T>
```

but alternatives could include:

```text
RawSpinLock + manually protected fields
Atomic<T>
per-CPU state
lock-free structure
```

The contract checker evaluates them.

---

## 331. Lock Encapsulation

One important Rust-native transformation is moving from:

```text
C:
    lock exists beside data
```

to:

```text
Rust:
    lock owns the data it protects
```

Example:

```c
struct foo {
    spinlock_t lock;
    int state;
};
```

Candidate:

```rust
struct Foo {
    state: SpinLock<State>,
}
```

This is a stronger abstraction.

But it creates obligations:

```text
O1:
    all C access paths to state are represented
O2:
    no external path bypasses lock
O3:
    lock ordering remains valid
O4:
    interrupt-context semantics remain valid
```

If those cannot be established, encapsulation is not yet justified.

---

## 332. Lock Ordering

The design IR should retain lock-order constraints.

Example:

```text
C:
    acquire A
    acquire B
```

creates:

```text
A → B
```

in the lock-order graph.

If another path:

```text
B → A
```

exists:

```text
Conflict:
    potential lock-order cycle
```

A Rust redesign must preserve or deliberately eliminate the cycle.

It cannot simply rename:

```text
spinlock A → Mutex A
```

and assume the problem disappears.

---

## 333. Atomic Mapping

The design IR must represent:

```text
operation
ordering
width
atomicity
synchronization role
```

not just:

```rust
AtomicU32
```

Example:

```c
atomic_set_release(&foo->state, READY)
```

candidate:

```rust
foo.state.store(READY, Ordering::Release)
```

The preservation relation is:

```text
C Release publication
        ↕
Rust Release publication
```

The checker must verify the ordering semantics.

---

## 334. RCU Design Mapping

RCU should not automatically become:

```rust
Arc<T>
```

because:

```text
RCU lifetime
```

and:

```text
reference-count lifetime
```

are different synchronization models.

The design IR needs:

```rust
RcuMapping {
    source_contract,
    reader_guard,
    publication,
    update,
    removal,
    grace_period,
    reclamation,
    callback,
}
```

Candidate design:

```rust
RcuGuard<'a, Foo>
```

with explicit:

```text
reader lifetime
```

and:

```text
reclamation mechanism
```

---

## 335. Context-Preserving API Design

A powerful Rust migration opportunity is to encode kernel context constraints into APIs.

Suppose:

```text
foo():
    may_sleep = false
```

while:

```text
foo_blocking():
    may_sleep = true
```

The design system can distinguish them at the type/API level.

Conceptually:

```text
AtomicContext
ProcessContext
```

and APIs requiring:

```text
ProcessContext
```

cannot be invoked from a context where sleeping is forbidden.

Whether such encoding is practical depends on the kernel integration model.

The design IR should therefore distinguish:

```text
ENFORCED_BY_TYPE
ENFORCED_BY_API
ENFORCED_BY_RUNTIME
DOCUMENTED_ONLY
UNREPRESENTED
```

That classification is valuable.

---

## 336. Contract Enforcement Strength

For every invariant:

```text
Invariant
    ↓
Enforcement mechanism
```

Possible states:

```text
TYPE_ENFORCED
BORROW_CHECKER_ENFORCED
TRAIT_ENFORCED
API_ENFORCED
STATIC_ANALYSIS_ENFORCED
RUNTIME_ENFORCED
TEST_ENFORCED
DOCUMENTED_ONLY
UNENFORCED
```

Example:

```text
C:
    state must be accessed under lock
Rust:
    state private inside SpinLock<State>
Enforcement:
    API + visibility + type structure
```

This is stronger than simply writing:

```rust
// caller must hold lock
```

The migration system should measure this distinction without turning it into a subjective
score.

---

## 337. FFI Boundary

Every C/Rust boundary becomes an explicit design object.

```rust
struct FFIBoundary {
    boundary_id: FfiBoundaryId,

    c_symbol: SymbolId,
    rust_symbol: RustSymbolId,

    calling_convention: CallingConvention,

    parameter_mapping: Vec<ParameterMapping>,
    return_mapping: ReturnMapping,

    ownership_transfer: OwnershipTransfer,

    lifetime_contract: LifetimeContract,

    layout_contract: LayoutContract,

    thread_context: ContextContract,

    unsafe_obligations: Vec<UnsafeObligation>,

    evidence: EvidenceSet,
}
```

This allows the project to deliberately minimize FFI rather than letting it emerge
accidentally.

---

## 338. FFI Trust Boundary

The system should classify boundaries:

```text
PURE_SAFE
SAFE_WRAPPER
UNSAFE_WRAPPER
RAW_FFI
OPAQUE_EXTERNAL
```

Example:

```rust
// Rust:
safe fn foo()

// internally:
unsafe extern "C" {
    fn c_foo(...);
}
```

The safe wrapper needs a proof obligation:

```text
SafeWrapperContract
    preconditions enforced
    lifetime valid
    ABI valid
    thread/context valid
    ownership valid
```

Otherwise it must remain unsafe.

---

## 339. ABI-Preserving vs ABI-Breaking Migration

The design IR should explicitly classify:

```text
ABI_MODE
├── PreserveExistingABI
├── IntroduceCompatibilityShim
├── InternalABIOnly
└── DeliberatelyBreakABI
```

A kernel-internal migration may allow a redesigned representation.

An exported or externally consumed symbol may not.

Therefore:

```text
C struct layout
```

does not automatically constrain:

```text
internal Rust struct layout
```

unless the contract says it does.

This avoids unnecessary C-shaped Rust.

---

## 340. Architecture Mapping

Rust design should separate:

```text
portable semantics
```

from:

```text
architecture implementation
```

For example:

```text
Kernel Contract
    ↓ atomic ordering requirement
Rust Design
    ↓ portable atomic abstraction
Architecture backend
    ↓ x86 / arm64 / riscv implementation
```

The design checker must verify that architecture-specific requirements are preserved.

---

## 341. Error Mapping

C frequently uses:

```text
negative errno
NULL
ERR_PTR()
special sentinel
partial result
```

Rust candidates include:

```text
Result<T, E>
Option<T>
Result<Option<T>, E>
typed error enum
```

But the mapping must preserve observable semantics.

Example:

```text
C:
    NULL = "not found"
Rust:
    Option<T>
```

versus:

```text
C:
    NULL = allocation failure
```

which might require:

```text
Result<T, AllocError>
```

The design engine must derive the distinction from control/dataflow and caller behavior.

---

## 342. Error Contract

```rust
struct ErrorContract {
    success_states: Vec<State>,
    failure_states: Vec<FailureState>,

    sentinel_meanings: Vec<SentinelMeaning>,

    rollback_requirements: Vec<RollbackRequirement>,

    resource_cleanup: Vec<CleanupRequirement>,

    propagation: ErrorPropagationGraph,
}
```

This prevents a particularly dangerous migration:

```text
C error paths
    ↓
Rust Result
    ↓
one generic Error
```

which may erase semantic distinctions.

---

## 343. Initialization Design

Kernel initialization often has ordering constraints.

Model:

```text
InitContract
├── prerequisites
├── initialization order
├── publication point
├── failure rollback
├── partial initialization
├── concurrency visibility
└── teardown relation
```

Example:

```text
allocate
  ↓
initialize lock
  ↓
initialize callback
  ↓
publish object
```

The Rust design must not publish:

```text
Foo
```

before required initialization has completed.

This naturally leads to:

```text
partially initialized object
```

being treated as a distinct design problem.

---

## 344. Typestate Candidate

Where useful, the design IR can propose:

```text
Foo<Uninitialized>
Foo<Initialized>
Foo<Published>
Foo<Running>
Foo<Stopping>
Foo<Stopped>
```

But this should only be introduced when the state machine is supported by the contract.

The system should not generate typestate for every C enum.

The question is:

> ### **Does the state transition represent an invariant boundary that materially benefits from static enforcement?**

If yes, candidate typestate.

If not, ordinary state representation may be preferable.

---

## 345. Callback Design

A C callback:

```c
void (*callback)(struct foo *);
```

may become:

```rust
trait Callback {
    fn call(&self, foo: ...);
}
```

or:

```text
FnOnce/FnMut/Fn
```

or remain:

```rust
extern "C" fn(...)
```

The design IR needs to preserve:

```text
callback lifetime
execution context
cancellation
reentrancy
ownership
thread affinity
```

A closure type by itself does not establish these properties.

---

## 346. Reentrancy

The contract system should explicitly detect:

```text
foo()
 ↓
callback()
 ↓
foo()
```

or indirect cycles.

Design representation:

```rust
ReentrancyContract {
    allowed: bool,
    recursion_scope,
    lock_state,
    callback_paths,
}
```

This matters because Rust's borrow structure may expose reentrancy that the C implementation
handled through carefully scoped locks or temporary state.

---

## 347. Design Rejection

The system should retain rejected designs.

```text
RejectedDesign
├── candidate
├── rejection_reason
├── violated_contracts
├── violated_obligations
├── evidence
└── timestamp
```

Example:

```text
Design D3:
    Arc<Foo>
REJECTED
violates:
    I-017 RCU grace-period reclamation
reason:
    reference counting does not preserve required grace-period semantics
evidence:
    contract C-17
```

This is valuable historical information.

It prevents the same agent—or future agent—from rediscovering and re-proposing the same
invalid architecture.

---

## 348. Design Search

The LLM is most useful here as a **candidate generator**.

Input:

```text
Kernel Contract
```

LLM proposes:

```text
D1
D2
D3
...
```

Deterministic machinery then evaluates:

```text
Contract preservation
ABI
Context
Concurrency
Lifetime
Unsafe obligations
Architecture
```

The loop becomes:

```text
                 ┌──────────┐
                 │ Kernel   │
                 │ Contract │
                 └─────┬────┘
                       │
                       ▼
              Candidate Generator
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
           D1         D2         D3
            │          │          │
            └──────────┼──────────┘
                       ▼
               Contract Checker
                       │
           ┌──────────┼──────────┐
           ▼          ▼          ▼
        REJECT     REVISE     ACCEPT
                                 │
                                 ▼
                        Design Obligations
```

This is a much safer role for an LLM than allowing it to autonomously rewrite a subsystem.

---

## 349. Design Selection Without "Best"

The system should not use:

```text
best design confidence = 0.93
```

Instead, classify designs by constraints:

```text
D1:
    all critical contracts preserved
    unsafe obligations = 2 unresolved

D2:
    all critical contracts preserved
    ABI incompatible

D3:
    RCU contract unresolved

D4:
    all required contracts preserved
    implementation complexity remains OPEN
```

Then the engineering authority chooses or authorizes one.

The system informs the decision; it does not hide architectural tradeoffs behind a score.

---

## 350. Design Gate

A candidate can enter implementation only if:

```text
DESIGN-GATE

[ ] source contract identified
[ ] all critical invariants mapped
[ ] ownership mapping complete
[ ] lifetime mapping complete
[ ] synchronization mapping complete
[ ] context mapping complete
[ ] callback mapping complete
[ ] ABI mapping complete where applicable
[ ] architecture assumptions explicit
[ ] error semantics mapped
[ ] initialization/teardown mapped
[ ] unsafe obligations enumerated
[ ] no unresolved critical conflicts
[ ] no unresolved critical unknowns
[ ] verification plan generated
```

Then:

```text
AUTHORIZED_FOR_IMPLEMENTATION
```

is a protocol event, not an LLM decision.

---

## 351. Rust Implementation Boundary

The implementation agent receives:

```text
RustDesign
+
KernelContract
+
VerificationPlan
+
AllowedScope
```

It does **not** receive unrestricted authority over the repository.

Its authority is:

```text
IMPLEMENTATION
```

within:

```text
migration unit
worktree
authorized paths
authorized commit scope
```

It produces:

```text
ImplementationArtifact
```

but cannot produce:

```text
VERIFIED
```

---

## 352. Generated Safety Obligations

The design phase should generate a concrete unsafe ledger:

```text
UnsafeObligation U-001
├── source invariant
├── Rust operation
├── required property
├── proof method
├── evidence
└── status
```

Example:

```text
U-001
Rust operation:
    raw pointer dereference
Required:
    pointer non-null
Proof method:
    preceding validated lookup
Status:
    PROVISIONAL
```

Another:

```text
U-002
Rust operation:
    FFI call
Required:
    ABI layout compatibility
Proof:
    compile-time layout assertions + emitted ABI inspection
Status:
    UNVERIFIED
```

This becomes the direct input to verification.

---

## 353. Rust Design IR → Verification Plan

The chain becomes automatic:

```text
Contract
   ↓
Design
   ↓
Obligations
   ↓
Verification Requirements
```

Example:

```text
C invariant:
    object cannot move after publication
Rust design:
    Pin<Foo>
obligation:
    no movement after publication
verification:
    static construction analysis
    Pin API restrictions
    runtime address-stability test
```

Another:

```text
C:
    field protected by spinlock
Rust:
    SpinLock<State>
verification:
    concurrent access test
    negative bypass test
    lock-order test
```

The design is therefore directly connected to the QA system.

---

## 354. The Complete Migration Compiler

At this point the architecture starts looking like a compiler pipeline:

```text
             Linux Kernel
                   │
                   ▼
         ┌──────────────────┐
         │ Frontend         │
         │ C/compiler facts │
         └─────────┬────────┘
                   ▼
         ┌──────────────────┐
         │ Semantic         │
         │ Reconstruction   │
         └─────────┬────────┘
                   ▼
                 KSIR
                   │
                   ▼
         ┌──────────────────┐
         │ Contract         │
         │ Reconstruction   │
         └─────────┬────────┘
                   ▼
              Contract IR
                   │
                   ▼
         ┌──────────────────┐
         │ Rust Design IR   │
         └─────────┬────────┘
                   ▼
         ┌──────────────────┐
         │ Rust Backend     │
         └─────────┬────────┘
                   ▼
              Rust Source
                   │
                   ▼
         ┌──────────────────┐
         │ Verification     │
         │ + Differential   │
         └─────────┬────────┘
                   ▼
          Migration Artifact
```

The analogy to a compiler is deliberate.

The LLM operates primarily as a **search/reasoning component inside the compiler pipeline**,
not as the compiler itself.

---

## 355. The Three IRs

The architecture now has three critical intermediate representations:

```text
               C
               │
               ▼
      ┌────────────────┐
      │      KSIR      │
      │ "what exists"  │
      └────────┬───────┘
               │
               ▼
      ┌────────────────┐
      │  Contract IR   │
      │   "what must   │
      │  remain true"  │
      └────────┬───────┘
               │
               ▼
      ┌────────────────┐
      │ Rust Design IR │
      │ "how Rust may  │
      │  realize it"   │
      └────────┬───────┘
               │
               ▼
             Rust
```

This separation is one of the most important architectural decisions in the entire system.

It prevents semantic contamination:

```text
Rust design
     X
     ↓
"therefore C must have meant..."
```

Instead:

```text
C evidence
     ↓
KSIR
     ↓
Contract
     ↓
Rust design
```

The direction is one-way.

---

## 356. Next Critical Problem: Verification Compiler

We now have:

```text
KSIR
Contract
Rust Design IR
Rust implementation
```

The remaining question is:

> ### **How does RFL-AE construct a verification argument strong enough to establish that the Rust implementation preserves the recovered kernel contract?**

That requires a **Verification IR** rather than a loose collection of tests.

The next layer should define:

```text
Verification IR
├── claim
├── invariant under test
├── preconditions
├── test/input generator
├── oracle
├── observation points
├── expected relation
├── static proof obligation
├── dynamic test
├── differential test
├── concurrency test
├── architecture matrix
├── configuration matrix
├── counterexample
├── execution receipt
└── evidence bundle
```

Then the full system becomes:

```text
C
 ↓
KSIR
 ↓
Contract IR
 ↓
Rust Design IR
 ↓
Rust
 ↓
Verification IR
 ↓
Evidence
 ↓
Migration Certificate
```

At that point, the system is no longer merely an AI coding architecture. It is becoming a
**machine-checkable semantic migration framework** whose central product is not Rust source
code, but a traceable argument that a particular Rust implementation preserves a particular,
explicitly scoped Linux kernel contract.
