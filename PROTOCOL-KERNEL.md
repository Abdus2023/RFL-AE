# RFL-AE — Protocol Kernel

> **Provenance and numbering.** This document was supplied as *RFL-AE — Protocol Kernel v0.1*. Its source sections are numbered §1–§29, followed by a closing section titled *Next artifact* that the source left unnumbered; that section is recorded as source **§30** so the mapping stays total. To keep the corpus contiguous, the sections are renumbered **§518–§547**, continuing directly from [ORCHESTRATION.md](ORCHESTRATION.md) (which ends at §517). The mapping is **`corpus_section = source_section + 517`**. The original source numbering is preserved on every heading as a machine-readable HTML comment of the form `<!-- source: PROTOCOL-KERNEL.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

The architecture now crosses an important boundary:

> The protocol specification becomes an executable state machine.

The protocol kernel should be deliberately small. It should not understand Rust semantics, Linux semantics, LLM reasoning, or scheduling policy. Its job is to answer one question:

> Given the current canonical state and a typed request, is this transition authorized and valid, and if so, what canonical events must be appended?

---

## Contents

- [518. Trust boundary](#518-trust-boundary)
- [519. Command ≠ Event](#519-command--event)
- [520. Canonical event envelope](#520-canonical-event-envelope)
- [521. Canonical IDs](#521-canonical-ids)
- [522. Transition algebra](#522-transition-algebra)
- [523. State model](#523-state-model)
- [524. Reducer](#524-reducer)
- [525. Transition specification](#525-transition-specification)
- [526. Atomicity](#526-atomicity)
- [527. Optimistic concurrency](#527-optimistic-concurrency)
- [528. Event-store protocol](#528-event-store-protocol)
- [529. Event hash chain](#529-event-hash-chain)
- [530. Rejection is structured](#530-rejection-is-structured)
- [531. Important distinction: rejected command vs failure event](#531-important-distinction-rejected-command-vs-failure-event)
- [532. Migration transition table](#532-migration-transition-table)
- [533. Verification transition is particularly strict](#533-verification-transition-is-particularly-strict)
- [534. Event-sourced projections](#534-event-sourced-projections)
- [535. Snapshotting](#535-snapshotting)
- [536. Protocol versioning](#536-protocol-versioning)
- [537. Event evolution](#537-event-evolution)
- [538. Protocol conformance suite](#538-protocol-conformance-suite)
- [539. Adversarial protocol tests](#539-adversarial-protocol-tests)
- [540. Minimal crate](#540-minimal-crate)
- [541. Minimal dependency direction](#541-minimal-dependency-direction)
- [542. First executable vertical slice](#542-first-executable-vertical-slice)
- [543. The first protocol theorem](#543-the-first-protocol-theorem)
- [544. The second theorem](#544-the-second-theorem)
- [545. The third theorem](#545-the-third-theorem)
- [546. Resulting architecture](#546-resulting-architecture)
- [547. Next artifact](#547-next-artifact)

---

## 518. Trust boundary
<!-- source: PROTOCOL-KERNEL.md §1 -->

```text
UNTRUSTED / PROPOSAL SIDE
┌─────────────────────────────────────────────────────────────┐
│ LLM agents                                                  │
│ analyzers                                                   │
│ designers                                                   │
│ implementers                                                │
│ verifiers                                                   │
│ scheduler                                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ Command
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    RFL PROTOCOL KERNEL                      │
│                                                             │
│  decode → validate → authorize → preconditions              │
│        → transition → invariant check → event construction  │
│                                                             │
└──────────────────────────┬──────────────────────────────────┘
                           │ Canonical Event(s)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  APPEND-ONLY EVENT STORE                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ replay
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    CANONICAL STATE                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ projections
             ┌─────────────┼──────────────┐
             ▼             ▼              ▼
        Migration      Agent/Lease    Evidence/Gate
         State           State           State
```

The critical property is:

```text
Agent → Protocol
        ↑
        │
   no direct state mutation
```

The scheduler therefore cannot bypass the protocol kernel.

---

## 519. Command ≠ Event
<!-- source: PROTOCOL-KERNEL.md §2 -->

This distinction should be normative.

### Command

A command is a request.

```rust
pub struct TransitionCommand {
    pub command_id: CommandId,
    pub actor: AgentId,
    pub task: TaskId,
    pub snapshot: KernelSnapshotId,
    pub epoch: Epoch,
    pub authorization: AuthorizationId,
    pub capability: CapabilityId,
    pub target: TargetRef,
    pub operation: Operation,
    pub expected_state: ExpectedState,
}
```

Examples:

```text
RequestContractEvidence
SubmitContract
AuthorizeImplementation
SubmitImplementation
RequestVerification
SubmitVerificationResult
AdvanceGate
QuarantineMigration
ResolveConflict
AdvanceEpoch
AcquireLease
ReleaseLease
```

### Event

An event records what the protocol accepted as having happened.

```rust
pub struct ProtocolEvent {
    pub event_id: EventId,
    pub sequence: Sequence,
    pub epoch: Epoch,

    pub command_id: CommandId,
    pub actor: AgentId,

    pub snapshot: KernelSnapshotId,
    pub target: TargetRef,

    pub kind: EventKind,

    pub state_before: Digest,
    pub state_after: Digest,

    pub payload: EventPayload,

    pub event_digest: Digest,
}
```

Therefore:

```text
COMMAND
  │
  │ validation
  ▼
ACCEPTED
  │
  ▼
EVENT
```

A rejected command does not become an event claiming the requested transition occurred.

---

## 520. Canonical event envelope
<!-- source: PROTOCOL-KERNEL.md §3 -->

Every protocol event should have the same envelope.

```rust
pub struct EventEnvelope {
    pub event_id: EventId,
    pub sequence: u64,

    pub protocol_version: ProtocolVersion,
    pub schema_version: SchemaVersion,

    pub epoch: Epoch,

    pub command_id: CommandId,
    pub actor: AgentId,

    pub snapshot: KernelSnapshotId,
    pub target: TargetRef,

    pub state_before: Digest,
    pub state_after: Digest,

    pub logical_time: LogicalTime,

    pub payload_digest: Digest,
    pub event_digest: Digest,
}
```

Why both state_before and state_after?

Because replay should be able to detect:

```text
event claims:
    state_before = A
    transition
    state_after  = B

actual replay:
    A → C
```

That is a protocol integrity failure.

It should not silently accept C.

---

## 521. Canonical IDs
<!-- source: PROTOCOL-KERNEL.md §4 -->

IDs should be opaque and typed.

```rust
pub struct TaskId(Uuid);
pub struct MigrationUnitId(Uuid);
pub struct AgentId(Uuid);
pub struct CapabilityId(Uuid);
pub struct AuthorizationId(Uuid);

pub struct CommandId(Uuid);
pub struct EventId(Uuid);
pub struct LeaseId(Uuid);

pub struct ArtifactId(Digest);
pub struct EvidenceId(Digest);
pub struct ContractId(Digest);
pub struct DesignId(Digest);
pub struct VerificationId(Digest);
pub struct CertificateId(Digest);

pub struct SnapshotId(Digest);
pub struct VariantId(Digest);
```

Do not use arbitrary strings throughout the protocol.

This prevents accidental substitution such as:

```text
ContractId ← ArtifactId
AgentId    ← MigrationUnitId
SnapshotId ← VariantId
```

The compiler should reject those mistakes.

---

## 522. Transition algebra
<!-- source: PROTOCOL-KERNEL.md §5 -->

The central protocol operation is:

```rust
pub fn apply(
    state: &ProtocolState,
    command: &TransitionCommand,
) -> Result<TransitionResult, ProtocolError>;
```

Where:

```rust
pub struct TransitionResult {
    pub events: Vec<ProtocolEvent>,
    pub new_state: ProtocolState,
}
```

But internally it should be conceptually:

```text
Apply(S, C)
    =
    if Validate(C) fails:
        Reject
    else if Authorize(S, C) fails:
        Reject
    else if Preconditions(S, C) fail:
        Reject
    else:
        E = Transition(S, C)
        S' = Reduce(S, E)
        Invariants(S') must hold
        Accept(E, S')
```

Formalized:

```text
Validate(C)
∧ Authorize(S,C)
∧ Preconditions(S,C)
∧ Invariants(Transition(S,C))
→ ACCEPT
```

Otherwise:

```text
→ REJECT
```

---

## 523. State model
<!-- source: PROTOCOL-KERNEL.md §6 -->

The protocol state should be explicit rather than reconstructed ad hoc by individual agents.

```rust
pub struct ProtocolState {
    pub protocol_version: ProtocolVersion,
    pub sequence: u64,
    pub epoch: Epoch,

    pub snapshot: KernelSnapshotId,

    pub tasks: Map<TaskId, TaskState>,
    pub migrations: Map<MigrationUnitId, MigrationState>,

    pub agents: Map<AgentId, AgentState>,
    pub capabilities: Map<CapabilityId, CapabilityState>,
    pub authorizations: Map<AuthorizationId, AuthorizationState>,

    pub leases: Map<LeaseId, LeaseState>,

    pub artifacts: Map<ArtifactId, ArtifactState>,
    pub evidence: Map<EvidenceId, EvidenceState>,

    pub gates: Map<GateId, GateState>,
    pub conflicts: Map<ConflictId, ConflictState>,

    pub event_head: Digest,
}
```

The state itself should be derived from events.

```text
Event 001 ─┐
Event 002  │
Event 003  ├── Reducer ──→ ProtocolState
Event 004  │
Event 005 ─┘
```

The event log is canonical.

The projection is derived.

---

## 524. Reducer
<!-- source: PROTOCOL-KERNEL.md §7 -->

The reducer must be deterministic.

```rust
pub fn reduce(
    state: &ProtocolState,
    event: &ProtocolEvent,
) -> Result<ProtocolState, ReduceError> {
    match &event.payload {
        EventPayload::MigrationDiscovered(e) =>
            migration_discovered(state, e),

        EventPayload::ContractSubmitted(e) =>
            contract_submitted(state, e),

        EventPayload::ImplementationAuthorized(e) =>
            implementation_authorized(state, e),

        EventPayload::ImplementationSubmitted(e) =>
            implementation_submitted(state, e),

        EventPayload::VerificationCompleted(e) =>
            verification_completed(state, e),

        EventPayload::GateEvaluated(e) =>
            gate_evaluated(state, e),

        EventPayload::MigrationQuarantined(e) =>
            migration_quarantined(state, e),

        // ...
    }
}
```

No LLM call belongs inside the reducer.

No wall-clock lookup.

No network request.

No filesystem inspection.

No randomness.

No scheduler decision.

That gives:

```text
same initial state
+
same event sequence
=
same final state
```

This becomes one of the strongest protocol properties.

---

## 525. Transition specification
<!-- source: PROTOCOL-KERNEL.md §8 -->

Instead of scattering rules through match statements, define transitions declaratively.

Example:

```rust
pub struct TransitionSpec {
    pub operation: Operation,

    pub allowed_states: &'static [MigrationStateKind],

    pub required_authority: AuthorityClass,

    pub required_capabilities: &'static [Capability],

    pub preconditions: &'static [Precondition],

    pub emitted_events: &'static [EventKind],

    pub resulting_states: &'static [MigrationStateKind],
}
```

Example:

```text
AUTHORIZED_FOR_IMPLEMENTATION
        │
        │ SubmitImplementation
        │
        ▼
IMPLEMENTED
```

Preconditions:

```text
P1 authorization exists
P2 authorization valid
P3 actor possesses implementation authority
P4 capability covers migration unit
P5 snapshot matches
P6 epoch matches
P7 implementation lease is held
P8 worktree is authorized
P9 required design artifact exists
P10 no blocking conflict
P11 no critical unknown
```

Failure of any one condition:

```text
SubmitImplementation
        ↓
REJECTED
```

No partial transition.

---

## 526. Atomicity
<!-- source: PROTOCOL-KERNEL.md §9 -->

A transition must be atomic from the protocol's perspective.

Bad:

```text
update migration state
        ↓
validate evidence
        ↓
discover authorization invalid
```

This leaves partial state.

Correct:

```text
load state
   ↓
validate
   ↓
authorize
   ↓
evaluate preconditions
   ↓
construct event
   ↓
validate resulting state
   ↓
append event
   ↓
publish new state
```

The event is the commit boundary.

---

## 527. Optimistic concurrency
<!-- source: PROTOCOL-KERNEL.md §10 -->

The protocol should use compare-and-swap semantics.

A command carries:

```rust
pub struct ExpectedState {
    pub sequence: u64,
    pub state_digest: Digest,
    pub epoch: Epoch,
}
```

Before committing:

```text
stored sequence == command.sequence
stored state digest == command.state_digest
stored epoch == command.epoch
```

If not:

```text
ConcurrentWriter
```

or:

```text
StaleEpoch
```

This prevents:

```text
Agent A reads state S
Agent B reads state S

Agent A → transition → S1
Agent B → transition based on S → invalid

Agent B must reload.
```

---

## 528. Event-store protocol
<!-- source: PROTOCOL-KERNEL.md §11 -->

Minimal interface:

```rust
pub trait EventStore {
    fn head(&self) -> Result<EventHead, StoreError>;

    fn append(
        &mut self,
        expected: EventHead,
        events: &[ProtocolEvent],
    ) -> Result<EventHead, StoreError>;

    fn read_from(
        &self,
        sequence: u64,
    ) -> Result<Vec<ProtocolEvent>, StoreError>;

    fn read_range(
        &self,
        start: u64,
        end: u64,
    ) -> Result<Vec<ProtocolEvent>, StoreError>;
}
```

The append operation must enforce:

```text
expected.sequence == actual.sequence
```

and:

```text
expected.digest == actual.head_digest
```

before accepting events.

This is the protocol's CAS boundary.

---

## 529. Event hash chain
<!-- source: PROTOCOL-KERNEL.md §12 -->

Events should form a cryptographic chain.

```text
E001
 │
 └─ digest D001
       │
       ▼
E002
 │
 └─ previous_digest = D001
       │
       ▼
E003
 │
 └─ previous_digest = D002
```

Envelope:

```rust
pub struct EventLink {
    pub previous_event: Option<EventId>,
    pub previous_digest: Option<Digest>,
}
```

This makes deletion/reordering detectable.

The event log therefore becomes:

```text
append-only
+
ordered
+
hash-linked
+
snapshot-bound
+
epoch-bound
```

---

## 530. Rejection is structured
<!-- source: PROTOCOL-KERNEL.md §13 -->

Do not represent protocol failures as strings.

```rust
pub enum ProtocolError {
    InvalidCommand(CommandError),
    Authorization(AuthorizationError),
    Capability(CapabilityError),
    Scope(ScopeError),
    Snapshot(SnapshotError),

    InvalidStateTransition {
        current: MigrationStateKind,
        requested: Operation,
    },

    MissingArtifact(ArtifactId),
    MissingEvidence(EvidenceId),

    CriticalUnknown(UnknownId),
    UnresolvedConflict(ConflictId),

    ConcurrentWriter {
        expected: Sequence,
        actual: Sequence,
    },

    StaleEpoch {
        expected: Epoch,
        actual: Epoch,
    },

    InvariantViolation(InvariantViolation),

    EventStore(StoreError),
}
```

This allows machine-readable handling:

```text
InvalidStateTransition
        → protocol bug / caller bug

MissingEvidence
        → evidence task

CriticalUnknown
        → investigation task

StaleEpoch
        → recompute / rebase

ConcurrentWriter
        → reload

CapabilityMissing
        → capability acquisition

ScopeViolation
        → reject permanently unless authorization changes
```

---

## 531. Important distinction: rejected command vs failure event
<!-- source: PROTOCOL-KERNEL.md §14 -->

A malformed or unauthorized command should not mutate canonical state.

For example:

```text
SubmitImplementation
    authorization expired
        ↓
ProtocolError::Authorization(...)
```

There is no:

```text
ImplementationSubmitted
```

However, an authorized execution that genuinely failed can produce an event:

```text
ImplementationExecutionFailed
```

Therefore:

```text
protocol rejection
≠
authorized operation failure
```

This distinction is essential for auditability.

---

## 532. Migration transition table
<!-- source: PROTOCOL-KERNEL.md §15 -->

The initial lifecycle can now become executable.

| Current | Command | Required condition | Result |
|---------|---------|--------------------|--------|
| DISCOVERED | MapMigration | scope + snapshot | MAPPED |
| MAPPED | SubmitContract | KSIR + evidence | CONTRACTED |
| CONTRACTED | SubmitDesign | contract complete | DESIGNED |
| DESIGNED | AuthorizeImplementation | design gates pass | AUTHORIZED_FOR_IMPLEMENTATION |
| AUTHORIZED_FOR_IMPLEMENTATION | SubmitImplementation | implementation lease | IMPLEMENTED |
| IMPLEMENTED | AuthorizeTesting | verification plan exists | AUTHORIZED_FOR_TESTING |
| AUTHORIZED_FOR_TESTING | SubmitVerification | valid execution evidence | VERIFIED / PARTIALLY_VERIFIED |
| VERIFIED | RequestAdversarialReview | verification complete | ADVERSARIALLY_VERIFIED |
| ADVERSARIALLY_VERIFIED | AuthorizeReview | release conditions | AUTHORIZED_FOR_REVIEW |
| AUTHORIZED_FOR_REVIEW | ApproveRelease | independent review | RELEASE_ELIGIBLE |
| RELEASE_ELIGIBLE | Release | release authority | RELEASED |

Every row becomes a protocol rule.

No agent can simply assign:

```text
state = VERIFIED
```

---

## 533. Verification transition is particularly strict
<!-- source: PROTOCOL-KERNEL.md §16 -->

A verification result should require:

```text
VerificationObligation exists
        AND
ExecutionReceipt exists
        AND
Receipt is valid
        AND
Artifact digests match
        AND
Snapshot matches
        AND
Variant matches
        AND
Oracle is valid
        AND
Evidence scope covers obligation
        AND
No blocking unknown
        AND
No unresolved critical conflict
        AND
independence requirements satisfied
```

Only then can the protocol accept:

```text
VerificationCompleted
```

This directly enforces:

> Execution receipt ≠ semantic proof.

And:

> NO EVIDENCE → NO VERIFIED CLAIM.

---

## 534. Event-sourced projections
<!-- source: PROTOCOL-KERNEL.md §17 -->

Do not make every consumer replay the entire log.

Create deterministic projections:

```text
Event Store
    │
    ├── MigrationProjection
    ├── AgentProjection
    ├── LeaseProjection
    ├── EvidenceProjection
    ├── ConflictProjection
    ├── GateProjection
    └── AuthorizationProjection
```

But:

```text
Projection ≠ authority
```

If a projection is corrupted:

```text
event log
   ↓
rebuild projection
```

The projection can always be reconstructed.

---

## 535. Snapshotting
<!-- source: PROTOCOL-KERNEL.md §18 -->

Large event histories eventually need snapshots.

```rust
pub struct StateSnapshot {
    pub snapshot_id: SnapshotStateId,
    pub sequence: u64,
    pub epoch: Epoch,
    pub state_digest: Digest,
    pub state: ProtocolState,
    pub created_from_event: EventId,
}
```

Replay becomes:

```text
Snapshot @ sequence 10,000
        +
Events 10,001..10,500
        ↓
Current State
```

But snapshotting must never alter semantics.

Test:

```text
replay(all events)
==
replay(snapshot + remaining events)
```

This should be a conformance property.

---

## 536. Protocol versioning
<!-- source: PROTOCOL-KERNEL.md §19 -->

There are at least three distinct versions:

```text
ProtocolVersion
SchemaVersion
ArtifactVersion
```

Do not collapse them.

### ProtocolVersion

Transition semantics.

### SchemaVersion

Serialization shape.

### ArtifactVersion

Individual artifact representation.

A schema migration must not silently change protocol semantics.

---

## 537. Event evolution
<!-- source: PROTOCOL-KERNEL.md §20 -->

Never mutate historical events.

Bad:

```text
Event V1
    ↓
rewrite as V2
```

Correct:

```text
historical V1 remains immutable

V1
 │
 ▼
upcaster
 │
 ▼
canonical current representation
```

Or explicitly:

```text
EventV1
EventV2
EventV3
```

with deterministic compatibility logic.

Historical evidence must remain reconstructible.

---

## 538. Protocol conformance suite
<!-- source: PROTOCOL-KERNEL.md §21 -->

The protocol itself now needs a QA corpus.

```text
tests/protocol/
├── transition/
│   ├── legal.rs
│   ├── illegal.rs
│   └── exhaustive.rs
├── authorization/
├── scope/
├── snapshot/
├── epoch/
├── leases/
├── event_store/
├── replay/
├── projection/
├── versioning/
├── invariants/
├── quarantine/
└── adversarial/
```

### Core tests

```text
PROTO-001  Same command + same state → same transition result.
PROTO-002  Illegal transition always rejected.
PROTO-003  Missing authorization always rejected.
PROTO-004  Expired authorization rejected.
PROTO-005  Snapshot mismatch rejected.
PROTO-006  Epoch mismatch rejected.
PROTO-007  Concurrent writer rejected.
PROTO-008  Event replay reproduces state exactly.
PROTO-009  Snapshot + replay equals full replay.
PROTO-010  Event mutation detected.
PROTO-011  Event reordering detected.
PROTO-012  Projection rebuild equals live projection.
PROTO-013  Implementation authority cannot perform verification transition.
PROTO-014  Scheduler cannot create release authority.
PROTO-015  Critical unknown prevents prohibited transitions.
PROTO-016  Critical conflict prevents prohibited transitions.
PROTO-017  Invalidated evidence cannot satisfy a gate.
PROTO-018  Stale artifacts cannot mutate current canonical state.
PROTO-019  Duplicate command handling is deterministic.
PROTO-020  Replay contains no nondeterministic dependencies.
```

---

## 539. Adversarial protocol tests
<!-- source: PROTOCOL-KERNEL.md §22 -->

The protocol kernel should be attacked independently of the agents.

```text
ATTACK-001  forge AuthorizationId
ATTACK-002  replace snapshot ID
ATTACK-003  reuse expired authorization
ATTACK-004  change command after authorization
ATTACK-005  change executable identity
ATTACK-006  submit event with fabricated state_before
ATTACK-007  submit event with fabricated state_after
ATTACK-008  remove an intermediate event
ATTACK-009  reorder events
ATTACK-010  duplicate an event
ATTACK-011  reuse stale epoch
ATTACK-012  race two implementation writers
ATTACK-013  implementation agent submits verification
ATTACK-014  scheduler submits release authorization
ATTACK-015  invalidated evidence used by gate
ATTACK-016  critical UNKNOWN hidden from transition
ATTACK-017  conflict marked resolved without evidence
ATTACK-018  projection manipulated while event log remains unchanged
ATTACK-019  snapshot restored from incompatible protocol version
ATTACK-020  event payload modified without digest change
```

The protocol should fail closed.

---

## 540. Minimal crate
<!-- source: PROTOCOL-KERNEL.md §23 -->

The first implementation should remain intentionally small:

```text
crates/rfl-protocol/
├── src/
│   ├── lib.rs
│   │
│   ├── id.rs
│   ├── version.rs
│   ├── epoch.rs
│   ├── sequence.rs
│   ├── digest.rs
│   │
│   ├── command.rs
│   ├── operation.rs
│   ├── event.rs
│   ├── payload.rs
│   │
│   ├── state.rs
│   ├── migration.rs
│   ├── authorization.rs
│   ├── capability.rs
│   ├── lease.rs
│   │
│   ├── transition.rs
│   ├── precondition.rs
│   ├── invariant.rs
│   ├── error.rs
│   │
│   ├── reducer.rs
│   ├── replay.rs
│   ├── projection.rs
│   │
│   ├── store.rs
│   └── validation.rs
│
├── tests/
│   ├── transitions.rs
│   ├── replay.rs
│   ├── concurrency.rs
│   ├── authorization.rs
│   ├── adversarial.rs
│   └── conformance.rs
│
└── Cargo.toml
```

Keep orchestration, KSIR, contract inference, and LLM integration outside this crate.

That is important.

---

## 541. Minimal dependency direction
<!-- source: PROTOCOL-KERNEL.md §24 -->

```text
rfl-types
    │
    ▼
rfl-protocol
    │
    ├───────────────┐
    ▼               ▼
rfl-execution   rfl-evidence
    │               │
    └───────┬───────┘
            ▼
         rfl-gates
            │
            ▼
      rfl-orchestration
```

Not:

```text
rfl-protocol
    ↓
LLM
    ↓
scheduler
    ↓
protocol
```

That would create authority recursion.

---

## 542. First executable vertical slice
<!-- source: PROTOCOL-KERNEL.md §25 -->

Do not implement the entire protocol at once.

Implement exactly this:

```text
CREATE TASK
    ↓
DISCOVER MIGRATION
    ↓
MAP MIGRATION
    ↓
SUBMIT CONTRACT
    ↓
CONTRACTED
```

With:

```text
command
  ↓
validation
  ↓
authorization
  ↓
preconditions
  ↓
event
  ↓
append
  ↓
reduce
  ↓
state digest
```

Then replay:

```text
event log
   ↓
fresh state
   ↓
replay
   ↓
same state digest
```

Only after that passes should implementation authorization be added.

---

## 543. The first protocol theorem
<!-- source: PROTOCOL-KERNEL.md §26 -->

The first important executable invariant should be:

> For a valid initial state and deterministic event sequence, protocol replay produces exactly one canonical state.

Formally:

```text
Replay(E) = S
```

and for any deterministic implementation of the reducer:

```text
Replay(E) = Replay(E)
```

More usefully:

```text
Reduce(S₀, E₁...Eₙ) = Sₙ
```

and:

```text
Digest(Sₙ)
```

must be stable.

This becomes the foundation for everything above it.

---

## 544. The second theorem
<!-- source: PROTOCOL-KERNEL.md §27 -->

Authorization cannot be manufactured by transition.

```text
Authorization ∉ State
        ↓
cannot perform protected transition
```

And:

```text
Capability ≠ Authorization
```

A capable agent without authorization remains unauthorized.

An authorized agent without the required capability remains ineligible.

Neither can be inferred from the other.

---

## 545. The third theorem
<!-- source: PROTOCOL-KERNEL.md §28 -->

Scheduler output is advisory until accepted by protocol.

```text
Scheduler
    │
    │ Assignment proposal
    ▼
Protocol
    │
    ├── accepted
    │      ↓
    │   Assignment event
    │
    └── rejected
```

Therefore:

```text
scheduler state
    ≠
canonical protocol state
```

This prevents the orchestration layer from becoming a hidden authority layer.

---

## 546. Resulting architecture
<!-- source: PROTOCOL-KERNEL.md §29 -->

The system now has a clean vertical boundary:

```text
RFL-AE
                       │
       ┌───────────────┴────────────────┐
       │                                │
 Semantic World                    Protocol World
       │                                │
       ▼                                ▼
      KSIR                         Commands
       │                                │
       ▼                                ▼
   Contracts                      Authorization
       │                                │
       ▼                                ▼
 Rust Design IR                  Preconditions
       │                                │
       ▼                                ▼
 Implementation ───────────────→ Protocol Events
                                        │
                                        ▼
                                  Event Store
                                        │
                                        ▼
                                  Canonical State
                                        │
                    ┌───────────────────┼─────────────────┐
                    ▼                   ▼                 ▼
                Evidence             Gates           Orchestration
```

The crucial separation is now:

```text
SEMANTIC AUTHORITY
    KSIR / Contract / Verification

PROTOCOL AUTHORITY
    State machine / Event log

EXECUTION AUTHORITY
    Execution runtime / CI

SCHEDULING AUTHORITY
    Scheduler only allocates authorized work

RELEASE AUTHORITY
    Release gate / review
```

No layer silently inherits authority from another.

---

## 547. Next artifact
<!-- source: PROTOCOL-KERNEL.md §30 -->

The next step should be implementation of the protocol kernel, not another conceptual abstraction:

```text
RFL-AE-PROTOCOL-001
        │
        ├── canonical typed IDs
        ├── Command / Event model
        ├── ProtocolState
        ├── transition algebra
        ├── authorization validator
        ├── deterministic reducer
        ├── append-only in-memory EventStore
        ├── replay engine
        ├── state/event hashing
        ├── CAS concurrency protection
        ├── transition conformance tests
        └── adversarial protocol tests
```

Once that executable kernel is green, KSIR should attach to it as a producer of typed semantic artifacts, rather than defining its own lifecycle or authority rules.

---

**Done — see [PROTOCOL-IMPL.md](PROTOCOL-IMPL.md)** (§548–§575, source §§1–§28), which turns the
protocol kernel into a concrete API and transition implementation: the repository skeleton,
`rfl-types` with the `typed_id!` macro so `TaskId != AgentId` even though both are UUIDs, the
`Digest` type and explicit `DigestAlgorithm`, snapshot identity where the immutable digest is
authoritative rather than `source_version`, `MigrationState`, `Operation`, `TransitionCommand`
and the `ExpectedState` optimistic-concurrency contract, explicit `Authorization` and
`AuthorityClass`, capability kept separate from authorization, `ProtocolState` over `BTreeMap`
for deterministic hashing, `MigrationRecord` with no confidence score, the `TransitionEngine`
and its validation ordering, `TransitionPlan`, `ProtocolEvent` and `EventKind`, the deliberately
boring reducer and the operations it must never perform, the in-memory `EventStore` and its CAS
append, `replay` with `state_before`/`state_after` divergence detection, the first lifecycle,
illegal-transition, authorization, epoch-invalidation and tamper tests, the `PROTO-GATE-001`
checklist, the frozen crate dependency boundary, the resulting hierarchy in which agents become
clients of the protocol, and the P0–P10 implementation progression. Same provenance convention
as `VERIFICATION.md`.
