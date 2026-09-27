# RFL-AE — Making the KSIR Vertical Slice Executable

> **Provenance and numbering.** This document was supplied as *Continue: make the KSIR vertical slice executable*, numbered §1–§19 in the source plus a final unnumbered *The immediate next build target* clause. To keep the corpus contiguous, its sections are renumbered **§660–§679**, continuing directly from [KSIR-IMPL.md](KSIR-IMPL.md) (which ends at §659). The mapping is **`corpus_section = source_section + 659`**, with the unnumbered closing clause recorded as source §20 — the convention already used by `PROTOCOL-KERNEL.md`, `FIRST-MIGRATION.md` and `KSIR-IMPL.md`. The original source numbering is preserved on every heading as a machine-readable HTML comment of the form `<!-- source: KSIR-SLICE.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/` tree, no `rfl-types` / `rfl-ksir` / `rfl-analysis-types` / `rfl-analysis-compiler` crate, no `fixtures/lab001/`, and no test has been written or compiled. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** In the pasted source every ASCII diagram arrived collapsed onto a single line. Those diagrams were therefore *redrawn* rather than copied, with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector and off-centre checks — they were not hand-typed. The generator is committed at [`diagrams/KSIR-SLICE.py`](diagrams/KSIR-SLICE.py); re-running it reproduces all 36 diagrams, so the redraw can be checked rather than trusted. The observation record in §670 is fenced as `json`, and the C snippet in §674 as `c`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The next step is to turn the previous schema into a **minimal compilable implementation**. Keep the scope deliberately narrow:

```text
rfl-types
   ↓
rfl-ksir
   ↓
rfl-analysis-types
   ↓
rfl-analysis-compiler
   ↓
lab001
   ↓
KSIR artifact
```

Do not connect the full scheduler yet. First prove that semantic reconstruction produces deterministic, evidence-bound artifacts.

---

## Contents

- [660. Repository addition](#660-repository-addition)
- [661. `rfl-types`](#661-rfl-types)
- [662. Digest type](#662-digest-type)
- [663. Snapshot identity](#663-snapshot-identity)
- [664. Build variant](#664-build-variant)
- [665. Provenance is mandatory](#665-provenance-is-mandatory)
- [666. KSIR pointer model](#666-ksir-pointer-model)
- [667. Lifetime model](#667-lifetime-model)
- [668. Concurrency model](#668-concurrency-model)
- [669. Context and effects](#669-context-and-effects)
- [670. Observation schema](#670-observation-schema)
- [671. Reconciler](#671-reconciler)
- [672. Compiler backend boundary](#672-compiler-backend-boundary)
- [673. First structural analyzer](#673-first-structural-analyzer)
- [674. The first deliberate failure](#674-the-first-deliberate-failure)
- [675. Deterministic KSIR digest](#675-deterministic-ksir-digest)
- [676. Snapshot invalidation test](#676-snapshot-invalidation-test)
- [677. First gate](#677-first-gate)
- [678. What this gives us](#678-what-this-gives-us)
- [679. The immediate next build target](#679-the-immediate-next-build-target)

---

## 660. Repository addition
<!-- source: KSIR-SLICE.md §1 -->

```text
RFL-AE/
├── crates/
│   ├── rfl-types/
│   ├── rfl-ksir/
│   ├── rfl-analysis-types/
│   └── rfl-analysis-compiler/
├── fixtures/
│   └── lab001/
│       ├── include/
│       │   └── lab_object.h
│       ├── c/
│       │   └── lab_object.c
│       ├── expected/
│       │   └── structural-ksir.json
│       └── negative/
└── tests/
    └── ksir/
        ├── deterministic.rs
        ├── provenance.rs
        ├── unknown.rs
        ├── conflict.rs
        └── snapshot.rs
```

The important architectural distinction is:

```text
rfl-types
    = universal identity / digest / snapshot primitives
rfl-ksir
    = semantic representation
rfl-analysis-types
    = observations produced by analyzers
rfl-analysis-compiler
    = one concrete observation producer
```

This prevents the analyzer from becoming the semantic authority.

---

## 661. `rfl-types`
<!-- source: KSIR-SLICE.md §2 -->

Start with strongly typed IDs.

```rust
macro_rules! id_type {
    ($name:ident) => {
        #[derive(
            Clone,
            Copy,
            Debug,
            Eq,
            Ord,
            PartialEq,
            PartialOrd,
            Hash,
            serde::Serialize,
            serde::Deserialize,
        )]
        #[serde(transparent)]
        pub struct $name(pub uuid::Uuid);
    };
}

id_type!(SnapshotId);
id_type!(VariantId);
id_type!(SubjectId);
id_type!(SymbolId);
id_type!(FunctionId);
id_type!(ObjectId);
id_type!(FieldId);
id_type!(FactId);
id_type!(UnknownId);
id_type!(ConflictId);
id_type!(ObservationId);
id_type!(ArtifactId);
```

Do not use strings everywhere.

A string such as:

```text
"lab_object"
```

is descriptive identity.

A typed `ObjectId` is protocol identity.

That distinction will matter when artifacts are invalidated.

---

## 662. Digest type
<!-- source: KSIR-SLICE.md §3 -->

Do not let hashing leak throughout the system.

```rust
#[derive(
    Clone,
    Copy,
    Debug,
    Eq,
    Ord,
    PartialEq,
    PartialOrd,
    Hash,
    serde::Serialize,
    serde::Deserialize,
)]
pub struct Digest {
    pub algorithm: DigestAlgorithm,
    pub bytes: [u8; 32],
}

#[derive(
    Clone,
    Copy,
    Debug,
    Eq,
    PartialEq,
    serde::Serialize,
    serde::Deserialize,
)]
pub enum DigestAlgorithm {
    Sha256,
}
```

The algorithm is part of the identity.

Later:

```text
sha256:...
sha3-256:...
blake3:...
```

must never become ambiguous.

---

## 663. Snapshot identity
<!-- source: KSIR-SLICE.md §4 -->

The authoritative snapshot should be structural, not merely:

```text
Linux 6.x
```

Use:

```rust
pub struct KernelSnapshot {
    pub id: SnapshotId,
    pub source_tree_digest: Digest,
    pub source_version: Option<String>,
}
```

`source_version` is descriptive.

`source_tree_digest` is authoritative.

This preserves:

```text
same version label ≠ same source tree
```

---

## 664. Build variant
<!-- source: KSIR-SLICE.md §5 -->

```rust
pub struct BuildVariant {
    pub id: VariantId,
    pub snapshot: SnapshotId,
    pub architecture: Architecture,
    pub config_digest: Digest,
    pub toolchain: ToolchainIdentity,
    pub generated_inputs: Vec<ArtifactId>,
}
```

For the first fixture:

```text
snapshot = fixture tree digest
architecture = host architecture
config = fixture configuration digest
toolchain = exact compiler identity
```

Later the same semantic subject can legitimately have:

```text
Variant A → x86_64 + CONFIG_X=y
Variant B → arm64 + CONFIG_X=n
```

Those are separate validity domains.

---

## 665. Provenance is mandatory
<!-- source: KSIR-SLICE.md §6 -->

```rust
pub struct Provenance {
    pub source: Vec<SourceRef>,
    pub backend: BackendIdentity,
    pub execution: ExecutionReceiptId,
}
```

With:

```rust
pub struct SourceRef {
    pub path: String,
    pub line_start: u32,
    pub line_end: u32,
    pub symbol: Option<String>,
}
```

The compiler backend therefore cannot emit:

```text
field.value = protected
```

without being able to answer:

```text
from where?
using which backend?
against which snapshot?
from which execution?
```

---

## 666. KSIR pointer model
<!-- source: KSIR-SLICE.md §7 -->

Now implement the semantic distinctions rather than collapsing everything into Rust-like ownership.

```rust
pub enum OwnershipKind {
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

```rust
pub enum Nullability {
    NonNullEstablished,
    MayBeNull,
    CheckedBeforeUse,
    SentinelValue,
    Unknown,
}
```

```rust
pub enum Aliasing {
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

The combination is important.

For example:

```text
Ownership = RefCounted
Aliasing  = MutableShared
Lifetime  = Unknown
```

is perfectly valid KSIR.

It must not be "helpfully" converted into:

```text
Arc<T>
```

---

## 667. Lifetime model
<!-- source: KSIR-SLICE.md §8 -->

```rust
pub enum LifetimeState {
    Allocated,
    Initialized,
    Published,
    Referenced,
    Quiescing,
    Reclaimable,
    Freed,
}
```

And:

```rust
pub struct LifetimeFact {
    pub object: ObjectId,
    pub state: LifetimeState,
    pub predecessor: Option<LifetimeState>,
    pub trigger: Option<SubjectId>,
}
```

For `lab_object`, the expected conceptual chain is:

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

The analyzer does not need to prove the entire chain initially.

It needs to report which transitions it has evidence for.

---

## 668. Concurrency model
<!-- source: KSIR-SLICE.md §9 -->

```rust
pub enum SyncPrimitive {
    SpinLock,
    RawSpinLock,
    Mutex,
    RwLock,
    Atomic,
    Refcount,
    Rcu,
    Completion,
    WaitQueue,
    PerCpu,
    Unknown,
}
```

```rust
pub struct ConcurrencyFact {
    pub subject: SubjectId,
    pub primitive: SyncPrimitive,
    pub operation: SyncOperation,
    pub protected: Vec<SubjectId>,
    pub context: ExecutionContext,
}
```

For the fixture:

```text
lab_object.lock
    ↓
SpinLock
    ↓
protects
    ↓
lab_object.value
```

But this relation must come from observations.

It should not be hard-coded merely because the field names suggest it.

---

## 669. Context and effects
<!-- source: KSIR-SLICE.md §10 -->

```rust
pub enum ExecutionContext {
    Process,
    Workqueue,
    SoftIrq,
    HardIrq,
    Nmi,
    Timer,
    Tasklet,
    RcuCallback,
    Unknown,
}
```

```rust
pub enum Sleepability {
    MustNotSleep,
    MaySleep,
    MustSleep,
    Conditional,
    Unknown,
}
```

Then:

```rust
pub struct ContextFact {
    pub function: FunctionId,
    pub contexts: Vec<ExecutionContext>,
    pub sleepability: Sleepability,
}
```

And:

```rust
pub enum Effect {
    Allocate,
    Free,
    Sleep,
    AcquireLock,
    ReleaseLock,
    RefAcquire,
    RefRelease,
    Publish,
    Unpublish,
    ScheduleCallback,
    CancelCallback,
    Unknown,
}
```

This becomes the basis for context checking.

---

## 670. Observation schema
<!-- source: KSIR-SLICE.md §11 -->

The analyzer output should look like this conceptually:

```json
{
  "observation_id": "...",
  "snapshot": "...",
  "variant": "...",
  "subject": "...",
  "fact_kind": "FunctionCall",
  "value": {
    "caller": "lab_schedule",
    "target": "schedule_work"
  },
  "backend": {
    "name": "compiler-frontend",
    "version": "...",
    "algorithm_revision": "..."
  },
  "epistemic": "Observed",
  "execution_receipt": "...",
  "digest": "sha256:..."
}
```

The observation says:

> this backend observed X.

It does **not** say:

> X is semantically verified.

---

## 671. Reconciler
<!-- source: KSIR-SLICE.md §12 -->

The first reconciler can be extremely small.

```rust
pub fn reconcile<T>(
    observations: &[AnalysisObservation<T>],
) -> ReconciliationResult<T>
where
    T: Eq + Clone,
{
    // deterministic grouping and comparison
}
```

Conceptually:

```text
0 observations
    → InsufficientEvidence
1 observation
    → resolved provisional fact
N identical observations
    → Consistent
N different observations
    → Conflicted
```

Later the reconciliation rules become domain-specific.

Do not introduce weighted voting.

---

## 672. Compiler backend boundary
<!-- source: KSIR-SLICE.md §13 -->

The compiler backend should have no direct access to canonical protocol state.

```text
Protocol
   │
   │ authorized execution
   ▼
Execution Runtime
   │
   ▼
Compiler Backend
   │
   ▼
ObservationBundle
   │
   ▼
KSIR Reconciler
```

The backend is therefore incapable of doing:

```text
state.migration = Verified
```

Its only legitimate output is:

```text
observations
unknowns
execution references
artifacts
```

---

## 673. First structural analyzer
<!-- source: KSIR-SLICE.md §14 -->

For `lab001`, implement only:

```text
A001 declarations
A002 definitions
A003 function calls
A004 struct fields
A005 basic field accesses
A006 function-pointer/callback registration markers
A007 compiler-visible layout
```

Do not pretend this is already a kernel semantic analyzer.

The capability status should explicitly be:

```text
SUPPORTED:
    ordinary structs
    ordinary functions
    direct calls
    field declarations
    basic field accesses
PARTIALLY_SUPPORTED:
    macros
    callbacks
    typedef-heavy constructs
OPAQUE:
    complex generated constructs
    inline assembly
UNKNOWN:
    unresolved indirect calls
    unresolved ownership
    unresolved lifetime
```

---

## 674. The first deliberate failure
<!-- source: KSIR-SLICE.md §15 -->

This is essential.

Create a fixture where:

```c
struct lab_object *obj = get_object();
schedule_work(&obj->work);
put_object(obj);
```

but the analyzer cannot establish whether:

```text
schedule_work()
```

takes a reference.

Expected result:

```text
Ownership:
    UNKNOWN
Lifetime:
    UNKNOWN
Callback lifetime:
    UNKNOWN
Severity:
    CRITICAL
Migration:
    BLOCKED
```

That is a successful test.

The analyzer **failing safely** is part of correctness.

---

## 675. Deterministic KSIR digest
<!-- source: KSIR-SLICE.md §16 -->

Canonical serialization:

```text
KSIR
 ↓
canonical serialization
 ↓
SHA-256
 ↓
ksir_digest
```

Two executions with identical:

```text
snapshot
variant
inputs
tool identities
algorithm revisions
```

must produce the same canonical digest.

Test:

```rust
#[test]
fn identical_input_produces_identical_ksir_digest() {
    let a = analyze_fixture();
    let b = analyze_fixture();

    assert_eq!(a.digest(), b.digest());
}
```

But the stronger test is:

```text
fresh process
fresh filesystem
fresh analyzer invocation
same inputs
        ↓
same semantic artifact
same digest
```

---

## 676. Snapshot invalidation test
<!-- source: KSIR-SLICE.md §17 -->

This should fail closed.

```text
Snapshot A
 ↓
Observation A
 ↓
KSIR A
 ↓
Contract A
```

Then modify one source byte:

```text
Snapshot B
```

The old KSIR must not silently remain current.

Expected:

```text
KSIR-A = SUPERSEDED
Contract-A = STALE
Design-A = STALE
Verification-A = STALE
Certificate-A = INVALIDATED / SUPERSEDED
```

The old artifacts remain historically available.

They simply lose current authority.

---

## 677. First gate
<!-- source: KSIR-SLICE.md §18 -->

Create:

```text
KSIR-GATE-001
```

Requirements:

```text
1. snapshot bound
2. variant bound
3. execution receipt bound
4. every fact has provenance
5. unsupported constructs preserved
6. conflicts explicit
7. critical unknowns explicit
8. deterministic serialization
9. analyzer failure cannot produce VERIFIED
10. stale snapshot cannot produce current KSIR
```

The gate output should be:

```text
PASS
FAIL
BLOCKED
```

not:

```text
87% semantic confidence
```

---

## 678. What this gives us
<!-- source: KSIR-SLICE.md §19 -->

After this slice, RFL-AE has a genuine semantic pipeline:

```text
              TRUSTED
                 │
                 ▼
        Snapshot / Variant
                 │
                 ▼
       Authorized Execution
                 │
                 ▼
            Observation
                 │
            ┌────┴────┐
            ▼         ▼
        Evidence   Unknown
            │         │
            ▼         ▼
        Reconcile  Blocker
            │
      ┌─────┴─────┐
      ▼           ▼
  Semantic    Conflict
    Fact
      │
      ▼
    KSIR
```

And the authority separation is now concrete:

| Component | May observe | May derive | May verify | May authorize |
| --- | --- | --- | --- | --- |
| Compiler backend | Yes | Limited | No | No |
| KSIR reconciler | Yes | Yes | No | No |
| Contract compiler | No | Yes | No | No |
| Rust designer | No | Yes | No | No |
| Implementer | No | Yes | No | No |
| Execution runtime | Execution facts | No semantic interpretation | No | No |
| Verification engine | Evidence | Yes | Yes | No |
| Gate engine | Evidence/results | Gate state | Yes | No |
| Protocol kernel | Protocol state | State transition | No semantic proof | Protocol transitions only |
| Release authority | Existing artifacts | No | Consumes gates | Release |

That separation is the point of the architecture.

---

## 679. The immediate next build target
<!-- source: KSIR-SLICE.md §20 -->

Now implement **`rfl-analysis-types` and `rfl-analysis-compiler` around `lab001`**, with the first executable chain:

```text
fixture
 → BuildManifest
 → authorized compiler execution
 → ExecutionReceipt
 → ObservationBundle
 → reconciliation
 → KSIR
 → deterministic digest
 → KSIR-GATE-001
```

Only after that produces a real artifact should ownership/lifetime/context reconstruction be expanded. This gives us the first point where RFL-AE can be tested against **actual evidence rather than architectural assertions**.

---

**Done — see [KSIR-ANALYZER.md](KSIR-ANALYZER.md)** (§680–§701, source §§1–§21 plus the unnumbered
*next implementation sequence*), which builds the first real analyzer instead of another schema:
the frozen analyzer boundary in which the analyzer **never receives permission to mutate
canonical protocol state**, `AnalysisArtifact` so the chain is
`KSIR fact ↓ Observation ↓ AnalysisArtifact ↓ ExecutionReceipt` rather than `"compiler said so"`,
a normalization layer that keeps compiler-specific structures out of KSIR, a reproducible
`BackendIdentity` where `executable_digest` and `algorithm_revision` mean an algorithm change
invalidates derived facts even with the source tree unchanged, build invocation driven by a real
`BuildManifest` and recorded as the **actual command**, the deliberately small `lab001` fixture
with a shim so it stays independently buildable, the expected structural graph, observed versus
derived versus unknown facts that must never be collapsed, direct-call effect propagation with
`DerivedFact` pointing back to both observations, versioned `RuleIdentity`, the callback,
context, ownership and lifetime rules that stop at `UNKNOWN` instead of guessing, the structural
KSIR artifact where `UNKNOWN` is useful data, three negative tests (analyzer failure, conflicting
observations, snapshot substitution) proving `execution failure ≠ semantic false ≠ verification
failure`, the first `KSIR-GATE-001` execution where **BLOCKED is the correct result**, Contract IR
with `C005 = BLOCKED`, and the two properties that become executable tests. Same provenance
convention as `VERIFICATION.md`.
