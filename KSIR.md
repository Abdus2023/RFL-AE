# RFL-AE — Kernel Semantic Intermediate Representation

**Sections 204–250** — KSIR.

> Continues the numbering of [ARCHITECTURE.md](ARCHITECTURE.md) (§1–§51),
> [SPECIFICATION.md](SPECIFICATION.md) (§52–§80), [FORMAL-CORE.md](FORMAL-CORE.md)
> (§81–§107), [PROTOCOL.md](PROTOCOL.md) (§109–§135), [RUST-CORE.md](RUST-CORE.md)
> (§136–§172), and [TRANSITIONS.md](TRANSITIONS.md) (§173–§203). §108 does not exist in the
> source.
>
> **Heading note:** two source headings contained characters that produce
> renderer-dependent anchor slugs — §204's em dash and §243's `→`. Both are written with plain
> wording here so the table-of-contents links resolve identically everywhere.

## Contents

| Part | Sections |
| --- | --- |
| [I. KSIR foundations](#204-ksir-kernel-semantic-intermediate-representation) | 204–208 |
| [II. Pointers, objects, lifetimes](#209-pointer-model) | 209–218 |
| [III. Concurrency & context](#219-concurrency-graph) | 219–226 |
| [IV. Time, memory, architecture](#227-callback-graph) | 227–236 |
| [V. Invariants & queries](#237-invariant-representation) | 237–244 |
| [VI. QA & pipeline](#245-ksir-failure-modes) | 245–250 |

<details>
<summary><strong>Full section index</strong></summary>

204. KSIR: Kernel Semantic Intermediate Representation
205. KSIR Layering
206. KSIR Root
207. Structural Layer
208. Function Model
209. Pointer Model
210. Pointer Ownership
211. Pointer Nullability
212. Aliasing
213. Object Model
214. Storage Classes
215. Lifetime Graph
216. Lifetime Invariant
217. Refcount Model
218. RCU Model
219. Concurrency Graph
220. Synchronization Primitive Taxonomy
221. Execution Context
222. Sleepability
223. Allocation Context
224. Effects System
225. Effect Propagation
226. Call Graph Is Not Enough
227. Callback Graph
228. Deferred Execution
229. Temporal Contracts
230. Memory Ordering
231. Architecture Dependencies
232. ABI Model
233. FFI Boundary
234. User Memory
235. DMA
236. MMIO
237. Invariant Representation
238. Invariant Examples
239. Semantic Classification
240. Evidence-Carrying KSIR
241. KSIR Query Engine
242. High-Value Query
243. KSIR to Rust Design
244. Design Obligations
245. KSIR Failure Modes
246. KSIR Acceptance Criteria
247. KSIR QA
248. The First Real Semantic Benchmark
249. The Full Semantic Pipeline
250. The Architecture Has Now Reached the Important Boundary

</details>

---

# I. KSIR foundations

## 204. KSIR: Kernel Semantic Intermediate Representation

This is the next critical layer.

The protocol tells us **who is allowed to do what**.

KSIR tells us **what the kernel code means**.

The important design decision is:

> ### **KSIR is not an AST with extra annotations. It is a semantic model of the kernel's observable behavior and invariants.**

A C AST can tell us:

```c
foo(struct bar *p)
```

KSIR needs to tell us:

```text
foo()
  receives borrowed pointer
  object lifetime governed by refcount
  field X protected by spinlock L
  callback may execute in softirq context
  allocation forbidden in atomic context
  pointer may be NULL
  publication uses release ordering
  reclamation uses RCU
  ABI representation must remain C-compatible
```

That is the information Rust migration actually needs.


---

## 205. KSIR Layering

Do not make KSIR one giant structure. Use layers.

```text
                       KSIR
                         │
         ┌───────────────┼─────────────────┐
         ▼               ▼                 ▼
    Structural      Behavioral        Contractual
       Layer           Layer             Layer
         │               │                 │
      symbols         effects         invariants
       types         ownership         pre/post
     functions       lifetime           safety
      fields        concurrency           ABI
       calls          context          security
         \               |                 /
          \              |                /
           \             |               /
            └────────────┼──────────────┘
                         ▼
                  Semantic Graph
```

This allows the system to distinguish:

```text
what the source contains
```

from:

```text
what the source means
```

and:

```text
what must remain true after migration
```

---

## 206. KSIR Root

```rust
pub struct Ksir {
    pub snapshot: SnapshotId,

    pub symbols: SymbolTable,
    pub types: TypeTable,
    pub functions: FunctionTable,

    pub objects: ObjectTable,
    pub regions: RegionTable,

    pub ownership: OwnershipGraph,
    pub lifetime: LifetimeGraph,
    pub concurrency: ConcurrencyGraph,
    pub context: ContextGraph,

    pub effects: EffectGraph,
    pub dependencies: SemanticDependencyGraph,

    pub invariants: InvariantTable,
    pub contracts: ContractTable,

    pub abi: AbiModel,
    pub architecture: ArchitectureModel,

    pub evidence: Vec<EvidenceId>,
}
```

The snapshot binding is mandatory.

```text
KSIR(S1) ≠ KSIR(S2)
```

even if the source looks superficially similar.

---

## 207. Structural Layer

The structural layer begins with familiar compiler concepts.

```rust
pub struct Symbol {
    pub id: SymbolId,
    pub name: String,
    pub kind: SymbolKind,
    pub location: SourceLocation,
}

pub enum SymbolKind {
    Function,
    Struct,
    Union,
    Enum,
    Typedef,
    Macro,
    Variable,
    Constant,
    Module,
}
```

But this is only the beginning.

---

## 208. Function Model

A function should contain more than its signature.

```rust
pub struct KsirFunction {
    pub id: FunctionId,

    pub symbol: SymbolId,

    pub parameters: Vec<Parameter>,
    pub return_type: KsirType,

    pub calls: Vec<CallEdge>,
    pub callers: Vec<FunctionId>,

    pub effects: Vec<Effect>,

    pub execution_context: ContextSet,

    pub may_sleep: Sleepability,

    pub allocation_behavior: AllocationBehavior,

    pub locking: LockBehavior,

    pub ownership_effects: Vec<OwnershipEffect>,
    pub lifetime_effects: Vec<LifetimeEffect>,

    pub error_behavior: ErrorBehavior,

    pub abi: AbiContract,

    pub evidence: Vec<EvidenceId>,
}
```

This is where kernel semantics begin appearing.

---

# II. Pointers, objects, lifetimes

## 209. Pointer Model

Pointers are one of the biggest obstacles to automatic C→Rust migration.

A C pointer should not initially be represented as simply:

```rust
*mut T
```

Instead:

```rust
pub struct KsirPointer {
    pub pointee: TypeId,

    pub mutability: Mutability,
    pub nullability: Nullability,
    pub ownership: PointerOwnership,
    pub lifetime: LifetimeRef,

    pub aliasing: AliasingModel,
    pub synchronization: AccessProtection,

    pub address_space: AddressSpace,

    pub provenance: PointerProvenance,

    pub special_role: PointerRole,
}
```

---

## 210. Pointer Ownership

```rust
pub enum PointerOwnership {
    Owned,
    Borrowed,
    Shared,
    RefCounted,
    RcuProtected,
    BorrowedFromUser,
    BorrowedFromKernel,
    DeviceOwned,
    DmaOwned,
    Mmio,
    Intrusive,
    Opaque,
    Unknown,
}
```

`Unknown` is essential.

> A system that forces every C pointer into a confident ownership category will manufacture
> incorrect semantics.

---

## 211. Pointer Nullability

Do not infer nullability merely from the C type. Represent evidence:

```rust
pub enum Nullability {
    NonNullEstablished,
    MayBeNull,
    CheckedBeforeUse,
    SentinelValue,
    Unknown,
}
```

For example:

```c
struct foo *p;
```

does not establish:

```c
p != NULL
```

The KSIR must derive that from control flow, contracts, callers, annotations, assertions, or
execution evidence.

---

## 212. Aliasing

Rust's ownership model requires stronger information than ordinary C type analysis.

Represent:

```rust
pub enum AliasingModel {
    Unique,
    ReadOnlyShared,
    MutableShared,
    InteriorMutable,
    LockDisjoint,
    RcuShared,
    AtomicShared,
    Intrusive,
    Unknown,
}
```

A particularly important distinction:

```text
multiple C pointers
```

does not automatically mean:

```text
Rust mutable aliases are legal
```

The Rust design agent must reconstruct how mutation is synchronized.

---

## 213. Object Model

KSIR needs an explicit object model.

```rust
pub struct KernelObject {
    pub id: ObjectId,

    pub type_id: TypeId,

    pub allocation: AllocationOrigin,
    pub storage: StorageClass,

    pub lifetime: LifetimeId,
    pub ownership: OwnershipModel,
    pub references: ReferenceModel,

    pub synchronization: AccessProtection,

    pub embedded_objects: Vec<ObjectId>,
    pub callbacks: Vec<CallbackId>,

    pub destruction: DestructionModel,
}
```

This lets us model objects that are more complicated than heap allocations.

---

## 214. Storage Classes

```rust
pub enum StorageClass {
    Stack,
    Static,
    Global,
    Slab,
    Page,
    Vmalloc,
    PerCpu,
    DeviceManaged,
    Dma,
    Mmio,
    Embedded,
    UserMemory,
    Unknown,
}
```

This matters because:

```text
kmalloc object
```

and:

```text
embedded struct
```

have completely different Rust ownership designs.

---

## 215. Lifetime Graph

The lifetime graph is one of the most valuable parts of KSIR.

```text
Object A
   |
   +── created_by ──> allocator X
   |
   +── referenced_by ──> pointer P
   |
   +── published_by ──> RCU
   |
   +── protected_by ──> refcount R
   |
   +── callback_owner ──> worker W
   |
   +── destroyed_by ──> function D
```

A lifecycle can then be represented:

```text
ALLOCATED
    ↓
INITIALIZED
    ↓
PUBLISHED
    ↓
REFERENCED
    ↓
QUIESCING
    ↓
RECLAIMABLE
    ↓
FREED
```

The exact states vary by object.

---

## 216. Lifetime Invariant

For each dereference:

```text
DEREFERENCE(P, O)
```

KSIR should be able to answer:

> What keeps `O` alive?

Possible answers:

```text
reference count
lock
RCU read-side critical section
caller contract
object ownership
static lifetime
device lifetime
explicit synchronization
unknown
```

If the answer is `unknown`, the Rust migration should normally be blocked at the relevant
boundary.

---

## 217. Refcount Model

Refcounts deserve their own semantic representation.

```rust
pub struct RefcountContract {
    pub counter: FieldId,

    pub acquisition: Vec<RefAcquire>,
    pub release: Vec<RefRelease>,

    pub zero_transition: ZeroTransition,

    pub resurrection: ResurrectionPolicy,
    pub saturation: SaturationPolicy,

    pub memory_ordering: MemoryOrdering,

    pub evidence: Vec<EvidenceId>,
}
```

The system needs to distinguish:

```text
refcount protects object lifetime
```

from:

```text
refcount happens to be present
```

Those are not equivalent.

---

## 218. RCU Model

RCU needs a dedicated semantic model.

```rust
pub struct RcuContract {
    pub object: ObjectId,

    pub publication: PublicationMechanism,

    pub read_side: Vec<RcuReadRegion>,
    pub updates: Vec<RcuUpdate>,

    pub reclamation: ReclamationMechanism,

    pub grace_period: GracePeriodRequirement,

    pub ordering: MemoryOrdering,

    pub callbacks: Vec<CallbackId>,
}
```

Then a relationship can be explicit:

```text
publish
   ↓
RCU-visible object
   ↓
read-side access
   ↓
update
   ↓
grace period
   ↓
reclamation
```

That semantic sequence is what the Rust design must preserve.

---

# III. Concurrency & context

## 219. Concurrency Graph

Instead of merely listing locks:

```c
spin_lock()
spin_unlock()
```

model relationships.

```rust
pub struct ConcurrencyEdge {
    pub protected_object: ObjectId,
    pub primitive: SyncPrimitiveId,

    pub access_kind: AccessKind,

    pub required_context: ContextSet,

    pub nesting: LockNesting,
    pub ordering: MemoryOrdering,

    pub evidence: Vec<EvidenceId>,
}
```

This allows:

```text
field X
   protected_by lock L
```

to become canonical knowledge.

---

## 220. Synchronization Primitive Taxonomy

```rust
pub enum SyncPrimitive {
    SpinLock,
    RawSpinLock,
    Mutex,
    RwLock,
    RawRwLock,
    Seqlock,
    Refcount,
    Atomic,
    Rcu,
    Completion,
    WaitQueue,
    Semaphore,
    PerCpu,
    LocalIrqDisable,
    PreemptDisable,
    Other,
    Unknown,
}
```

The model should also record the semantic variant.

For example, `spinlock` is insufficient when behavior differs under:

```text
PREEMPT_RT
```

---

## 221. Execution Context

This deserves first-class representation.

```rust
pub enum ExecutionContext {
    Process,
    Atomic,
    SoftIrq,
    HardIrq,
    Nmi,
}
```

A function may have multiple contexts:

```rust
pub struct ContextSet {
    pub possible: BTreeSet<ExecutionContext>,
}
```

Example:

```text
foo()
    PROCESS
    SOFTIRQ
```

Then `may_sleep(foo)` cannot simply be assumed from its source.

It must be reconciled with every reachable execution context.

---

## 222. Sleepability

```rust
pub enum Sleepability {
    MustNotSleep,
    MaySleep,
    MustSleep,
    Conditional,
    Unknown,
}
```

The interesting case is `Conditional`. For example:

```text
if atomic_context
    → no sleep
else
    → may sleep
```

The semantic model must preserve the condition.

---

## 223. Allocation Context

Memory allocation is also contextual.

```rust
pub struct AllocationEffect {
    pub allocator: Allocator,
    pub flags: AllocationFlags,

    pub may_block: bool,
    pub may_reclaim: bool,

    pub context_requirements: ContextSet,
}
```

Then `allocation()` becomes:

```text
allocation(
    allocator = SLUB,
    flags = GFP_ATOMIC,
    may_block = false
)
```

rather than a generic `alloc()` operation.

---

## 224. Effects System

Functions should expose semantic effects.

```rust
pub enum Effect {
    Allocates,
    Frees,
    Sleeps,
    AcquiresLock,
    ReleasesLock,
    EntersRcuRead,
    ExitsRcuRead,
    SchedulesWork,
    CancelsWork,
    EnablesIrq,
    DisablesIrq,
    AccessesUserMemory,
    AccessesMmio,
    PerformsDma,
    ModifiesGlobalState,
    PublishesObject,
    ReclaimsObject,
    MayReturnError,
}
```

This allows a function contract to be composed.

---

## 225. Effect Propagation

Suppose:

```text
foo()
  calls bar()
  calls baz()
```

and:

```text
bar → Sleeps
baz → Allocates(GFP_KERNEL)
```

Then KSIR can derive:

```text
foo
  may_sleep
  may_allocate
```

unless control-flow conditions constrain those effects.

This is far more useful than merely inspecting the body of `foo`.

---

## 226. Call Graph Is Not Enough

Traditional call graph:

```text
foo → bar
foo → baz
```

Semantic graph:

```text
foo
 ├── invokes → bar
 │              └── may_sleep
 │
 └── invokes → baz
                ├── allocates
                └── acquires lock L

foo therefore:
    may_sleep
    may_allocate
    may acquire L
```

The second graph is what the Rust design layer needs.

---

# IV. Time, memory, architecture

## 227. Callback Graph

Kernel behavior frequently escapes ordinary call graphs. Callbacks need their own graph.

```text
Registration
      |
      v
Callback object
      |
      v
Dispatcher
      |
      v
Callback execution
      |
      v
Completion / cancellation
      |
      v
Reclamation
```

For each callback:

```rust
pub struct CallbackContract {
    pub id: CallbackId,

    pub registration: FunctionId,
    pub invocation: Vec<FunctionId>,

    pub context: ContextSet,

    pub lifetime_requirements: Vec<InvariantId>,

    pub cancellation: CancellationContract,

    pub reclamation: ReclamationContract,
}
```

This is especially important for:

- workqueues
- timers
- tasklets
- IRQ handlers
- RCU callbacks
- completions
- asynchronous I/O

---

## 228. Deferred Execution

A function such as `queue_work(...)` has semantic effects that extend beyond its return.

The model should represent:

```text
enqueue
   ↓
deferred execution
   ↓
callback
   ↓
completion
```

Therefore:

```text
function returned
```

does not necessarily mean:

```text
operation finished
```

This is exactly the kind of hidden temporal relationship that causes naïve C→Rust translation
failures.

---

## 229. Temporal Contracts

Introduce temporal relationships:

```rust
pub enum TemporalRelation {
    Before,
    After,
    During,
    Eventually,
    Until,
    UntilGracePeriod,
    UntilCompletion,
}
```

Example:

```text
object must remain alive
    UNTIL callback completion
```

or:

```text
publication
    BEFORE reader access
```

These can later map into Rust lifetime/type designs or runtime verification.

---

## 230. Memory Ordering

Atomics should not be represented merely as `AtomicStore`. Represent:

```rust
pub struct AtomicOperation {
    pub location: FieldId,
    pub operation: AtomicOp,
    pub ordering: MemoryOrdering,
    pub synchronization_role: SynchronizationRole,
}
```

For example, `store-release` / `load-acquire` may encode publication.

That relationship should become explicit:

```text
    writer
       │
    release
       │
       ▼
published state
       │
    acquire
       │
       ▼
    reader
```

---

## 231. Architecture Dependencies

A portable Rust design can be invalidated by architecture-specific behavior.

KSIR should explicitly record:

```rust
pub struct ArchitectureDependency {
    pub symbol: SymbolId,

    pub architectures: BTreeSet<Architecture>,

    pub assumption: String,

    pub semantic_requirement: InvariantId,

    pub evidence: Vec<EvidenceId>,
}
```

Examples include:

```text
atomic width
memory ordering
MMIO semantics
interrupt behavior
page-table layout
calling convention
alignment
cache behavior
```

No architecture-specific assumption should disappear merely because the Rust implementation
compiles on one machine.

---

## 232. ABI Model

The ABI representation needs to cover more than function names.

```rust
pub struct AbiContract {
    pub calling_convention: CallingConvention,

    pub layout: Vec<LayoutConstraint>,
    pub alignment: Vec<AlignmentConstraint>,
    pub field_offsets: Vec<FieldOffsetConstraint>,

    pub symbol_visibility: SymbolVisibility,
    pub linkage: Linkage,

    pub representation: Representation,

    pub compatibility: CompatibilityRequirement,
}
```

The Rust side must satisfy the ABI contract where the migration retains a C boundary.

---

## 233. FFI Boundary

Every C/Rust boundary becomes explicit:

```rust
pub struct FfiBoundary {
    pub id: FfiBoundaryId,

    pub c_symbol: SymbolId,
    pub rust_symbol: SymbolId,

    pub direction: FfiDirection,

    pub ownership_transfer: OwnershipTransfer,
    pub lifetime_contract: LifetimeContract,

    pub abi: AbiContract,

    pub safety_obligations: Vec<UnsafeObligation>,
}
```

This makes the FFI boundary a **trust boundary**.

---

## 234. User Memory

User pointers should be semantically distinct.

```rust
pub enum AddressSpace {
    Kernel,
    User,
    Mmio,
    Dma,
    Physical,
    Unknown,
}
```

A pointer to userspace memory should never accidentally become equivalent to an
`ordinary kernel reference`.

The Rust design layer needs that distinction.

---

## 235. DMA

DMA similarly needs explicit semantics.

```rust
pub struct DmaContract {
    pub object: ObjectId,
    pub device: DeviceId,

    pub direction: DmaDirection,

    pub mapping_lifetime: LifetimeId,

    pub synchronization: DmaSynchronization,

    pub address_constraints: AddressConstraints,
}
```

The CPU-visible Rust ownership model cannot simply be substituted for device ownership.

We need:

```text
CPU ownership  ↕  DMA ownership
```

as an explicit state machine.

---

## 236. MMIO

MMIO must not be modeled as ordinary memory.

```rust
pub struct MmioRegion {
    pub region: RegionId,

    pub width_constraints: Vec<WidthConstraint>,

    pub ordering: MmioOrdering,

    pub side_effects: Vec<MmioSideEffect>,
}
```

A Rust abstraction that turns `readl()` into an ordinary memory dereference would violate the
semantic model.

---

# V. Invariants & queries

## 237. Invariant Representation

An invariant should have structure.

```rust
pub struct Invariant {
    pub id: InvariantId,

    pub subject: Subject,
    pub predicate: Predicate,

    pub scope: InvariantScope,
    pub severity: Severity,

    pub status: VerificationStatus,

    pub evidence: Vec<EvidenceId>,
}
```

The predicate should eventually become machine-readable.

---

## 238. Invariant Examples

Instead of:

```text
"be careful with this pointer"
```

we want:

```text
INV-OBJ-017:
  subject:
    object O
  predicate:
    dereference(O)
      requires lifetime(O) == ACTIVE
  severity:
    CRITICAL
```

Another:

```text
INV-LOCK-044:
  subject:
    field X
  predicate:
    write(X)
      requires lock(L) held
```

Another:

```text
INV-RCU-009:
  subject:
    object O
  predicate:
    reclaim(O)
      requires grace_period_complete(G)
```

These become migration targets.

---

## 239. Semantic Classification

Every KSIR fact should carry epistemic provenance.

```text
OBSERVED  DERIVED  HYPOTHESIS  UNKNOWN
```

Example:

```text
Function foo may execute in SOFTIRQ
    DERIVED
    from:
        callgraph C17
        registration R4
        dispatcher D2
```

Whereas:

```text
foo may execute in NMI
    HYPOTHESIS
```

must not become part of a verified contract without evidence.

---

## 240. Evidence-Carrying KSIR

A semantic node should be traceable.

```rust
pub struct SemanticFact<T> {
    pub value: T,

    pub epistemic: EpistemicStatus,

    pub evidence: Vec<EvidenceId>,

    pub derived_from: Vec<ArtifactId>,

    pub snapshot: SnapshotId,
}
```

Thus:

```text
KSIR fact
   ↓
source lines
   ↓
analysis
   ↓
evidence
```

can be traversed backwards.

---

## 241. KSIR Query Engine

Once this exists, agents should query KSIR rather than repeatedly rediscovering source
semantics.

Examples:

```text
find all objects reclaimed by RCU
find all functions reachable from callback X
find all fields protected by lock L
find all functions callable from SOFTIRQ that may allocate
find all pointers whose ownership is UNKNOWN
find all unsafe Rust obligations derived from invariant I
```

This becomes a semantic database rather than a document.

---

## 242. High-Value Query

One particularly useful query: **Find migration blockers.**

Conceptually:

```text
BLOCKERS(MU) =
    critical_unknowns
  ∪ unresolved_conflicts
  ∪ missing_contracts
  ∪ stale_artifacts
  ∪ ABI_uncertainties
  ∪ lifetime_uncertainties
  ∪ concurrency_uncertainties
```

The agent scheduler can then work directly on the blocker set.

```text
Migration Unit
      |
      v
Blocker Query
      |
      ├── lifetime unknown
      ├── RCU ambiguity
      └── ABI unknown
             |
             v
       spawn investigators
```

This is substantially more efficient than continuously asking an LLM:

> "What should we do next?"

---

## 243. KSIR to Rust Design

The translation boundary should be explicit:

```text
                 KSIR
                   │
       ┌───────────┼─────────────┐
       ▼           ▼             ▼
   ownership  concurrency     context
       │           │             │
       └───────────┼─────────────┘
                   ▼
          Design Constraints
                   │
                   ▼
            Rust Design IR
```

For example:

```text
KSIR:
    object O
    refcounted
    callback lifetime
    lock L
```

may produce design candidates such as:

```text
Rust:
    Arc-like ownership
    callback token
    lock-protected interior state
```

But the design agent must **propose** that mapping.

It must not claim semantic equivalence merely because the types look plausible.

---

## 244. Design Obligations

Every Rust design mapping should say:

> What C invariant does this Rust construct preserve?

Example:

```text
RustType:
    WorkItemOwner

preserves:
    INV-WQ-002

mechanism:
    lifetime token

remaining unsafe:
    callback trampoline

verification:
    differential + concurrency
```

This produces traceability all the way into the generated code.

---

# VI. QA & pipeline

## 245. KSIR Failure Modes

The system should explicitly test for these.

### F1 — Type-only understanding

`C pointer → Rust reference` without ownership evidence.

### F2 — Callgraph-only understanding

Ignoring:

```text
callbacks
interrupts
workqueues
RCU
function pointers
```

### F3 — Local lifetime reasoning

Ignoring:

```text
other CPUs
deferred callbacks
reclamation
```

### F4 — Lock blindness

Seeing `spin_lock()` without determining what it protects.

### F5 — Context blindness

Treating `process`, `softirq`, `hardirq`, `NMI` as interchangeable.

### F6 — Architecture erasure

Assuming `x86 behavior = universal kernel behavior`.

### F7 — Evidence laundering

Turning `LLM hypothesis` into `KSIR fact` without an evidentiary transition.

---

## 246. KSIR Acceptance Criteria

Before calling KSIR v0.1 usable, require:

| ID | Requirement |
| --- | --- |
| KSIR-001 | Every symbol maps to snapshot source evidence. |
| KSIR-002 | Pointer nullability is explicit. |
| KSIR-003 | Pointer ownership may be UNKNOWN. |
| KSIR-004 | Object lifetimes are explicit or UNKNOWN. |
| KSIR-005 | Synchronization relationships are represented. |
| KSIR-006 | Execution context is represented. |
| KSIR-007 | Allocation context is represented. |
| KSIR-008 | Callbacks are represented. |
| KSIR-009 | RCU relationships are represented. |
| KSIR-010 | Refcount relationships are represented. |
| KSIR-011 | ABI constraints are represented. |
| KSIR-012 | Architecture dependencies are represented. |
| KSIR-013 | Every derived fact has provenance. |
| KSIR-014 | Critical unknowns cannot be silently downgraded. |
| KSIR-015 | KSIR is snapshot-bound. |

---

## 247. KSIR QA

The first KSIR test corpus should be intentionally adversarial.

```text
ksir-qa/
├── pointers/
│   ├── borrowed.c
│   ├── nullable.c
│   ├── aliasing.c
│   └── unknown.c
├── lifetime/
│   ├── refcount.c
│   ├── rcu.c
│   ├── callback.c
│   └── deferred.c
├── concurrency/
│   ├── spinlock.c
│   ├── mutex.c
│   ├── atomic.c
│   ├── lock_nesting.c
│   └── irq_lock.c
├── context/
│   ├── process.c
│   ├── softirq.c
│   ├── hardirq.c
│   └── nmi.c
├── memory/
│   ├── slab.c
│   ├── percpu.c
│   ├── dma.c
│   └── mmio.c
└── architecture/
    ├── atomic_width.c
    ├── alignment.c
    └── arch_conditional.c
```

Each fixture should have:

```text
expected structural facts
expected semantic facts
expected unknowns
expected evidence links
expected blockers
```

---

## 248. The First Real Semantic Benchmark

A useful benchmark is not:

> "Can the model translate this C function?"

Instead:

> "Can the system reconstruct the contract of this function?"

Scoring should therefore compare:

```text
source facts
ownership
lifetimes
context
locking
atomics
callbacks
ABI
invariants
unknowns
```

before judging generated Rust.

The benchmark can then deliberately contain cases where the correct answer is:

```text
UNKNOWN
```

That is important.

A system that says `UNKNOWN` when evidence is insufficient has demonstrated a capability that
a hallucinating translator does not.

---

## 249. The Full Semantic Pipeline

We now have:

```text
        Linux C
           │
           ▼
C AST / compiler facts
           │
           ▼
     Structural IR
           │
           ▼
  Semantic extraction
           │
   +── ownership
   +── lifetime
   +── concurrency
   +── context
   +── effects
   +── callbacks
   +── memory
   +── ABI
   +── architecture
           │
           ▼
         KSIR
           │
           ▼
   Invariant Ledger
           │
           ▼
    Kernel Contract
           │
           ▼
    Rust Design IR
           │
           ▼
         Rust
```

And alongside it:

```text
Every transition
       │
       ▼
   Evidence
       │
       ▼
  Claim graph
       │
       ▼
 Verification
```

---

## 250. The Architecture Has Now Reached the Important Boundary

The system is no longer simply:

```text
AI + Linux + Rust
```

It is becoming:

```text
                    RFL-AE
                       │
        ┌──────────────┼────────────────┐
        ▼              ▼                ▼
    PROTOCOL       SEMANTICS        EVIDENCE
        │              │                │
    authority        KSIR          provenance
      state        contracts        execution
  capabilities    invariants         claims
      gates         design        verification
        │              │                │
        └──────────────┼────────────────┘
                       ▼
                MIGRATION UNIT
                       │
                       ▼
              Rust implementation
                       │
                       ▼
              Differential proof
```

The remaining major piece before the actual subsystem-specific agents is the **semantic
reconstruction engine** itself.

That should be the next layer:

```text
C source
  ↓
compiler/AST facts
  ↓
CFG
  ↓
call graph
  ↓
points-to / alias analysis
  ↓
data-flow
  ↓
lock/access analysis
  ↓
context propagation
  ↓
lifetime/refcount/RCU analysis
  ↓
callback/deferred-execution analysis
  ↓
architecture/config conditional analysis
  ↓
KSIR synthesis
  ↓
UNKNOWN + CONFLICT extraction
```

That is where we define the actual **skills and tools the AI agents need to acquire kernel
semantics**, rather than merely giving them access to source code.

---

**Done — see [RECONSTRUCTION.md](RECONSTRUCTION.md)** (§251–§291), which specifies the
compiler-grade evidence pipeline that produces those semantics: the analysis backend
architecture and its authority table, `AnalysisObservation` and backend identity, build
variants and configuration domains, compiler command fidelity, Linux-specific semantic
hazards, the structural pipeline, call graphs and indirect-call reachability, effect and
execution-context propagation, the context lattice, lock and lockset analysis, ownership,
refcount, RCU, callback, temporal-ownership, alias, memory-region, ABI and architecture
reconstruction, the reconciliation engine and its states, conflict as data, the no-consensus
rule, evidence reconciliation, semantic vs verified claims, the semantic dependency graph,
migration dependency extraction, agent decomposition, the worker contract, the critical
unknown detector, the crate structure, and acceptance criteria SR-001–SR-012.
