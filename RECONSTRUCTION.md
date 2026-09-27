# RFL-AE — Semantic Reconstruction Engine

**Sections 251–291** — the compiler-grade evidence pipeline that turns a Linux snapshot into
semantic facts.

> Continues the numbering of [ARCHITECTURE.md](ARCHITECTURE.md) (§1–§51),
> [SPECIFICATION.md](SPECIFICATION.md) (§52–§80), [FORMAL-CORE.md](FORMAL-CORE.md)
> (§81–§107), [PROTOCOL.md](PROTOCOL.md) (§109–§135), [RUST-CORE.md](RUST-CORE.md)
> (§136–§172), [TRANSITIONS.md](TRANSITIONS.md) (§173–§203), and [KSIR.md](KSIR.md)
> (§204–§250). §108 does not exist in the source.
>
> **Note on derived material:** the source's "Backend authority" grid (§251) and the
> `SR-001`…`SR-012` acceptance list (§290) are rendered as markdown tables; the collapsed
> ASCII figures are redrawn in `text` fences from computed column layouts. No content was
> added beyond that.

## Contents

| Part | Sections | |
| --- | --- | --- |
| [I. Analysis backends and observations](#251-analysis-backend-architecture) | 251–257 |
| [II. Structural and semantic analysis](#258-structural-analysis-pipeline) | 258–274 |
| [III. Reconciliation and evidence](#275-reconciliation-engine) | 275–280 |
| [IV. Dependencies, agents, and tasks](#281-semantic-dependency-graph) | 281–287 |
| [V. Output, crates, and architecture](#288-analysis-output) | 288–291 |

---

The next layer should be treated as a **compiler-grade evidence pipeline**, not as an LLM
analysis pass.

The central transformation is:

```text
     Linux snapshot + build variant
                    │
                    ▼
             Build Manifest
                    │
                    ├── compiler-native observations
                    ├── source-level observations
                    ├── static-analysis observations
                    ├── emitted-binary observations
                    └── runtime observations
                    │
                    ▼
            Observation Store
                    │
                    ▼
       Fact Reconciliation Engine
                    │
             ┌──────┴──────┐
             ▼             ▼
         RESOLVED      CONFLICT
             │             │
             ▼             ▼
           KSIR       QUARANTINE
             │
             ▼
        Critical Unknown Detector
                    │
                    ▼
       Kernel Contract / Migration
```

The important distinction is:

> ### **Analysis produces observations. Reconciliation produces semantic facts. KSIR stores the resulting facts together with their provenance.**

An analyzer must never be allowed to silently convert an observation into truth.

---

## 251. Analysis Backend Architecture

RFL-AE should not have one monolithic "kernel analyzer".

Instead:

```text
                         ┌────────────────────┐
                         │ Snapshot + Variant │
                         └──────────┬─────────┘
                                    │
                         ┌─────────────────────┐
                         │ Build Manifest      │
                         │ exact commands      │
                         │ config / arch / env │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
      Compiler Backend       Source Backend        Binary Backend
              │                     │                     │
          AST/types            Coccinelle             DWARF/BTF
             CFG                 sparse                  ELF
         diagnostics             Smatch                objdump
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
                            Observation Store
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
          Dataflow             Concurrency             Context
          ownership           locks/atomics         sleepability
          aliasing                 RCU                   IRQ
          lifetimes             refcount             preemption
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
                          Reconciliation Engine
```

Each backend has a narrowly defined authority domain.

### Backend authority

| Backend | Strong evidence for | Not authoritative for |
| --- | --- | --- |
| compiler frontend | syntax, types, declarations, compiler-visible attributes | actual runtime ownership |
| compiler diagnostics | compilation constraints | intended semantics |
| CFG | compiler-visible control structure | indirect runtime behavior |
| LLVM IR | lowered operations/control/dataflow | source-level kernel intent |
| sparse | annotation/type-domain observations | complete ownership model |
| Smatch | specialized static observations | universal correctness |
| Coccinelle | source-pattern transformations/matches | runtime semantics |
| DWARF/BTF | emitted type/layout information | source-only conditional paths |
| ELF/readelf/objdump | symbols, sections, relocation/code properties | source ownership |
| runtime instrumentation | observed execution | unexecuted paths |
| Git history | historical intent/evolution | present behavior by itself |

The architecture therefore avoids:

```text
"Analyzer X says it is RCU protected."
                   ↓
         KSIR = RCU protected
```

and instead requires:

```text
Observation O1:
    backend = X
    claim = "access occurs under rcu_read_lock()"
    source = ...
    variant = ...
    evidence = ...

Observation O2:
    backend = Y
    claim = "same object can be accessed outside RCU read-side section"
    source = ...
    variant = ...
                     ↓
              RECONCILIATION
                     ↓
                CONFLICTED
                     ↓
                  BLOCKED
```

That distinction is foundational.

---

## 252. `AnalysisObservation`

The primitive output of every analysis backend should be an immutable observation.

Conceptually:

```rust
struct AnalysisObservation<T> {
    observation_id: ObservationId,

    snapshot: KernelSnapshotId,
    variant: BuildVariantId,

    subject: SubjectId,

    fact_kind: FactKind,
    value: T,

    source: SourceEvidence,

    backend: BackendIdentity,
    execution: ExecutionReceipt,

    epistemic_status: EpistemicStatus,

    dependencies: Vec<ArtifactDigest>,

    algorithm: AlgorithmIdentity,
    created_at: Timestamp,

    digest: Digest,
}
```

Where:

```rust
enum EpistemicStatus {
    Observed,
    Derived,
    Hypothesis,
}
```

`Verified` does **not** belong here.

Verification is a later property of the resulting claim.

---

## 253. Backend Identity Must Be Reproducible

Every observation needs enough information to reproduce the analysis.

```text
BackendIdentity
├── backend_name
├── backend_version
├── executable_digest
├── configuration_digest
├── schema_version
└── algorithm_revision
```

For example:

```yaml
backend:
    name: "lock-analysis"
    version: "0.3.1"
    executable_sha256: ...
    algorithm_revision: ...
    config_sha256: ...
```

This prevents:

```text
2026-09-27:
    analyzer says LOCK_A protects field X

2027-03-11:
    analyzer changed semantics

old claim still appears authoritative
```

Instead:

```text
Claim
 ├── Observation O1
 │    └── backend revision A
 │
 └── Observation O2
      └── backend revision B
```

The claim can therefore be recomputed or invalidated.

---

## 254. Build Variant Is a First-Class Semantic Dimension

A major error would be to treat one `.config` as "the Linux kernel".

Linux behavior is conditional on:

```text
CONFIG_*
ARCH
compiler
compiler options
architecture extensions
generated headers
feature combinations
```

Therefore:

```rust
struct BuildVariant {
    variant_id: BuildVariantId,

    arch: Architecture,
    config_digest: Digest,

    toolchain: ToolchainFingerprint,
    compiler: CompilerFingerprint,

    build_commands: ArtifactDigest,
    generated_headers: ArtifactDigest,
    linker_configuration: ArtifactDigest,

    environment: EnvironmentFingerprint,
}
```

A semantic fact must therefore answer:

> ### **For which configuration domain is this fact valid?**

---

## 255. Configuration Domain

The model should eventually support:

```text
Fact F valid for:

ARCH = x86_64
CONFIG_A = y
CONFIG_B = n
CONFIG_C ∈ {y,m}
```

rather than simply:

```text
Fact F = true
```

This becomes particularly important for migration.

Suppose:

```c
#ifdef CONFIG_X
    acquire_lock();
#endif

    object->field = value;

#ifdef CONFIG_X
    release_lock();
#endif
```

An analysis of:

```text
CONFIG_X=y
```

cannot automatically establish:

```text
field is universally protected
```

It establishes:

```text
field protected under configuration predicate P
```

So the KSIR needs a conditional validity domain.

Conceptually:

```rust
struct ValidityDomain {
    constraints: Vec<ConfigConstraint>,
}
```

with:

```text
ConfigConstraint
├── Symbol
├── Operator
└── Value
```

Examples:

```text
CONFIG_PREEMPT_RT = y
CONFIG_SMP = y
CONFIG_NET = y
ARCH = arm64
```

This allows the semantic engine to represent:

```text
Invariant I:
    field X requires lock L
Validity:
    CONFIG_FOO=y
```

instead of incorrectly universalizing it.

---

## 256. Compiler Command Fidelity

The analyzer must not invent compilation commands.

This is especially important for kernel code because preprocessing and compiler flags
materially affect semantics.

The canonical source should be:

```text
actual kernel build system
        ↓
actual compile invocation
        ↓
captured command
        ↓
normalized build manifest
        ↓
analysis
```

Not:

```text
LLM guesses clang flags
        ↓
AST
        ↓
"kernel semantics"
```

The build manifest should capture:

```text
TranslationUnit
├── source path
├── generated source dependencies
├── compiler
├── compiler arguments
├── include paths
├── defines
├── target
├── language mode
├── dependency files
├── generated headers
└── command digest
```

If the command cannot be reconstructed faithfully:

```text
Analysis status = PARTIALLY_OBSERVABLE
```

not:

```text
Analysis status = VERIFIED
```

---

## 257. Linux-Specific Semantic Hazards

The reconstruction engine needs explicit detectors for constructs that defeat naïve C
analysis.

At minimum:

```text
container_of()
typeof()
__builtin_*
statement expressions
inline assembly
compiler barriers
memory barriers
volatile
READ_ONCE()
WRITE_ONCE()
atomic operations
RCU annotations
__user
__iomem
__rcu
section attributes
likely()/unlikely()
CONFIG_* branches
architecture-specific macros
generated headers
linker-defined symbols
per-CPU variables
init/exit sections
function pointers
callbacks
workqueues
timers
interrupt handlers
softirq dispatch
static keys
jump labels
tracing hooks
BPF hooks
module boundaries
```

These should not all be "understood" immediately.

They should have explicit semantic states:

```text
SUPPORTED
PARTIALLY_SUPPORTED
OPAQUE
UNKNOWN
```

That gives the migration system a measurable boundary.

---

## 258. Structural Analysis Pipeline

The first stage should deliberately remain boring.

```text
Source
  │
  ▼
Preprocessor / Compiler Frontend
  │
  ├── declarations
  ├── types
  ├── expressions
  ├── statements
  ├── attributes
  └── diagnostics
  │
  ▼
AST
  │
  ▼
CFG
  │
  ▼
Call Graph
  │
  ▼
Type / Layout Graph
```

No ownership inference yet.

This gives the system a clean structural substrate.

---

## 259. Call Graph Is Not Enough

The call graph should contain multiple edge classes.

```rust
enum CallEdgeKind {
    Direct,
    FunctionPointer,
    CallbackRegistration,
    MacroExpansion,
    Generated,
    Assembly,
    LinkerResolved,
    WeakSymbol,
    Unknown,
}
```

For example:

```text
foo()
 └── callback_table->handler
```

must not become:

```text
foo → UNKNOWN
```

if the system can discover:

```text
callback_table registration
        ↓
handler = bar
        ↓
dispatch(...)
        ↓
bar()
```

But if it cannot establish the target:

```text
CallTarget:
    Unknown
```

is preferable to guessing.

---

## 260. Indirect Calls Require a Reachability Lattice

Function pointers are a major semantic boundary.

Use:

```text
EXACT
FINITE_SET
CONDITIONAL_SET
UNKNOWN
```

Example:

```c
handler = foo
```

becomes:

```text
FINITE_SET { foo }
```

while:

```c
handler = condition ? foo : bar
```

becomes:

```text
CONDITIONAL_SET {
    condition → foo
    !condition → bar
}
```

If arbitrary external input determines the callback:

```text
UNKNOWN
```

This directly affects:

```text
lifetime
locking
execution context
sleepability
```

because the target function may impose constraints on the caller.

---

## 261. Effect Propagation

Once CFG and call graph exist, the next abstraction is **effect analysis**.

Example:

```text
foo()
 └── bar()
      └── mutex_lock()
```

Then:

```text
bar:
    AcquiresLock(L)
foo:
    Calls(bar)
```

propagates:

```text
foo:
    AcquiresLock(L)
```

Likewise:

```text
foo
 └── bar
      └── kmalloc(GFP_KERNEL)
```

produces:

```text
foo:
    Allocates
    MaySleep
```

But the propagation must preserve uncertainty.

If:

```text
foo
 └── function_pointer()
```

and the target is unknown:

```text
foo:
    Effects = {
        Known effects,
        Unknown callee effects
    }
```

It must not collapse into:

```text
foo = safe
```

---

## 262. Execution Context Propagation

The engine should build a reverse constraint graph.

Known entry points:

```text
process context
softirq
hardirq
NMI
workqueue
timer
tasklet
RCU callback
interrupt handler
syscall
filesystem callback
network callback
```

Then propagate restrictions.

Example:

```text
IRQ handler
     ↓
foo()
     ↓
bar()
     ↓
kmalloc(GFP_KERNEL)
```

Produces:

```text
bar:
    MaySleep = true
foo:
    MaySleep = true
IRQ handler:
    Context = HARDIRQ
    Calls potentially sleeping function
```

The resulting invariant is not:

```text
"bar is buggy"
```

It is:

```text
Conflict:
    HARDIRQ context
    +
    callee effect MAY_SLEEP
```

The migration gate decides whether that conflict blocks the migration.

---

## 263. Context Lattice

Use a partial order rather than a single Boolean.

```text
UNKNOWN
   │
   ├── PROCESS
   │
   ├── SOFTIRQ
   │
   ├── HARDIRQ
   │
   └── NMI
```

But context composition should preserve multiple possible contexts.

For example:

```text
foo()
```

called from:

```text
syscall
workqueue
timer
```

becomes:

```text
PossibleContexts = {
    PROCESS,
    ATOMIC
}
```

not simply:

```text
PROCESS
```

Similarly:

```text
MaySleep(foo)
```

can be modeled as:

```text
RequiredContext(foo):
    PROCESS
```

and checked against each caller context.

---

## 264. Lock Analysis

Lock analysis should not merely detect:

```text
mutex_lock()
mutex_unlock()
```

It needs a lock-state graph.

```text
LockState
├── lock identity
├── acquisition sites
├── release sites
├── nesting
├── conditionality
├── IRQ state
├── preemption state
├── owner relation
├── protection targets
└── evidence
```

For every field access:

```text
Access A
    object = task
    field = foo
    operation = WRITE

Required protection:
    lock = L
```

The engine asks:

```text
At every reachable access path:
     Is L held?
```

Possible results:

```text
PROTECTED
UNPROTECTED
CONDITIONALLY_PROTECTED
UNKNOWN
CONFLICTED
```

This is much more useful for Rust migration than merely generating a call graph.

---

## 265. Lockset Must Be Path-Sensitive

Consider:

```c
if (condition)
    spin_lock(&obj->lock);

obj->field = value;

if (condition)
    spin_unlock(&obj->lock);
```

A flow-insensitive analyzer may incorrectly report:

```text
field protected by obj->lock
```

A path-sensitive model reports:

```text
Path P1:
    condition=true
    lock held
    field write
    SAFE

Path P2:
    condition=false
    lock not held
    field write
    UNPROTECTED
```

Then:

```text
Fact:
    protection = CONDITIONAL
```

The exact path predicate should be retained where practical.

---

## 266. Ownership Reconstruction

Ownership should be treated as a graph inference problem.

Sources include:

```text
allocation
initialization
assignment
return
parameter passing
container insertion
reference acquisition
reference release
publication
callback registration
unregistration
free
```

Example:

```c
obj = kmalloc(...);
list_add(&obj->node, &global_list);
```

Candidate lifecycle:

```text
ALLOCATED
    ↓
INITIALIZED
    ↓
PUBLISHED(global_list)
```

Later:

```c
list_del(&obj->node);
kfree(obj);
```

produces:

```text
UNPUBLISHED
    ↓
RECLAIMED
    ↓
FREED
```

But the engine must not assume:

```text
list_add = ownership transfer
```

universally.

That relationship is a **candidate semantic fact** requiring evidence.

---

## 267. Reference Counting

Reference counting deserves its own analyzer.

Detect:

```text
refcount_t
atomic_t used as reference counter
kref
custom get/put
per-object reference helpers
embedded reference counts
```

The output should describe operations rather than simply declaring:

```rust
Arc<T>
```

For example:

```text
RefcountContract R17
counter:
    obj->refcount
acquire:
    foo_get()
release:
    foo_put()
zero transition:
    foo_release()
resurrection:
    UNKNOWN
saturation:
    OBSERVED
ordering:
    PARTIALLY_VERIFIED
destruction:
    foo_release → kfree(obj)
```

Only the Rust design layer can later propose:

```rust
Arc<T>
```

or:

```rust
// custom intrusive refcount
```

The semantic engine must remain representation-neutral.

---

## 268. RCU Reconstruction

RCU requires temporal reasoning.

Represent:

```text
Publication
     ↓
RCU read-side access
     ↓
Update
     ↓
Removal
     ↓
Grace period
     ↓
Reclamation
```

For every RCU object:

```text
RcuContract
├── object
├── publication mechanism
├── read-side primitive
├── access paths
├── update primitive
├── removal
├── callback
├── grace-period mechanism
├── reclamation target
├── ordering
└── evidence
```

Example:

```text
rcu_assign_pointer(p, obj)
         ↓
rcu_dereference(p)
         ↓
read-side use
         ↓
RCU_INIT_POINTER(p, NULL)
         ↓
call_rcu(...)
         ↓
free(obj)
```

The migration system can then ask:

```text
What guarantees obj remains alive during each dereference?
```

If the answer is:

```text
RCU grace period
```

that becomes a semantic fact.

If the callback target cannot be established:

```text
reclamation = UNKNOWN
```

and potentially a migration blocker.

---

## 269. Callback / Deferred Execution Graph

Callbacks should be modeled independently of ordinary calls.

```text
Registration
      │
      ▼
Callback Object
      │
      ▼
Dispatcher
      │
      ▼
Invocation
      │
      ▼
Cancellation
      │
      ▼
Reclamation
```

This covers:

```text
work_struct
timer_list
tasklet
irq callbacks
notifier chains
completion callbacks
RCU callbacks
network callbacks
filesystem operations
device callbacks
trace callbacks
```

A callback fact should include:

```rust
struct CallbackContract {
    registration_site: SourceLocation,
    callback_target: TargetSet,
    dispatcher: SymbolId,
    execution_context: ContextSet,
    cancellation: CancellationContract,
    lifetime_requirement: LifetimeContract,
}
```

This is essential because many kernel lifetimes are not visible in lexical scope.

---

## 270. Temporal Ownership

A Rust migration needs more than:

```text
T owns X
```

It often needs:

```text
T owns X until event E
```

For example:

```text
Device driver owns buffer
    until DMA completion

workqueue owns work item
    until cancellation + quiescence

RCU subsystem permits readers
    until grace period

filesystem object remains valid
    while reference held
```

Therefore introduce:

```text
TemporalOwnership
├── holder
├── resource
├── acquisition
├── validity interval
├── release event
├── reclamation event
└── evidence
```

This will become one of the most important inputs to Rust lifetime design.

---

## 271. Alias Analysis

The engine needs to distinguish:

```text
same object
same field
overlapping memory
possibly same object
unknown
```

For example:

```c
struct foo *a;
struct foo *b;

b = container_of(...);
```

The system should not simply infer:

```text
a != b
```

or:

```text
a == b
```

without evidence.

Use:

```text
AliasRelation
├── MustAlias
├── MayAlias
├── NoAlias
└── Unknown
```

Then connect this to synchronization.

If:

```c
a->field
```

is protected by lock L, and:

```c
b->field
```

may alias `a`, the protection analysis must account for that.

---

## 272. Memory Regions

Pointer analysis becomes much more useful when tied to regions.

Example:

```text
Pointer p
     ↓
Object O
     ↓
Region R
```

Region:

```text
R:
    allocator = SLAB
    storage = heap
    ownership = refcounted
    reclamation = RCU
    address_space = KERNEL
```

Special regions:

```text
STACK
GLOBAL
STATIC
SLAB
PAGE
VMALLOC
PERCPU
DMA
MMIO
USER
TEXT
MODULE
```

This helps prevent category errors such as proposing ordinary Rust references for MMIO or
userspace pointers.

---

## 273. ABI / Layout Reconstruction

Before any FFI boundary is generated, the engine needs:

```text
size
alignment
field offsets
packing
calling convention
symbol visibility
linkage
representation
section
architecture constraints
```

A Rust representation that happens to look structurally similar is insufficient.

The design relation must be:

```text
C ABI fact
      │
      ▼
Rust representation proposal
      │
      ▼
ABI proof obligation
      │
      ├── layout
      ├── alignment
      ├── calling convention
      ├── ownership
      ├── initialization
      └── architecture
```

Only after the obligation is satisfied can the FFI boundary progress.

---

## 274. Architecture Analysis

Architecture-specific behavior should be explicit rather than scattered through generic
facts.

```text
ArchitectureContract
├── arch
├── instruction constraints
├── atomic implementation
├── barriers
├── alignment
├── endian
├── ABI
├── interrupt model
├── MMIO semantics
├── cache assumptions
└── source evidence
```

An analyzer encountering:

```c
#ifdef CONFIG_X86
    ...
#elif defined(CONFIG_ARM64)
    ...
#endif
```

should produce variant-specific observations.

The reconciliation engine can later determine whether the semantic invariant is:

```text
UNIVERSAL
ARCH_SPECIFIC
CONFIG_SPECIFIC
ARCH×CONFIG_SPECIFIC
UNKNOWN
```

---

## 275. Reconciliation Engine

This is the core epistemic boundary.

Input:

```text
O1
O2
O3
...
On
```

Output:

```text
ResolvedFact
```

or:

```text
Conflict
```

or:

```text
InsufficientEvidence
```

Never:

```text
best_guess
```

The resolver should be deterministic.

```text
Observations
      │
      ▼
Normalize
      │
      ▼
Group by:
    snapshot
    variant
    subject
    fact kind
      │
      ▼
Apply domain-specific rules
      │
      ├── consistent
      ├── conditional
      ├── insufficient
      └── contradictory
      │
      ▼
ResolvedFact / Conflict / Unknown
```

---

## 276. Reconciliation States

```rust
enum ReconciliationStatus {
    Consistent,
    ConditionallyConsistent,
    InsufficientEvidence,
    Conflicted,
    Invalidated,
}
```

Example:

```text
Compiler:
    pointer may be NULL
Static analyzer:
    all observed paths check NULL

Result:
    ConditionallyConsistent
```

Not:

```text
NonNull
```

unless a rule establishes that the path condition is sufficient for the claimed scope.

---

## 277. Conflict Is Data

A conflict should be stored as a first-class artifact.

```text
Conflict C42
subject:
    foo->bar
fact:
    lifetime
observation A:
    valid until refcount zero
observation B:
    free possible after list removal
scope:
    CONFIG_X=y
severity:
    Critical
status:
    OPEN
required_resolution:
    additional evidence / experiment / human review
```

This prevents the common failure mode:

```text
Agent A says X
Agent B says Y
LLM chooses X
```

Instead:

```text
A says X
B says Y
system records conflict
migration blocked
```

---

## 278. No-Consensus Rule

Multiple agents should never vote on semantic truth.

Bad:

```text
7 agents: protected by lock
3 agents: not protected
→ 7 wins
```

Correct:

```text
7 observations support proposition P
3 observations contradict P
→ CONFLICTED
```

The next action is:

```text
find missing evidence
```

not:

```text
increase confidence
```

This is particularly important for concurrency and memory safety.

---

## 279. Evidence Reconciliation

Every resolved fact should carry its derivation:

```text
ResolvedFact F91
derived_from:
    O11
    O17
    O31
rule:
    LOCK_PROTECTION_RULE_V3
inputs:
    snapshot S
    variant V
algorithm:
    reconciliation-engine@...
status:
    DERIVED
verification:
    UNVERIFIED
```

Therefore:

```text
KSIR fact
```

is itself reproducible.

This gives the project the proof-carrying property you want:

```text
semantic artifact + inputs + algorithm + execution evidence + digest
```

---

## 280. Semantic Fact vs Verified Claim

This distinction should remain absolute.

```text
Observation
    ↓
Resolved Semantic Fact
    ↓
Invariant / Contract
    ↓
Verification
    ↓
Verified Claim
```

For example:

```text
Observation:
    foo_get() increments refcount

Resolved fact:
    foo_get acquires reference

Contract:
    object remains valid while reference exists

Verification:
    static + runtime + differential evidence

Claim:
    Rust ownership design preserves this lifecycle
```

A successful AST parse proves none of the final claim.

---

## 281. Semantic Dependency Graph

The reconstruction engine should generate:

```text
Function
   │
   ├── uses → Object
   │             │
   │             └── protected_by → Lock
   │
   ├── calls → Callback
   │
   ├── allocates → Region
   │
   ├── accesses → RCU object
   │
   └── requires → Context
```

This is different from:

```text
source dependency graph
```

because semantic dependencies answer:

> ### **What assumptions must remain true for this code to remain correct?**

That graph should drive migration ordering.

---

## 282. Migration Dependency Extraction

Suppose:

```text
driver.c
     ↓
device object
     ↓
refcount
     ↓
RCU
     ↓
callback
     ↓
workqueue
```

The system should derive:

```text
Migration Unit A:
    object representation
depends_on:
    refcount contract
    RCU contract
    callback contract
    workqueue context contract
```

Therefore it should not permit:

```text
Rustify object
```

while:

```text
object lifetime = UNKNOWN
```

This converts semantic analysis directly into migration scheduling.

---

## 283. Agent Decomposition

For 10–100 agents, agents should specialize by **evidence domain**, not by arbitrary
source-file partitions.

Possible workers:

```text
AST-Agent
CFG-Agent
CallGraph-Agent
TypeLayout-Agent

Alias-Agent
Dataflow-Agent
Ownership-Agent
Lifetime-Agent

Lock-Agent
Atomic-Agent
RCU-Agent
Refcount-Agent

Context-Agent
Sleepability-Agent
Allocation-Agent

Callback-Agent
Workqueue-Agent
Timer-Agent
IRQ-Agent

DMA-Agent
MMIO-Agent
UserspacePointer-Agent

ABI-Agent
Architecture-Agent
Config-Agent

History-Agent
RuntimeEvidence-Agent

Conflict-Agent
EvidenceBinder-Agent
Gate-Agent
```

An agent should publish artifacts such as:

```text
ObservationBundle
FactCandidate
ConflictReport
VerificationRequirement
```

It should not directly modify canonical KSIR.

---

## 284. Worker Contract

Each worker receives:

```text
Task
├── snapshot
├── build variant
├── semantic scope
├── input artifact digests
├── allowed tools
├── analysis algorithm
└── output schema
```

And returns:

```text
AnalysisResult
├── observations
├── derived artifacts
├── unknowns
├── conflicts
├── execution receipts
└── artifact digests
```

No free-form:

```text
"I think this function probably owns the object."
```

That can exist only as:

```text
HypothesisArtifact
```

with explicit status.

---

## 285. Semantic Reconstruction Task Example

```text
TASK SR-004821
snapshot:
    linux@<digest>
variant:
    x86_64/config-A
scope:
    drivers/foo/foo.c
required domains:
    ownership
    lifetime
    locking
    context
    callbacks
inputs:
    AST digest
    CFG digest
    callgraph digest
required outputs:
    observations
    unknowns
    conflicts
    evidence bundle
```

Worker result:

```text
OBSERVATIONS: 47
DERIVED: 19
UNKNOWN: 8
CONFLICTS: 2

CRITICAL:
    lifetime of foo->bar unresolved
STATUS:
    BLOCKED
```

That is useful engineering output.

---

## 286. Semantic Reconstruction State Machine

The analyzer itself should have a lifecycle.

```text
NOT_STARTED
    ↓
INPUT_VALIDATED
    ↓
STRUCTURAL_ANALYSIS
    ↓
CONTROL_FLOW_ANALYSIS
    ↓
SEMANTIC_ANALYSIS
    ↓
CROSS_DOMAIN_RECONSTRUCTION
    ↓
RECONCILIATION
    ↓
UNKNOWN_EXTRACTION
    ↓
CONFLICT_ANALYSIS
    ↓
EVIDENCE_BINDING
    ↓
COMPLETED
```

Failure:

```text
ANY STATE
    ↓
QUARANTINED
```

Partial completion is explicit:

```text
COMPLETED_PARTIAL
```

rather than falsely presenting a complete KSIR.

---

## 287. The Critical Unknown Detector

After reconciliation:

```text
Resolved Facts + Unknowns + Conflicts
```

feed into:

```text
CriticalUnknownDetector
```

Example rules:

```text
UNKNOWN ownership
    + object crosses FFI
    → CRITICAL

UNKNOWN lifetime
    + object is asynchronously accessed
    → CRITICAL

UNKNOWN lock protection
    + mutable shared access
    → CRITICAL

UNKNOWN execution context
    + function may sleep
    → CRITICAL

UNKNOWN ABI
    + exported symbol
    → CRITICAL

UNKNOWN DMA lifetime
    + buffer is device-visible
    → CRITICAL
```

The important point is that "critical" is **rule-derived**, not model-confidence-derived.

---

## 288. Analysis Output

The semantic reconstruction engine should produce four primary artifacts:

```text
1. ObservationBundle
2. SemanticFactSet
3. ConflictSet
4. UnknownSet
```

Then:

```text
SemanticFactSet
       ↓
     KSIR

ConflictSet       ──→ Quarantine
UnknownSet        ──→ Migration blockers
ObservationBundle ──→ Evidence store
```

---

## 289. Proposed Crate Structure

The previous repository can now be extended:

```text
crates/
├── rfl-analysis-types/
├── rfl-analysis-core/
├── rfl-build-manifest/
├── rfl-c-front/
├── rfl-ast/
├── rfl-cfg/
├── rfl-callgraph/
├── rfl-type-layout/
├── rfl-dataflow/
├── rfl-alias/
├── rfl-effects/
├── rfl-context/
├── rfl-locks/
├── rfl-atomics/
├── rfl-refcount/
├── rfl-rcu/
├── rfl-lifetime/
├── rfl-ownership/
├── rfl-callbacks/
├── rfl-dma/
├── rfl-mmio/
├── rfl-abi/
├── rfl-arch/
├── rfl-config/
├── rfl-history/
├── rfl-runtime-evidence/
├── rfl-reconcile/
├── rfl-conflicts/
├── rfl-unknowns/
└── rfl-ksir/
```

I would keep the specialized analyzers separate initially. They can share a common
observation schema without sharing semantic authority.

---

## 290. First Implementation Target

Do **not** start with ownership inference.

The first executable vertical slice should be:

```text
Linux snapshot
      ↓
build manifest
      ↓
compiler invocation capture
      ↓
AST
      ↓
CFG
      ↓
call graph
      ↓
typed observations
      ↓
evidence bundle
      ↓
KSIR structural layer
```

Acceptance:

| ID | Acceptance criterion |
| --- | --- |
| SR-001 | exact snapshot binding |
| SR-002 | exact build-variant binding |
| SR-003 | reproducible compile command |
| SR-004 | source-span provenance |
| SR-005 | deterministic AST extraction |
| SR-006 | deterministic CFG extraction |
| SR-007 | deterministic callgraph extraction |
| SR-008 | every fact carries observation provenance |
| SR-009 | unsupported construct becomes UNKNOWN |
| SR-010 | analyzer failure cannot become VERIFIED |
| SR-011 | variant-specific facts remain variant-specific |
| SR-012 | repeated execution produces identical artifact digests |

Only after that should the first semantic domain be added.

I would choose **execution context + effect propagation** as the first semantic domain,
because it provides a relatively clean demonstration of:

```text
structural facts
    → semantic facts
    → interprocedural propagation
    → unknown handling
    → conflict handling
    → migration blocker
```

without immediately taking on the full complexity of RCU or MM.

---

## 291. The Resulting Architecture

At this point RFL-AE becomes a genuine semantic engineering system:

```text
                                ┌────────────────┐
                                │ Linux Snapshot │
                                └────────┬───────┘
                                         │
                                ┌────────────────┐
                                │ Build Variants │
                                └────────┬───────┘
                                         │
                                  ┌─────────────┐
                                  │ Observation │
                                  │ Backends    │
                                  └──────┬──────┘
                                         │
               ┌─────────────────────────┼─────────────────────────┐
               │                         │                         │
               ▼                         ▼                         ▼
          Structural                 Semantic                   Runtime
         observations             reconstruction             observations
               │                         │                         │
               └─────────────────────────┼─────────────────────────┘
                                         ▼
                                ┌────────────────┐
                                │ Reconciliation │
                                └────────┬───────┘
                                         │
               ┌─────────────────────────┼─────────────────────────┐
               ▼                         ▼                         ▼
             FACTS                   CONFLICTS                 UNKNOWNS
               │                         │                         │
               ▼                         ▼                         ▼
             KSIR                   QUARANTINE                 BLOCKERS
               │
               ▼
        Kernel Contract
               │
               ▼
        Rust Design IR
               │
               ▼
      Rust Implementation
               │
       ┌───────┴───────┐
       ▼               ▼
 Verification    Differential
       │               │
       └───────┬───────┘
               ▼
        Adversarial QA
               │
               ▼
        Evidence Bundle
               │
               ▼
     Migration Certificate
```

The key invariant now becomes stronger:

> ### **No analyzer output is truth. No LLM output is truth. A semantic claim exists only as an evidence-bound, snapshot/variant-scoped reconciled artifact.**

That gives us the foundation needed for the next layer: **Kernel Contract Reconstruction** —
turning the KSIR facts into explicit preconditions, postconditions, invariants, temporal
obligations, concurrency obligations, ABI obligations, and migration-preservation obligations
that the Rust design must satisfy.

---

**Done — see [CONTRACTS.md](CONTRACTS.md)** (§292–§320), which turns those facts into what
the Rust implementation must preserve: `KernelContract` and contract status, preconditions
and postconditions, invariants and invariant preservation, contract normal form, the
contract categories surface, temporal / concurrency / context contracts, API contract
generation, Rust design alternatives, design obligations, unsafe boundary generation and the
unsafe budget, contract-to-test generation, contract differential testing, contract
refinement, contract completeness and the completeness gate, the contract compiler, the agent
boundary, the contract review agent, the counterexample engine, the migration unit contract
package, the end-to-end proof chain, and the Rust Design IR transition.
