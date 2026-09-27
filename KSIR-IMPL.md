# RFL-AE — KSIR v0.1 and the First Semantic Reconstruction Vertical Slice

> **Provenance and numbering.** This document was supplied as *Next stage: implement KSIR v0.1 + the first semantic reconstruction vertical slice*, numbered §1–§18 in the source plus a final unnumbered *The implementation order is now fixed* clause. To keep the corpus contiguous, its sections are renumbered **§641–§659**, continuing directly from [FIRST-MIGRATION.md](FIRST-MIGRATION.md) (which ends at §640). The mapping is **`corpus_section = source_section + 640`**, with the unnumbered closing clause recorded as source §19 — the same convention `PROTOCOL-KERNEL.md` and `FIRST-MIGRATION.md` use for their unnumbered closing clauses. The original source numbering is preserved on every heading as a machine-readable HTML comment of the form `<!-- source: KSIR-IMPL.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/` tree, no `rfl-types` or `rfl-ksir` crate, no `fixtures/lab001/`, and no compiler-observation backend has been written. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** In the pasted source every ASCII diagram arrived collapsed onto a single line. Those diagrams were therefore *redrawn* rather than copied, with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector and off-centre checks — they were not hand-typed. The generator is committed at [`diagrams/KSIR-IMPL.py`](diagrams/KSIR-IMPL.py); re-running it reproduces all 36 diagrams, so the redraw can be checked rather than trusted. JSON snippets are fenced as `json` (the first use of that language in the corpus) rather than `text`, since they are machine-readable records. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The architecture is now far enough along that another abstraction layer would add little value. The next move is to make **KSIR executable against a real C fixture**, while keeping the protocol/evidence rules already frozen.

The target is:

```text
C fixture
   │
   ├── compiler observations
   ├── source observations
   ├── CFG / call graph
   └── execution receipts
            │
            ▼
    ObservationBundle
            │
            ▼
     Reconciliation
       ┌────┴────┐
       │         │
   resolved  conflict
       │         │
       └────┬────┘
            ▼
          KSIR
            │
      ┌─────┴─────┐
      ▼           ▼
   UNKNOWN    CONTRACT
      │
      └─────► blocking gates
```

---

## Contents

- [641. Freeze KSIR v0.1](#641-freeze-ksir-v01)
- [642. Core Rust types](#642-core-rust-types)
- [643. UNKNOWN must carry a reason](#643-unknown-must-carry-a-reason)
- [644. Observation layer](#644-observation-layer)
- [645. Backend contract](#645-backend-contract)
- [646. Build manifest comes first](#646-build-manifest-comes-first)
- [647. First backend: compiler-native structural observations](#647-first-backend-compiler-native-structural-observations)
- [648. Call graph representation](#648-call-graph-representation)
- [649. Context reconstruction](#649-context-reconstruction)
- [650. Effect propagation](#650-effect-propagation)
- [651. Ownership reconstruction](#651-ownership-reconstruction)
- [652. Lock reconstruction](#652-lock-reconstruction)
- [653. Reconciliation](#653-reconciliation)
- [654. KSIR synthesis](#654-ksir-synthesis)
- [655. Critical-unknown extraction](#655-critical-unknown-extraction)
- [656. First executable test corpus](#656-first-executable-test-corpus)
- [657. Acceptance tests](#657-acceptance-tests)
- [658. The first end-to-end execution](#658-the-first-end-to-end-execution)
- [659. The implementation order is now fixed](#659-the-implementation-order-is-now-fixed)

---

## 641. Freeze KSIR v0.1
<!-- source: KSIR-IMPL.md §1 -->

Do not attempt to model the whole kernel yet.

The first implementation should support only:

| Domain | v0.1 |
| --- | --- |
| symbols | REQUIRED |
| functions | REQUIRED |
| types/layout | REQUIRED |
| calls | REQUIRED |
| execution context | REQUIRED |
| effects | REQUIRED |
| ownership | REQUIRED |
| lifetime | REQUIRED |
| locks | REQUIRED |
| callbacks | REQUIRED |
| refcount | REQUIRED |
| RCU | schema only initially |
| ABI | REQUIRED |
| architecture | REQUIRED |
| configuration | REQUIRED |
| provenance | REQUIRED |
| UNKNOWN | REQUIRED |
| conflicts | REQUIRED |

The important point is that **unsupported analysis must serialize as an explicit limitation**, not disappear.

---

## 642. Core Rust types
<!-- source: KSIR-IMPL.md §2 -->

Start with `rfl-types`, then let `rfl-ksir` depend on it.

```text
crates/
├── rfl-types/
│   └── src/
│       ├── ids.rs
│       ├── digest.rs
│       ├── snapshot.rs
│       ├── variant.rs
│       ├── provenance.rs
│       └── status.rs
└── rfl-ksir/
    └── src/
        ├── lib.rs
        ├── symbol.rs
        ├── function.rs
        ├── object.rs
        ├── pointer.rs
        ├── ownership.rs
        ├── lifetime.rs
        ├── concurrency.rs
        ├── context.rs
        ├── effects.rs
        ├── callback.rs
        ├── refcount.rs
        ├── abi.rs
        ├── architecture.rs
        ├── config.rs
        ├── fact.rs
        ├── unknown.rs
        ├── conflict.rs
        └── graph.rs
```

The central rule:

```rust
pub struct SemanticFact<T> {
    pub fact_id: FactId,
    pub subject: SubjectId,
    pub value: T,
    pub epistemic: EpistemicStatus,
    pub validity: ValidityDomain,
    pub provenance: Provenance,
}
```

And:

```rust
pub enum EpistemicStatus {
    Observed,
    Derived,
    Hypothesis,
    Unknown,
}
```

Do **not** put `Verified` here.

Verification belongs downstream.

---

## 643. UNKNOWN must carry a reason
<!-- source: KSIR-IMPL.md §3 -->

This is important enough to make structural.

```rust
pub struct UnknownFact {
    pub id: UnknownId,
    pub subject: SubjectId,
    pub domain: UnknownDomain,
    pub reason: UnknownReason,
    pub severity: UnknownSeverity,
    pub validity: ValidityDomain,
    pub provenance: Vec<ProvenanceRef>,
}
```

For example:

```rust
pub enum UnknownDomain {
    Ownership,
    Lifetime,
    Aliasing,
    Synchronization,
    ExecutionContext,
    Sleepability,
    Allocation,
    CallbackReachability,
    Abi,
    Architecture,
    Configuration,
    InlineAssembly,
    GeneratedCode,
    FunctionPointerTarget,
    UserspacePointer,
    DmaLifetime,
    MmioSemantics,
}
```

And:

```rust
pub enum UnknownReason {
    UnsupportedConstruct,
    InsufficientEvidence,
    AnalysisFailure,
    ConditionalPathUnresolved,
    ExternalDefinitionUnavailable,
    GeneratedArtifactUnavailable,
    ArchitectureVariantUnavailable,
    IndirectCallUnresolved,
    ConflictingObservations,
}
```

This gives the system something much stronger than:

```json
{
  "ownership": null
}
```

It becomes:

```json
{
  "domain": "Ownership",
  "reason": "IndirectCallUnresolved",
  "severity": "Critical"
}
```

That is actionable.

---

## 644. Observation layer
<!-- source: KSIR-IMPL.md §4 -->

KSIR should **not directly trust analyzer output**.

Introduce:

```text
Analyzer
   │
   ▼
AnalysisObservation
   │
   ▼
ObservationBundle
   │
   ▼
Reconciler
   │
   ▼
SemanticFact
```

Core structure:

```rust
pub struct AnalysisObservation<T> {
    pub observation_id: ObservationId,
    pub snapshot: KernelSnapshotId,
    pub variant: BuildVariantId,
    pub subject: SubjectId,
    pub fact_kind: FactKind,
    pub value: T,
    pub backend: BackendIdentity,
    pub algorithm: AlgorithmIdentity,
    pub provenance: Provenance,
    pub execution: ExecutionReceiptId,
    pub epistemic: ObservationEpistemic,
    pub dependencies: Vec<ObservationId>,
    pub digest: Digest,
}
```

The observation itself can say:

```text
OBSERVED
```

but never:

```text
VERIFIED
```

---

## 645. Backend contract
<!-- source: KSIR-IMPL.md §5 -->

Every backend gets exactly the same basic contract.

```rust
pub trait AnalysisBackend {
    fn identity(&self) -> BackendIdentity;

    fn analyze(
        &self,
        request: AnalysisRequest,
    ) -> Result<ObservationBundle, AnalysisError>;
}
```

`AnalysisRequest` must include:

```rust
pub struct AnalysisRequest {
    pub snapshot: KernelSnapshotId,
    pub variant: BuildVariantId,
    pub scope: AnalysisScope,
    pub inputs: Vec<ArtifactRef>,
    pub algorithm: AlgorithmIdentity,
}
```

The backend cannot silently select:

- another kernel commit
- another `.config`
- another compiler
- another generated-header tree
- another architecture

If it does, the evidence is invalid.

---

## 646. Build manifest comes first
<!-- source: KSIR-IMPL.md §6 -->

Before AST extraction, create:

```text
Build Manifest
```

It becomes the root of semantic evidence.

```rust
pub struct BuildManifest {
    pub snapshot: KernelSnapshotId,
    pub variant: BuildVariantId,
    pub architecture: ArchitectureId,
    pub config_digest: Digest,
    pub compiler: ToolIdentity,
    pub linker: Option<ToolIdentity>,
    pub generated_headers: Vec<ArtifactRef>,
    pub generated_sources: Vec<ArtifactRef>,
    pub invocations: Vec<CommandRef>,
    pub environment: EnvironmentFingerprint,
}
```

The critical invariant:

```text
No BuildManifest
        ↓
No authoritative compiler observation
        ↓
No VERIFIED semantic claim
```

This prevents a surprisingly common failure mode: analyzing source from one tree while compiling another generated state.

---

## 647. First backend: compiler-native structural observations
<!-- source: KSIR-IMPL.md §7 -->

Do not begin with Smatch, Coccinelle, or an LLM.

Begin with the compiler.

The first vertical slice should acquire:

```text
source
 ↓
compiler frontend
 ↓
AST/type information
 ↓
function declarations
 ↓
struct declarations
 ↓
field layout
 ↓
calls
```

For the fixture, the expected graph is roughly:

```text
lab_object
  ├── refs
  ├── lock
  ├── value
  └── work
lab_get
  └── refcount_inc
lab_put
  ├── refcount_dec
  └── lab_free
lab_update
  ├── spin_lock
  ├── value =
  └── spin_unlock
lab_schedule
  ├── refcount_inc
  └── schedule_work
lab_work
  ├── container_of
  ├── value =
  └── refcount_dec
```

The initial backend does **not** need to solve every kernel macro.

It needs to preserve uncertainty when it cannot.

---

## 648. Call graph representation
<!-- source: KSIR-IMPL.md §8 -->

```rust
pub struct CallEdge {
    pub caller: FunctionId,
    pub target: CallTarget,
    pub kind: CallEdgeKind,
    pub provenance: Provenance,
}
```

```rust
pub enum CallTarget {
    Exact(FunctionId),
    Finite(Vec<FunctionId>),
    Conditional(Vec<ConditionalTarget>),
    Unknown,
}
```

This is preferable to pretending every indirect call can be resolved.

The semantic lattice becomes:

```text
EXACT
  ↓
FINITE_SET
  ↓
CONDITIONAL_SET
  ↓
UNKNOWN
```

But these are **precision states**, not confidence scores.

---

## 649. Context reconstruction
<!-- source: KSIR-IMPL.md §9 -->

This should be the first real semantic analysis.

Define:

```rust
pub enum ExecutionContext {
    Process,
    SoftIrq,
    HardIrq,
    Nmi,
    Workqueue,
    Timer,
    Tasklet,
    RcuCallback,
    Unknown,
}
```

And:

```rust
pub struct ContextFact {
    pub function: FunctionId,
    pub reachable_contexts: ContextSet,
    pub may_sleep: Sleepability,
    pub provenance: Provenance,
}
```

For `lab_work`:

```text
registration:
    schedule_work()
        ↓
    workqueue dispatcher
        ↓
    lab_work()
```

Therefore:

```text
lab_work:
    context = WORKQUEUE
    may_sleep = MAY_SLEEP
```

That fact is derived from the callback graph rather than merely the function body.

---

## 650. Effect propagation
<!-- source: KSIR-IMPL.md §10 -->

Represent effects explicitly:

```rust
pub enum Effect {
    Allocates,
    Frees,
    Sleeps,
    AcquiresLock(LockId),
    ReleasesLock(LockId),
    RefAcquire(RefcountId),
    RefRelease(RefcountId),
    Publishes(ObjectId),
    Unpublishes(ObjectId),
    SchedulesCallback(CallbackId),
    CancelsCallback(CallbackId),
    EntersRcuRead,
    ExitsRcuRead,
    Unknown,
}
```

Then calculate:

```text
Direct effects
      + Callee effects
      + Callback effects
      + Context effects
      ↓
Effective function contract
```

Example:

```text
lab_schedule
    direct:
        ref_acquire
        schedule_callback
lab_work
    direct:
        lock_acquire
        mutation
        lock_release
        ref_release
lab_put
    direct:
        ref_release
        possible_free
```

---

## 651. Ownership reconstruction
<!-- source: KSIR-IMPL.md §11 -->

Do not encode simplistic rules such as:

```text
list_add() = ownership transfer
```

Instead collect evidence:

```text
allocation
    ↓
initialization
    ↓
publication
    ↓
reference acquisition
    ↓
callback registration
    ↓
callback completion
    ↓
reference release
    ↓
destruction
```

For `lab_object` the expected preliminary model is:

```text
Object
  │
  ├── initial owner
  │
  ├── refs
  │    ├── lab_get
  │    ├── lab_schedule
  │    └── lab_put
  │
  └── work callback
       │
       └── requires object alive
```

The important semantic question is:

> What prevents the callback from observing a freed object?

If the analyzer cannot establish the answer:

```text
UNKNOWN:
    Lifetime
    severity = Critical
```

That should block migration.

---

## 652. Lock reconstruction
<!-- source: KSIR-IMPL.md §12 -->

Represent accesses rather than only lock calls.

```rust
pub struct ProtectedAccess {
    pub object: ObjectId,
    pub field: FieldId,
    pub operation: AccessKind,
    pub lock: LockId,
    pub protection: ProtectionStatus,
    pub provenance: Provenance,
}
```

Expected result:

```text
lab_object.value
lab_update:
    WRITE
    lock = lab_object.lock
    PROTECTED
lab_work:
    WRITE
    lock = ?
    PROTECTED / UNKNOWN
```

If `lab_work` mutates `value` without the lock, that should be surfaced as:

```text
CONFLICT
```

or:

```text
UNPROTECTED
```

depending on the available evidence.

The analyzer must not repair the source semantics by assumption.

---

## 653. Reconciliation
<!-- source: KSIR-IMPL.md §13 -->

This is the point where multiple tools become useful.

Suppose:

```text
Compiler:
    field offset = 16
DWARF:
    field offset = 16
Rust layout probe:
    field offset = 24
```

The reconciler must produce:

```text
CONFLICT
```

not:

```text
field offset = 16
confidence = 0.91
```

Formally:

```rust
pub enum ReconciliationStatus {
    Consistent,
    ConditionallyConsistent,
    InsufficientEvidence,
    Conflicted,
    Invalidated,
}
```

And:

```rust
pub struct Conflict {
    pub conflict_id: ConflictId,
    pub subject: SubjectId,
    pub observations: Vec<ObservationId>,
    pub status: ConflictStatus,
    pub reason: ConflictReason,
}
```

No agent voting.

No majority rule.

No confidence aggregation.

---

## 654. KSIR synthesis
<!-- source: KSIR-IMPL.md §14 -->

Only reconciled facts enter canonical KSIR.

```rust
pub struct Ksir {
    pub snapshot: KernelSnapshotId,
    pub variants: Vec<BuildVariantId>,
    pub symbols: Vec<SemanticFact<Symbol>>,
    pub functions: Vec<SemanticFact<Function>>,
    pub objects: Vec<SemanticFact<Object>>,
    pub ownership: Vec<SemanticFact<OwnershipFact>>,
    pub lifetimes: Vec<SemanticFact<LifetimeFact>>,
    pub concurrency: Vec<SemanticFact<ConcurrencyFact>>,
    pub contexts: Vec<SemanticFact<ContextFact>>,
    pub effects: Vec<SemanticFact<EffectFact>>,
    pub callbacks: Vec<SemanticFact<CallbackFact>>,
    pub abi: Vec<SemanticFact<AbiFact>>,
    pub architecture: Vec<SemanticFact<ArchitectureFact>>,
    pub unknowns: Vec<UnknownFact>,
    pub conflicts: Vec<Conflict>,
    pub provenance: ProvenanceGraph,
}
```

The KSIR is therefore not merely:

```text
AST + annotations
```

It is:

```text
observations
    ↓
    reconciled semantic facts
    + explicit unknowns
    + explicit conflicts
    + validity domains
    + provenance
```

---

## 655. Critical-unknown extraction
<!-- source: KSIR-IMPL.md §15 -->

The first deterministic blocker rules should be deliberately small.

```text
UNKNOWN ownership
    + FFI crossing
    → CRITICAL
UNKNOWN lifetime
    + callback/async access
    → CRITICAL
UNKNOWN synchronization
    + mutable shared state
    → CRITICAL
UNKNOWN context
    + potentially sleeping operation
    → CRITICAL
UNKNOWN ABI
    + exported symbol
    → CRITICAL
```

The output becomes:

```json
{
  "blockers": [
    {
      "domain": "Lifetime",
      "subject": "lab_object",
      "reason": "CallbackReachabilityUnresolved",
      "severity": "Critical"
    }
  ]
}
```

The scheduler can then treat this as an evidence task.

---

## 656. First executable test corpus
<!-- source: KSIR-IMPL.md §16 -->

Build the fixture before building broad kernel support.

```text
fixtures/lab001/
├── include/
│   └── lab_object.h
├── c/
│   └── lab_object.c
├── rust/
│   └── lib.rs
├── tests/
│   ├── lifecycle.c
│   └── differential.rs
├── expected/
│   ├── ksir.json
│   ├── contract.json
│   └── obligations.json
└── negative/
    ├── missing_ref.rs
    ├── double_put.rs
    ├── use_after_free.rs
    ├── lock_bypass.rs
    ├── wrong_layout.rs
    ├── wrong_callback_context.rs
    └── ffi_lifetime_violation.rs
```

The expected KSIR should itself be treated as a **fixture specification**, not generated and blindly accepted as truth.

---

## 657. Acceptance tests
<!-- source: KSIR-IMPL.md §17 -->

The first KSIR gate should include at least:

```text
KSIR-001 Exact source snapshot is bound.
KSIR-002 Exact build variant is bound.
KSIR-003 Compiler invocation has an execution receipt.
KSIR-004 Every canonical fact has provenance.
KSIR-005 Unsupported constructs become UNKNOWN.
KSIR-006 Analyzer failure cannot produce VERIFIED.
KSIR-007 Unknown ownership is preserved.
KSIR-008 Unknown lifetime is preserved.
KSIR-009 Call graph preserves unresolved indirect calls.
KSIR-010 Context propagation is deterministic.
KSIR-011 Effect propagation is deterministic.
KSIR-012 Conflicting observations produce CONFLICT.
KSIR-013 Critical UNKNOWN produces a blocker.
KSIR-014 Facts are variant-scoped.
KSIR-015 Changing snapshot invalidates dependent KSIR.
KSIR-016 Changing compiler identity invalidates compiler-derived evidence.
KSIR-017 Changing generated headers changes the build-variant identity.
KSIR-018 KSIR serialization is deterministic.
KSIR-019 KSIR replay produces identical digest.
KSIR-020 No LLM-generated assertion can enter canonical KSIR without provenance.
```

That last one is particularly important.

---

## 658. The first end-to-end execution
<!-- source: KSIR-IMPL.md §18 -->

The real milestone should look like this:

```text
RFL-AE-LAB-001
        │
        ▼
MU-000001
        │
        ▼
exact Linux/C fixture snapshot
        │
        ▼
BuildManifest
        │
        ▼
authorized compiler execution
        │
        ▼
ExecutionReceipt
        │
        ▼
compiler observations
        │
        ▼
ObservationBundle
        │
        ├──────────────┐
        ▼              ▼
    resolved   UNKNOWN/CONFLICT
        │              │
        └──────┬───────┘
               ▼
             KSIR
               │
               ▼
          Contract IR
               │
               ▼
        Rust Design IR
               │
               ▼
        Verification IR
               │
               ▼
     authorized execution
               │
               ▼
           Evidence
               │
               ▼
             Gates
               │
               ▼
     Migration Certificate
```

And the certificate must be able to answer, mechanically:

```text
Which source?
Which snapshot?
Which configuration?
Which compiler?
Which command?
Which observations?
Which semantic facts?
Which unknowns?
Which conflicts?
Which contract?
Which design?
Which implementation?
Which exact tests?
Which receipts?
Which evidence?
Which obligations were verified?
Which authority performed verification?
Which gates passed?
What remains outside scope?
```

If any answer is:

```text
"the agent said so"
```

then **MU-000001 has not passed**.

---

## 659. The implementation order is now fixed
<!-- source: KSIR-IMPL.md §19 -->

I would freeze the next sequence as:

```text
M0
│
├── 1. rfl-types
├── 2. rfl-ksir schema
├── 3. BuildManifest
├── 4. compiler execution backend
├── 5. ObservationBundle
├── 6. structural reconciliation
├── 7. context/effect reconstruction
├── 8. ownership/lifetime reconstruction
├── 9. lock/callback/refcount reconstruction
├── 10. UNKNOWN + CONFLICT extraction
├── 11. KSIR deterministic serialization
├── 12. KSIR QA corpus
└── 13. feed MU-000001
```

**Do not implement RCU, DMA, full architecture analysis, or whole-kernel analysis yet.**

The next concrete artifact should therefore be the **actual `rfl-types` + `rfl-ksir` crate skeleton and Rust schemas**, followed immediately by the `lab001` compiler-observation backend. That gives RFL-AE its first executable semantic core rather than another document describing one.

---

**Done — see [KSIR-SLICE.md](KSIR-SLICE.md)** (§660–§679, source §§1–§19 plus the unnumbered
*immediate next build target*), which turns that schema into a minimal compilable
implementation: the `rfl-types` / `rfl-ksir` / `rfl-analysis-types` /
`rfl-analysis-compiler` split that stops the analyzer from becoming the semantic authority,
`id_type!` so that a typed `ObjectId` is protocol identity rather than a descriptive string,
a `Digest` that carries its algorithm, snapshot identity where `source_tree_digest` is
authoritative and `source_version` merely descriptive, build variants as separate validity
domains, mandatory provenance, the pointer model in which `Ownership = RefCounted`,
`Aliasing = MutableShared`, `Lifetime = Unknown` is valid KSIR and must not be "helpfully"
converted into `Arc<T>`, lifetime / concurrency / context / effect models, the observation
schema that says *this backend observed X* and never *X is semantically verified*, a
reconciler with no weighted voting, the compiler-backend boundary that cannot write
`state.migration = Verified`, the deliberately narrow `A001…A007` first analyzer with explicit
`SUPPORTED / PARTIALLY_SUPPORTED / OPAQUE / UNKNOWN` capability status, the first **deliberate
failure** where the analyzer failing safely is the correct result, deterministic KSIR digests,
fail-closed snapshot invalidation, `KSIR-GATE-001`, and the authority-separation table. Same
provenance convention as `VERIFICATION.md`.
