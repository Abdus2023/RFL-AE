# RFL-AE — The First Real Analyzer

> **Provenance and numbering.** This document was supplied as *Continue: implement the first real analyzer, not another schema*, numbered §1–§21 in the source plus a final unnumbered *The next implementation sequence* clause. To keep the corpus contiguous, its sections are renumbered **§680–§701**, continuing directly from [KSIR-SLICE.md](KSIR-SLICE.md) (which ends at §679). The mapping is **`corpus_section = source_section + 679`**, with the unnumbered closing clause recorded as source §22 — the convention already used by `PROTOCOL-KERNEL.md`, `FIRST-MIGRATION.md`, `KSIR-IMPL.md` and `KSIR-SLICE.md`. The original source numbering is preserved on every heading as a machine-readable HTML comment of the form `<!-- source: KSIR-ANALYZER.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/` tree, no `rfl-analysis-types` or `rfl-analysis-compiler` crate, no `fixtures/lab001/`, and no test has been written or compiled. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** Most ASCII diagrams in the pasted source arrived collapsed onto a single line and were therefore *redrawn*, with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector and off-centre checks. The generator is committed at [`diagrams/KSIR-ANALYZER.py`](diagrams/KSIR-ANALYZER.py); re-running it reproduces all 53 diagrams. Two diagrams arrived already laid out: the gate flow in §698 is structurally consistent and is reproduced unchanged, while the analyzer-boundary boxes in §680 had one interior row one column short of the other nine, so the box is re-emitted with its padding computed rather than typed. The structural KSIR artifact in §694 is fenced as `json`, the `lab_object` definition in §685 as `c`, and the build invocation in §684 as `bash` — the first `bash` fence in the corpus. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The next slice should establish **compiler acquisition → normalized observations → structural KSIR**. Once this works, semantic reconstruction can safely build on it.

---

## Contents

- [680. Freeze the analyzer boundary](#680-freeze-the-analyzer-boundary)
- [681. Introduce `AnalysisArtifact`](#681-introduce-analysisartifact)
- [682. Normalize compiler output](#682-normalize-compiler-output)
- [683. Backend identity must be reproducible](#683-backend-identity-must-be-reproducible)
- [684. Build invocation](#684-build-invocation)
- [685. `lab001` should be intentionally small](#685-lab001-should-be-intentionally-small)
- [686. Expected structural graph](#686-expected-structural-graph)
- [687. Separate observed and derived facts](#687-separate-observed-and-derived-facts)
- [688. First semantic rule: direct-call propagation](#688-first-semantic-rule-direct-call-propagation)
- [689. Rule identity](#689-rule-identity)
- [690. First callback rule](#690-first-callback-rule)
- [691. First context rule](#691-first-context-rule)
- [692. First ownership rule](#692-first-ownership-rule)
- [693. First lifetime rule](#693-first-lifetime-rule)
- [694. Structural KSIR artifact](#694-structural-ksir-artifact)
- [695. Negative test: analyzer failure](#695-negative-test-analyzer-failure)
- [696. Negative test: conflicting observations](#696-negative-test-conflicting-observations)
- [697. Negative test: snapshot substitution](#697-negative-test-snapshot-substitution)
- [698. First KSIR gate execution](#698-first-ksir-gate-execution)
- [699. Then connect it to Contract IR](#699-then-connect-it-to-contract-ir)
- [700. The first meaningful RFL-AE theorem](#700-the-first-meaningful-rfl-ae-theorem)
- [701. The next implementation sequence](#701-the-next-implementation-sequence)

---

## 680. Freeze the analyzer boundary
<!-- source: KSIR-ANALYZER.md §1 -->

```text
┌─────────────────────────────────────────────────────────────┐
│                    RFL-AE Protocol                          │
│                                                             │
│ authorization / snapshot / scope / capability / epoch       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                     Execution Runtime
                             │
                  exact command + receipt
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 rfl-analysis-compiler                       │
│                                                             │
│ source → compiler frontend → normalized observations        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                     ObservationBundle
                             │
                             ▼
                      Reconciliation
                             │
                             ▼
                         KSIR v0.1
```

The analyzer **never receives permission to mutate canonical protocol state**.

---

## 681. Introduce `AnalysisArtifact`
<!-- source: KSIR-ANALYZER.md §2 -->

Every analyzer result should have a concrete artifact identity.

```rust
pub struct AnalysisArtifact {
    pub artifact_id: ArtifactId,
    pub snapshot: SnapshotId,
    pub variant: VariantId,
    pub backend: BackendIdentity,

    pub observations: Vec<ObservationId>,
    pub unknowns: Vec<UnknownId>,
    pub conflicts: Vec<ConflictId>,

    pub execution: ExecutionReceiptId,
    pub digest: Digest,
}
```

This solves an important provenance problem:

```text
KSIR fact
 ↓
Observation
 ↓
AnalysisArtifact
 ↓
ExecutionReceipt
```

rather than:

```text
KSIR fact
 ↓
"compiler said so"
```

---

## 682. Normalize compiler output
<!-- source: KSIR-ANALYZER.md §3 -->

Do not let compiler-specific structures become KSIR.

Use an intermediate normalization layer:

```text
clang / GCC / sparse / ...
         │
         ▼
CompilerObservation
         │
         ▼
NormalizedObservation
         │
         ▼
KSIR
```

For example:

```rust
pub enum NormalizedFact {
    FunctionDeclared {
        function: FunctionId,
    },

    FunctionDefined {
        function: FunctionId,
    },

    DirectCall {
        caller: FunctionId,
        callee: FunctionId,
    },

    StructDeclared {
        object: ObjectId,
    },

    FieldDeclared {
        object: ObjectId,
        field: FieldId,
    },

    FieldAccess {
        function: FunctionId,
        field: FieldId,
        access: AccessKind,
    },

    Layout {
        subject: SubjectId,
        size: u64,
        alignment: u64,
    },
}
```

The compiler-specific parser can change later without changing KSIR.

---

## 683. Backend identity must be reproducible
<!-- source: KSIR-ANALYZER.md §4 -->

```rust
pub struct BackendIdentity {
    pub name: String,
    pub version: String,
    pub executable_digest: Digest,
    pub schema_version: String,
    pub algorithm_revision: String,
}
```

For example:

```text
compiler-frontend
version: X.Y.Z
executable: sha256:...
schema: compiler-observation/0.1
algorithm: clang-structural-v1
```

This matters because changing the analyzer algorithm can invalidate derived facts even when the source tree is unchanged.

---

## 684. Build invocation
<!-- source: KSIR-ANALYZER.md §5 -->

The first backend should never construct an imaginary compiler invocation.

Instead:

```text
BuildManifest
├── source tree
├── generated headers
├── compiler
├── flags
├── include paths
└── environment
              │
              ▼
   CommandSpec
```

The execution receipt records the **actual command**.

For the fixture:

```bash
cc -I fixtures/lab001/include -c fixtures/lab001/c/lab_object.c -o ...
```

Whatever command is actually used becomes evidence.

Do not merely record:

```text
"compiled successfully"
```

---

## 685. `lab001` should be intentionally small
<!-- source: KSIR-ANALYZER.md §6 -->

Use something close to:

```c
struct lab_object {
    refcount_t refs;
    spinlock_t lock;
    int value;
    struct work_struct work;
};
```

Functions:

```text
lab_alloc
lab_get
lab_put
lab_update
lab_schedule
lab_work
```

But there is one important adjustment:

**Do not require Linux's entire `refcount_t`, `spinlock_t`, and workqueue implementation for the first structural backend.**

Provide a fixture shim:

```text
fixtures/lab001/include/
├── linux/
│   ├── refcount.h
│   ├── spinlock.h
│   └── workqueue.h
└── lab_object.h
```

The analyzer then sees realistic type and call structure while the fixture remains independently buildable.

---

## 686. Expected structural graph
<!-- source: KSIR-ANALYZER.md §7 -->

The first analyzer should produce approximately:

```text
STRUCT lab_object
├── refs : refcount_t
├── lock : spinlock_t
├── value : int
└── work : work_struct

FUNCTION lab_alloc
FUNCTION lab_get
FUNCTION lab_put
FUNCTION lab_update
FUNCTION lab_schedule
FUNCTION lab_work

CALL GRAPH
lab_alloc
    └── allocation
lab_get
    └── refcount_inc
lab_put
    ├── refcount_dec
    └── lab_free
lab_update
    ├── spin_lock
    ├── value WRITE
    └── spin_unlock
lab_schedule
    ├── refcount_inc
    └── schedule_work
lab_work
    ├── container_of
    ├── value ACCESS
    └── refcount_dec
```

At this stage, the analyzer is allowed to know:

```text
lab_schedule calls schedule_work
```

but it is **not yet allowed to infer**:

```text
schedule_work guarantees object lifetime
```

That belongs to semantic reconstruction.

---

## 687. Separate observed and derived facts
<!-- source: KSIR-ANALYZER.md §8 -->

This distinction should become executable.

Example:

```text
OBSERVED
    lab_schedule → schedule_work
```

Then:

```text
DERIVED
    lab_schedule establishes callback reachability
```

And potentially:

```text
UNKNOWN
    callback lifetime guarantee
```

This gives:

```text
source observation
 ↓
semantic derivation
 ↓
remaining uncertainty
```

The system should never collapse these three states.

---

## 688. First semantic rule: direct-call propagation
<!-- source: KSIR-ANALYZER.md §9 -->

Now add the first derived analysis.

Given:

```text
A → B
```

and:

```text
B has effect E
```

derive:

```text
A has effect E
```

But preserve provenance:

```rust
pub struct DerivedFact {
    pub fact: FactId,
    pub inputs: Vec<ObservationId>,
    pub rule: RuleIdentity,
}
```

Example:

```text
OBS-001:
    lab_update calls spin_lock
OBS-002:
    spin_lock acquires SpinLock
DER-001:
    lab_update acquires SpinLock
```

The derived fact must point back to both observations.

---

## 689. Rule identity
<!-- source: KSIR-ANALYZER.md §10 -->

Never encode semantic inference as anonymous code.

```rust
pub struct RuleIdentity {
    pub rule_id: String,
    pub revision: String,
}
```

Example:

```text
CALL-EFFECT-PROPAGATION-001
```

Then if the algorithm changes:

```text
CALL-EFFECT-PROPAGATION-002
```

Old derived facts remain historically interpretable.

---

## 690. First callback rule
<!-- source: KSIR-ANALYZER.md §11 -->

Add:

```text
schedule_work(&obj->work)
→
callback registration
```

Represent:

```rust
pub struct CallbackFact {
    pub callback: CallbackId,
    pub registration_site: SubjectId,
    pub callback_function: FunctionId,
    pub dispatcher: Option<FunctionId>,
    pub source_object: Option<ObjectId>,
}
```

The first result can safely be:

```text
callback = lab_work
registration = lab_schedule
dispatcher = UNKNOWN
```

This is preferable to pretending the dispatcher is known.

---

## 691. First context rule
<!-- source: KSIR-ANALYZER.md §12 -->

Once:

```text
schedule_work
 ↓
callback registration
 ↓
lab_work
```

and the backend has a known fact:

```text
schedule_work → WORKQUEUE
```

derive:

```text
lab_work:
    reachable_context = WORKQUEUE
```

This is a semantic derivation:

```text
callback registration + dispatcher context = callback context
```

If dispatcher context cannot be established:

```text
lab_work.context = UNKNOWN
```

Again: no guessing.

---

## 692. First ownership rule
<!-- source: KSIR-ANALYZER.md §13 -->

Start with only one safe rule:

```text
refcount_inc(obj)
    → evidence of reference acquisition
```

and:

```text
refcount_dec(obj)
    → evidence of reference release
```

Do **not** initially infer:

```text
refcount_inc → ownership
```

because a reference count can have different semantic roles.

Instead:

```text
RefcountFact
├── counter
├── acquire operations
├── release operations
├── zero transition
└── destruction relation
```

Only when the destruction relation is established can the lifetime model become stronger.

---

## 693. First lifetime rule
<!-- source: KSIR-ANALYZER.md §14 -->

If:

```text
schedule_work(obj)
```

is followed by:

```text
put(obj)
```

the analyzer should ask:

```text
Does callback registration itself retain obj?
```

If the evidence does not establish that:

```text
UNKNOWN:
    callback lifetime
```

This is exactly the kind of issue RFL-AE exists to expose.

A normal source translator might generate apparently valid Rust.

RFL-AE must instead say:

```text
Migration blocked:
    callback lifetime is unresolved.
```

---

## 694. Structural KSIR artifact
<!-- source: KSIR-ANALYZER.md §15 -->

The first real artifact should resemble:

```json
{
  "schema": "rfl-ksir/0.1",
  "snapshot": "sha256:...",
  "variant": "variant:...",
  "functions": [
    "lab_alloc",
    "lab_get",
    "lab_put",
    "lab_update",
    "lab_schedule",
    "lab_work"
  ],
  "objects": [
    "lab_object"
  ],
  "calls": [
    ["lab_get", "refcount_inc"],
    ["lab_put", "refcount_dec"],
    ["lab_update", "spin_lock"],
    ["lab_update", "spin_unlock"],
    ["lab_schedule", "schedule_work"]
  ],
  "callbacks": [
    {
      "registration": "lab_schedule",
      "callback": "lab_work",
      "dispatcher": "UNKNOWN"
    }
  ],
  "unknowns": [
    {
      "domain": "CallbackReachability",
      "reason": "ExternalDefinitionUnavailable"
    }
  ]
}
```

Notice that `UNKNOWN` is actually useful data.

---

## 695. Negative test: analyzer failure
<!-- source: KSIR-ANALYZER.md §16 -->

Inject a malformed source fixture.

The expected result is **not**:

```text
KSIR = empty
status = VERIFIED
```

It must be:

```text
AnalysisStatus:
    FAILED
KSIR:
    unavailable / partial
Evidence:
    execution receipt exists
Verification:
    BLOCKED
```

This distinction is foundational:

```text
execution failure ≠ semantic false ≠ verification failure
```

---

## 696. Negative test: conflicting observations
<!-- source: KSIR-ANALYZER.md §17 -->

Create two observation backends:

```text
backend-A:
    sizeof(lab_object) = 32
backend-B:
    sizeof(lab_object) = 40
```

The reconciler must produce:

```text
CONFLICT
```

and:

```text
critical conflict = true
KSIR gate = BLOCKED
```

It must not select the compiler result merely because it is "more trusted."

If a precedence rule is eventually needed, that rule itself must be explicit, versioned, and evidence-backed.

---

## 697. Negative test: snapshot substitution
<!-- source: KSIR-ANALYZER.md §18 -->

This should be one of the first adversarial tests.

```text
Request:
    snapshot A
Execution:
    source tree B
```

Expected:

```text
SnapshotMismatch
```

No observation becomes canonical.

Likewise:

```text
Request:
    Variant A
Compiler execution:
    Variant B
```

must produce:

```text
VariantMismatch
```

---

## 698. First KSIR gate execution
<!-- source: KSIR-ANALYZER.md §19 -->

The actual flow should now be:

```text
             MU-000001
                      │
                      ▼
   protocol authorization
                      │
                      ▼
         BuildManifest
                      │
                      ▼
    compiler execution
                      │
                      ▼
         receipt R-001
                      │
                      ▼
     observations O-*
                      │
                      ▼
          reconciler
               /         \
      resolved       conflict
             │              │
             ▼              ▼
         KSIR        quarantine
             │
             ▼
  KSIR-GATE-001
             │
        ┌────┴────┐
        ▼         ▼
    PASS     BLOCKED
```

A **BLOCKED** result here is not a failed implementation.

It is the correct result when semantic evidence is insufficient.

---

## 699. Then connect it to Contract IR
<!-- source: KSIR-ANALYZER.md §20 -->

Only after the structural KSIR gate works should we compile the first contract.

For `lab_object`:

```text
KSIR
├── refcount observations
├── lock observations
├── callback observations
├── field accesses
└── lifetime unknown
          │
          ▼
  Contract
```

The contract should initially contain:

```text
C001: object must be initialized before publication
C002: value mutation requires the established lock
C003: reference acquisition must precede asynchronous use
C004: final reference release permits destruction
C005: callback must not access object after destruction
C006: callback execution context must satisfy its operations
```

And because C005 cannot yet be established:

```text
C005 = BLOCKED
```

That is exactly what we want.

---

## 700. The first meaningful RFL-AE theorem
<!-- source: KSIR-ANALYZER.md §21 -->

At this point we can state a much stronger property than the original architecture documents:

> **If a KSIR fact is admitted into the canonical semantic artifact, then its source snapshot, build variant, analyzer execution, provenance, and derivation path are mechanically recoverable.**

And separately:

> **If a required semantic property cannot be established, the absence is represented as UNKNOWN or CONFLICT rather than silently converted into a positive claim.**

Those two properties should become executable tests.

---

## 701. The next implementation sequence
<!-- source: KSIR-ANALYZER.md §22 -->

```text
NOW
 │
 ├── rfl-analysis-types
 │
 ├── compiler backend
 │
 ├── normalized observations
 │
 ├── structural reconciler
 │
 ├── KSIR serializer
 │
 └── KSIR-GATE-001
        │
        ▼
THEN
 │
 ├── context propagation
 ├── effect propagation
 ├── callback graph
 ├── refcount analysis
 ├── lifetime reconstruction
 └── lock/access analysis
        │
        ▼
THEN
 │
 ├── Contract IR generation
 ├── obligations
 └── first Rust Design IR
        │
        ▼
MU-000001
        │
        ▼
full evidence → verification → gate → certificate
```

The key change from the previous stage is that **we now have a concrete implementation boundary**. The next useful work is writing the actual crate contents and fixture implementation, then running the first deterministic KSIR test suite.

---

**Done — see [EXECUTABLE-KERNEL.md](EXECUTABLE-KERNEL.md)** (§702–§717, source *Current state* plus
§§1–§14 plus the unnumbered *Immediate implementation sequence*), which stops adding conceptual
layers and starts making the invariants executable: a `Current state` table that still records the
protocol as **PROVISIONAL** and the transition engine, evidence ledger and gate engine as **NOT
IMPLEMENTED**; the governing principle that **RFL-AE must be able to reject an invalid agent
action without asking an LLM whether the action is valid**; a `DOMAIN-TYPES.md` registry that
eliminates the `SnapshotId` / `KernelSnapshotId` ambiguity; the three-way gate algebra where
`Gate ≠ GateStatus ≠ GateResult`; a canonical `Epoch` with `REJECT` rather than `WARNING` on
mismatch; `rfl-types` as a deliberately boring crate with **domain types and invariants only**;
`rfl-transition` where agents **request** transitions and only the engine produces authoritative
state; a transition relation that is never `"probably okay"`, `"LLM believes valid"` or
`"majority of agents approved"`; the task state machine that makes `FAILED → VERIFIED` and
`EXECUTING → CERTIFIED` structurally impossible; seven adversarial negative tests; an event
ledger whose `previous_state + operation + resulting_state` makes replay divergence detectable;
evidence bound to objects rather than `"cargo test passed"`; the separation of
`TechnicalCertification` from `UpstreamAcceptanceState`; the Linux subsystem manifest; the
inverted agent hierarchy; a one-engine-first milestone with **0 autonomous mutation agents**;
eleven implementation phases; and a release gate that RFL-AE v0.1 cannot be called complete
without. Same provenance convention as `VERIFICATION.md`.
