# RFL-AE — Protocol Kernel P5–P8

> **Provenance and numbering.** This document was supplied as *RFL-AE — Protocol Kernel P5–P8*, numbered §1–§35 in the source. To keep the corpus contiguous, its sections are renumbered **§576–§610**, continuing directly from [PROTOCOL-IMPL.md](PROTOCOL-IMPL.md) (which ends at §575). The mapping is **`corpus_section = source_section + 575`**. The original source numbering is preserved on every heading as a machine-readable HTML comment of the form `<!-- source: PROTOCOL-P58.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. The Rust blocks below are normative API and behaviour definitions, not a compiled crate; no `crates/` tree, `Cargo.toml`, or executable test has been written. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** In the pasted source every ASCII diagram arrived collapsed onto a single line. Those diagrams were therefore *redrawn* rather than copied, with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector and off-centre checks — they were not hand-typed. The generator is committed at [`diagrams/PROTOCOL-P58.py`](diagrams/PROTOCOL-P58.py); re-running it reproduces all 63 diagrams byte for byte, so the redraw can be checked rather than trusted. Where a diagram's geometry was under-determined by the collapse, it was re-derived structurally from box widths and shared spine columns. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`); the alignment padding visible in the pasted source was not reproducible and carries no semantic content.

The protocol kernel is now defined enough that the next step is to connect **persistence, evidence, and gates** without allowing any of those layers to become hidden authority.

The key architecture becomes:

```text
                 COMMAND
                    │
                    ▼
             ┌─────────────┐
             │  PROTOCOL   │
             │   KERNEL    │
             └──────┬──────┘
                    │
                    │ canonical
                    │ events
                    │
                    ▼
             ┌─────────────┐
             │ EVENT STORE │
             └──────┬──────┘
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     PROJECTION            REPLAY
          │                   │
          └─────────┬─────────┘
                    ▼
             CANONICAL STATE
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      EVIDENCE              GATES
          │                   │
          └─────────┬─────────┘
                    ▼
            RELEASE DECISION
```

The important distinction remains:

```text
Evidence says:       WHAT WAS OBSERVED
Verification says:   WHAT THE OBSERVATION ESTABLISHES
Gate says:           WHETHER REQUIREMENTS ARE SATISFIED
Protocol says:       WHETHER THE STATE TRANSITION IS ALLOWED
```

---

## Contents

- [576. P5 — Persistent event store](#576-p5--persistent-event-store)
- [577. Physical event record](#577-physical-event-record)
- [578. Append protocol](#578-append-protocol)
- [579. Crash recovery](#579-crash-recovery)
- [580. Durability is not execution success](#580-durability-is-not-execution-success)
- [581. Event-store receipt](#581-event-store-receipt)
- [582. P6 — Evidence binding](#582-p6--evidence-binding)
- [583. Evidence reference](#583-evidence-reference)
- [584. Evidence validity](#584-evidence-validity)
- [585. Evidence invalidation](#585-evidence-invalidation)
- [586. Evidence-binding transition](#586-evidence-binding-transition)
- [587. Verification result](#587-verification-result)
- [588. Verification coverage](#588-verification-coverage)
- [589. Oracle model](#589-oracle-model)
- [590. Differential verification](#590-differential-verification)
- [591. P7 — Gate engine](#591-p7--gate-engine)
- [592. Gate algebra](#592-gate-algebra)
- [593. Example implementation gate](#593-example-implementation-gate)
- [594. Gate result](#594-gate-result)
- [595. Why `BLOCKED` matters](#595-why-blocked-matters)
- [596. Gate evidence chain](#596-gate-evidence-chain)
- [597. P8 — Certificate compiler](#597-p8--certificate-compiler)
- [598. Certificate is a claim, not authority](#598-certificate-is-a-claim-not-authority)
- [599. Full evidence-to-release chain](#599-full-evidence-to-release-chain)
- [600. Protocol events for P5–P8](#600-protocol-events-for-p5p8)
- [601. Dependency invalidation](#601-dependency-invalidation)
- [602. Stale vs invalid](#602-stale-vs-invalid)
- [603. Epoch advancement](#603-epoch-advancement)
- [604. One important correction](#604-one-important-correction)
- [605. Canonical serialization](#605-canonical-serialization)
- [606. Protocol state machine as a transition table](#606-protocol-state-machine-as-a-transition-table)
- [607. The quarantine invariant](#607-the-quarantine-invariant)
- [608. Protocol QA matrix](#608-protocol-qa-matrix)
- [609. Protocol kernel release boundary](#609-protocol-kernel-release-boundary)
- [610. What should happen immediately after this](#610-what-should-happen-immediately-after-this)

---

## 576. P5 — Persistent event store
<!-- source: PROTOCOL-P58.md §1 -->

The in-memory store proves the semantics. Persistence proves that those semantics survive process boundaries.

Do not begin with PostgreSQL.

The first persistent implementation should be a deliberately boring **append-only event log**.

```text
crates/rfl-protocol/src/store/
├── mod.rs
├── memory.rs
├── append_log.rs
├── record.rs
├── recovery.rs
└── integrity.rs
```

---

## 577. Physical event record
<!-- source: PROTOCOL-P58.md §2 -->

Use length-delimited records.

```text
┌──────────────┬──────────────┬────────────────┐
│ magic        │ schema       │ payload_length │
├──────────────┼──────────────┼────────────────┤
│ sequence     │ event_digest │ payload        │
├──────────────┴──────────────┴────────────────┤
│ record_checksum                              │
└──────────────────────────────────────────────┘
```

The physical format is not the semantic event itself.

It is merely a durable container.

---

## 578. Append protocol
<!-- source: PROTOCOL-P58.md §3 -->

The store must enforce:

```text
LOCK
  ↓
read current head
  ↓
compare expected head
  ↓
validate sequence
  ↓
validate previous digest
  ↓
append complete record
  ↓
flush according to durability policy
  ↓
publish new head
  ↓
UNLOCK
```

A failed append must not expose a partially accepted event.

---

## 579. Crash recovery
<!-- source: PROTOCOL-P58.md §4 -->

The store needs explicit recovery semantics.

```text
START
  ↓
scan records
  ↓
validate framing
  ↓
validate sequence
  ↓
validate hash chain
  ↓
validate event digest
  ↓
validate state transition
  ↓
reconstruct head
```

Possible outcomes:

```rust
pub enum RecoveryStatus {
    Clean,
    RecoveredTail,
    CorruptHistory,
    InvalidEvent,
    SequenceGap,
    DigestMismatch,
    SchemaUnsupported,
}
```

Do not silently truncate corrupted history.

If recovery finds:

```text
E001
E002
E003
CORRUPTED
```

the result should be:

```text
CORRUPT_HISTORY
```

unless an explicitly defined recovery policy authorizes tail recovery.

---

## 580. Durability is not execution success
<!-- source: PROTOCOL-P58.md §5 -->

This distinction needs to be explicit.

```text
event constructed
      ≠
event accepted
      ≠
event durably persisted
      ≠
operation executed
      ≠
claim verified
```

These are separate states.

This prevents the event store from becoming another source of semantic ambiguity.

---

## 581. Event-store receipt
<!-- source: PROTOCOL-P58.md §6 -->

Persistence can itself generate an infrastructure receipt:

```rust
pub struct AppendReceipt {
    pub event_id: EventId,
    pub sequence: u64,
    pub event_digest: Digest,
    pub storage_identity: StorageIdentity,
    pub durability: DurabilityStatus,
    pub record_offset: u64,
}
```

For example:

```rust
pub enum DurabilityStatus {
    Buffered,
    Flushed,
    Synced,
}
```

The protocol can require `Synced` for particularly important transitions if policy demands it.

But that is a **durability property**, not semantic verification.

---

## 582. P6 — Evidence binding
<!-- source: PROTOCOL-P58.md §7 -->

Now connect the execution/evidence architecture to the protocol.

The central rule:

```text
Artifact
   │
   ▼
Observation
   │
   ▼
EvidenceRecord
   │
   ▼
VerificationClaim
   │
   ▼
Gate
```

Never:

```text
test output
   ↓
VERIFIED
```

---

## 583. Evidence reference
<!-- source: PROTOCOL-P58.md §8 -->

The protocol should store references, not duplicate evidence.

```rust
pub struct EvidenceRef {
    pub evidence_id: EvidenceId,
    pub digest: Digest,
    pub snapshot: KernelSnapshotId,
    pub variant: BuildVariantId,
    pub validity: EvidenceValidity,
}
```

This means a migration can reference evidence without owning its bytes.

The evidence ledger remains authoritative for evidence integrity.

---

## 584. Evidence validity
<!-- source: PROTOCOL-P58.md §9 -->

```rust
pub enum EvidenceValidity {
    Valid,
    Superseded,
    Invalidated,
    Unreachable,
    Incomplete,
}
```

A gate must explicitly reject:

```text
Invalidated
Superseded
```

when the gate requires current evidence.

---

## 585. Evidence invalidation
<!-- source: PROTOCOL-P58.md §10 -->

Suppose:

```text
Kernel snapshot S1
    ↓
Contract C1
    ↓
Design D1
    ↓
Implementation I1
    ↓
Verification V1
```

Then source changes:

```text
S2
```

The dependency graph determines what remains valid.

Potentially:

```text
S1
 ↓
C1   INVALIDATED
 ↓
D1   INVALIDATED
 ↓
I1   STALE
 ↓
V1   INVALIDATED
```

But unrelated evidence might remain valid.

Therefore invalidation must be **dependency-driven**, not global.

---

## 586. Evidence-binding transition
<!-- source: PROTOCOL-P58.md §11 -->

Example:

```text
SubmitVerification
```

cannot simply contain:

```text
status: Verified
```

Instead:

```rust
pub struct VerificationSubmission {
    pub verification_id: VerificationId,
    pub obligations: Vec<ObligationId>,
    pub evidence: Vec<EvidenceRef>,
    pub oracle_results: Vec<OracleResultRef>,
    pub counterexamples: Vec<CounterexampleRef>,
}
```

The protocol records the submission.

The verification engine determines whether the evidence actually satisfies each obligation.

---

## 587. Verification result
<!-- source: PROTOCOL-P58.md §12 -->

```rust
pub enum VerificationStatus {
    Unverified,
    Provisional,
    PartiallyVerified,
    Verified,
    Blocked,
}
```

And per obligation:

```rust
pub struct ObligationResult {
    pub obligation: ObligationId,
    pub status: VerificationStatus,
    pub evidence: Vec<EvidenceRef>,
    pub oracle_result: OracleResultRef,
    pub blocking_unknowns: Vec<UnknownId>,
    pub conflicts: Vec<ConflictId>,
}
```

This prevents the dangerous aggregate:

```text
97/100 tests passed → VERIFIED
```

There is no such inference unless the gate explicitly defines it.

---

## 588. Verification coverage
<!-- source: PROTOCOL-P58.md §13 -->

Coverage should be semantic.

```rust
pub struct VerificationCoverage {
    pub obligations_total: usize,
    pub obligations_satisfied: usize,
    pub obligations_blocked: usize,
    pub obligations_unverified: usize,
    pub dimensions: BTreeMap<VerificationDimension, DimensionStatus>,
}
```

Dimensions:

```text
Compile
ABI
Return/Error
StateTransition
ResourceLifecycle
Synchronization
Security
ObservableIO
Performance
Architecture
Configuration
Regression
```

No numerical score should determine correctness.

The numbers are descriptive coverage metadata.

---

## 589. Oracle model
<!-- source: PROTOCOL-P58.md §14 -->

An oracle is not necessarily the original C implementation.

```rust
pub enum OracleKind {
    ExactOutput,
    Relational,
    StateInvariant,
    StateTransition,
    Temporal,
    ResourceLifecycle,
    AbiLayout,
    Concurrency,
    Security,
    Differential,
}
```

For differential testing:

```text
C implementation
      │
      ├──── normalized observation ────┐
      │                                │
      ▼                                ▼
Rust implementation               comparison
```

The comparison relation must be explicit.

---

## 590. Differential verification
<!-- source: PROTOCOL-P58.md §15 -->

Do not define:

```text
C output == Rust output
```

as a universal rule.

Kernel behavior can contain:

- nondeterminism
- architecture differences
- timing
- pointer identity
- scheduler effects
- allocator differences
- intentionally unspecified representation

Instead define:

```rust
pub enum ComparisonRelation {
    Exact,
    Equivalent,
    InvariantPreserving,
    StateEquivalent,
    TraceEquivalent,
    AllowedDifference,
}
```

And:

```rust
pub struct DifferentialContract {
    pub relation: ComparisonRelation,
    pub normalization: Option<NormalizationRule>,
    pub allowed_differences: Vec<AllowedDifference>,
}
```

The oracle itself becomes an auditable artifact.

---

## 591. P7 — Gate engine
<!-- source: PROTOCOL-P58.md §16 -->

Now gates consume the protocol state plus evidence and verification results.

But:

```text
Gate Engine ≠ Protocol Engine
```

The gate engine answers:

```text
Are the declared requirements satisfied?
```

The protocol answers:

```text
Is the requested state transition permitted?
```

---

## 592. Gate algebra
<!-- source: PROTOCOL-P58.md §17 -->

Represent gates as typed predicates.

```rust
pub enum GateRequirement {
    ArtifactExists(ArtifactId),
    EvidenceValid(EvidenceId),
    ObligationVerified(ObligationId),
    NoCriticalUnknown,
    NoCriticalConflict,
    SnapshotMatches,
    VariantMatches,
    IndependentVerification,
    RequiredAuthority(AuthorityClass),
    RequiredReview,
    RequiredRegressionCoverage,
}
```

Composite gates:

```rust
pub enum GateExpr {
    Requirement(GateRequirement),
    All(Vec<GateExpr>),
    Any(Vec<GateExpr>),
    Not(Box<GateExpr>),
}
```

But avoid unrestricted logic if it becomes difficult to audit.

For v0.1, `All` should dominate release gates.

---

## 593. Example implementation gate
<!-- source: PROTOCOL-P58.md §18 -->

```text
IMPLEMENTATION_RELEASE_GATE = ALL(
    SnapshotMatches,
    ContractVerified,
    DesignVerified,
    ImplementationArtifactExists,
    ABIContractSatisfied,
    NoCriticalUnknown,
    NoCriticalConflict
)
```

Testing gate:

```text
TEST_GATE = ALL(
    VerificationPlanExists,
    RequiredObligationsEvaluated,
    ExecutionReceiptsValid,
    EvidenceValid,
    RequiredVariantsExecuted,
    NoBlockingCounterexample
)
```

Release gate:

```text
RELEASE_GATE = ALL(
    ContractSatisfied,
    DesignSatisfied,
    VerificationSatisfied,
    AdversarialVerificationSatisfied,
    RegressionSatisfied,
    ReviewApproved,
    NoBlockingUnknown,
    NoBlockingConflict,
    SnapshotCurrent
)
```

---

## 594. Gate result
<!-- source: PROTOCOL-P58.md §19 -->

A gate should never return only:

```text
bool
```

Use:

```rust
pub struct GateResult {
    pub gate_id: GateId,
    pub status: GateStatus,
    pub satisfied: Vec<RequirementResult>,
    pub unsatisfied: Vec<RequirementResult>,
    pub blocked: Vec<RequirementResult>,
    pub evidence: Vec<EvidenceRef>,
    pub digest: Digest,
}
```

Status:

```rust
pub enum GateStatus {
    Pass,
    Fail,
    Blocked,
    NotApplicable,
}
```

This makes:

```text
FAIL
```

different from:

```text
BLOCKED
```

That distinction matters.

---

## 595. Why `BLOCKED` matters
<!-- source: PROTOCOL-P58.md §20 -->

Consider:

```text
ABI verification
```

with:

```text
ABI layout = UNKNOWN
```

This is not evidence that the ABI is wrong.

It is:

```text
UNKNOWN
```

Therefore:

```text
GateStatus::Blocked
```

rather than:

```text
GateStatus::Fail
```

Again:

```text
UNKNOWN ≠ FALSE
```

---

## 596. Gate evidence chain
<!-- source: PROTOCOL-P58.md §21 -->

Every gate result should expose its provenance:

```text
Gate
 │
 ├── Requirement
 │      │
 │      ├── Obligation
 │             │
 │             ├── Verification
 │                    │
 │                    ├── Oracle Result
 │                           │
 │                           ├── Evidence
 │                                  │
 │                                  ├── Receipt
 │                                         │
 │                                         └── Artifact
```

This becomes the basis for the migration certificate.

---

## 597. P8 — Certificate compiler
<!-- source: PROTOCOL-P58.md §22 -->

Only now should we construct the certificate.

```rust
pub struct MigrationCertificate {
    pub certificate_id: CertificateId,
    pub migration_unit: MigrationUnitId,
    pub snapshot: KernelSnapshotId,
    pub variant: BuildVariantId,
    pub contract: ContractId,
    pub design: DesignId,
    pub implementation: ArtifactId,
    pub verification: VerificationId,
    pub gates: Vec<GateResult>,
    pub unresolved_nonblocking_unknowns: Vec<UnknownId>,
    pub unresolved_nonblocking_conflicts: Vec<ConflictId>,
    pub scope: CertificateScope,
    pub generated_at: LogicalTime,
    pub digest: Digest,
}
```

Certificate scope must be explicit.

---

## 598. Certificate is a claim, not authority
<!-- source: PROTOCOL-P58.md §23 -->

This is subtle.

```text
Certificate
    ≠
Release authorization
```

The certificate says:

```text
these conditions were established
within this declared scope
against this snapshot/variant
using these artifacts/evidence/gates
```

Release authority then decides whether the certificate satisfies the release policy.

So:

```text
Certificate
    ↓
Release Gate
    ↓
Release Authorization
```

not:

```text
Certificate
    ↓
automatic release
```

unless the protocol explicitly defines release automation as the authorized policy.

---

## 599. Full evidence-to-release chain
<!-- source: PROTOCOL-P58.md §24 -->

We now have:

```text
SOURCE
  │
  ▼
OBSERVATION
  │
  ▼
KSIR FACT
  │
  ▼
CONTRACT
  │
  ▼
OBLIGATION
  │
  ▼
DESIGN
  │
  ▼
IMPLEMENTATION
  │
  ▼
EXECUTION
  │
  ▼
RECEIPT
  │
  ▼
EVIDENCE
  │
  ▼
VERIFICATION
  │
  ▼
GATE
  │
  ▼
CERTIFICATE
  │
  ▼
REVIEW
  │
  ▼
RELEASE
```

Every arrow has a defined artifact.

That is much stronger than an agent producing a final report saying:

```text
"Migration appears safe."
```

---

## 600. Protocol events for P5–P8
<!-- source: PROTOCOL-P58.md §25 -->

Add:

```rust
pub enum EventKind {
    // existing
    MigrationDiscovered,
    MigrationMapped,
    ContractSubmitted,
    DesignSubmitted,
    ImplementationAuthorized,
    ImplementationSubmitted,
    TestingAuthorized,
    VerificationSubmitted,
    AdversarialVerificationSubmitted,
    ReviewAuthorized,
    ReleaseApproved,
    MigrationReleased,
    MigrationQuarantined,
    QuarantineResolved,
    EpochAdvanced,

    // evidence
    EvidenceBound,
    EvidenceInvalidated,

    // gates
    GateEvaluated,
    GateInvalidated,

    // certificate
    CertificateGenerated,
}
```

Notice that:

```text
GateEvaluated
```

does not necessarily mean:

```text
GatePassed
```

The payload contains the actual result.

---

## 601. Dependency invalidation
<!-- source: PROTOCOL-P58.md §26 -->

The protocol now needs a graph of authority dependencies.

```rust
pub enum DependencyKind {
    Semantic,
    Contract,
    Design,
    Implementation,
    Verification,
    Evidence,
    Gate,
    Certificate,
}
```

Example:

```text
KSIR fact
   │
   ▼
Contract
   │
   ▼
Design
   │
   ▼
Implementation
   │
   ▼
Verification
   │
   ▼
Gate
   │
   ▼
Certificate
```

If the KSIR fact is invalidated:

```text
KSIR
 ↓
Contract INVALID
 ↓
Design STALE
 ↓
Verification INVALID
 ↓
Gate INVALID
 ↓
Certificate INVALID
```

The invalidation engine follows explicit dependency edges.

---

## 602. Stale vs invalid
<!-- source: PROTOCOL-P58.md §27 -->

These must remain different.

### Invalid

Evidence has been demonstrated to be unusable.

Example:

```text
receipt digest mismatch
```

### Stale

The artifact may have been correct for an earlier state, but the current state changed.

Example:

```text
Contract C1 valid at epoch 4
Contract changes at epoch 5
C1 → STALE
```

This is important for historical reconstruction.

---

## 603. Epoch advancement
<!-- source: PROTOCOL-P58.md §28 -->

Epoch advancement should itself be a protocol transition.

```text
CURRENT EPOCH = 4
contract changed
      ↓
AdvanceEpoch
      ↓
EPOCH = 5
      ↓
dependent work becomes stale
```

The event:

```rust
pub struct EpochAdvanced {
    pub old_epoch: Epoch,
    pub new_epoch: Epoch,
    pub reason: EpochAdvanceReason,
    pub invalidated: Vec<ArtifactId>,
}
```

The invalidation list should be derivable from dependency state rather than being trusted merely because an agent supplied it.

---

## 604. One important correction
<!-- source: PROTOCOL-P58.md §29 -->

At this stage, avoid making the protocol event payload carry arbitrary JSON.

Bad:

```text
payload: serde_json::Value
```

That would create a type escape hatch.

Instead:

```rust
pub enum EventPayload {
    MigrationDiscovered(MigrationDiscovered),
    MigrationMapped(MigrationMapped),
    ContractSubmitted(ContractSubmitted),
    DesignSubmitted(DesignSubmitted),
    ImplementationAuthorized(ImplementationAuthorized),
    ImplementationSubmitted(ImplementationSubmitted),
    VerificationSubmitted(VerificationSubmitted),
    EvidenceBound(EvidenceBound),
    GateEvaluated(GateEvaluated),
    CertificateGenerated(CertificateGenerated),
    // ...
}
```

Every event gets a typed schema.

---

## 605. Canonical serialization
<!-- source: PROTOCOL-P58.md §30 -->

Hashing must operate over canonical bytes.

```text
Rust struct
    ↓
canonical serialization
    ↓
bytes
    ↓
SHA-256
    ↓
Digest
```

Never:

```text
Debug formatting
JSON with arbitrary map ordering
platform-dependent serialization
```

The serialization specification should become part of `PROTOCOL.md`.

---

## 606. Protocol state machine as a transition table
<!-- source: PROTOCOL-P58.md §31 -->

Freeze the lifecycle formally:

```text
                     ┌─────────────┐
                     │ DISCOVERED  │
                     └──────┬──────┘
                            │ Map
                            ▼
                     ┌─────────────┐
                     │   MAPPED    │
                     └──────┬──────┘
                            │ Contract
                            ▼
                     ┌─────────────┐
                     │ CONTRACTED  │
                     └──────┬──────┘
                            │ Design
                            ▼
                     ┌─────────────┐
                     │  DESIGNED   │
                     └──────┬──────┘
                            │ authorize
                            ▼
             ┌──────────────────────────────┐
             │ AUTHORIZED_FOR_IMPLEMENTATION│
             └──────────────┬───────────────┘
                            │ implementation
                            ▼
                     ┌─────────────┐
                     │ IMPLEMENTED │
                     └──────┬──────┘
                            │ authorize test
                            ▼
                ┌────────────────────────┐
                │ AUTHORIZED_FOR_TESTING │
                └───────────┬────────────┘
                            │ verify
                    ┌───────┴────────┐
                    ▼                ▼
             PARTIALLY_VERIFIED   VERIFIED
                    │                │
                    └───────┬────────┘
                            │ adversarial
                            ▼
                ADVERSARIALLY_VERIFIED
                            │
                            ▼
                 AUTHORIZED_FOR_REVIEW
                            │
                            ▼
                    RELEASE_ELIGIBLE
                            │
                            ▼
                        RELEASED
```

At every node:

```text
                ┌─────────────┐
                │ QUARANTINED │
                └─────────────┘
```

is reachable when blocking conditions require it.

---

## 607. The quarantine invariant
<!-- source: PROTOCOL-P58.md §32 -->

Quarantine is not an ordinary lifecycle state.

It is an **authority suppression state**.

While quarantined:

```text
implementation authority = suspended
release authority = unavailable
canonical promotion = unavailable
```

Historical artifacts remain readable.

New investigation work can still be authorized.

```text
QUARANTINED
    │
    ▼
Investigation
    │
    ├── evidence resolves issue
    │
    └── conflict remains
            │
            ▼
         QUARANTINED
```

Resolution must generate evidence and a new epoch when required.

---

## 608. Protocol QA matrix
<!-- source: PROTOCOL-P58.md §33 -->

The first complete protocol QA should look like this:

| Domain | Property | Expected |
| --- | --- | --- |
| State | deterministic reducer | PASS |
| State | canonical digest | PASS |
| Transition | legal transition | PASS |
| Transition | illegal transition | REJECT |
| Authority | wrong authority | REJECT |
| Capability | missing capability | REJECT |
| Scope | out-of-scope command | REJECT |
| Snapshot | mismatch | REJECT |
| Epoch | stale command | REJECT |
| Concurrency | stale CAS | REJECT |
| Event | modified payload | DETECT |
| Event | reordered event | DETECT |
| Replay | full replay | IDENTICAL |
| Replay | snapshot replay | IDENTICAL |
| Projection | rebuild | IDENTICAL |
| Evidence | invalid evidence | REJECT |
| Evidence | stale evidence | BLOCK/REJECT |
| Gate | missing obligation | FAIL/BLOCK |
| Gate | critical unknown | BLOCK |
| Gate | critical conflict | BLOCK |
| Authority | implementation self-verification | REJECT |
| Authority | scheduler release authority | REJECT |
| Quarantine | bypass | REJECT |

---

## 609. Protocol kernel release boundary
<!-- source: PROTOCOL-P58.md §34 -->

The first actual repository tag should be something like:

```text
rfl-ae-protocol-v0.1.0-alpha
```

but only after:

```text
PROTOCOL-GATE-001
```

passes.

The release artifact should contain:

```text
protocol version
schema version
source commit
event format version
state schema version
test corpus digest
conformance results
adversarial test results
toolchain fingerprint
artifact digests
```

That gives us:

```text
Protocol Release
      │
      ├── source identity
      ├── semantic identity
      ├── schema identity
      └── verification evidence
```

---

## 610. What should happen immediately after this
<!-- source: PROTOCOL-P58.md §35 -->

Now the architecture has reached the point where another large conceptual chapter would have diminishing value.

The next implementation target is:

```text
RFL-AE v0.1
│
├── rfl-types
├── rfl-protocol
│   ├── typed commands
│   ├── typed events
│   ├── authorization
│   ├── transition algebra
│   ├── deterministic reducer
│   ├── event store
│   ├── replay
│   ├── CAS
│   └── protocol QA
├── rfl-evidence
│   ├── evidence records
│   ├── dependency graph
│   ├── invalidation
│   └── provenance
├── rfl-verification
│   ├── obligations
│   ├── oracle
│   ├── results
│   └── differential verification
└── rfl-gates
    ├── requirement algebra
    ├── gate evaluation
    └── certificate compilation
```

Then the first **real RFL-AE vertical slice** becomes possible:

```text
Migration discovery
       ↓
KSIR structural facts
       ↓
Contract
       ↓
Rust design
       ↓
Implementation artifact
       ↓
Authorized execution
       ↓
Execution receipt
       ↓
Evidence
       ↓
Verification obligation
       ↓
Gate
       ↓
Migration certificate
```

At that point we should stop extending the architecture temporarily and build **MU-000001 end-to-end**.

That is the first point where the architecture can be tested against reality rather than against itself.
