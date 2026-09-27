# RFL-AE — Gate Engine + Migration Certificate Compiler

**Sections 387–418** — the policy/execution layer that decides release eligibility from
artifacts already produced.

> **Corpus numbering:** §§387–§418.
> **Original source numbering:** §§1–§32.
> **Mapping:** `corpus §N = source §(N−386)`.
> Source numbering is preserved for traceability — each section carries a
> `<!-- source: GATES.md §n -->` provenance comment on the line following its heading.
>
> Continues the numbering of [ARCHITECTURE.md](ARCHITECTURE.md) (§1–§51),
> [SPECIFICATION.md](SPECIFICATION.md) (§52–§80), [FORMAL-CORE.md](FORMAL-CORE.md)
> (§81–§107), [PROTOCOL.md](PROTOCOL.md) (§109–§135), [RUST-CORE.md](RUST-CORE.md)
> (§136–§172), [TRANSITIONS.md](TRANSITIONS.md) (§173–§203), [KSIR.md](KSIR.md)
> (§204–§250), [RECONSTRUCTION.md](RECONSTRUCTION.md) (§251–§291), [CONTRACTS.md](CONTRACTS.md)
> (§292–§320), [DESIGN-IR.md](DESIGN-IR.md) (§321–§356), and [VERIFICATION.md](VERIFICATION.md)
> (§357–§386). §108 does not exist in the source.
>
> **Note on derived material:** the collapsed ASCII figures are redrawn in `text` fences from
> computed column layouts; the source numbering map below is a derived table. No content was
> added beyond that.

## Contents

| Part | Sections | |
| --- | --- | --- |
| [I. The gate engine](#387-gate-engine-invariant) | 387–393 |
| [II. Gate families](#394-snapshot-gates) | 394–403 |
| [III. Evidence validity and policy](#404-evidence-validity) | 404–409 |
| [IV. The certificate compiler](#410-migration-certificate-compiler) | 410–415 |
| [V. The complete architecture](#416-complete-rfl-ae-architecture) | 416–418 |

### Source numbering map

| Source § | Corpus § | Section |
| --- | --- | --- |
| 1 | 387 | Gate Engine invariant |
| 2 | 388 | Gate model |
| 3 | 389 | Gate predicate algebra |
| 4 | 390 | Gate evaluation |
| 5 | 391 | Why BLOCKED matters |
| 6 | 392 | Gate dependency graph |
| 7 | 393 | Gate families |
| 8 | 394 | Snapshot gates |
| 9 | 395 | Scope gate |
| 10 | 396 | Contract gates |
| 11 | 397 | Design gates |
| 12 | 398 | Unsafe gate |
| 13 | 399 | ABI gate |
| 14 | 400 | Context gate |
| 15 | 401 | Lifetime gate |
| 16 | 402 | Concurrency gate |
| 17 | 403 | Verification gate |
| 18 | 404 | Evidence validity |
| 19 | 405 | Evidence freshness |
| 20 | 406 | Gate policy versioning |
| 21 | 407 | Release eligibility |
| 22 | 408 | Release gate |
| 23 | 409 | Unknown handling |
| 24 | 410 | Migration Certificate compiler |
| 25 | 411 | Certificate structure |
| 26 | 412 | Certificate is not proof of the whole kernel |
| 27 | 413 | Certificate invalidation |
| 28 | 414 | Release authority |
| 29 | 415 | Human review |
| 30 | 416 | Complete RFL-AE architecture |
| 31 | 417 | RFL-AE trust architecture |
| 32 | 418 | Next layer: Execution & Evidence Runtime |

---

The next layer should enforce a strict distinction:

```text
Verification Results
         ↓
Gate Evaluation
         ↓
Release Eligibility
         ↓
Migration Certificate
```

The **gate engine does not discover truth**. It evaluates whether the already-produced
artifacts satisfy predefined release conditions.

That makes it a policy/execution layer, not another reasoning agent.

---

## 387. Gate Engine invariant

<!-- source: GATES.md §1 -->

The fundamental rule:

```text
Evidence
   ↓
Verification Result
   ↓
Gate Predicate
   ↓
Gate Result
```

Never:

```text
LLM judgment
   ↓
Gate PASS
```

And never:

```text
test count
   ↓
confidence
   ↓
release
```

The gate engine should be deterministic.

Given identical:

```text
snapshot + artifacts + evidence + gate policy
```

it must produce the identical gate result.

---

## 388. Gate model

<!-- source: GATES.md §2 -->

```rust
struct Gate {
    gate_id: GateId,

    name: String,
    version: GateVersion,
    predicate: GatePredicate,

    required_artifacts: Vec<ArtifactType>,
    required_evidence: Vec<EvidenceRequirement>,

    severity: GateSeverity,

    applicability: ApplicabilityRule,
}
```

Gate severity:

```rust
enum GateSeverity {
    Advisory,
    Required,
    Blocking,
}
```

A blocking gate failure prevents release eligibility.

---

## 389. Gate predicate algebra

<!-- source: GATES.md §3 -->

Do not implement gates as arbitrary executable scripts alone.

Define a constrained predicate language.

```rust
enum GatePredicate {
    ArtifactExists(ArtifactSelector),

    EvidenceExists(EvidenceSelector),

    StatusEquals {
        subject: SubjectSelector,
        status: Status,
    },

    NoCriticalUnknowns,
    NoCriticalConflicts,
    AllObligationsSatisfied,

    RequiredDimensionsVerified(Vec<VerificationDimension>),
    RequiredVariantsCovered(Vec<BuildVariantId>),

    AbiContractsVerified,
    LifetimeContractsVerified,
    ConcurrencyContractsVerified,
    UnsafeObligationsResolved,
    DifferentialRequirementsSatisfied,
    RegressionRequirementsSatisfied,
    CounterexamplesResolved,

    ScopeMatches,
    SnapshotMatches,

    Composite {
        operator: GateOperator,
        predicates: Vec<GatePredicate>,
    },
}
```

Operators:

```text
AND
OR
NOT
ALL
ANY
```

But avoid arbitrary Boolean expressions becoming a hidden programming language.

The initial gate language should remain deliberately small.

---

## 390. Gate evaluation

<!-- source: GATES.md §4 -->

A gate evaluation is itself an evidence-bearing artifact.

```rust
struct GateEvaluation {
    evaluation_id: GateEvaluationId,

    gate: GateId,
    gate_version: GateVersion,
    subject: MigrationUnitId,

    inputs: Vec<ArtifactId>,

    predicate: GatePredicate,
    observed_facts: Vec<GateFact>,
    result: GateResult,

    evaluator: EvaluatorIdentity,
    execution_receipt: ExecutionReceipt,

    digest: Digest,
}
```

Result:

```rust
enum GateResult {
    Pass,
    Fail,
    Blocked,
    NotApplicable,
    Invalidated,
}
```

Important:

```text
FAIL != BLOCKED
```

For example:

```text
RCU verification failed
```

is different from:

```text
RCU verification could not execute because the required kernel configuration was unavailable.
```

---

## 391. Why BLOCKED matters

<!-- source: GATES.md §5 -->

Use the existing epistemic discipline.

Example:

```text
G-RCU-004
Result:
    BLOCKED
Reason:
    Required PREEMPT_RT runtime environment unavailable.

This means:
    no verification evidence exists.

It does NOT mean:
    the implementation failed.
```

That distinction prevents infrastructure failures from becoming false implementation defects.

---

## 392. Gate dependency graph

<!-- source: GATES.md §6 -->

Gates themselves can have dependencies.

```text
               Snapshot Gate
                     │
                     ▼
               Contract Gate
                     │
          ┌──────────┴───────────┐
          ▼                      ▼
     Design Gate             ABI Gate
          │                      │
          ▼                      │
 Implementation Gate             │
          │                      │
          ├───────────────┬──────┘
          ▼               ▼
    Runtime Gate  Differential Gate
          │               │
          └───────┬───────┘
                  ▼
          Adversarial Gate
                  │
                  ▼
            Release Gate
```

This prevents the release gate from independently trying to rediscover all prerequisites.

---

## 393. Gate families

<!-- source: GATES.md §7 -->

Initial gate set:

```text
G-SNAPSHOT
G-SCOPE
G-KSIR
G-CONTRACT
G-DESIGN
G-IMPLEMENTATION
G-ABI
G-CONTEXT
G-LIFETIME
G-CONCURRENCY
G-UNSAFE
G-BUILD
G-RUNTIME
G-DIFFERENTIAL
G-ADVERSARIAL
G-REGRESSION
G-EVIDENCE
G-RELEASE
```

Each family should contain narrowly scoped gates.

---

## 394. Snapshot gates

<!-- source: GATES.md §8 -->

### G-SNAPSHOT-001

```text
Migration snapshot exists.
```

### G-SNAPSHOT-002

```text
Source tree digest matches declared snapshot.
```

### G-SNAPSHOT-003

```text
Build variant is identified.
```

### G-SNAPSHOT-004

```text
Toolchain identity is recorded.
```

### G-SNAPSHOT-005

```text
Generated artifacts required by analysis are identified.
```

Failure example:

```text
Declared Linux commit:
    abc123
Observed source tree:
    def456
```

Result:

```text
BLOCKED
```

Not:

```text
"probably equivalent"
```

---

## 395. Scope gate

<!-- source: GATES.md §9 -->

This prevents accidental generalization.

```text
ScopeGate:
    contract.validity_domain
        ⊇
    verification.scope
```

Actually, for verification, the desired relationship is:

```text
Verification scope
    must cover required contract domain
```

So:

```text
required domain
    ⊆
verified domain
```

If:

```text
Contract:
    x86_64 + arm64
Verification:
    x86_64 only
```

then:

```text
G-SCOPE = FAIL/BLOCKED
```

depending on whether the missing variant was expected to be verified or unavailable.

---

## 396. Contract gates

<!-- source: GATES.md §10 -->

The previously defined gates become executable.

```text
G-CONTRACT-001     no critical unknowns
G-CONTRACT-002     no unresolved critical conflicts
G-CONTRACT-003     exported ABI contracts reconstructed
G-CONTRACT-004     async lifetime contracts reconstructed
G-CONTRACT-005     mutable shared-state protection reconstructed
G-CONTRACT-006     unsafe obligations enumerated
G-CONTRACT-007     configuration scope explicit
G-CONTRACT-008     architecture assumptions explicit
```

Notice that:

```text
unsafe obligations enumerated
```

is not the same as:

```text
unsafe obligations resolved
```

Resolution belongs to a later gate.

---

## 397. Design gates

<!-- source: GATES.md §11 -->

```text
G-DESIGN-001     every critical contract obligation has a mapping
G-DESIGN-002     every Rust unsafe operation has an obligation
G-DESIGN-003     FFI boundaries explicitly modeled
G-DESIGN-004     callback lifecycle modeled
G-DESIGN-005     initialization and teardown modeled
G-DESIGN-006     ABI mode declared
G-DESIGN-007     architecture-specific behavior represented
G-DESIGN-008     rejected alternatives recorded where ambiguity exists
```

A design can therefore be:

```text
VALID
```

without being:

```text
PROVEN CORRECT
```

Design validation precedes implementation.

---

## 398. Unsafe gate

<!-- source: GATES.md §12 -->

This should be unusually strict.

For every unsafe block:

```text
unsafe block
     │
     ▼
UnsafeObligation
     │
     ├── pointer validity
     ├── initialization
     ├── lifetime
     ├── aliasing
     ├── synchronization
     ├── ABI
     ├── architecture
     └── provenance
```

Gate:

```text
G-UNSAFE-001
```

requires:

```text
every unsafe operation
    → identified obligation
    → verification method
    → evidence
    → resolved status
```

No:

```rust
unsafe {
    // SAFETY: trust me
}
```

as sufficient evidence.

---

## 399. ABI gate

<!-- source: GATES.md §13 -->

ABI deserves independent release authority.

```text
G-ABI-001     symbol identity verified
G-ABI-002     calling convention verified
G-ABI-003     parameter representation verified
G-ABI-004     return representation verified
G-ABI-005     struct layout verified
G-ABI-006     alignment verified
G-ABI-007     field offsets verified
G-ABI-008     visibility/linkage verified
G-ABI-009     architecture ABI constraints verified
```

For internal Rust-only objects, the gate can be:

```text
NOT_APPLICABLE
```

rather than inventing an ABI requirement.

---

## 400. Context gate

<!-- source: GATES.md §14 -->

Kernel context must be explicit.

For each callable function:

```text
entry context
    ↓
reachable calls
    ↓
effects
    ↓
sleepability
    ↓
allocation
```

Gate:

```text
G-CONTEXT-001
```

must ensure:

```text
all reachable operations
    are permitted
    by caller context
```

Example:

```text
NMI
 ↓
Rust function
 ↓
allocation
 ↓
may sleep
```

would generate a blocking result if the allocation path can sleep.

---

## 401. Lifetime gate

<!-- source: GATES.md §15 -->

For each object:

```text
ALLOCATE
    ↓
INITIALIZE
    ↓
PUBLISH
    ↓
USE
    ↓
UNPUBLISH
    ↓
QUIESCE
    ↓
RECLAIM
    ↓
FREE
```

The gate checks that all transitions required by the contract are represented.

Particularly:

```text
async callback + object lifetime
```

must establish:

```text
callback cannot execute after object becomes invalid
```

or prove an equivalent lifetime relationship.

---

## 402. Concurrency gate

<!-- source: GATES.md §16 -->

The concurrency gate should operate on the semantic model rather than test names.

For every mutable shared object:

```text
object
  │
  ├── access A
  ├── access B
  ├── access C
  │
  └── synchronization relation
```

Required evidence can include:

```text
static lock analysis
atomic ordering analysis
runtime race detection
schedule exploration
differential behavior
adversarial mutation
```

The exact combination is contract-dependent.

---

## 403. Verification gate

<!-- source: GATES.md §17 -->

The verification gate evaluates obligation coverage.

For each obligation:

```text
┌───────────────────────────────┐
│ VO-123                        │
├───────────────────────────────┤
│ Proposition                   │
│ Scope                         │
│ Oracle                        │
│ Evidence                      │
│ Result                        │
│ Limitations                   │
└───────────────────────────────┘
```

The gate asks:

```text
Is the required evidence present?
Is it valid?
Was it executed?
Does its scope cover the proposition?
Did the oracle establish the proposition?
Are there unresolved counterexamples?
```

Only then:

```text
VERIFIED
```

---

## 404. Evidence validity

<!-- source: GATES.md §18 -->

An evidence item needs a validity predicate.

```rust
struct EvidenceValidity {
    snapshot_matches: bool,
    variant_matches: bool,

    artifact_digest_matches: bool,
    execution_receipt_valid: bool,

    producer_authorized: bool,
    tool_identity_known: bool,

    scope_satisfied: bool,

    dependencies_valid: bool,

    superseded: bool,
}
```

One invalid dependency should propagate.

```text
Observation
    ↓ invalidated
DerivedFact
    ↓ invalidated
Contract evidence
    ↓ invalidated
Gate
    ↓
INVALIDATED
```

This is the artifact equivalent of dependency invalidation.

---

## 405. Evidence freshness

<!-- source: GATES.md §19 -->

Evidence should be immutable but not timeless.

```text
Evidence:
    valid_for snapshot S
```

If:

```text
S → S'
```

and the relevant contract changes:

```text
Evidence(S)
```

cannot automatically support:

```text
Claim(S')
```

Instead:

```text
SUPERSEDED
```

or:

```text
REQUIRES_REVALIDATION
```

This prevents stale green results.

---

## 406. Gate policy versioning

<!-- source: GATES.md §20 -->

The gate itself is versioned.

```text
G-CONCURRENCY-004@1
```

might require:

```text
static analysis + runtime race detection
```

A later version:

```text
G-CONCURRENCY-004@2
```

might additionally require:

```text
schedule exploration
```

Old certificates remain historically valid under their recorded gate policy.

They do not silently acquire the newer requirements.

---

## 407. Release eligibility

<!-- source: GATES.md §21 -->

Release eligibility is a derived state.

```rust
enum ReleaseEligibility {
    Eligible,
    Ineligible,
    Blocked,
    Invalidated,
}
```

The compiler evaluates:

```text
required gates
+ scope
+ artifact validity
+ authority
```

No human-readable prose such as:

```text
"looks ready"
```

is part of the authoritative result.

---

## 408. Release gate

<!-- source: GATES.md §22 -->

A minimal release predicate:

```text
RELEASE_ELIGIBLE iff

    snapshot_valid
AND scope_valid
AND contract_gate_pass
AND design_gate_pass
AND implementation_gate_pass
AND required_verification_gates_pass
AND unsafe_gate_pass
AND ABI_gate_pass
AND regression_gate_pass
AND adversarial_gate_pass
AND evidence_gate_pass
AND no_blocking_unknowns
AND no_unresolved_critical_conflicts
AND no_invalidated_dependencies
```

Importantly:

```text
non-critical UNKNOWN
```

does not necessarily block release.

But it must be listed.

---

## 409. Unknown handling

<!-- source: GATES.md §23 -->

The certificate should contain:

```text
Resolved
Partially verified
Open
Blocked
Not observable
Not reachable
Not present
Not applicable
```

Example:

```text
Unknowns
─────────────────────────────────────────────
U-004  arch-specific asm       OPEN
U-009  optional CONFIG path    NOT_REACHABLE
U-013  external driver ABI     NOT_OBSERVABLE
```

The system does not turn:

```text
UNKNOWN
```

into:

```text
probably safe
```

---

## 410. Migration Certificate compiler

<!-- source: GATES.md §24 -->

The compiler consumes:

```text
KernelSnapshot
BuildVariants
KSIR
Contract
RustDesign
Implementation
VerificationPlan
VerificationResults
GateEvaluations
Evidence
```

and emits:

```text
MigrationCertificate
```

Pipeline:

```text
Artifacts
    ↓
Dependency Validation
    ↓
Scope Validation
    ↓
Evidence Validation
    ↓
Gate Evaluation
    ↓
Conflict/Unknown Aggregation
    ↓
Certificate Compilation
    ↓
Certificate Digest
```

---

## 411. Certificate structure

<!-- source: GATES.md §25 -->

A certificate should be machine-readable first.

```rust
struct MigrationCertificate {
    certificate_id: CertificateId,
    schema_version: SchemaVersion,

    snapshot: KernelSnapshotId,
    variants: Vec<BuildVariantId>,

    migration_unit: MigrationUnitId,

    source_scope: SourceScope,

    ksir: ArtifactRef,
    contract: ArtifactRef,
    design: ArtifactRef,
    implementation: ArtifactRef,

    verification_plan: ArtifactRef,
    verification_results: Vec<ArtifactRef>,

    gate_evaluations: Vec<GateEvaluationRef>,

    unknowns: Vec<UnknownRef>,
    conflicts: Vec<ConflictRef>,
    counterexamples: Vec<CounterexampleRef>,

    evidence_root: EvidenceDigest,

    eligibility: ReleaseEligibility,

    limitations: Vec<Limitation>,

    compiler: CertificateCompilerIdentity,

    digest: Digest,
}
```

---

## 412. Certificate is not proof of the whole kernel

<!-- source: GATES.md §26 -->

This distinction must be encoded into the schema.

```text
Migration Certificate

Subject:
    MU-004821
Snapshot:
    Linux S
Scope:
    drivers/example/foo.c
Variants:
    x86_64/config-A
Status:
    RELEASE_ELIGIBLE
```

It does **not** mean:

```text
Linux kernel verified.
```

It means:

```text
this migration unit was verified to the declared scope under the declared
snapshot/variants against the declared contract using the declared evidence.
```

---

## 413. Certificate invalidation

<!-- source: GATES.md §27 -->

A certificate becomes invalid when its semantic dependencies become invalid.

Examples:

```text
Contract changed
    → certificate invalidated

Snapshot changed
    → certificate superseded

ABI changed
    → ABI evidence invalidated

Verification tool algorithm changed
    → affected evidence may require re-execution

Build configuration changed
    → variant-specific evidence no longer covers new variant
```

Dependency graph:

```text
Snapshot
   ├── KSIR
   │   │
   │   └── Contract
   │       │
   │       └── Design
   │           │
   │           └── Implementation
   │               │
   │               └── Verification
   │                   │
   │                   └── Gates
   │                       │
                           ▼
                           Certificate
```

Any upstream semantic invalidation propagates downstream.

---

## 414. Release authority

<!-- source: GATES.md §28 -->

Keep release authority independent.

```text
DISCOVERY
         ↓
DESIGN
         ↓
IMPLEMENTATION
         ↓
VERIFICATION
         ↓
REVIEW
         ↓
RELEASE
```

Recommended authority rule:

```text
Implementation Agent     MAY implement
Verification Agent       MAY verify
Release Authority        MAY release
```

And:

```text
Implementation Agent
    MUST NOT
authorize its own implementation for release
```

---

## 415. Human review

<!-- source: GATES.md §29 -->

The system should not eliminate human review.

Instead, it should make review tractable.

The reviewer receives:

```text
Migration Certificate
├── contract summary
├── unresolved unknowns
├── conflicts
├── unsafe obligations
├── ABI boundaries
├── concurrency assumptions
├── adversarial findings
├── differential mismatches
└── evidence graph
```

Rather than asking a human to inspect thousands of generated agent messages.

The human's role becomes:

```text
review bounded claims
+ inspect exceptions
+ authorize release
```

rather than:

```text
trust AI
```

---

## 416. Complete RFL-AE architecture

<!-- source: GATES.md §30 -->

We now have a complete compiler-like chain:

```text
                 LINUX SNAPSHOT
                        │
                        ▼
             Semantic Reconstruction
                        │
                        ▼
                      KSIR
                 "WHAT EXISTS?"
                        │
                        ▼
                   CONTRACT IR
               "WHAT MUST REMAIN?"
                        │
                        ▼
                 RUST DESIGN IR
               "HOW MAY IT WORK?"
                        │
                        ▼
                    RUST CODE
                        │
                        ▼
                 VERIFICATION IR
                "HOW DO WE KNOW?"
                        │
                        ▼
                 EXECUTION LAYER
                        │
                        ▼
                 EVIDENCE STORE
                        │
                        ▼
                   GATE ENGINE
                "DO REQUIREMENTS
                     HOLD?"
                        │
                        ▼
              CERTIFICATE COMPILER
                        │
                        ▼
              MIGRATION CERTIFICATE
                        │
                        ▼
                RELEASE AUTHORITY
```

And the epistemic boundary is clean:

```text
LLM
 │
 ├── hypotheses
 ├── semantic interpretations
 ├── design candidates
 ├── test candidates
 └── adversarial ideas
        │
        ▼
deterministic machinery
 │
 ├── state transitions
 ├── scope
 ├── hashes
 ├── evidence binding
 ├── gate predicates
 ├── authorization
 └── certificate generation
```

The LLM can propose.

It cannot manufacture the authoritative state.

---

## 417. RFL-AE trust architecture

<!-- source: GATES.md §31 -->

This gives us four increasingly trusted layers:

```text
┌─────────────────────────────────────────┐
│ UNTRUSTED REASONING                     │
│ LLM / agent hypotheses / generated code │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│ OBSERVATIONAL EVIDENCE                  │
│ compiler / runtime / CI / binary / Git  │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│ DETERMINISTIC RECONSTRUCTION            │
│ KSIR / Contract / Verification / Gates  │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│ AUTHORITY                               │
│ authorization / release / immutable log │
└─────────────────────────────────────────┘
```

This is the point where **RFL-AE stops being merely an agent framework and becomes a governed
engineering system**.

---

## 418. Next layer: Execution & Evidence Runtime

<!-- source: GATES.md §32 -->

There is one remaining architectural layer before implementation can be considered complete:

**the Execution & Evidence Runtime.**

It should answer:

> ### **How does an authorized verification or analysis action actually execute, and how do we guarantee that the resulting evidence corresponds to exactly what was executed?**

That layer needs to formalize:

```text
Agent
   ↓
Capability Request
   ↓
Authorization Check
   ↓
Sandbox / Worktree
   ↓
Command Execution
   ↓
Artifact Capture
   ↓
Execution Receipt
   ↓
Digest
   ↓
Evidence Record
   ↓
Immutable Evidence Ledger
```

That is where we should go next, because otherwise the entire `NO EVIDENCE → NO VERIFIED CLAIM`
architecture still has an unformalized trust boundary between **“the system says it ran”** and
**“we can prove exactly what ran.”**
