# RFL-AE — Verification IR v0.1

**Sections 357–386** — verification treated as a compilation problem, not as "generate tests →
run tests → green".

> **Corpus numbering:** §§357–§386.
> **Original source numbering:** §§1–§30.
> **Mapping:** `corpus §N = source §(N−356)`.
> Source numbering is preserved for traceability — each section carries a
> `<!-- source: VERIFICATION.md §n -->` provenance comment on the line following its heading.
>
> Continues the numbering of [ARCHITECTURE.md](ARCHITECTURE.md) (§1–§51),
> [SPECIFICATION.md](SPECIFICATION.md) (§52–§80), [FORMAL-CORE.md](FORMAL-CORE.md)
> (§81–§107), [PROTOCOL.md](PROTOCOL.md) (§109–§135), [RUST-CORE.md](RUST-CORE.md)
> (§136–§172), [TRANSITIONS.md](TRANSITIONS.md) (§173–§203), [KSIR.md](KSIR.md)
> (§204–§250), [RECONSTRUCTION.md](RECONSTRUCTION.md) (§251–§291), [CONTRACTS.md](CONTRACTS.md)
> (§292–§320), and [DESIGN-IR.md](DESIGN-IR.md) (§321–§356). §108 does not exist in the source.
>
> **Note on derived material:** the collapsed ASCII figures are redrawn in `text` fences from
> computed column layouts; the source numbering map below is a derived table. No content was
> added beyond that.

## Contents

| Part | Sections | |
| --- | --- | --- |
| [I. The verification model](#357-verification-ir-purpose) | 357–362 |
| [II. Oracles and differential verification](#363-oracle-model) | 363–366 |
| [III. Scope, matrices, static and dynamic](#367-verification-scope) | 367–372 |
| [IV. Concurrency, counterexamples, adequacy](#373-concurrency-verification) | 373–378 |
| [V. Authority, compiler, certificate](#379-verification-authority-separation) | 379–386 |

### Source numbering map

| Source § | Corpus § | Section |
| --- | --- | --- |
| 1 | 357 | Verification IR purpose |
| 2 | 358 | Verification IR root |
| 3 | 359 | Verification obligation |
| 4 | 360 | Verification categories |
| 5 | 361 | Verification proposition |
| 6 | 362 | Claim ≠ test ≠ evidence |
| 7 | 363 | Oracle model |
| 8 | 364 | Oracle independence |
| 9 | 365 | Differential verification |
| 10 | 366 | Normalization |
| 11 | 367 | Verification scope |
| 12 | 368 | Configuration matrix |
| 13 | 369 | Architecture matrix |
| 14 | 370 | Static verification |
| 15 | 371 | Dynamic verification |
| 16 | 372 | CI authority |
| 17 | 373 | Concurrency verification |
| 18 | 374 | Counterexamples |
| 19 | 375 | Counterexample shrinking |
| 20 | 376 | Mutation verification |
| 21 | 377 | Verification adequacy |
| 22 | 378 | Verification state machine |
| 23 | 379 | Verification authority separation |
| 24 | 380 | Adversarial verifier |
| 25 | 381 | Verification compiler |
| 26 | 382 | Crate architecture |
| 27 | 383 | Verification certificate |
| 28 | 384 | Complete evidence chain |
| 29 | 385 | The critical invariant |
| 30 | 386 | Updated RFL-AE compiler |

---

The key move is to stop treating verification as:

```text
"generate tests → run tests → green"
```

and instead model it as a compilation problem:

```text
            Kernel Contract
                   │
                   ▼
       Verification Obligations
                   │
                   ▼
            Verification IR
                   │
                   ├── Static Proof
                   ├── Compile / Build
                   ├── Unit
                   ├── Integration
                   ├── Runtime
                   ├── Concurrency
                   ├── Memory
                   ├── ABI
                   ├── Differential
                   ├── Adversarial
                   └── Regression
                   │
                   ▼
              Executions
                   │
                   ▼
             Observations
                   │
                   ▼
                Oracles
                   │
                   ▼
         Verification Results
                   │
                   ▼
            Evidence Bundle
                   │
                   ▼
         Migration Certificate
```

The important distinction is:

> ### **A test execution is evidence. It is not automatically a verification claim.**

---

## 357. Verification IR purpose

<!-- source: VERIFICATION.md §1 -->

Verification IR answers:

> ### **What exact proposition are we trying to establish, under what conditions, using what evidence and oracle?**

It should be possible to inspect a verification artifact without reading the generated test
code and determine:

- what is being claimed;
- which contract obligation it addresses;
- which invariant is under test;
- what assumptions are required;
- what execution environment is required;
- what constitutes success;
- what constitutes failure;
- what evidence is produced;
- what the test does **not** establish.

That last point is important.

A test that demonstrates:

```text
put(obj)
```

does not establish:

```text
all possible paths to put(obj) are correct
```

unless its coverage and proof scope actually justify that claim.

---

## 358. Verification IR root

<!-- source: VERIFICATION.md §2 -->

A first schema:

```rust
struct VerificationPlan {
    verification_id: VerificationId,

    snapshot: KernelSnapshotId,
    variant: BuildVariantId,
    migration_unit: MigrationUnitId,

    contract: ContractId,
    design: DesignId,
    implementation: ImplementationId,

    obligations: Vec<VerificationObligation>,

    assumptions: Vec<VerificationAssumption>,
    generators: Vec<InputGenerator>,
    oracles: Vec<Oracle>,
    observation_points: Vec<ObservationPoint>,

    executions: Vec<VerificationExecution>,

    coverage: VerificationCoverage,
    counterexamples: Vec<CounterexampleId>,

    evidence: EvidenceSet,

    status: VerificationStatus,
}
```

The plan is declarative.

It says what must be verified.

It does **not** itself constitute execution evidence.

---

## 359. Verification obligation

<!-- source: VERIFICATION.md §3 -->

The central unit:

```rust
struct VerificationObligation {
    obligation_id: ObligationId,

    source_contract: ContractId,
    invariant: Option<InvariantId>,

    category: VerificationCategory,
    proposition: Proposition,
    preconditions: Vec<Condition>,
    required_evidence: EvidenceRequirement,
    oracle: OracleId,
    scope: VerificationScope,

    status: ObligationStatus,
}
```

Example:

```text
VO-004821-LOCK-003

Contract:
    C-004821
Invariant:
    INV-LOCK-007

Proposition:
    Mutable access to object X occurs only while lock L is held.

Category:
    CONCURRENCY

Preconditions:
    X is initialized
    X is published
    execution reaches access path A

Oracle:
    ORACLE-LOCK-PROTECTION-001

Required evidence:
    static access analysis
    lock-path analysis
    runtime race instrumentation

Status:
    PARTIALLY_VERIFIED
```

Notice that the proposition is more precise than:

```text
"lock test passes"
```

---

## 360. Verification categories

<!-- source: VERIFICATION.md §4 -->

Use a closed taxonomy initially.

```rust
enum VerificationCategory {
    StaticProof,
    Compile,
    Build,
    Unit,
    Integration,
    Runtime,
    Concurrency,
    MemorySafety,
    ABI,
    Differential,
    Architecture,
    Configuration,
    Security,
    Adversarial,
    Regression,
}
```

These are **verification mechanisms**, not confidence levels.

A concurrency property might require:

```text
StaticProof + Concurrency + Differential + Adversarial
```

rather than choosing one category.

---

## 361. Verification proposition

<!-- source: VERIFICATION.md §5 -->

Do not encode propositions as arbitrary strings alone.

Start with a structured proposition algebra.

```rust
enum Proposition {
    Equal(ValueExpr, ValueExpr),

    Equivalent {
        lhs: ValueExpr,
        rhs: ValueExpr,
        normalization: NormalizationId,
    },

    InvariantHolds(InvariantId),

    StateTransition {
        from: StateExpr,
        operation: OperationExpr,
        to: StateExpr,
    },

    Temporal {
        relation: TemporalRelation,
        lhs: EventExpr,
        rhs: EventExpr,
    },

    ResourceLifecycle {
        resource: ResourceExpr,
        lifecycle: LifecycleProperty,
    },

    AbiCompatible(AbiContractId),
    LayoutCompatible(LayoutContractId),

    NoForbiddenEffect {
        operation: OperationExpr,
        effect: Effect,
    },

    Reachability {
        source: NodeId,
        target: NodeId,
    },

    Unreachable {
        source: NodeId,
        target: NodeId,
    },

    Safety(SafetyProperty),

    Custom {
        predicate: PredicateId,
    },
}
```

This gives the verification engine something it can reason about.

---

## 362. Claim ≠ test ≠ evidence

<!-- source: VERIFICATION.md §6 -->

This separation should be explicit.

```text
CLAIM
  │
  │ says something is true
  ▼
OBLIGATION
  │
  │ specifies what must be established
  ▼
VERIFICATION METHOD
  │
  │ describes how to investigate it
  ▼
EXECUTION
  │
  │ actually runs something
  ▼
OBSERVATION
  │
  │ records what happened
  ▼
ORACLE
  │
  │ interprets observation
  ▼
RESULT
  │
  │ establishes limited proposition
  ▼
EVIDENCE
```

Therefore:

```text
test_exists != test_executed
test_executed != test_passed
test_passed != claim_verified
```

A valid verification claim requires the complete chain.

---

## 363. Oracle model

<!-- source: VERIFICATION.md §7 -->

The oracle is one of the most important pieces.

```rust
enum OracleKind {
    ExactValue,
    Relational,
    Invariant,
    StateTransition,
    Temporal,
    ResourceLifecycle,
    AbiLayout,
    ErrorBehavior,
    NoForbiddenEffect,
    ConcurrencyProperty,
    SecurityProperty,
    Differential,
    CrashFreedom,
}
```

Examples:

### Exact

```text
Rust result == expected errno
```

### Relational

```text
Rust observable state == C observable state
```

### Invariant

```text
refcount never reaches invalid state
```

### Temporal

```text
remove(obj)
    BEFORE
free(obj)
```

### Grace-period

```text
RCU callback executes
    AFTER required grace period
```

### Resource lifecycle

```text
alloc → init → publish → use → unpublish → reclaim
```

### Forbidden effect

```text
NMI function MUST NOT sleep
```

### ABI

```text
sizeof(struct X)
alignment
field offsets
calling convention
symbol visibility
```

---

## 364. Oracle independence

<!-- source: VERIFICATION.md §8 -->

A dangerous design would be:

```text
C implementation
      ↓
expected result
      ↓
Rust
```

because this silently makes C authoritative.

Instead:

```text
           ┌─────────────────┐
           │ Kernel Contract │
           └────────┬────────┘
                    │
           independent oracle
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
    C execution         Rust execution
         │                     │
         └──────────┬──────────┘
                    ▼
               comparison
```

The C implementation can be a **reference implementation for characterized behavior**, but it
is not automatically the specification.

This distinction matters especially when migrating a pre-existing bug.

If:

```text
C behavior = incorrect
Rust behavior = contract-correct
```

then naïve differential testing would falsely report a Rust failure.

Therefore every differential relation needs a provenance classification:

```rust
enum ReferenceAuthority {
    ContractDerived,
    IndependentOracle,
    CharacterizedCBehavior,
    HistoricalBehavior,
    ExternalSpecification,
    RuntimeObservation,
}
```

---

## 365. Differential verification

<!-- source: VERIFICATION.md §9 -->

Differential verification should operate on **observable semantics**, not byte-for-byte
implementation similarity.

```text
C
 │
 ├── raw execution
 │
 ▼
C Observation
 │
 │ normalization
 ▼
Normalized C State
                ┌──────────┐
                │ Relation │
                │ Oracle   │
                └─────┬────┘
Normalized Rust State ▲
 ▲
 │ normalization
 │
Rust Observation
 ▲
 │
Rust execution
```

For example:

```text
C pointer address != Rust pointer address
```

does not imply failure.

But:

```text
object lifetime
error return
state transition
lock discipline
ABI layout
observable output
```

may need equivalence.

---

## 366. Normalization

<!-- source: VERIFICATION.md §10 -->

Differential testing requires explicit normalization.

```rust
struct NormalizationRule {
    normalization_id: NormalizationId,

    input_domain: ObservationDomain,
    output_domain: ObservationDomain,

    transformations: Vec<NormalizationOperation>,

    justified_by: Vec<ContractId>,
    evidence: EvidenceSet,
}
```

Examples:

```text
IGNORE:
    heap addresses

NORMALIZE:
    timestamps

CANONICALIZE:
    unordered collections

PRESERVE:
    errno

PRESERVE:
    externally visible ordering

COMPARE:
    resource lifecycle

COMPARE:
    synchronization-visible state
```

No implicit normalization.

---

## 367. Verification scope

<!-- source: VERIFICATION.md §11 -->

Every result needs scope.

```rust
struct VerificationScope {
    snapshot: KernelSnapshotId,
    variants: Vec<BuildVariantId>,

    architectures: Vec<ArchitectureId>,

    configs: Vec<ConfigConstraint>,

    entry_points: Vec<SymbolId>,

    paths: Vec<PathId>,

    inputs: InputDomain,

    temporal_scope: TemporalScope,
}
```

Therefore:

```text
VERIFIED
```

really means:

```text
VERIFIED for
    snapshot S
    variant V
    architecture A
    configuration domain C
    scope X
    using evidence E
```

Not:

```text
verified everywhere
```

---

## 368. Configuration matrix

<!-- source: VERIFICATION.md §12 -->

Linux makes this particularly important.

A contract may only be valid under:

```text
CONFIG_X=y
ARCH=x86_64
PREEMPT=y
```

while another path exists under:

```text
CONFIG_X=n
ARCH=arm64
PREEMPT_RT=y
```

So:

```rust
struct VerificationVariant {
    variant: BuildVariantId,
    obligations: Vec<ObligationId>,
    executions: Vec<ExecutionId>,
}
```

The verifier should detect:

```text
contract validity domain
        ≠
verification domain
```

and produce:

```text
INSUFFICIENT_SCOPE
```

rather than silently generalizing.

---

## 369. Architecture matrix

<!-- source: VERIFICATION.md §13 -->

Architecture-dependent contracts become first-class.

```text
                    x86_64     arm64      arm      riscv
──────────────────────────────────────────────────────────
ABI                    ✓         ✓         ✓         ✓
atomic ordering        ✓         ✓         ?         ✓
alignment              ✓         ✓         ?         ?
MMIO                   ✓         ✓         ✓         ✓
inline asm             ?         ?         ?         ?
interrupt model        ✓         ✓         ?         ?
page assumptions       ✓         ✓         ?         ?
```

Those symbols are not scores.

They are statuses:

```text
VERIFIED
PARTIALLY_VERIFIED
OPEN
NOT_APPLICABLE
BLOCKED
```

---

## 370. Static verification

<!-- source: VERIFICATION.md §14 -->

Static verification can establish properties without executing the system.

Examples:

```text
all accesses to field X have lock L
function F has no sleeping path
all FFI pointers satisfy required nullability contract
all RCU dereferences occur inside required read-side protection
```

But static analysis must report its limitations.

```rust
struct StaticProof {
    proof_id: ProofId,

    proposition: Proposition,

    analysis_algorithm: AlgorithmId,

    assumptions: Vec<Assumption>,

    covered_domain: AnalysisDomain,
    uncovered_domain: AnalysisDomain,

    counterexamples: Vec<CounterexampleId>,

    evidence: EvidenceSet,
}
```

If the analyzer cannot resolve:

```text
container_of()
```

it must not quietly convert that uncertainty into proof.

---

## 371. Dynamic verification

<!-- source: VERIFICATION.md §15 -->

Dynamic verification produces observations.

```rust
struct VerificationExecution {
    execution_id: ExecutionId,

    plan: VerificationId,
    obligation: ObligationId,

    environment: ExecutionEnvironment,
    command: CommandSpec,
    input: InputArtifact,

    observations: Vec<ObservationId>,

    oracle: OracleId,
    result: OracleResult,

    receipt: ExecutionReceipt,
    evidence: EvidenceSet,
}
```

Execution receipt should capture at minimum:

```text
snapshot
variant
source revision
binary digest
test artifact digest
toolchain
tool versions
command
environment
exit status
stdout/stderr digests
runtime duration
timestamp
executor identity
CI run identity
```

---

## 372. CI authority

<!-- source: VERIFICATION.md §16 -->

Keep the existing rule:

> ### **CI is execution authority. Local inspection is evidence for diagnosis, not evidence of execution.**

Thus:

```text
Developer says:
    "cargo test passed"
```

is not sufficient.

The system needs:

```text
CI execution receipt
    +
artifact digest
    +
test identity
    +
variant
    +
result
```

Then:

```text
OBSERVED
```

can become evidence.

---

## 373. Concurrency verification

<!-- source: VERIFICATION.md §17 -->

Concurrency deserves its own IR.

```rust
struct ConcurrencyVerification {
    shared_objects: Vec<ObjectId>,
    accesses: Vec<AccessId>,
    synchronization: Vec<SyncEventId>,

    schedules: Vec<ScheduleConstraint>,
    race_properties: Vec<RaceProperty>,

    memory_ordering: Vec<AtomicOrderingRequirement>,

    evidence: EvidenceSet,
}
```

Test generation should deliberately produce schedules such as:

```text
T1                         T2
 acquire ref
                           remove object
                           drop ownership
                           schedule reclaim
 use object
                           reclaim
```

The verifier should search for violations of:

```text
use-before-reclaim
```

rather than merely run the operation once.

---

## 374. Counterexamples

<!-- source: VERIFICATION.md §18 -->

A failed verification should produce a reusable artifact.

```rust
struct Counterexample {
    counterexample_id: CounterexampleId,

    obligation: ObligationId,
    proposition: Proposition,

    input: InputArtifact,
    schedule: Option<ScheduleArtifact>,

    trace: ExecutionTrace,
    first_failure: ObservationId,

    minimized_input: Option<InputArtifact>,
    minimized_trace: Option<ExecutionTrace>,

    classification: CounterexampleClass,

    evidence: EvidenceSet,
}
```

Classification:

```rust
enum CounterexampleClass {
    ImplementationDefect,
    ContractDefect,
    OracleDefect,
    TestHarnessDefect,
    EnvironmentMismatch,
    UnsupportedBehavior,
    Unknown,
}
```

This is critical.

A failed test does **not** necessarily mean the Rust implementation is wrong.

It could expose:

```text
bad contract
bad oracle
bad harness
wrong build variant
```

---

## 375. Counterexample shrinking

<!-- source: VERIFICATION.md §19 -->

For concurrency especially:

```text
1000-event failing trace
        ↓
remove irrelevant events
        ↓
500
        ↓
100
        ↓
20
        ↓
minimal reproducer
```

The minimized counterexample becomes a permanent regression fixture.

```text
COUNTEREXAMPLE
      ↓
SHRINK
      ↓
REPRODUCER
      ↓
REGRESSION TEST
```

This gives the system a learning loop without allowing the LLM to rewrite the historical
truth.

---

## 376. Mutation verification

<!-- source: VERIFICATION.md §20 -->

The verification compiler should deliberately introduce known violations.

For example:

```text
remove lock acquisition
remove refcount increment
change Acquire → Relaxed
free before RCU grace period
change nullable pointer → unchecked dereference
alter errno
change struct layout
remove cancellation barrier
```

Then ask:

```text
Does the verification suite detect the defect?
```

This tests the verifier itself.

---

## 377. Verification adequacy

<!-- source: VERIFICATION.md §21 -->

Instead of:

```text
95% tests passed
```

use obligation coverage.

```rust
struct VerificationCoverage {
    obligations_total: usize,
    obligations_verified: usize,
    obligations_partial: usize,
    obligations_blocked: usize,
    obligations_open: usize,

    dimensions: DimensionCoverage,
    variants: VariantCoverage,

    uncovered_contract_surface: Vec<ContractRegion>,
}
```

No aggregate score is necessary.

Example:

```text
Contract surface
Ownership           VERIFIED
Lifetime            VERIFIED
Locking             VERIFIED
RCU                 PARTIALLY_VERIFIED
Context             VERIFIED
ABI                 VERIFIED
Architecture        OPEN
Error behavior      VERIFIED
DMA                 NOT_APPLICABLE
```

That is much more informative than:

```text
Verification: 87%
```

---

## 378. Verification state machine

<!-- source: VERIFICATION.md §22 -->

```text
PLANNED
   │
   ▼
INPUT_VALIDATED
   │
   ▼
OBLIGATIONS_COMPILED
   │
   ▼
VERIFICATION_GENERATED
   │
   ▼
AUTHORIZED_FOR_EXECUTION
   │
   ▼
EXECUTING
   │
   ├────────────────────┐
   ▼                    ▼
OBSERVED        EXECUTION_FAILED
   │                    │
   ▼                    ▼
ORACLE_EVALUATED   INVESTIGATE
   │
   ├── PASS
   ├── FAIL
   ├── INCONCLUSIVE
   └── OUT_OF_SCOPE
   │
   ▼
EVIDENCE_BOUND
   │
   ▼
RECONCILED
   │
   ├── VERIFIED
   ├── PARTIALLY_VERIFIED
   ├── BLOCKED
   └── QUARANTINED
```

---

## 379. Verification authority separation

<!-- source: VERIFICATION.md §23 -->

The same authority separation applies here.

```text
               ┌────────────────────┐
               │ Contract Authority │
               └──────────┬─────────┘
                          │
                          ▼
                Verification Compiler
                          │
                          ▼
                  Verification Plan
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
   Implementation                     Verifier
        Agent                           Agent
          │                               │
          ▼                               ▼
        Rust                          Evidence
          │                               │
          └───────────────┬───────────────┘
                          ▼
                  Independent Gate
```

The implementation agent cannot:

```text
implement → test → declare VERIFIED
```

by itself.

---

## 380. Adversarial verifier

<!-- source: VERIFICATION.md §24 -->

The adversarial agent gets a different objective:

```text
Find a counterexample to the claimed preservation.
```

Not:

```text
confirm that implementation looks correct.
```

Its input:

```text
KernelContract
RustDesign
Implementation
VerificationPlan
ExistingEvidence
```

Its output:

```text
Counterexample
MissingObligation
OracleWeakness
ScopeGap
UnsupportedAssumption
ContractContradiction
```

A successful adversarial search is itself evidence, but failure to find a counterexample is
**not** proof of absence unless the search domain is formally bounded.

---

## 381. Verification compiler

<!-- source: VERIFICATION.md §25 -->

Now the overall compiler pipeline becomes:

```text
                   ┌──────────┐
                   │ Kernel C │
                   └─────┬────┘
                         ▼
                       KSIR
                   "what exists"
                         │
                         ▼
                    Contract IR
                "what must remain"
                         │
                         ▼
                  Rust Design IR
                 "how to realize"
                         │
                         ▼
                       Rust
                         │
                         ▼
                  Verification IR
                "how to establish"
                         │
                         ▼
            ┌────────────┼─────────────┐
            ▼            ▼             ▼
         Static       Dynamic    Differential
            │            │             │
            └────────────┼─────────────┘
                         │
                         ▼
                     Evidence
                         │
                         ▼
               Migration Certificate
```

This gives each transformation a single semantic responsibility.

---

## 382. Crate architecture

<!-- source: VERIFICATION.md §26 -->

I would split the next layer as:

```text
crates/
├── rfl-verification-types/
│   ├── obligation.rs
│   ├── proposition.rs
│   ├── oracle.rs
│   ├── scope.rs
│   ├── execution.rs
│   ├── counterexample.rs
│   └── status.rs
├── rfl-verification-plan/
│   ├── compile.rs
│   ├── obligations.rs
│   ├── dependencies.rs
│   └── coverage.rs
├── rfl-oracle/
│   ├── exact.rs
│   ├── relational.rs
│   ├── invariant.rs
│   ├── temporal.rs
│   ├── lifecycle.rs
│   ├── abi.rs
│   └── differential.rs
├── rfl-testgen/
│   ├── unit.rs
│   ├── integration.rs
│   ├── property.rs
│   ├── mutation.rs
│   └── regression.rs
├── rfl-differential/
│   ├── execute.rs
│   ├── normalize.rs
│   ├── compare.rs
│   └── counterexample.rs
├── rfl-concurrency/
│   ├── schedule.rs
│   ├── race.rs
│   ├── ordering.rs
│   └── stress.rs
├── rfl-adversarial/
│   ├── obligations.rs
│   ├── mutation.rs
│   ├── counterexample.rs
│   └── scope_attack.rs
├── rfl-verification-evidence/
│   ├── receipt.rs
│   ├── observation.rs
│   ├── binding.rs
│   └── digest.rs
└── rfl-certificate/
    ├── compile.rs
    ├── gates.rs
    └── certificate.rs
```

---

## 383. Verification certificate

<!-- source: VERIFICATION.md §27 -->

The certificate is the final artifact, but it must be **descriptive**, not a magic seal.

```rust
struct MigrationCertificate {
    certificate_id: CertificateId,

    snapshot: KernelSnapshotId,
    variants: Vec<BuildVariantId>,

    migration_unit: MigrationUnitId,

    contract: ContractId,
    design: DesignId,
    implementation: ImplementationId,

    obligations: Vec<ObligationResult>,
    evidence: EvidenceSet,

    unresolved_unknowns: Vec<UnknownId>,
    unresolved_conflicts: Vec<ConflictId>,

    gate_results: Vec<GateResult>,

    scope: VerificationScope,

    status: CertificateStatus,
}
```

Possible status:

```text
VERIFIED
PARTIALLY_VERIFIED
BLOCKED
QUARANTINED
INVALIDATED
SUPERSEDED
```

The certificate must never merely say:

```text
PASS
```

It must answer:

```text
What was verified?
Against which contract?
For which snapshot?
For which variants?
Using which evidence?
With which limitations?
Which obligations remain unresolved?
```

---

## 384. Complete evidence chain

<!-- source: VERIFICATION.md §28 -->

We now have the full traceability path:

```text
Rust source line
       │
       ▼
Rust Design element
       │
       ▼
Unsafe obligation
       │
       ▼
Contract obligation
       │
       ▼
Invariant
       │
       ▼
KSIR semantic fact
       │
       ▼
Observation
       │
       ▼
Source/build evidence
       │
       ▼
Verification obligation
       │
       ▼
Execution
       │
       ▼
Observation
       │
       ▼
Oracle result
       │
       ▼
Evidence record
       │
       ▼
Gate
       │
       ▼
Migration Certificate
```

That is the architecture we want.

It turns:

```text
"the AI says this Rust code is safe"
```

into a machine-auditable chain of propositions and evidence.

---

## 385. The critical invariant

<!-- source: VERIFICATION.md §29 -->

The central rule now becomes stronger:

```text
NO EVIDENCE
    ↓
NO VERIFIED CLAIM
```

with a second rule:

```text
EVIDENCE
    ≠
PROOF OF EVERYTHING
```

And therefore:

```text
VERIFIED(scope S)
```

must never silently become:

```text
VERIFIED(all Linux)
```

---

## 386. Updated RFL-AE compiler

<!-- source: VERIFICATION.md §30 -->

The architecture is now:

```text
                  Linux Snapshot
                         │
                         ▼
              Semantic Reconstruction
                         │
                         ▼
                       KSIR
                  ┌──────┴──────┐
                  │             │
              Evidence      Unknowns
                  │             │
                  └──────┬──────┘
                         │
                         ▼
                    Contract IR
                         │
                         ▼
                  Rust Design IR
                         │
                         ▼
                  Implementation
                         │
                         ▼
                  Verification IR
                         │
                         ▼
           ┌─────────────┼──────────────┐
           ▼             ▼              ▼
        Static        Dynamic     Differential
           │             │              │
           └─────────────┼──────────────┘
                         │
                         ▼
                  Adversarial QA
                         │
                         ▼
                  Evidence Store
                         │
                         ▼
                    Gate Engine
                         │
                         ▼
               Migration Certificate
                         │
                         ▼
                     RELEASED
```

At this point the system has crossed an important architectural boundary:

> ### **KSIR reconstructs semantics. Contract IR defines preservation obligations. Rust Design IR proposes an implementation. Verification IR defines how preservation is established.**

The next layer should therefore be **the Gate Engine + Migration Certificate compiler**,
because that is where all four IRs become an enforceable release decision rather than merely a
collection of artifacts.
