# RFL-AE — `rfl-gates`: Gates, the Certification Predicate and the Implementation Boundary

> **Provenance and numbering.** This document was supplied untitled (the heading above is derived from its content — rename freely), numbered **§90–§120** in the source plus a final unnumbered *The architecture has now reached the implementation boundary* section: the author continued the numbering of [RFL-EVIDENCE.md](RFL-EVIDENCE.md) (§62–§89), which continued [RFL-LEDGER.md](RFL-LEDGER.md), [RFL-TRANSITION.md](RFL-TRANSITION.md) and [RFL-TYPES.md](RFL-TYPES.md). To keep the corpus contiguous, its sections are renumbered **§894–§925**, continuing directly from `RFL-EVIDENCE.md` (which ends at §893). The mapping is the plain **`corpus_section = source_section + 804`** — the same offset as the three previous `RFL-*` documents — with the unnumbered closing section recorded as source **§121**, the convention already used by `PROOF-CARRYING.md`, `EXECUTABLE-KERNEL.md` and the `KSIR-*` documents. (§121 is synthetic: if a later paste numbers its first section §121, that paste's offset becomes +805.) The source's own §108 (*No "ready" boolean*) is corpus §912; it is unrelated to the corpus's known §108 gap. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: RFL-GATES.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/rfl-gates/` tree, no gate evaluator, requirement algebra, invalidation engine or certificate has been written or compiled, and the vertical slice of §921–§923 has not been started. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** The pasted source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/RFL-GATES.py`](diagrams/RFL-GATES.py); re-running it reproduces all 62 diagrams. Box-drawing art stays box-drawing; no block mixes an ASCII `|` with box glyphs. Two diagrams were normalised geometrically, with no content change: in the §909 gate graph the vertical lines sat about one column left of the labels hung on them, so they moved one column right and every label is centred on its line (the fork and merge keep the source's lengths); in the §920 protocol kernel, `HUMAN`, `RFL-TYPES` and `RFL-TRANSITION` were one or two columns off the line every other label sits on, and are now centred on it, as are the two leaf labels. Several runs of words arrived with single spaces only and were broken into lines by meaning — rejoin any that were meant as one line: §900 `Build unknown` / `KUnit unknown` / `therefore maybe pass`; §907 `B` / `C`; §908 `G1 passed` / `then` / `G1 became invalidated`; §916 the five record IDs; §922 `RCU-heavy core` / `scheduler` / `VFS internals` / `MM` / `architecture-specific assembly` (this could also read `RCU-heavy` / `core scheduler`); and §924, one conjunct per line, which the source's spacing supports because `AND ` is four columns wide, exactly the indent of the first conjunct. The §905 LaTeX is fenced as `math`. Rust types and the Rust-syntax fragments — `Any(BuildPassed, KUnitPassed)` in §900, `GateStatus::Pass` in §903 and the `pub ready: bool` field in §912 — are fenced as `rust`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`). As with `RFL-LEDGER.md`, this paste did not end with a "save it as markdown" instruction; it was saved on the same basis as the previous ones.

The next layer is **`rfl-gates`**. This is where RFL-AE turns independently established facts into a controlled release decision without collapsing uncertainty into a boolean.

---

## Contents

- [894. `rfl-gates`](#894-rfl-gates)
- [895. A gate is not a test](#895-a-gate-is-not-a-test)
- [896. Gate structure](#896-gate-structure)
- [897. Gate result](#897-gate-result)
- [898. Gate status semantics](#898-gate-status-semantics)
- [899. Gate requirement](#899-gate-requirement)
- [900. Composite requirements](#900-composite-requirements)
- [901. Three-valued evaluation is not enough](#901-three-valued-evaluation-is-not-enough)
- [902. Requirement evaluation](#902-requirement-evaluation)
- [903. Why the evaluator cannot be probabilistic](#903-why-the-evaluator-cannot-be-probabilistic)
- [904. Required versus optional gates](#904-required-versus-optional-gates)
- [905. Certification predicate](#905-certification-predicate)
- [906. Certification is monotonic with respect to failure](#906-certification-is-monotonic-with-respect-to-failure)
- [907. Dependency invalidation](#907-dependency-invalidation)
- [908. Invalidated is different from failed](#908-invalidated-is-different-from-failed)
- [909. Gate dependency graph](#909-gate-dependency-graph)
- [910. Gate evaluation order](#910-gate-evaluation-order)
- [911. Gate explanation](#911-gate-explanation)
- [912. No "ready" boolean](#912-no-ready-boolean)
- [913. Technical certification](#913-technical-certification)
- [914. Upstream acceptance remains independent](#914-upstream-acceptance-remains-independent)
- [915. Certification certificate](#915-certification-certificate)
- [916. Certificate invalidation](#916-certificate-invalidation)
- [917. Dependency closure](#917-dependency-closure)
- [918. Critical invariant](#918-critical-invariant)
- [919. Semantic conflicts now connect directly](#919-semantic-conflicts-now-connect-directly)
- [920. This gives us the full protocol kernel](#920-this-gives-us-the-full-protocol-kernel)
- [921. The next layer is not another protocol layer](#921-the-next-layer-is-not-another-protocol-layer)
- [922. First vertical-slice candidate](#922-first-vertical-slice-candidate)
- [923. Vertical-slice repository shape](#923-vertical-slice-repository-shape)
- [924. The critical release invariant](#924-the-critical-release-invariant)
- [925. The architecture has now reached the implementation boundary](#925-the-architecture-has-now-reached-the-implementation-boundary)

---

## 894. `rfl-gates`
<!-- source: RFL-GATES.md §90 -->

```text
crates/rfl-gates/
├── Cargo.toml
└── src/
    ├── lib.rs
    ├── gate.rs
    ├── predicate.rs
    ├── evaluation.rs
    ├── dependency.rs
    ├── certification.rs
    ├── invalidation.rs
    └── tests/
        ├── gate_status.rs
        ├── predicates.rs
        ├── dependencies.rs
        ├── certification.rs
        └── adversarial.rs
```

Dependency direction:

```text
rfl-types
    ↓
rfl-transition
    ↓
rfl-ledger
    ↓
rfl-evidence
    ↓
rfl-gates
```

`rfl-gates` must consume facts from the previous layers. It must not create them.

## 895. A gate is not a test
<!-- source: RFL-GATES.md §91 -->

This distinction is fundamental.

A test produces evidence:

```text
KUnit
   ↓
EvidenceRecord
```

A gate evaluates whether the evidence satisfies a release condition:

```text
EvidenceRecord
   + Contract
   + Policy
   ↓
GateResult
```

Therefore:

```text
Test ≠ Gate
```

A gate may require several tests.

A test may support several gates.

## 896. Gate structure
<!-- source: RFL-GATES.md §92 -->

Start with:

```rust
pub struct Gate {
    pub id: GateId,
    pub epoch: Epoch,

    pub subject: SubjectId,

    pub kind: GateKind,

    pub requirement: GateRequirement,

    pub dependencies: Vec<GateId>,
}
```

Where:

```rust
pub enum GateKind {
    Scope,
    SourceIdentity,
    SemanticContract,
    EvidenceCompleteness,
    Verification,
    Dependency,
    Provenance,
    Build,
    Test,
    Abi,
    Differential,
    Concurrency,
    HumanReview,
}
```

This gives us explicit semantics rather than a collection of ad-hoc checks.

## 897. Gate result
<!-- source: RFL-GATES.md §93 -->

Keep status separate from the gate definition.

```rust
pub struct GateResult {
    pub gate: GateId,
    pub epoch: Epoch,
    pub status: GateStatus,
    pub evidence: Vec<EvidenceId>,
    pub evaluated_at: Timestamp,
}
```

So:

```text
Gate
    = requirement

GateResult
    = evaluation of requirement
```

This avoids overwriting the rule with its current result.

## 898. Gate status semantics
<!-- source: RFL-GATES.md §94 -->

```text
PASS
    predicate evaluated true

FAIL
    predicate evaluated false

BLOCKED
    predicate cannot validly be evaluated

NOT_APPLICABLE
    requirement is outside declared scope

INVALIDATED
    prior result no longer applies
```

The distinction between `FAIL` and `BLOCKED` remains mandatory.

Example:

```text
KUnit ran and failed
    → FAIL

KUnit required but infrastructure unavailable
    → BLOCKED
```

Those are different engineering facts.

## 899. Gate requirement
<!-- source: RFL-GATES.md §95 -->

A gate needs a declarative predicate.

Do not encode arbitrary executable closures as the canonical protocol representation.

Use a typed algebra:

```rust
pub enum GateRequirement {
    ArtifactExists,
    ArtifactMatchesSource,
    ScopeSatisfied,

    ContractsVerified,
    RequiredEvidencePresent,

    DependenciesValid,
    NoCriticalConflicts,

    BuildPassed,
    TestsPassed,
    AbiSatisfied,
    DifferentialSatisfied,
    ConcurrencySatisfied,

    IndependentReviewComplete,
}
```

Later this can become richer, but the initial language should remain closed and auditable.

## 900. Composite requirements
<!-- source: RFL-GATES.md §96 -->

Gates will need composition.

```rust
pub enum RequirementExpr {
    Atom(GateRequirement),

    All(Vec<RequirementExpr>),

    Any(Vec<RequirementExpr>),

    Not(Box<RequirementExpr>),

    Conditional {
        condition: Box<RequirementExpr>,
        when_true: Box<RequirementExpr>,
        when_false: Box<RequirementExpr>,
    },
}
```

But there is an important restriction:

`Any` must not silently turn missing evidence into success.

For example:

```rust
Any(
    BuildPassed,
    KUnitPassed
)
```

means either genuinely established condition may satisfy the requirement.

It must **not** mean:

```text
Build unknown
KUnit unknown
therefore maybe pass
```

Unknown remains unknown.

## 901. Three-valued evaluation is not enough
<!-- source: RFL-GATES.md §97 -->

Ordinary boolean logic gives:

```text
true / false
```

Three-valued logic adds:

```text
true / false / unknown
```

RFL-AE needs something closer to:

```text
PASS
FAIL
BLOCKED
NOT_APPLICABLE
INVALIDATED
```

because these states have different operational meanings.

For example:

```text
FAIL
```

means we learned something negative.

Whereas:

```text
BLOCKED
```

means we did not acquire the necessary evidence.

## 902. Requirement evaluation
<!-- source: RFL-GATES.md §98 -->

Conceptually:

```rust
pub fn evaluate(
    requirement: &RequirementExpr,
    context: &GateContext,
) -> GateStatus
```

The evaluator must be deterministic.

Its inputs should include:

```rust
pub struct GateContext {
    pub epoch: Epoch,
    pub artifact: ArtifactId,

    pub contracts: ContractState,
    pub evidence: EvidenceIndex,
    pub verification: VerificationIndex,

    pub dependencies: DependencyState,
    pub policy: GatePolicy,
}
```

No LLM judgment belongs here.

## 903. Why the evaluator cannot be probabilistic
<!-- source: RFL-GATES.md §99 -->

Suppose an agent says:

```text
"I think the remaining tests are low risk."
```

That cannot become:

```rust
GateStatus::Pass
```

The gate evaluator needs an explicit fact.

This creates the trust boundary:

```text
Agent:
    proposes interpretation

Gate evaluator:
    evaluates declared predicate
```

## 904. Required versus optional gates
<!-- source: RFL-GATES.md §100 -->

A gate policy should distinguish:

```rust
pub enum GateRequirementLevel {
    Required,
    Optional,
    Conditional,
}
```

Why?

Because:

```text
Optional gate = FAIL
```

need not necessarily block certification.

But:

```text
Required gate = FAIL
```

must block certification.

Likewise:

```text
Required gate = BLOCKED
```

must also block certification.

## 905. Certification predicate
<!-- source: RFL-GATES.md §101 -->

Now define the central predicate:

```math
RELEASE\_ELIGIBLE(A,E)
```

Conceptually:

```text
RELEASE_ELIGIBLE(A, E)
    :=
        EpochValid
    ∧   ScopeValid
    ∧   SourceIdentityValid
    ∧   ArtifactValid
    ∧   ContractsSatisfied
    ∧   RequiredEvidenceComplete
    ∧   RequiredVerificationSatisfied
    ∧   RequiredGatesPass
    ∧   DependenciesValid
    ∧   NoCriticalConflict
    ∧   ReplayValid
    ∧   ProvenanceValid
```

This is not a score.

It is a conjunction of necessary conditions.

## 906. Certification is monotonic with respect to failure
<!-- source: RFL-GATES.md §102 -->

If:

```text
RequiredGate = Fail
```

then certification cannot become true by adding unrelated evidence.

Likewise:

```text
RequiredGate = Blocked
```

cannot become true because an agent "believes" the missing evidence would probably pass.

This produces an important monotonicity rule:

```text
insufficient evidence
    → not certified
```

until sufficient evidence actually arrives.

## 907. Dependency invalidation
<!-- source: RFL-GATES.md §103 -->

Suppose:

```text
MigrationUnit A
    ↓
MigrationUnit B
    ↓
MigrationUnit C
```

and A becomes invalidated.

Then:

```text
B
C
```

may have stale certification.

Therefore gate evaluation needs dependency propagation.

```rust
pub enum DependencyState {
    Valid,
    Invalidated,
    Missing,
    Conflicting,
    Unknown,
}
```

A required dependency that is invalidated must prevent certification.

## 908. Invalidated is different from failed
<!-- source: RFL-GATES.md §104 -->

Consider:

```text
Gate G1:
    PASS

later:

Evidence E:
    INVALIDATED

therefore:

G1:
    INVALIDATED
```

We should not change history and claim:

```text
G1 never passed
```

The correct historical record is:

```text
G1 passed
then
G1 became invalidated
```

This is essential for auditability.

## 909. Gate dependency graph
<!-- source: RFL-GATES.md §105 -->

Gates can depend on other gates:

```text
SourceIdentity
       │
       ├──────────┐
       ▼          ▼
   Artifact   Contracts
       │          │
       └────┬─────┘
            ▼
      Verification
            │
            ▼
    EvidenceComplete
            │
            ▼
       ReleaseGate
```

This is a DAG, not an arbitrary recursive structure.

Therefore:

```text
cycle detection
```

must be mandatory.

A gate graph containing:

```text
G1 → G2 → G3 → G1
```

must be rejected.

## 910. Gate evaluation order
<!-- source: RFL-GATES.md §106 -->

The evaluator should topologically order dependencies:

```text
dependency gates
      ↓
source/artifact gates
      ↓
contract gates
      ↓
verification gates
      ↓
release gates
```

This gives deterministic evaluation.

It also makes failures explainable.

Instead of:

```text
Release = FAIL
```

we can produce:

```text
Release
  └── Verification
        └── Contract C17
              └── DifferentialEvidence
                    └── BLOCKED
```

## 911. Gate explanation
<!-- source: RFL-GATES.md §107 -->

A gate result should retain structured reasons.

```rust
pub struct GateExplanation {
    pub gate: GateId,
    pub status: GateStatus,
    pub failed_requirements: Vec<RequirementId>,
    pub blocked_requirements: Vec<RequirementId>,
    pub invalidated_dependencies: Vec<GateId>,
}
```

This is not merely UI information.

It is part of audit evidence.

## 912. No "ready" boolean
<!-- source: RFL-GATES.md §108 -->

Do not create:

```rust
pub ready: bool
```

as the authoritative certification state.

That field would inevitably become detached from the facts producing it.

Instead:

```text
CertificationState
    = derived from
    gate results
    + verification
    + dependencies
    + epoch
    + evidence
```

If somebody asks:

> Is this migration ready?

the system should be able to answer:

```text
CERTIFICATION BLOCKED

Required:
  SourceIdentity       PASS
  ContractVerification PASS
  Build                PASS
  KUnit                PASS
  ABI                  BLOCKED
  Differential         PASS
  DependencyIntegrity  PASS
```

rather than:

```text
ready = false
```

## 913. Technical certification
<!-- source: RFL-GATES.md §109 -->

Keep:

```rust
pub enum TechnicalCertification {
    Unverified,
    Verified,
    Invalidated,
}
```

But the transition:

```text
Unverified → Verified
```

requires the release predicate to hold.

And:

```text
Verified → Invalidated
```

must be possible when a supporting fact becomes invalid.

## 914. Upstream acceptance remains independent
<!-- source: RFL-GATES.md §110 -->

The final object should therefore contain two states:

```rust
pub enum UpstreamAcceptanceState {
    NotSubmitted,
    UnderReview,
    Reviewed,
    Accepted,
    Rejected,
    Superseded,
}
```

So:

```text
TechnicalCertification = Verified
UpstreamAcceptance    = UnderReview
```

is completely valid.

Likewise:

```text
TechnicalCertification = Verified
UpstreamAcceptance    = Rejected
```

does not imply that the technical certificate was false.

They represent different authorities and different questions.

## 915. Certification certificate
<!-- source: RFL-GATES.md §111 -->

The certificate should be a derived, content-addressed object:

```rust
pub struct Certificate {
    pub id: CertificateId,
    pub epoch: Epoch,

    pub subject: ArtifactId,

    pub certification: TechnicalCertification,

    pub required_gates: Vec<GateResult>,
    pub verification_results: Vec<VerificationResult>,
    pub evidence: Vec<EvidenceId>,

    pub dependency_digest: Digest,

    pub certificate_digest: Digest,
}
```

The certificate is **not** the source of truth.

The underlying records are.

Therefore:

```text
Certificate
    ↓
derived view over
    ↓
ledger + evidence + verification + gates
```

## 916. Certificate invalidation
<!-- source: RFL-GATES.md §112 -->

Suppose certificate `C42` was derived from:

```text
E17
E19
E22
G4
G7
```

If E19 becomes invalid:

```text
E19
 ↓
invalidate dependent verification
 ↓
invalidate dependent gate
 ↓
invalidate C42
```

The system should propagate invalidation.

It should not require manually editing every downstream object.

## 917. Dependency closure
<!-- source: RFL-GATES.md §113 -->

This leads to a formal dependency graph:

```text
Certificate
    ↓
Gate
    ↓
Verification
    ↓
Evidence
    ↓
Execution
    ↓
Artifact
    ↓
Source
```

If any required node becomes invalid:

```text
dependent derived claims
        ↓
potentially invalid
```

The invalidation engine should traverse this graph.

## 918. Critical invariant
<!-- source: RFL-GATES.md §114 -->

A certified artifact must never depend on an unresolved critical fact.

Define:

```text
CriticalDependencyState
    ∈ {
    Resolved,
    Invalidated,
    Unknown,
    Conflicting
}
```

Then:

```text
Unknown
    → no certification

Conflicting
    → no certification

Invalidated
    → no certification
```

Only:

```text
Resolved
```

can satisfy the dependency condition.

## 919. Semantic conflicts now connect directly
<!-- source: RFL-GATES.md §115 -->

Recall:

```text
SemanticConflict
    Ownership
    Lifetime
    Locking
    RCU
    ControlFlow
    ABI
    Configuration
    Architecture
    ...
```

A critical unresolved conflict becomes:

```text
NoCriticalConflicts = FAIL/BLOCKED
```

depending on whether the conflict itself establishes a violation or merely prevents determination.

For example:

```text
Two analyses disagree about lock protection
```

should normally produce:

```text
BLOCKED
```

until evidence resolves the disagreement.

Whereas:

```text
Formal verification proves the generated code violates lock invariant
```

produces:

```text
FAIL
```

## 920. This gives us the full protocol kernel
<!-- source: RFL-GATES.md §116 -->

```text
                 HUMAN
                   │
                   ▼
             AUTHORIZATION
                   │
                   ▼
               RFL-TYPES
                   │
                   ▼
            RFL-TRANSITION
                   │
                   ▼
              RFL-LEDGER
                   │
                   ▼
             RFL-EVIDENCE
                   │
                   ▼
             VERIFICATION
                   │
                   ▼
               RFL-GATES
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
   TECHNICAL CERT.   UPSTREAM STATE
```

At this point the core authority path is sufficiently defined to begin integration with the semantic migration system.

## 921. The next layer is not another protocol layer
<!-- source: RFL-GATES.md §117 -->

This is the point where we should **stop adding abstractions**.

The next step should be the first vertical slice:

```text
ONE C SUBSYSTEM
      ↓
ONE MigrationUnit
      ↓
SOURCE IDENTITY
      ↓
KSIR
      ↓
3–10 CONTRACTS
      ↓
RUST DESIGN IR
      ↓
RUST ARTIFACT
      ↓
BUILD
      ↓
TEST
      ↓
EVIDENCE
      ↓
VERIFICATION
      ↓
GATES
      ↓
CERTIFICATE
```

The purpose is not to migrate a large Linux subsystem yet.

The purpose is to prove that **the entire chain can carry one small migration without a trust-boundary bypass**.

## 922. First vertical-slice candidate
<!-- source: RFL-GATES.md §118 -->

Use a deliberately bounded subsystem/function family with:

- ordinary C control flow
- explicit ownership
- at least one error path
- at least one cleanup path
- at least one synchronization rule
- a manageable test surface

Do **not** begin with:

```text
RCU-heavy core
scheduler
VFS internals
MM
architecture-specific assembly
```

Those should come later.

The first slice should exercise the protocol, not maximize Linux complexity.

## 923. Vertical-slice repository shape
<!-- source: RFL-GATES.md §119 -->

```text
crates/
├── rfl-types/
├── rfl-transition/
├── rfl-ledger/
├── rfl-evidence/
├── rfl-gates/
└── rfl-ksir/

migration/
└── example/
    ├── source/
    ├── observations/
    ├── ksir/
    ├── contracts/
    ├── design/
    ├── rust/
    ├── verification/
    ├── evidence/
    ├── gates/
    └── certificate/
```

This is where the conceptual architecture becomes testable against real artifacts.

## 924. The critical release invariant
<!-- source: RFL-GATES.md §120 -->

The entire system should ultimately reduce to this:

```text
CERTIFIED(A,E)
    ⇒

    source_identity_valid
AND epoch_valid
AND migration_closure_known
AND critical_semantics_resolved
AND contracts_defined
AND contracts_verified
AND artifact_bound
AND required_evidence_complete
AND required_gates_pass
AND dependencies_valid
AND replay_valid
AND provenance_valid
```

And importantly:

```text
CERTIFIED(A,E)
    ⇏ upstream_accepted
```

That final distinction prevents RFL-AE from quietly turning its own internal certification into an assertion of Linux community authority.

## 925. The architecture has now reached the implementation boundary
<!-- source: RFL-GATES.md §121 -->

The conceptual sequence is complete enough:

```text
RFL-TYPES
    ↓
RFL-TRANSITION
    ↓
RFL-LEDGER
    ↓
RFL-EVIDENCE
    ↓
RFL-GATES
    ↓
MIGRATION UNIT
    ↓
KSIR
    ↓
CONTRACTS
    ↓
RUST DESIGN IR
    ↓
RUST
```

The next work should therefore be **implementation and conformance**, not another 50-section conceptual layer.

The immediate target is a frozen **`rfl-types v0.1` API + `rfl-transition v0.1` transition table + `rfl-ledger v0.1` replay model + `rfl-evidence v0.1` binding rules + `rfl-gates v0.1` certification predicate**, followed by the first end-to-end MigrationUnit and adversarial test suite.

---

**Done — see [RFL-TYPES-V01.md](RFL-TYPES-V01.md)** (§926–§946, source §§1–§20 plus the unnumbered
closing section — the author restarted the numbering at §1, so the offset is +925), which acts on
this document's conclusion and freezes the **first executable API contract**, beginning with
`rfl-types v0.1`: a deliberately boring crate of domain vocabulary and invariants; one newtype per
protocol identity; a canonical `sha256:` digest; a four-part epoch with all-or-nothing equality;
`KernelSnapshotId` replacing `SnapshotId`; a closed operation algebra and structured scope;
authorization with revocation state instead of a `valid` flag; closed request targets; retries as
attempts rather than backward moves; separate status axes; a stable rejection taxonomy; canonical
serialization (RFC 8785 JCS) kept apart from semantics; the `rfl-types` invariant tests; property
P1; the `rfl-transition v0.1` engine, precondition order and eight-row transition table; attacks
A01–A18; a first synthetic conformance scenario; and the implementation freeze point. Same
provenance convention as `VERIFICATION.md`.
