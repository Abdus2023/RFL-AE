# RFL-AE — Protocol Kernel Implementation

> **Provenance and numbering.** This document was supplied as *RFL-AE — Protocol Kernel Implementation v0.1*, numbered §1–§28 in the source. To keep the corpus contiguous, its sections are renumbered **§548–§575**, continuing directly from [PROTOCOL-KERNEL.md](PROTOCOL-KERNEL.md) (which ends at §547). The mapping is **`corpus_section = source_section + 547`**. The original source numbering is preserved on every heading as a machine-readable HTML comment of the form `<!-- source: PROTOCOL-IMPL.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. The Rust blocks below are normative API and behaviour definitions, not a compiled crate; no `crates/` tree, `Cargo.toml`, or executable test has been written. The repository status remains `v0.0` — documentation only.

The next artifact should now be the actual protocol kernel API and transition implementation.

The design should freeze around one invariant:

```text
Command
  ↓
Validate
  ↓
Authorize
  ↓
Check Preconditions
  ↓
Construct Event
  ↓
Reduce
  ↓
Check Invariants
  ↓
CAS Append
  ↓
Canonical State
```

No agent writes canonical state directly.

---

## Contents

- [548. Repository state](#548-repository-state)
- [549. rfl-types](#549-rfl-types)
- [550. Digest type](#550-digest-type)
- [551. Snapshot identity](#551-snapshot-identity)
- [552. Migration state](#552-migration-state)
- [553. Operations](#553-operations)
- [554. Command](#554-command)
- [555. Authorization](#555-authorization)
- [556. Capability](#556-capability)
- [557. Protocol state](#557-protocol-state)
- [558. Migration record](#558-migration-record)
- [559. Transition engine](#559-transition-engine)
- [560. TransitionPlan](#560-transitionplan)
- [561. Event](#561-event)
- [562. Event kinds](#562-event-kinds)
- [563. Reducer](#563-reducer)
- [564. Critical design rule](#564-critical-design-rule)
- [565. Event store](#565-event-store)
- [566. Replay](#566-replay)
- [567. First lifecycle test](#567-first-lifecycle-test)
- [568. Illegal transition tests](#568-illegal-transition-tests)
- [569. Authorization tests](#569-authorization-tests)
- [570. Epoch invalidation](#570-epoch-invalidation)
- [571. Tamper test](#571-tamper-test)
- [572. The first protocol gate](#572-the-first-protocol-gate)
- [573. Protocol crate boundary](#573-protocol-crate-boundary)
- [574. What this gives us](#574-what-this-gives-us)
- [575. Next implementation slice](#575-next-implementation-slice)

---

## 548. Repository state
<!-- source: PROTOCOL-IMPL.md §1 -->

Use this as the first implementation skeleton:

```text
rfl-ae/
├── Cargo.toml
├── PROTOCOL.md
├── ARCHITECTURE.md
├── VERIFICATION.md
├── EXECUTION.md
├── ORCHESTRATION.md
├── EVIDENCE.md
│
├── crates/
│   ├── rfl-types/
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── ids.rs
│   │       ├── digest.rs
│   │       ├── snapshot.rs
│   │       └── version.rs
│   │
│   └── rfl-protocol/
│       ├── Cargo.toml
│       ├── src/
│       │   ├── lib.rs
│       │   ├── command.rs
│       │   ├── operation.rs
│       │   ├── authorization.rs
│       │   ├── capability.rs
│       │   ├── state.rs
│       │   ├── migration.rs
│       │   ├── event.rs
│       │   ├── transition.rs
│       │   ├── precondition.rs
│       │   ├── invariant.rs
│       │   ├── reducer.rs
│       │   ├── store.rs
│       │   ├── replay.rs
│       │   ├── validation.rs
│       │   └── error.rs
│       │
│       └── tests/
│           ├── lifecycle.rs
│           ├── authorization.rs
│           ├── epoch.rs
│           ├── replay.rs
│           ├── tamper.rs
│           └── adversarial.rs
│
└── schemas/
    └── protocol/
        ├── command.schema.json
        ├── event.schema.json
        └── state.schema.json
```

The first implementation deliberately excludes:

```text
LLM
scheduler
KSIR analyzer
Rust designer
kernel source analysis
execution sandbox
```

Those attach later.

---

## 549. rfl-types
<!-- source: PROTOCOL-IMPL.md §2 -->

The common types crate must contain no protocol transition logic.

`ids.rs`

```rust
use uuid::Uuid;

macro_rules! typed_id {
    ($name:ident) => {
        #[derive(
            Clone,
            Copy,
            Debug,
            Eq,
            Hash,
            Ord,
            PartialEq,
            PartialOrd,
        )]
        pub struct $name(pub Uuid);
    };
}

typed_id!(TaskId);
typed_id!(MigrationUnitId);
typed_id!(AgentId);
typed_id!(CapabilityId);
typed_id!(AuthorizationId);
typed_id!(CommandId);
typed_id!(EventId);
typed_id!(LeaseId);
typed_id!(GateId);
```

The important property is that:

```text
TaskId != AgentId
TaskId != MigrationUnitId
AuthorizationId != CapabilityId
```

even though all are physically UUIDs.

---

## 550. Digest type
<!-- source: PROTOCOL-IMPL.md §3 -->

Do not pass arbitrary strings as hashes.

```rust
#[derive(
    Clone,
    Copy,
    Debug,
    Eq,
    Hash,
    PartialEq,
)]
pub struct Digest([u8; 32]);
```

Initially:

```text
SHA-256
```

can be used.

The hashing algorithm itself should be explicit in the serialized representation:

```rust
pub enum DigestAlgorithm {
    Sha256,
}
```

Eventually this can support additional algorithms without changing the semantic meaning of Digest.

---

## 551. Snapshot identity
<!-- source: PROTOCOL-IMPL.md §4 -->

Snapshot identity is fundamental.

```rust
pub struct KernelSnapshotId {
    pub tree_digest: Digest,
    pub source_version: String,
}
```

But do not make source_version authoritative.

The authoritative identity is the immutable digest.

For a build variant:

```rust
pub struct BuildVariantId(pub Digest);
```

And:

```rust
pub struct BuildVariant {
    pub id: BuildVariantId,
    pub snapshot: KernelSnapshotId,
    pub architecture: String,
    pub config_digest: Digest,
    pub toolchain_digest: Digest,
}
```

---

## 552. Migration state
<!-- source: PROTOCOL-IMPL.md §5 -->

```rust
#[derive(
    Clone,
    Copy,
    Debug,
    Eq,
    PartialEq,
)]
pub enum MigrationState {
    Discovered,
    Mapped,
    Contracted,
    Designed,

    AuthorizedForImplementation,
    Implemented,

    AuthorizedForTesting,

    PartiallyVerified,
    Verified,

    AdversariallyVerified,

    AuthorizedForReview,
    ReleaseEligible,
    Released,

    Quarantined,
}
```

Do not represent this as a free-form string.

---

## 553. Operations
<!-- source: PROTOCOL-IMPL.md §6 -->

```rust
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Operation {
    DiscoverMigration,
    MapMigration,

    SubmitContract,
    SubmitDesign,

    AuthorizeImplementation,
    SubmitImplementation,

    AuthorizeTesting,
    SubmitVerification,

    SubmitAdversarialVerification,

    AuthorizeReview,
    ApproveRelease,
    Release,

    Quarantine,
    ResolveQuarantine,

    AdvanceEpoch,
}
```

The protocol kernel knows these operations.

It does not know what an LLM thinks about them.

---

## 554. Command
<!-- source: PROTOCOL-IMPL.md §7 -->

The command becomes the only public request mechanism.

```rust
pub struct TransitionCommand {
    pub command_id: CommandId,

    pub actor: AgentId,

    pub task_id: TaskId,
    pub migration_unit: MigrationUnitId,

    pub snapshot: KernelSnapshotId,
    pub variant: BuildVariantId,

    pub authorization: AuthorizationId,
    pub capability: CapabilityId,

    pub epoch: Epoch,

    pub expected: ExpectedState,

    pub operation: Operation,

    pub payload: CommandPayload,
}
```

Expected state:

```rust
pub struct ExpectedState {
    pub sequence: u64,
    pub state_digest: Digest,
}
```

This is the optimistic concurrency contract.

---

## 555. Authorization
<!-- source: PROTOCOL-IMPL.md §8 -->

Authorization must be explicit.

```rust
pub struct Authorization {
    pub id: AuthorizationId,

    pub actor: AgentId,

    pub authority: AuthorityClass,

    pub task_id: TaskId,
    pub migration_unit: MigrationUnitId,

    pub snapshot: KernelSnapshotId,
    pub epoch: Epoch,

    pub allowed_operations: Vec<Operation>,

    pub expires_at: LogicalTime,

    pub status: AuthorizationStatus,
}
```

Authority:

```rust
pub enum AuthorityClass {
    Discovery,
    Design,
    Implementation,
    Verification,
    AdversarialVerification,
    Review,
    Release,
}
```

This prevents the classic failure:

```text
ImplementationAgent
        │
        └── SubmitVerification
```

The command validator rejects it.

---

## 556. Capability
<!-- source: PROTOCOL-IMPL.md §9 -->

Capability and authorization remain separate.

```rust
pub enum Capability {
    AnalyzeKernel,
    ConstructContract,
    ConstructRustDesign,
    ModifyImplementation,
    ExecuteTests,
    Verify,
    AdversarialVerify,
    Review,
    Release,
}
```

An agent can possess:

```text
Capability::Verify
```

without currently possessing:

```text
Authorization::Verify(MigrationUnit X)
```

Both checks are required.

---

## 557. Protocol state
<!-- source: PROTOCOL-IMPL.md §10 -->

```rust
pub struct ProtocolState {
    pub protocol_version: ProtocolVersion,

    pub sequence: u64,
    pub epoch: Epoch,

    pub snapshot: KernelSnapshotId,

    pub migrations:
        BTreeMap<MigrationUnitId, MigrationRecord>,

    pub authorizations:
        BTreeMap<AuthorizationId, Authorization>,

    pub capabilities:
        BTreeMap<CapabilityId, CapabilityRecord>,

    pub agents:
        BTreeMap<AgentId, AgentRecord>,

    pub leases:
        BTreeMap<LeaseId, LeaseRecord>,

    pub evidence:
        BTreeMap<EvidenceId, EvidenceRecord>,

    pub gates:
        BTreeMap<GateId, GateRecord>,

    pub event_head: Option<Digest>,
}
```

Use deterministic containers such as BTreeMap where ordering can become observable.

Do not make state hashing depend on unspecified hash-map iteration order.

---

## 558. Migration record
<!-- source: PROTOCOL-IMPL.md §11 -->

```rust
pub struct MigrationRecord {
    pub id: MigrationUnitId,

    pub task_id: TaskId,

    pub snapshot: KernelSnapshotId,
    pub variant: BuildVariantId,

    pub state: MigrationState,

    pub contract: Option<ContractId>,
    pub design: Option<DesignId>,
    pub implementation: Option<ArtifactId>,
    pub verification: Option<VerificationId>,

    pub blocking_unknowns: Vec<UnknownId>,
    pub conflicts: Vec<ConflictId>,

    pub lease: Option<LeaseId>,
}
```

Notice what is missing:

```text
confidence: f64
```

There is no confidence score.

The protocol deals in explicit state and evidence.

---

## 559. Transition engine
<!-- source: PROTOCOL-IMPL.md §12 -->

This becomes the heart of rfl-protocol.

```rust
pub struct TransitionEngine;

impl TransitionEngine {
    pub fn apply(
        state: &ProtocolState,
        command: &TransitionCommand,
        auth: &Authorization,
        capability: &CapabilityRecord,
    ) -> Result<TransitionPlan, ProtocolError> {
        validate_command(state, command)?;

        validate_snapshot(state, command)?;

        validate_epoch(state, command)?;

        validate_expected_state(state, command)?;

        validate_authorization(
            state,
            command,
            auth,
        )?;

        validate_capability(
            command,
            capability,
        )?;

        validate_scope(
            state,
            command,
            auth,
        )?;

        validate_transition(
            state,
            command,
        )?;

        let event =
            construct_event(state, command)?;

        let new_state =
            reduce(state, &event)?;

        validate_invariants(
            state,
            &new_state,
            &event,
        )?;

        Ok(TransitionPlan {
            event,
            new_state,
        })
    }
}
```

The ordering matters.

Do not allow the reducer to determine whether an actor was authorized.

Authorization must be established before event construction.

---

## 560. TransitionPlan
<!-- source: PROTOCOL-IMPL.md §13 -->

```rust
pub struct TransitionPlan {
    pub event: ProtocolEvent,
    pub new_state: ProtocolState,
}
```

This lets the event store perform the final CAS.

```text
Current State
     │
     ▼
TransitionEngine
     │
     ├── reject
     │
     └── TransitionPlan
             │
             ├── Event
             └── NewState
                    │
                    ▼
                 EventStore
```

---

## 561. Event
<!-- source: PROTOCOL-IMPL.md §14 -->

```rust
pub struct ProtocolEvent {
    pub id: EventId,

    pub sequence: u64,
    pub epoch: Epoch,

    pub command_id: CommandId,
    pub actor: AgentId,

    pub snapshot: KernelSnapshotId,
    pub variant: BuildVariantId,

    pub target: MigrationUnitId,

    pub state_before: Digest,
    pub state_after: Digest,

    pub previous_event: Option<Digest>,

    pub kind: EventKind,

    pub payload: EventPayload,

    pub digest: Digest,
}
```

---

## 562. Event kinds
<!-- source: PROTOCOL-IMPL.md §15 -->

```rust
pub enum EventKind {
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
}
```

The event describes the accepted transition, not the requested operation.

---

## 563. Reducer
<!-- source: PROTOCOL-IMPL.md §16 -->

Example:

```rust
pub fn reduce(
    state: &ProtocolState,
    event: &ProtocolEvent,
) -> Result<ProtocolState, ReduceError> {
    let mut next = state.clone();

    match &event.payload {
        EventPayload::MigrationDiscovered {
            migration,
        } => {
            if next.migrations.contains_key(&migration.id) {
                return Err(
                    ReduceError::DuplicateMigration
                );
            }

            next.migrations.insert(
                migration.id,
                migration.clone(),
            );
        }

        EventPayload::MigrationMapped {
            migration_id,
        } => {
            let migration =
                next.migrations
                    .get_mut(migration_id)
                    .ok_or(
                        ReduceError::UnknownMigration
                    )?;

            if migration.state
                != MigrationState::Discovered
            {
                return Err(
                    ReduceError::InvalidState
                );
            }

            migration.state =
                MigrationState::Mapped;
        }

        // ...
    }

    next.sequence = event.sequence;
    next.event_head = Some(event.digest);

    Ok(next)
}
```

The reducer is intentionally boring.

That is a feature.

---

## 564. Critical design rule
<!-- source: PROTOCOL-IMPL.md §17 -->

The reducer must never perform:

```text
network I/O
filesystem I/O
LLM calls
Git operations
compiler execution
test execution
clock reads
random generation
authorization lookup outside state
```

It transforms:

```text
State + Event → State
```

and nothing else.

That makes it testable and replayable.

---

## 565. Event store
<!-- source: PROTOCOL-IMPL.md §18 -->

First implementation can be in-memory.

```rust
pub trait EventStore {
    fn head(&self)
        -> Result<EventHead, StoreError>;

    fn append(
        &mut self,
        expected: &EventHead,
        event: ProtocolEvent,
    ) -> Result<EventHead, StoreError>;

    fn events(
        &self,
    ) -> &[ProtocolEvent];
}
```

The append implementation:

```rust
if self.head.sequence != expected.sequence {
    return Err(StoreError::ConcurrentWriter);
}

if self.head.digest != expected.digest {
    return Err(StoreError::HeadMismatch);
}

self.events.push(event);

Ok(new_head)
```

Later implementations can use:

```text
SQLite
PostgreSQL
append-only files
content-addressed storage
```

without changing protocol semantics.

---

## 566. Replay
<!-- source: PROTOCOL-IMPL.md §19 -->

```rust
pub fn replay(
    initial: ProtocolState,
    events: &[ProtocolEvent],
) -> Result<ProtocolState, ReplayError> {
    let mut state = initial;

    for event in events {
        if event.sequence != state.sequence + 1 {
            return Err(
                ReplayError::SequenceMismatch
            );
        }

        let before = digest_state(&state);

        if event.state_before != before {
            return Err(
                ReplayError::StateBeforeMismatch
            );
        }

        state = reduce(&state, event)?;

        let after = digest_state(&state);

        if event.state_after != after {
            return Err(
                ReplayError::StateAfterMismatch
            );
        }
    }

    Ok(state)
}
```

This creates a very strong property:

```text
event.state_before
        ↓
actual state
        ↓
reducer
        ↓
event.state_after
```

Any divergence is detected.

---

## 567. First lifecycle test
<!-- source: PROTOCOL-IMPL.md §20 -->

The first integration test should be almost trivial.

```rust
#[test]
fn migration_lifecycle_replays_deterministically() {
    let initial = test_state();

    let e1 = command(
        Operation::DiscoverMigration,
    );

    let s1 = apply(initial.clone(), e1);

    let e2 = command(
        Operation::MapMigration,
    );

    let s2 = apply(s1.state.clone(), e2);

    let e3 = command(
        Operation::SubmitContract,
    );

    let s3 = apply(s2.state.clone(), e3);

    let events = vec![
        s1.event,
        s2.event,
        s3.event,
    ];

    let replayed =
        replay(initial, &events)
            .expect("replay");

    assert_eq!(
        digest_state(&s3.state),
        digest_state(&replayed)
    );
}
```

This test establishes the core architecture.

---

## 568. Illegal transition tests
<!-- source: PROTOCOL-IMPL.md §21 -->

```rust
#[test]
fn cannot_submit_contract_before_mapping() {
    let state = discovered_state();

    let command =
        command(Operation::SubmitContract);

    let result =
        apply_command(state, command);

    assert!(matches!(
        result,
        Err(
            ProtocolError::InvalidStateTransition { .. }
        )
    ));
}
```

Likewise:

```text
DISCOVERED
    └── SubmitImplementation → REJECT

MAPPED
    └── SubmitVerification → REJECT

CONTRACTED
    └── Release → REJECT

IMPLEMENTED
    └── Release → REJECT
```

---

## 569. Authorization tests
<!-- source: PROTOCOL-IMPL.md §22 -->

The protocol must explicitly prove:

```rust
#[test]
fn implementation_agent_cannot_verify() {
    let state = testing_state();

    let command =
        command(Operation::SubmitVerification);

    let result =
        apply_with_authority(
            state,
            command,
            AuthorityClass::Implementation,
        );

    assert!(matches!(
        result,
        Err(ProtocolError::Authorization(_))
    ));
}
```

This is not merely documentation.

It is an executable security invariant.

---

## 570. Epoch invalidation
<!-- source: PROTOCOL-IMPL.md §23 -->

Suppose:

```text
Epoch 7
  │
  ├── Agent A receives assignment
  │
  └── Contract changes
          ↓
       Epoch 8
```

Agent A's result is now stale.

```rust
#[test]
fn stale_epoch_cannot_mutate_state() {
    let state = state_at_epoch(8);

    let command =
        command_from_epoch(7);

    let result =
        apply_command(state, command);

    assert!(matches!(
        result,
        Err(ProtocolError::StaleEpoch { .. })
    ));
}
```

The artifact may remain historically useful.

It simply loses current canonical authority.

---

## 571. Tamper test
<!-- source: PROTOCOL-IMPL.md §24 -->

```rust
#[test]
fn modified_event_is_rejected() {
    let events = valid_event_log();

    let mut tampered = events.clone();

    tampered[1].state_after =
        fake_digest();

    let result =
        replay(test_state(), &tampered);

    assert!(matches!(
        result,
        Err(ReplayError::StateAfterMismatch)
    ));
}
```

Also test:

```text
modified payload
modified actor
modified command ID
modified snapshot
modified epoch
modified previous digest
modified sequence
deleted event
duplicated event
reordered event
```

---

## 572. The first protocol gate
<!-- source: PROTOCOL-IMPL.md §25 -->

Before implementing anything above the protocol:

```text
PROTO-GATE-001
```

must require:

```text
[ ] cargo check
[ ] cargo test
[ ] deterministic replay passes
[ ] illegal transitions rejected
[ ] authorization violations rejected
[ ] scope violations rejected
[ ] epoch violations rejected
[ ] CAS race rejected
[ ] event tampering detected
[ ] event deletion detected
[ ] event reordering detected
[ ] projection reconstruction passes
[ ] state digest deterministic
[ ] no network dependency
[ ] no wall-clock dependency
[ ] no LLM dependency
```

And critically:

```text
NO EXECUTION EVIDENCE
        ↓
NO VERIFIED GATE
```

The gate itself should eventually consume an execution receipt rather than trusting the developer's assertion that tests passed.

---

## 573. Protocol crate boundary
<!-- source: PROTOCOL-IMPL.md §26 -->

The dependency rule should now be frozen:

```text
rfl-protocol
    MAY depend on:
        rfl-types

    MUST NOT depend on:
        rfl-ksir
        rfl-contract
        rfl-design
        rfl-verification
        rfl-execution
        rfl-evidence
        rfl-gates
        rfl-orchestration
        LLM SDKs
        Git clients
        kernel analyzers
```

This is important because the protocol kernel is supposed to be the lower-level authority substrate.

---

## 574. What this gives us
<!-- source: PROTOCOL-IMPL.md §27 -->

We now have a concrete hierarchy:

```text
RFL-AE
                  │
                  ▼
          ┌───────────────┐
          │ Protocol Core │
          └───────┬───────┘
                  │
          immutable events
                  │
                  ▼
          canonical state
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
     KSIR       Evidence   Agents
       │          │          │
       ▼          ▼          ▼
   Contracts    Gates     Scheduler
       │          │
       ▼          ▼
     Design   Verification
       │          │
       └─────┬────┘
             ▼
        Release Gate
```

The important inversion is that agents become clients of the protocol, not owners of the protocol.

---

## 575. Next implementation slice
<!-- source: PROTOCOL-IMPL.md §28 -->

After this kernel, the correct progression is:

```text
P0  Protocol types
 ↓
P1  Transition engine
 ↓
P2  In-memory event store
 ↓
P3  Deterministic replay
 ↓
P4  Conformance/adversarial suite
 ↓
P5  Persistent event store
 ↓
P6  Evidence binding
 ↓
P7  Gate engine
 ↓
P8  KSIR integration
 ↓
P9  Contract integration
 ↓
P10 Orchestration integration
```

Do not implement P8–P10 before P0–P4 are mechanically green.

The protocol kernel is the foundation on which the rest of RFL-AE can safely become autonomous. Its first release criterion is not "it can migrate Rust code"; it is:

> Given the same authorized command stream, RFL-AE reconstructs exactly the same canonical protocol state, rejects every unauthorized or semantically illegal transition in the conformance corpus, and detects tampered history.

That is the first real executable theorem of the system.

---

**Done — see [PROTOCOL-P58.md](PROTOCOL-P58.md)** (§576–§610, source §§1–§35), which connects
persistence, evidence and gates to the kernel without letting any of those layers become hidden
authority: P5's append-only event log, its length-delimited physical record, the locking append
protocol, explicit `RecoveryStatus` crash semantics with no silent truncation, the chain
`event constructed ≠ event accepted ≠ event durably persisted ≠ operation executed ≠ claim
verified`, and the `AppendReceipt`/`DurabilityStatus` distinction that durability is not
verification; P6's evidence binding where the protocol stores `EvidenceRef` rather than bytes,
`EvidenceValidity` and dependency-driven rather than global invalidation, `VerificationSubmission`
that cannot merely carry `status: Verified`, per-obligation `ObligationResult`, semantic coverage,
the `OracleKind` model and `ComparisonRelation`/`DifferentialContract` so that `C output == Rust
output` is never a universal rule; P7's gate algebra as typed predicates, `GateExpr`, the
implementation/test/release gates, `GateResult` with `GateStatus` keeping `FAIL` distinct from
`BLOCKED` because `UNKNOWN ≠ FALSE`, and the gate evidence chain; and P8's `MigrationCertificate`,
which is a claim and not release authority, the full source-to-release chain, the extended
`EventKind` and typed `EventPayload`, dependency invalidation, stale versus invalid, epoch
advancement as a transition, canonical serialization, the frozen lifecycle transition table, the
quarantine authority-suppression invariant, the protocol QA matrix, the release boundary, and the
next implementation slice. Same provenance convention as `VERIFICATION.md`.
