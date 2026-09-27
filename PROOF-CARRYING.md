# RFL-AE — From Semantic Reconstruction to a Proof-Carrying Migration

> **Provenance and numbering.** This document was supplied as *RFL-AE — From Semantic Reconstruction to a Proof-Carrying Migration*, numbered §1–§28 in the source plus a final unnumbered *The next boundary* section. To keep the corpus contiguous, its sections are renumbered **§775–§803**, continuing directly from [SEMANTIC-LAYER.md](SEMANTIC-LAYER.md) (which ends at §774). The mapping is **`corpus_section = source_section + 774`**, with the unnumbered closing section recorded as source §29 — the convention already used by `PROTOCOL-KERNEL.md`, `FIRST-MIGRATION.md`, `KSIR-IMPL.md`, `KSIR-SLICE.md`, `KSIR-ANALYZER.md`, `EXECUTABLE-KERNEL.md` and `SEMANTIC-LAYER.md`. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: PROOF-CARRYING.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `MigrationUnit`, contract graph, `RustGenerator`, `GenerationRecord`, certificate type, benchmark, `rfl-*` crate, or conformance test has been written or compiled. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** The pasted source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/PROOF-CARRYING.py`](diagrams/PROOF-CARRYING.py); re-running it reproduces all 87 diagrams. Diagrams that arrive as box-drawing art stay box-drawing (the `foo()` call tree, the trust boundary, the certificate chain and the final architecture); those that arrive as ASCII art — `|`, `v`, `+--`, `\`, `/` — stay ASCII, and `↓` chains stay `↓`. No block mixes an ASCII `|` with box glyphs. Two source rows were normalised by one column each: in §796 the `scope enforcement` row was one column wider than the rest of its box, and in §802 the `Epoch ─ Authorization ─ …` row was one column narrower than its box; in §802 the upper and lower spines, which drifted between columns 27 and 31 in the source, now both sit on the box's `┬` at column 27. The §791 coverage matrix arrived as a markdown table inside a code span and is rendered as a real table. Rust types, the two struct-literal examples in §781 and the `unsafe fn ...` in §784 are fenced as `rust`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The next step is to close the loop between **semantic reconstruction** and **actual C→Rust migration**.

The central idea is:

> A migrated Rust artifact should carry enough structured information to answer not only “does it compile?” but “which C semantics does it claim to preserve, what evidence supports those semantics, and which obligations remain unresolved?”

That leads to a proof-carrying migration object.

---

## Contents

- [775. Introduce `MigrationUnit`](#775-introduce-migrationunit)
- [776. Why function-by-function translation is insufficient](#776-why-function-by-function-translation-is-insufficient)
- [777. Dependency closure](#777-dependency-closure)
- [778. Dependency states](#778-dependency-states)
- [779. Contract graph](#779-contract-graph)
- [780. Contract identity](#780-contract-identity)
- [781. Never identify semantics by prose](#781-never-identify-semantics-by-prose)
- [782. Rust Design must map contracts explicitly](#782-rust-design-must-map-contracts-explicitly)
- [783. Design decisions require justification](#783-design-decisions-require-justification)
- [784. Unsafe design decisions](#784-unsafe-design-decisions)
- [785. Generator contract](#785-generator-contract)
- [786. Generation provenance](#786-generation-provenance)
- [787. Human modification is a new artifact transition](#787-human-modification-is-a-new-artifact-transition)
- [788. Differential verification](#788-differential-verification)
- [789. Differential testing is not universal proof](#789-differential-testing-is-not-universal-proof)
- [790. Verification strength](#790-verification-strength)
- [791. Coverage matrix](#791-coverage-matrix)
- [792. Semantic coverage ≠ code coverage](#792-semantic-coverage--code-coverage)
- [793. Migration readiness](#793-migration-readiness)
- [794. Implementation authorization](#794-implementation-authorization)
- [795. Scope + capability + epoch](#795-scope--capability--epoch)
- [796. The protocol kernel now has a real trust boundary](#796-the-protocol-kernel-now-has-a-real-trust-boundary)
- [797. The actual AI architecture](#797-the-actual-ai-architecture)
- [798. Agent disagreement protocol](#798-agent-disagreement-protocol)
- [799. The first real benchmark](#799-the-first-real-benchmark)
- [800. The most important metric](#800-the-most-important-metric)
- [801. End-to-end certificate chain](#801-end-to-end-certificate-chain)
- [802. Final architecture](#802-final-architecture)
- [803. The next boundary](#803-the-next-boundary)

---

## 775. Introduce `MigrationUnit`
<!-- source: PROOF-CARRYING.md §1 -->

A subsystem is too large to be the unit of verification.

A function is often too small.

The practical unit should be:

```text
MigrationUnit
```

For example:

```text
scheduler/
    migration-unit:
        sched_entity_lifecycle
```

or:

```text
net/
    migration-unit:
        napi_poll_path
```

A unit may contain:

```text
1..N C functions
1..N C types
1..N macros
1..N data structures
required call-graph neighborhood
required synchronization context
```

Define:

```rust
pub struct MigrationUnit {
    pub id: MigrationUnitId,
    pub epoch: Epoch,

    pub source: SourceSet,
    pub ksir: SemanticModelId,

    pub contracts: Vec<ContractId>,
    pub design: RustDesignId,

    pub artifact: Option<ArtifactId>,
}
```

This becomes the fundamental object moving through RFL-AE.

## 776. Why function-by-function translation is insufficient
<!-- source: PROOF-CARRYING.md §2 -->

Consider:

```text
foo()
 ├── bar()
 │    └── alloc()
 ├── schedule_work()
 └── put_ref()
```

The semantics of `foo()` may depend on:

```text
bar()
allocation context
worker lifetime
reference counting
```

Therefore:

```text
foo()
```

cannot necessarily be certified independently.

Instead:

```text
MigrationUnit
    |
    +-- foo()
    +-- bar()
    +-- object lifetime
    +-- worker
    +-- reference contract
```

The unit boundary must be **semantic**, not merely syntactic.

## 777. Dependency closure
<!-- source: PROOF-CARRYING.md §3 -->

Define:

```text
Closure(U)
```

as the set of artifacts necessary to establish the contracts of migration unit `U`.

Conceptually:

```text
              U
              |
      +-------+-------+
      |       |       |
      v       v       v
    type   caller  callback
              |       |
              v       v
            lock   worker
              \       /
               \     /
                v   v
              lifetime
```

Then:

```text
Complete(U)
```

cannot mean:

```text
all files in U were translated
```

It means:

```text
all required semantic dependencies have been accounted for.
```

## 778. Dependency states
<!-- source: PROOF-CARRYING.md §4 -->

Every dependency should have an explicit state:

```rust
pub enum DependencyState {
    Resolved,
    PartiallyResolved,
    External,
    Deferred,
    Unknown,
    Conflicting,
}
```

This prevents the dangerous behavior:

```text
unexamined dependency
        ↓
implicitly assumed correct
```

Instead:

```text
unexamined dependency
        ↓
UNKNOWN
        ↓
gate decides whether UNKNOWN is tolerable
```

For a critical ownership or concurrency dependency:

```text
UNKNOWN
    → BLOCKED
```

rather than:

```text
UNKNOWN
    → PASS
```

## 779. Contract graph
<!-- source: PROOF-CARRYING.md §5 -->

The contract system should become a graph.

```text
                    MigrationUnit
                          |
                 +--------+--------+
                 |        |        |
                 v        v        v
              Type-C    Lock-C   Lifetime-C
                 |        |        |
                 +--------+--------+
                          |
                          v
                  Semantic Contract
                          |
                          v
                     Rust Design
```

But contracts can depend on other contracts:

```text
LifetimeContract
       |
       v
ReferenceContract
       |
       v
CallbackContract
       |
       v
WorkerContract
```

So certification needs dependency closure.

## 780. Contract identity
<!-- source: PROOF-CARRYING.md §6 -->

A contract must have stable identity.

```rust
pub struct Contract {
    pub id: ContractId,
    pub epoch: Epoch,

    pub subject: SubjectId,
    pub kind: ContractKind,

    pub statement: ContractStatement,

    pub dependencies: Vec<ContractId>,
    pub evidence: Vec<EvidenceId>,
}
```

The human-readable statement is useful for humans and LLMs.

It is **not** the canonical identity.

Canonical identity should derive from structured content.

Conceptually:

```text
ContractId =
    H(
        epoch,
        subject,
        kind,
        canonical_statement,
        dependencies
    )
```

## 781. Never identify semantics by prose
<!-- source: PROOF-CARRYING.md §7 -->

Bad:

```text
"foo probably owns bar"
```

Better:

```rust
OwnershipContract {
    owner: Foo,
    object: Bar,
    state: Owned,
}
```

Bad:

```text
"this function seems safe under the lock"
```

Better:

```rust
LockContract {
    protected_object: X,
    lock: L,
    required_context: Held(L),
}
```

The LLM can generate the prose.

The protocol must consume structured semantics.

## 782. Rust Design must map contracts explicitly
<!-- source: PROOF-CARRYING.md §8 -->

Suppose the C reconstruction produces:

```text
C Contract:
    object X is reference-counted
```

The Rust design must state:

```text
Rust Design:
    representation = RefCounted<X>
```

and the mapping becomes:

```rust
pub struct ContractMapping {
    pub contract: ContractId,
    pub design_element: DesignElementId,
    pub rationale: DesignRationale,
}
```

Then:

```text
C semantic contract
       |
       | mapping
       v
Rust design decision
```

is inspectable.

## 783. Design decisions require justification
<!-- source: PROOF-CARRYING.md §9 -->

A Rust agent should not silently choose between:

```text
&T
&mut T
Box<T>
Arc<T>
Pin<Box<T>>
UnsafeCell<T>
Atomic<T>
raw pointer
kernel wrapper
```

The choice becomes a design decision:

```rust
pub struct DesignDecision {
    pub id: DesignDecisionId,
    pub question: DesignQuestion,

    pub selected: DesignOption,

    pub rejected: Vec<RejectedOption>,

    pub supporting_contracts: Vec<ContractId>,
    pub evidence: Vec<EvidenceId>,
}
```

Now the system can ask:

> Why was `Arc<T>` selected?

and obtain:

```text
ownership contract + lifetime contract + concurrency contract
```

instead of:

```text
because the model thought it looked right.
```

## 784. Unsafe design decisions
<!-- source: PROOF-CARRYING.md §10 -->

Suppose the selected design is:

```rust
unsafe fn ...
```

The design decision automatically creates obligations.

```text
DesignDecision
      |
      v
UnsafeObligation
      |
      +-- required invariant A
      +-- required invariant B
      +-- required invariant C
```

No obligation may disappear merely because the generated code compiles.

## 785. Generator contract
<!-- source: PROOF-CARRYING.md §11 -->

The Rust generator should have a narrow interface:

```rust
pub trait RustGenerator {
    fn generate(
        &self,
        design: &RustDesign,
    ) -> GenerationResult;
}
```

Output:

```rust
pub struct GenerationResult {
    pub artifact: ArtifactId,
    pub source_digest: Digest,
    pub generation_record: GenerationRecord,
}
```

The generator does **not** decide:

```text
Verified
```

or:

```text
Certified
```

Its authority ends at artifact generation.

## 786. Generation provenance
<!-- source: PROOF-CARRYING.md §12 -->

This is particularly important for AI-assisted kernel work.

Introduce:

```rust
pub struct GenerationRecord {
    pub id: GenerationId,

    pub agent: AgentId,
    pub model: ModelIdentity,

    pub task: TaskId,
    pub epoch: Epoch,

    pub input_digests: Vec<Digest>,
    pub output_digest: Digest,

    pub prompt_digest: Option<Digest>,
    pub tool_digests: Vec<Digest>,

    pub generated_at: Timestamp,
}
```

Then later:

```text
GenerationRecord
       |
       v
Human modification
       |
       v
Final artifact
```

must also be represented.

## 787. Human modification is a new artifact transition
<!-- source: PROOF-CARRYING.md §13 -->

Do not pretend:

```text
AI-generated source = final source
```

Instead:

```text
GeneratedArtifact
       |
       | human edit
       v
ModifiedArtifact
```

Record:

```rust
pub struct ArtifactLineage {
    pub parent: ArtifactId,
    pub child: ArtifactId,
    pub transformation: TransformationKind,
}
```

Possible:

```rust
pub enum TransformationKind {
    Generated,
    HumanModified,
    MechanicalFormat,
    MechanicalRewrite,
    Merge,
    CherryPick,
}
```

Now provenance is a graph:

```text
C source
   |
   v
KSIR
   |
   v
Design
   |
   v
AI-generated Rust
   |
   v
Human-modified Rust
   |
   v
Verified artifact
```

## 788. Differential verification
<!-- source: PROOF-CARRYING.md §14 -->

This becomes one of the most important verification modes.

For behavior `B`:

```text
C implementation
       |
       | test input I
       v
     result C
```

and:

```text
Rust implementation
       |
       | same test input I
       v
     result R
```

Then:

```text
Compare(result_C, result_R)
```

But the comparison itself requires a contract.

For some kernel behavior:

```text
exact equality
```

may be appropriate.

For others:

```text
observational equivalence
```

is more appropriate.

Therefore:

```rust
pub enum EquivalenceKind {
    Exact,
    Structural,
    Observational,
    Temporal,
    SetEquivalent,
}
```

The equivalence criterion must be part of the verification contract.

## 789. Differential testing is not universal proof
<!-- source: PROOF-CARRYING.md §15 -->

Important failure mode:

```text
C and Rust behave identically on 100 tests
```

does **not** establish:

```text
C and Rust are equivalent for all inputs.
```

So:

```text
DifferentialTest
    = Evidence
```

not:

```text
DifferentialTest
    = Proof of universal semantic equivalence
```

This distinction needs to be encoded in the verification status.

## 790. Verification strength
<!-- source: PROOF-CARRYING.md §16 -->

Introduce a verification method taxonomy:

```rust
pub enum VerificationMethod {
    StaticAnalysis,
    TypeChecking,
    Build,
    UnitTest,
    KUnit,
    Kselftest,
    RuntimeTest,
    DifferentialTest,
    ModelCheck,
    FormalProof,
    HumanReview,
}
```

Then:

```rust
pub struct VerificationClaim {
    pub subject: ArtifactId,
    pub property: ContractId,
    pub method: VerificationMethod,
    pub evidence: Vec<EvidenceId>,
}
```

Now the certificate can say exactly **what was verified and how**.

## 791. Coverage matrix
<!-- source: PROOF-CARRYING.md §17 -->

For each migration unit:

| Domain    | Required | Evidence | Status  |
|-----------|----------|----------|---------|
| Type      | yes      | E1,E2    | PASS    |
| Ownership | yes      | E3       | PASS    |
| Lifetime  | yes      | E4,E5    | PASS    |
| Locking   | yes      | E6       | BLOCKED |
| RCU       | yes      | —        | UNKNOWN |
| ABI       | yes      | E7       | PASS    |

The overall unit cannot be:

```text
CERTIFIED
```

while a required critical domain is:

```text
UNKNOWN
```

or:

```text
BLOCKED
```

## 792. Semantic coverage ≠ code coverage
<!-- source: PROOF-CARRYING.md §18 -->

This distinction is essential.

A test suite may achieve:

```text
95% code coverage
```

while leaving:

```text
RCU lifetime semantics
```

unverified.

Therefore RFL-AE should track at least:

```text
CodeCoverage
PathCoverage
ContractCoverage
EvidenceCoverage
ConfigurationCoverage
ArchitectureCoverage
ConcurrencyCoverage
```

None should be substituted for another.

## 793. Migration readiness
<!-- source: PROOF-CARRYING.md §19 -->

Before generation, define:

```text
MIGRATION_READY(U)
```

requiring:

```text
source identity valid
AND dependency closure known
AND required semantic domains analyzed
AND critical conflicts resolved
AND contracts extracted
AND contracts sufficiently evidenced
AND design authority granted
```

Then:

```text
MIGRATION_READY
```

authorizes:

```text
Rust design generation
```

but not necessarily:

```text
repository mutation
```

## 794. Implementation authorization
<!-- source: PROOF-CARRYING.md §20 -->

Separate these:

```text
DESIGN_AUTHORIZED
IMPLEMENTATION_AUTHORIZED
EXECUTION_AUTHORIZED
RELEASE_AUTHORIZED
```

For example:

```text
Agent may:
    generate Rust
```

without being allowed to:

```text
modify repository
```

or:

```text
run privileged commands
```

or:

```text
publish patch
```

This gives RFL-AE a capability lattice.

```text
Observe
   ↓
Analyze
   ↓
Propose
   ↓
Design
   ↓
Generate
   ↓
Modify
   ↓
Execute
   ↓
Verify
   ↓
Release
```

Higher levels should not automatically imply lower-level authority across scopes.

## 795. Scope + capability + epoch
<!-- source: PROOF-CARRYING.md §21 -->

Every privileged operation should satisfy:

```text
ALLOW(op)
```

iff:

```text
actor_has_capability
AND authorization_exists
AND authorization_epoch == current_epoch
AND operation_within_scope
AND task_allows_operation
AND preconditions_hold
```

This becomes the central security equation of RFL-AE.

## 796. The protocol kernel now has a real trust boundary
<!-- source: PROOF-CARRYING.md §22 -->

```text
          UNTRUSTED / PROBABILISTIC
┌────────────────────────────────────────────┐
│                                            │
│  LLM agents                                │
│  planners                                  │
│  semantic analyzers                        │
│  code generators                           │
│  review agents                             │
│                                            │
└─────────────────────┬──────────────────────┘
                      │
               typed requests
                      │
══════════════════════╪════════════════════════
                      │
              TRUSTED PROTOCOL
                      │
┌─────────────────────▼──────────────────────┐
│                                            │
│  type validation                           │
│  epoch validation                          │
│  authorization                             │
│  scope enforcement                         │
│  transitions                               │
│  event ledger                              │
│  evidence binding                          │
│  gate evaluation                           │
│  certificate derivation                    │
│                                            │
└─────────────────────┬──────────────────────┘
                      │
              external evidence
                      │
══════════════════════╪════════════════════════
                      │
              EXECUTION SYSTEMS
                      │
┌─────────────────────▼──────────────────────┐
│ Linux build/test/toolchain infrastructure  │
└────────────────────────────────────────────┘
```

The protocol does not need to trust the LLM.

It needs to trust only:

```text
typed state + deterministic rules + authorized execution + authenticated evidence
```

## 797. The actual AI architecture
<!-- source: PROOF-CARRYING.md §23 -->

With this foundation, the agents can finally become interesting.

### Semantic agents

```text
C-ControlFlow
C-DataFlow
C-Memory
C-Lifetime
C-Locking
C-RCU
C-Context
C-ABI
C-Config
C-Architecture
```

### Synthesis agents

```text
ContractSynthesizer
ConflictResolver
RustDesigner
UnsafeReviewer
```

### Verification agents

```text
StaticVerifier
BuildVerifier
KUnitVerifier
RuntimeVerifier
DifferentialVerifier
ConcurrencyVerifier
ABIVerifier
```

### Governance agents

```text
EvidenceAuditor
GateAuditor
ProvenanceAuditor
```

But none of them become authoritative merely because they have a specialized role.

## 798. Agent disagreement protocol
<!-- source: PROOF-CARRYING.md §24 -->

Suppose:

```text
LifetimeAgent:
    ownership transfers at A

ConcurrencyAgent:
    ownership remains with B

RCUAgent:
    object cannot be freed at A
```

The coordinator must not resolve this through voting.

Instead:

```text
Conflict
   |
   +-- claim A
   +-- claim B
   +-- claim C
   |
   v
Evidence acquisition
   |
   +-- source analysis
   +-- call graph
   +-- runtime instrumentation
   +-- maintainer knowledge
   |
   v
Resolution
```

If unresolved:

```text
OPEN / BLOCKED
```

That is a feature, not a failure of the AI system.

## 799. The first real benchmark
<!-- source: PROOF-CARRYING.md §25 -->

RFL-AE should eventually have a benchmark that measures the entire pipeline.

Not:

```text
"Can an LLM translate this C function?"
```

Instead:

```text
Given C migration unit U:

1. identify source closure
2. reconstruct semantics
3. extract contracts
4. identify conflicts
5. produce Rust design
6. enumerate unsafe obligations
7. generate Rust
8. execute verification
9. collect evidence
10. produce certificate
```

Metrics:

```text
SemanticRecall
ContractPrecision
ConflictDetectionRate
UnsafeObligationRecall
DesignConformance
BuildSuccess
TestConformance
DifferentialConformance
EvidenceCompleteness
ReplayDeterminism
FalseCertificationRate
```

The last one is particularly important.

## 800. The most important metric
<!-- source: PROOF-CARRYING.md §26 -->

I would explicitly optimize for:

```text
FALSE_CERTIFICATION_RATE
```

rather than:

```text
CODE_GENERATION_SUCCESS
```

Because:

```text
wrong Rust + no certificate
```

is recoverable.

But:

```text
wrong Rust + valid-looking certificate
```

is a catastrophic failure of the architecture.

Therefore the system should be conservative.

```text
UNCERTAIN
   ↓
BLOCKED
```

is preferable to:

```text
UNCERTAIN
   ↓
PASS
```

when the uncertainty affects a required invariant.

## 801. End-to-end certificate chain
<!-- source: PROOF-CARRYING.md §27 -->

The final object should look conceptually like:

```text
CERTIFICATE
│
├── Epoch
│
├── MigrationUnit
│   ├── C source digest
│   └── source closure
│
├── KSIR
│   ├── observations
│   ├── derivations
│   └── invariants
│
├── Contracts
│   ├── ownership
│   ├── lifetime
│   ├── concurrency
│   ├── ABI
│   └── configuration
│
├── Rust Design
│   ├── mappings
│   └── unsafe obligations
│
├── Artifact
│   └── Rust digest
│
├── Generation Provenance
│
├── Execution Evidence
│
├── Verification Results
│
├── Gate Results
│
└── Replay Verification
```

Then:

```text
CertificateDigest =
    H(canonical_certificate)
```

The certificate becomes a content-addressed statement about a particular migration state.

## 802. Final architecture
<!-- source: PROOF-CARRYING.md §28 -->

At this point the complete RFL-AE system becomes:

```text
                    HUMAN AUTHORITY
                           │
                           ▼
                    POLICY / SCOPE
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    RFL-AE PROTOCOL                      │
│                                                         │
│  Epoch ─ Authorization ─ Transition ─ Ledger ─ Gates    │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
                    MIGRATION UNIT
                           │
                           ▼
                    SOURCE EVIDENCE
                           │
                           ▼
                         KSIR
                           │
                           ▼
                  SEMANTIC CONTRACTS
                           │
                           ▼
                    RUST DESIGN IR
                           │
                           ▼
                     RUST ARTIFACT
                           │
                           ▼
                   EXECUTION SYSTEMS
                           │
                           ▼
                       EVIDENCE
                           │
                           ▼
                     VERIFICATION
                           │
                           ▼
                         GATES
                           │
                           ▼
                      CERTIFICATE
                           │
                           ▼
                 UPSTREAM REVIEW STATE
```

And the authority direction is strictly one-way:

```text
AI proposes
    ↓
protocol authorizes
    ↓
execution produces evidence
    ↓
independent verification evaluates
    ↓
gates derive status
    ↓
certificate records result
```

Not:

```text
AI proposes
    ↓
AI verifies
    ↓
AI certifies
```

## 803. The next boundary
<!-- source: PROOF-CARRYING.md §29 -->

The architecture is now ready for the first **executable vertical slice**.

The next implementation should be:

```text
rfl-types
   + rfl-transition
   + rfl-ledger
   + rfl-evidence
   + rfl-gates
   + one MigrationUnit
   + 18 adversarial conformance tests
```

Before any Linux subsystem is migrated.

That vertical slice should become the **RFL-AE protocol-kernel reference implementation**. Once it passes, the same machinery can be applied to the first real kernel migration unit, and the AI agents become replaceable workers operating under a deterministic authority layer rather than being part of the authority itself.

---

**Done — see [RFL-TYPES.md](RFL-TYPES.md)** (§804–§822, source §§1–§18 plus the unnumbered
*The next concrete layer*), which makes the protocol kernel concrete starting with
**`rfl-types`**, the crate whose one job is to define the canonical data model and invariants
shared by every RFL-AE component: newtype identifiers so the compiler becomes part of the
protocol boundary; an algorithm-bearing `Digest`; `Epoch` as a first-class object that state,
evidence and authorization cannot silently cross; a status algebra keeping `GateStatus`,
`VerificationStatus` and `EvidenceStatus` apart, with **`FAIL ≠ BLOCKED`**; a closed
`OperationKind`; `Capability` distinct from `Authorization`; `OperationRequest` instead of
`execute(command: String)`; `MigrationUnit` with source identity; a deterministic transition
engine with no third result; retries as new `TaskAttempt`s rather than state rewinds; a
hash-chained event ledger where **replay is a theorem of the implementation**; the evidence
boundary between an agent saying *"I verified it"* and execution infrastructure; the
self-verification attack as a transition invariant; the **18 adversarial conformance tests**,
the last of which must accept; and `rfl-transition` as the next concrete layer. Same provenance
convention as `VERIFICATION.md`.
