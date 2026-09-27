# RFL-AE — Orchestration IR + Deterministic Scheduler

> **Provenance and numbering.** This document was supplied as *RFL-AE — Orchestration IR + Deterministic Scheduler v0.1*, numbered §1–§55 in the source. To keep the corpus contiguous, its sections are renumbered **§463–§517**, continuing directly from [EXECUTION.md](EXECUTION.md) (which ends at §462). The mapping is **`corpus_section = source_section + 462`**. The original source numbering is preserved on every heading as a machine-readable HTML comment of the form `<!-- source: ORCHESTRATION.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

The scheduler should be treated as a **protocol executor**, not an intelligent project manager.

Its job is:

```text
select work
  ↓
acquire authority
  ↓
dispatch bounded work
  ↓
collect artifacts
  ↓
advance protocol state
  ↓
recover failures
  ↓
invalidate stale work
  ↓
schedule independent verification
```

It must never decide:

```text
"the Rust version is probably equivalent"
```

That belongs to the contract/verification system.

---

## Contents

- [463. Orchestration architecture](#463-orchestration-architecture)
- [464. Orchestration IR](#464-orchestration-ir)
- [465. Migration graph](#465-migration-graph)
- [466. Why source dependency is insufficient](#466-why-source-dependency-is-insufficient)
- [467. Migration-unit readiness](#467-migration-unit-readiness)
- [468. Scheduling is a state transition](#468-scheduling-is-a-state-transition)
- [469. Agent model](#469-agent-model)
- [470. Capability is not competence](#470-capability-is-not-competence)
- [471. Agent capability matching](#471-agent-capability-matching)
- [472. Authority matching](#472-authority-matching)
- [473. Work leases](#473-work-leases)
- [474. Lease ownership](#474-lease-ownership)
- [475. Worktree leases](#475-worktree-leases)
- [476. Epochs](#476-epochs)
- [477. Stale work](#477-stale-work)
- [478. Deterministic scheduler](#478-deterministic-scheduler)
- [479. Scheduling key](#479-scheduling-key)
- [480. Fairness](#480-fairness)
- [481. Dependency-aware scheduling](#481-dependency-aware-scheduling)
- [482. Critical-path scheduling](#482-critical-path-scheduling)
- [483. Event-driven scheduler](#483-event-driven-scheduler)
- [484. Scheduler state](#484-scheduler-state)
- [485. Scheduler transition](#485-scheduler-transition)
- [486. Assignment artifact](#486-assignment-artifact)
- [487. Agent crash recovery](#487-agent-crash-recovery)
- [488. Crash recovery states](#488-crash-recovery-states)
- [489. Idempotency](#489-idempotency)
- [490. Exactly-once versus at-least-once](#490-exactly-once-versus-at-least-once)
- [491. Duplicate execution](#491-duplicate-execution)
- [492. Quarantine](#492-quarantine)
- [493. Quarantine record](#493-quarantine-record)
- [494. Quarantine recovery](#494-quarantine-recovery)
- [495. Conflict resolution](#495-conflict-resolution)
- [496. Scheduler and unknowns](#496-scheduler-and-unknowns)
- [497. Automatic evidence tasks](#497-automatic-evidence-tasks)
- [498. Orchestration state machine](#498-orchestration-state-machine)
- [499. Orchestration is not workflow scripting](#499-orchestration-is-not-workflow-scripting)
- [500. Deterministic replay](#500-deterministic-replay)
- [501. Logical time](#501-logical-time)
- [502. Scheduler event log](#502-scheduler-event-log)
- [503. Restart recovery](#503-restart-recovery)
- [504. External reconciliation](#504-external-reconciliation)
- [505. Resource scheduler](#505-resource-scheduler)
- [506. Resource starvation](#506-resource-starvation)
- [507. Cancellation](#507-cancellation)
- [508. Priority inversion](#508-priority-inversion)
- [509. Multi-agent verification topology](#509-multi-agent-verification-topology)
- [510. No self-verification](#510-no-self-verification)
- [511. Orchestration policy](#511-orchestration-policy)
- [512. Scheduler acceptance criteria](#512-scheduler-acceptance-criteria)
- [513. Scheduler crate architecture](#513-scheduler-crate-architecture)
- [514. Complete system now](#514-complete-system-now)
- [515. The resulting authority model](#515-the-resulting-authority-model)
- [516. Final invariant set](#516-final-invariant-set)
- [517. What remains](#517-what-remains)

---

## 463. Orchestration architecture
<!-- source: ORCHESTRATION.md §1 -->

```text
                         Migration Graph
                                │
                                ▼
                        Orchestration IR
                                │
                                ▼
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
          Dependency       Capability         Policy
             State          Matching           Rules
               │                │                │
               └────────────────┼────────────────┘
                                │
                                ▼
                     Deterministic Scheduler
                                │
                                ▼
                      ┌─────────┼─────────┐
                      ▼         ▼         ▼
                   Agent A   Agent B   Agent C
                      │         │         │
                      ▼         ▼         ▼
                  Worktree  Worktree  Read-only
                      │         │         │
                      └─────────┼─────────┘
                                │
                                ▼
                         Protocol Events
                                │
                                ▼
                          State Machine
                                │
                                ▼
                  ┌─────────────┼─────────────┐
                  ▼             ▼             ▼
              Progress     Quarantine     Recovery
```

The scheduler observes protocol state; it does not replace the protocol.

---

## 464. Orchestration IR
<!-- source: ORCHESTRATION.md §2 -->

Define the scheduling problem explicitly.

```rust
struct OrchestrationPlan {
    orchestration_id: OrchestrationId,
    snapshot: KernelSnapshotId,
    migration_units: Vec<MigrationUnitId>,
    dependency_graph: DependencyGraph,
    capability_requirements: Vec<CapabilityRequirement>,
    scheduling_policy: SchedulingPolicy,
    resource_policy: ResourcePolicy,
    verification_policy: VerificationPolicy,
    recovery_policy: RecoveryPolicy,
    epoch: Epoch,
    status: OrchestrationStatus,
}
```

The plan is itself versioned and snapshot-bound.

---

## 465. Migration graph
<!-- source: ORCHESTRATION.md §3 -->

The source tree dependency graph is insufficient.

We need a semantic migration graph:

```text
MU-001
  │
  ├── requires contract from MU-004
  └── shares ABI with MU-007

MU-004
  │
  └── requires KSIR facts from MU-002

MU-007
  │
  └── requires architecture analysis
```

Represent these separately:

```rust
enum MigrationDependency {
    SourceDependency,
    SemanticDependency,
    ContractDependency,
    AbiDependency,
    VerificationDependency,
    EvidenceDependency,
    ArchitectureDependency,
    ConfigurationDependency,
}
```

---

## 466. Why source dependency is insufficient
<!-- source: ORCHESTRATION.md §4 -->

Suppose:

```text
foo.c
bar.c
```

have no direct source dependency.

But both manipulate:

```rust
struct foo_state
```

protected by:

```text
foo->lock
```

Migrating `foo.c` without understanding `bar.c` could invalidate the reconstructed concurrency contract.

Therefore:

```text
source graph ≠ semantic graph
```

The scheduler must consume both.

---

## 467. Migration-unit readiness
<!-- source: ORCHESTRATION.md §5 -->

A migration unit should not be scheduled merely because an agent is available.

Define:

```rust
enum Readiness {
    Ready,
    WaitingDependency,
    WaitingEvidence,
    WaitingAuthorization,
    WaitingCapability,
    Blocked,
    Quarantined,
    Stale,
}
```

And:

```rust
struct ReadinessReport {
    migration_unit: MigrationUnitId,
    state: MigrationState,
    dependencies: DependencyStatus,
    authorization: AuthorizationStatus,
    required_capabilities: Vec<CapabilityId>,
    missing_evidence: Vec<EvidenceId>,
    blockers: Vec<BlockerId>,
    readiness: Readiness,
}
```

---

## 468. Scheduling is a state transition
<!-- source: ORCHESTRATION.md §6 -->

The scheduler does not directly modify:

```text
migration_state = IMPLEMENTED
```

Instead:

```text
Scheduler
  ↓
Transition Request
  ↓
Protocol Validator
  ↓
Canonical Event
  ↓
State Projection
```

This preserves the earlier authority model.

```text
scheduler ≠ state authority
```

The protocol remains authoritative.

---

## 469. Agent model
<!-- source: ORCHESTRATION.md §7 -->

Agents need explicit identities and capabilities.

```rust
struct AgentDescriptor {
    agent_id: AgentId,
    agent_class: AgentClass,
    capabilities: Vec<Capability>,
    authority: AuthorityClass,
    supported_artifacts: Vec<ArtifactType>,
    supported_architectures: Vec<ArchitectureId>,
    supported_tools: Vec<ToolId>,
    concurrency_limit: usize,
    epoch: Epoch,
}
```

Agent classes might include:

```text
CAnalyzer
KernelHistorian
ContractAnalyst
RustDesigner
RustImplementer
Verifier
ConcurrencyVerifier
AdversarialVerifier
ABIVerifier
EvidenceAuditor
Reviewer
```

---

## 470. Capability is not competence
<!-- source: ORCHESTRATION.md §8 -->

Do not encode:

```text
Agent A = "expert"
```

Instead encode demonstrable capabilities:

```text
can:
    analyze RCU
    inspect sparse output
    construct contract IR
    execute KCSAN
    verify ABI
```

And evidence:

```rust
struct CapabilityEvidence {
    capability: CapabilityId,
    demonstrated_by: Vec<ArtifactId>,
    validity_scope: ValidityDomain,
    status: CapabilityStatus,
}
```

Capability status:

```text
UNKNOWN
REQUESTED
DEMONSTRATED
EXPIRED
REVOKED
```

This connects the scheduler to the RFL-QA philosophy.

---

## 471. Agent capability matching
<!-- source: ORCHESTRATION.md §9 -->

A task declares:

```rust
struct CapabilityRequirement {
    capability: CapabilityId,
    minimum_status: CapabilityStatus,
    architecture: Option<ArchitectureId>,
    required_tools: Vec<ToolId>,
}
```

The scheduler computes:

```text
required capabilities
    ∩
available demonstrated capabilities
```

If empty:

```text
WAITING_CAPABILITY
```

not:

```text
assign_any_agent()
```

---

## 472. Authority matching
<!-- source: ORCHESTRATION.md §10 -->

Capability alone is insufficient.

Example:

```text
RustImplementer
```

may have:

```text
RCU analysis capability
```

but cannot be assigned:

```text
VERIFICATION AUTHORITY
```

because authority is a separate dimension.

```rust
struct AssignmentEligibility {
    capability_satisfied: bool,
    authority_satisfied: bool,
    scope_satisfied: bool,
    epoch_current: bool,
    lease_available: bool,
}
```

All must hold.

---

## 473. Work leases
<!-- source: ORCHESTRATION.md §11 -->

Concurrent agents require leases.

```rust
struct WorkLease {
    lease_id: LeaseId,
    migration_unit: MigrationUnitId,
    agent: AgentId,
    worktree: WorktreeId,
    epoch: Epoch,
    acquired_at: Timestamp,
    expires_at: Timestamp,
    renewable: bool,
}
```

Invariant:

```text
one authoritative writer per migration unit per epoch
```

Read-only analysis can remain parallel.

---

## 474. Lease ownership
<!-- source: ORCHESTRATION.md §12 -->

```text
                     MU-004821
                         │
               ┌─────────┴─────────┐
               │                   │
         Writer lease        Reader leases
               │                   │
            Agent A           Agent B  Agent C  Agent D
```

Only one may possess:

```text
WRITE
```

but many may possess:

```text
READ
```

This avoids unnecessary serialization.

---

## 475. Worktree leases
<!-- source: ORCHESTRATION.md §13 -->

A worktree is itself a resource.

```rust
struct WorktreeLease {
    worktree_id: WorktreeId,
    repository: RepositoryId,
    branch: BranchIdentity,
    migration_unit: MigrationUnitId,
    owner: AgentId,
    epoch: Epoch,
    status: WorktreeStatus,
}
```

No two writers can silently share a mutable worktree.

---

## 476. Epochs
<!-- source: ORCHESTRATION.md §14 -->

Epochs solve stale-agent problems.

```text
Epoch 17
   │
   ├── Agent A working
   ├── Agent B verifying
   └── Agent C analyzing

Contract changes
   │
   ▼
Epoch 18
   │
   ├── A's design → STALE
   ├── B's verification → STALE
   └── C's historical evidence → maybe VALID
```

Not every artifact becomes invalid.

Invalidation follows dependency edges.

---

## 477. Stale work
<!-- source: ORCHESTRATION.md §15 -->

An agent might finish after its lease has expired.

Its result must not automatically enter canonical state.

```text
Agent result
          │
          ▼
     epoch check
          │
   ┌──────┴──────┐
   │             │
current        stale
   │             │
   ▼             ▼
accept      quarantine
```

The stale artifact can still be retained as historical evidence.

It simply cannot mutate current canonical state.

---

## 478. Deterministic scheduler
<!-- source: ORCHESTRATION.md §16 -->

The scheduler should not rely on:

```text
thread completion order
network timing
LLM preference
random selection
```

for authoritative scheduling decisions.

Given:

```text
same orchestration state
same agent inventory
same leases
same dependencies
same policy
```

the selected assignment should be deterministic.

---

## 479. Scheduling key
<!-- source: ORCHESTRATION.md §17 -->

A deterministic key might be:

```text
(priority_class,
 dependency_depth,
 readiness_epoch,
 migration_unit_id)
```

But do not create a hidden correctness score.

Scheduling priority is operational, not semantic.

Example:

```rust
enum SchedulingPriority {
    BlockingDependency,
    ReleaseCriticalPath,
    VerificationUnblock,
    Normal,
    Background,
}
```

These are categories, not quality rankings.

---

## 480. Fairness
<!-- source: ORCHESTRATION.md §18 -->

A scheduler must prevent:

```text
large subsystem
    → consumes every worker
    → small subsystem starves forever
```

Use explicit quotas:

```rust
struct SchedulingQuota {
    subsystem: SubsystemId,
    max_concurrent_writers: usize,
    max_concurrent_verifiers: usize,
}
```

Fairness is a resource-management property.

It must not affect verification status.

---

## 481. Dependency-aware scheduling
<!-- source: ORCHESTRATION.md §19 -->

Suppose:

```text
MU-A → MU-B → MU-C
```

Then:

```text
A
↓ contract verified
↓
B
↓ design verified
↓
C
```

But independent:

```text
MU-D    MU-E    MU-F
```

can proceed concurrently.

The scheduler should exploit parallelism only where semantic dependencies permit it.

---

## 482. Critical-path scheduling
<!-- source: ORCHESTRATION.md §20 -->

A useful operational property:

```text
dependency graph
  ↓
topological analysis
  ↓
identify blockers
  ↓
dispatch work that unlocks downstream units
```

This is not a correctness ranking.

It is simply:

```text
which authorized task currently prevents other authorized tasks from becoming runnable?
```

---

## 483. Event-driven scheduler
<!-- source: ORCHESTRATION.md §21 -->

Avoid polling whenever possible.

Events:

```rust
enum OrchestrationEvent {
    UnitDiscovered,
    AnalysisCompleted,
    ContractChanged,
    DesignCompleted,
    ImplementationCompleted,
    VerificationCompleted,
    GateFailed,
    DependencyResolved,
    DependencyInvalidated,
    LeaseAcquired,
    LeaseExpired,
    AgentRegistered,
    AgentLost,
    ArtifactPublished,
    ConflictRaised,
    EpochAdvanced,
}
```

Each event produces a deterministic state transition.

---

## 484. Scheduler state
<!-- source: ORCHESTRATION.md §22 -->

```rust
struct SchedulerState {
    orchestration: OrchestrationId,
    epoch: Epoch,
    units: Map<MigrationUnitId, UnitRuntimeState>,
    agents: Map<AgentId, AgentRuntimeState>,
    leases: Map<LeaseId, WorkLease>,
    worktrees: Map<WorktreeId, WorktreeLease>,
    pending_events: Vec<OrchestrationEvent>,
    assignments: Vec<Assignment>,
    failures: Vec<FailureRecord>,
}
```

---

## 485. Scheduler transition
<!-- source: ORCHESTRATION.md §23 -->

```text
Event
  ↓
Validate epoch
  ↓
Update dependency state
  ↓
Recalculate readiness
  ↓
Find eligible agents
  ↓
Acquire lease
  ↓
Create assignment
  ↓
Emit canonical event
```

The scheduler should never perform an implicit transition.

---

## 486. Assignment artifact
<!-- source: ORCHESTRATION.md §24 -->

Every assignment becomes an immutable record.

```rust
struct Assignment {
    assignment_id: AssignmentId,
    migration_unit: MigrationUnitId,
    agent: AgentId,
    authority: AuthorityClass,
    capability_requirements: Vec<CapabilityRequirement>,
    lease: LeaseId,
    worktree: Option<WorktreeId>,
    input_artifacts: Vec<ArtifactId>,
    epoch: Epoch,
    created_at: Timestamp,
}
```

This answers:

> Why did agent X work on migration unit Y?

without relying on logs.

---

## 487. Agent crash recovery
<!-- source: ORCHESTRATION.md §25 -->

Suppose:

```text
Agent A
  lease MU-42
  executing
```

and disappears.

The scheduler must not immediately assume:

```text
implementation failed
```

Instead:

```text
AGENT_LOST
  ↓
lease enters recovery grace period
  ↓
execution status inspected
  ↓
receipt/artifacts recovered
  ↓
resume / retry / quarantine
```

---

## 488. Crash recovery states
<!-- source: ORCHESTRATION.md §26 -->

```rust
enum RecoveryState {
    Running,
    SuspectedLost,
    Recovering,
    Resumable,
    Retryable,
    Quarantined,
    Reconciled,
}
```

This avoids duplicate writes.

---

## 489. Idempotency
<!-- source: ORCHESTRATION.md §27 -->

Every operation requiring external side effects receives an idempotency key.

```text
assignment_id + operation_id + epoch
```

If an agent retries:

```text
same operation
```

the runtime can recognize:

```text
already executed
```

rather than duplicating the side effect.

---

## 490. Exactly-once versus at-least-once
<!-- source: ORCHESTRATION.md §28 -->

Do not promise exactly-once execution unless the infrastructure can actually provide it.

The scheduler can safely provide:

```text
at-least-once dispatch + idempotent protocol transitions + deduplicated evidence
```

This is much more realistic.

For example:

```text
test executes twice
```

may produce two execution receipts:

```text
EX-101
EX-102
```

but only one canonical transition.

---

## 491. Duplicate execution
<!-- source: ORCHESTRATION.md §29 -->

Duplicate execution is not automatically bad.

It can provide independent evidence.

```text
    Agent A             Agent B
       ↓                   ↓
  Toolchain X         Toolchain Y
       ↓                   ↓
  Evidence E1         Evidence E2
```

If they independently establish the same proposition:

```text
cross-validation
```

becomes possible.

But the scheduler must not call duplication "independence" unless the evidence actually differs in producer/method/tool as required.

---

## 492. Quarantine
<!-- source: ORCHESTRATION.md §30 -->

Quarantine is a first-class scheduler state.

```text
NORMAL
  │
  ├── conflict
  ├── critical unknown
  ├── stale epoch
  ├── ABI mismatch
  ├── unexplained race
  └── evidence corruption
  │
  ▼
QUARANTINE
```

A quarantined unit is removed from normal scheduling.

No agent can silently bypass it.

---

## 493. Quarantine record
<!-- source: ORCHESTRATION.md §31 -->

```rust
struct QuarantineRecord {
    quarantine_id: QuarantineId,
    migration_unit: MigrationUnitId,
    epoch: Epoch,
    trigger: QuarantineTrigger,
    evidence: Vec<EvidenceId>,
    blocking_unknowns: Vec<UnknownId>,
    conflicts: Vec<ConflictId>,
    required_resolution: ResolutionRequirement,
    created_at: Timestamp,
}
```

Possible triggers:

```text
ContractConflict
LifetimeUnknown
ConcurrencyConflict
AbiMismatch
StaleArtifact
EvidenceInvalid
ToolFailure
UnauthorizedMutation
ScopeViolation
```

---

## 494. Quarantine recovery
<!-- source: ORCHESTRATION.md §32 -->

Recovery must itself be governed.

```text
QUARANTINED
  ↓
Resolution Task
  ↓
Independent Analysis
  ↓
Evidence
  ↓
Conflict Resolution
  ↓
New Epoch
  ↓
Re-evaluate
```

Never:

```text
quarantine → manual flag flip → continue
```

---

## 495. Conflict resolution
<!-- source: ORCHESTRATION.md §33 -->

The system must not vote.

If agents disagree:

```text
Agent A:
    lock L protects X

Agent B:
    lock L does not protect X
```

the scheduler creates:

```text
Conflict C-77
```

Then schedules:

```text
Conflict Investigation
```

Required output:

```text
evidence
```

not:

```text
majority vote
```

---

## 496. Scheduler and unknowns
<!-- source: ORCHESTRATION.md §34 -->

Unknowns become scheduling dependencies.

Example:

```text
MU-A
  requires:
    ownership of X

ownership X = UNKNOWN
```

Then:

```text
MU-A = WAITING_EVIDENCE
```

Scheduler searches for an analysis capable of resolving:

```text
Ownership(X)
```

rather than assigning an implementation agent anyway.

---

## 497. Automatic evidence tasks
<!-- source: ORCHESTRATION.md §35 -->

This gives the scheduler a useful capability:

```text
blocking unknown
  ↓
capability resolver
  ↓
analysis task
  ↓
evidence
  ↓
unknown resolution
  ↓
dependent task becomes READY
```

Example:

```text
UNKNOWN:
    "Does callback C outlive object X?"
         ↓
schedule:
    CallbackLifecycleAnalysis
         ↓
evidence:
         ↓
Contract update
         ↓
Rust design becomes schedulable
```

---

## 498. Orchestration state machine
<!-- source: ORCHESTRATION.md §36 -->

```text
DISCOVERED
    │
    ▼
PLANNED
    │
    ▼
DEPENDENCIES_RESOLVED
    │
    ▼
READY
    │
    ▼
LEASED
    │
    ▼
EXECUTING
    │
    ├── FAILED → RECOVERY
    │
    ├── CONFLICT → QUARANTINE
    │
    ├── STALE → REPLAN
    │
    ▼
RESULT_AVAILABLE
    │
    ▼
PROTOCOL_TRANSITION
    │
    ▼
NEXT_STATE
```

---

## 499. Orchestration is not workflow scripting
<!-- source: ORCHESTRATION.md §37 -->

Avoid encoding:

```text
if agent says X:
    run Y
```

The scheduler should operate on typed facts:

```text
MigrationState
DependencyState
CapabilityState
EvidenceState
AuthorizationState
LeaseState
Epoch
```

This makes it replayable.

---

## 500. Deterministic replay
<!-- source: ORCHESTRATION.md §38 -->

Record:

```rust
struct SchedulerEvent {
    event_id: EventId,
    sequence: u64,
    epoch: Epoch,
    timestamp: LogicalTime,
    event: OrchestrationEvent,
    state_before: Digest,
    state_after: Digest,
}
```

Then:

```text
initial state + event log = scheduler state
```

This gives deterministic recovery.

---

## 501. Logical time
<!-- source: ORCHESTRATION.md §39 -->

Do not make scheduling semantics depend on wall-clock time where unnecessary.

Use:

```text
logical sequence
```

for authoritative ordering.

Wall-clock time remains diagnostic metadata.

Thus:

```text
Event 101
Event 102
Event 103
```

defines ordering even if physical timestamps are imperfect.

---

## 502. Scheduler event log
<!-- source: ORCHESTRATION.md §40 -->

```text
E001  UnitDiscovered           MU-001
E002  UnitDiscovered           MU-002
E003  DependencyResolved       MU-001
E004  AgentRegistered          A1
E005  LeaseAcquired            MU-001 A1
E006  AssignmentCreated        MU-001 A1
E007  ImplementationCompleted  MU-001
E008  VerificationRequested    MU-001
E009  AgentRegistered          V1
E010  LeaseAcquired            MU-001 V1
...   
```

This is a **protocol history**, not a chat transcript.

---

## 503. Restart recovery
<!-- source: ORCHESTRATION.md §41 -->

On scheduler crash:

```text
persistent state
  ↓
+ event log
  ↓
replay
  ↓
reconstructed scheduler state
```

Then reconcile external reality:

```text
worktrees
processes
receipts
leases
artifacts
```

against reconstructed state.

Any mismatch becomes:

```text
RECONCILIATION_REQUIRED
```

rather than silently choosing one side.

---

## 504. External reconciliation
<!-- source: ORCHESTRATION.md §42 -->

Example:

```text
Scheduler says:     Agent A lease active
Runtime says:       process gone
Worktree contains:  uncommitted changes
```

The scheduler must produce:

```text
ReconciliationRecord
```

and investigate.

Never:

```text
delete worktree
```

automatically before evidence capture.

---

## 505. Resource scheduler
<!-- source: ORCHESTRATION.md §43 -->

Resources are first-class.

```rust
struct ResourcePool {
    cpu: ResourceCapacity,
    memory: ResourceCapacity,
    storage: ResourceCapacity,
    tool_slots: Map<ToolId, usize>,
    architecture_slots: Map<ArchitectureId, usize>,
    hardware_slots: Map<HardwareResourceId, usize>,
}
```

A KCSAN run may require different resources from:

```text
AST analysis
```

The scheduler matches them.

---

## 506. Resource starvation
<!-- source: ORCHESTRATION.md §44 -->

If a task cannot run because:

```text
hardware slot unavailable
```

it becomes:

```text
WAITING_RESOURCE
```

not:

```text
FAILED
```

This distinction should propagate to orchestration reports.

---

## 507. Cancellation
<!-- source: ORCHESTRATION.md §45 -->

Cancellation must be explicit.

```rust
enum CancellationReason {
    Superseded,
    ScopeChanged,
    SnapshotChanged,
    DependencyInvalidated,
    UserRequested,
    ResourceReallocation,
    SecurityViolation,
}
```

Cancellation does not erase execution history.

```text
RUNNING
  ↓
CANCEL_REQUESTED
  ↓
CANCELLED
  ↓
receipt
```

---

## 508. Priority inversion
<!-- source: ORCHESTRATION.md §46 -->

Suppose:

```text
MU-A
  depends on MU-B

MU-B
  waiting for scarce verifier
```

A scheduler that keeps running unrelated work can leave the system blocked.

Therefore track:

```text
blocking dependency
```

and permit controlled resource reservation.

Again, this is operational scheduling, not semantic ranking.

---

## 509. Multi-agent verification topology
<!-- source: ORCHESTRATION.md §47 -->

The system should deliberately create separation:

```text
                  Migration Unit
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Implementation        Contract Review
              │                     │
              ▼                     ▼
        Rust artifact       Contract artifact
              │                     │
              └──────────┬──────────┘
                         ▼
               Independent Verifier
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
            ABI     Concurrency   Memory
             │           │           │
             └───────────┼───────────┘
                         │
                         ▼
                  Adversarial QA
                         │
                         ▼
                  Release Review
```

The scheduler should enforce this topology where required by policy.

---

## 510. No self-verification
<!-- source: ORCHESTRATION.md §48 -->

A hard scheduling rule:

```text
agent that authored implementation
    ≠
required independent verification authority
```

Potentially:

```text
same model family
```

may still be insufficient for certain high-criticality obligations.

The policy can require:

```text
different agent
different tool
different method
different authority
```

depending on the obligation.

---

## 511. Orchestration policy
<!-- source: ORCHESTRATION.md §49 -->

Separate scheduling policy from correctness policy.

```rust
struct SchedulingPolicy {
    fairness: FairnessPolicy,
    concurrency: ConcurrencyPolicy,
    retry: RetryPolicy,
    lease: LeasePolicy,
    resource: ResourcePolicy,
    independence: IndependencePolicy,
    quarantine: QuarantinePolicy,
}
```

Do not place:

```text
"Rust design is probably safe"
```

in scheduling policy.

---

## 512. Scheduler acceptance criteria
<!-- source: ORCHESTRATION.md §50 -->

### ORCH-001

Every assignment references an authorized migration unit.

### ORCH-002

Every writer has an exclusive write lease.

### ORCH-003

Read-only agents may execute concurrently where permitted.

### ORCH-004

Assignments are epoch-bound.

### ORCH-005

Stale results cannot mutate current canonical state.

### ORCH-006

Dependency state is explicit.

### ORCH-007

Critical unknowns can generate analysis tasks.

### ORCH-008

Conflicts create quarantine rather than consensus.

### ORCH-009

Agent loss triggers recovery.

### ORCH-010

External state is reconciled after restart.

### ORCH-011

Scheduling decisions are deterministic under identical state.

### ORCH-012

Every assignment is auditable.

### ORCH-013

Cancellation preserves history.

### ORCH-014

Retries are idempotent.

### ORCH-015

Resource exhaustion is distinguishable from semantic failure.

### ORCH-016

Implementation authority cannot be silently promoted to verification authority.

### ORCH-017

Release authority cannot be acquired through scheduling.

---

## 513. Scheduler crate architecture
<!-- source: ORCHESTRATION.md §51 -->

```text
crates/
├── rfl-orchestration-types/
│   ├── plan.rs
│   ├── state.rs
│   ├── assignment.rs
│   ├── event.rs
│   ├── dependency.rs
│   └── policy.rs
├── rfl-scheduler/
│   ├── readiness.rs
│   ├── selection.rs
│   ├── fairness.rs
│   ├── resources.rs
│   └── dispatch.rs
├── rfl-leases/
│   ├── migration.rs
│   ├── worktree.rs
│   ├── resource.rs
│   └── expiry.rs
├── rfl-recovery/
│   ├── agent_loss.rs
│   ├── restart.rs
│   ├── reconciliation.rs
│   └── retry.rs
├── rfl-quarantine/
│   ├── record.rs
│   ├── triggers.rs
│   ├── resolution.rs
│   └── recovery.rs
├── rfl-event-log/
│   ├── append.rs
│   ├── replay.rs
│   ├── sequence.rs
│   └── digest.rs
└── rfl-orchestration-gates/
    ├── determinism.rs
    ├── lease.rs
    ├── authority.rs
    ├── recovery.rs
    └── isolation.rs
```

---

## 514. Complete system now
<!-- source: ORCHESTRATION.md §52 -->

The architecture has expanded into a real autonomous engineering system:

```text
                       ┌──────────────────────┐
                       │    Linux Snapshot    │
                       └───────────┬──────────┘
                                   │
                                   ▼
                     ┌──────────────────────────┐
                     │ Semantic Reconstruction  │
                     └─────────────┬────────────┘
                                   ▼
                                 KSIR               WHAT EXISTS?
                                   │
                                   ▼
                              Contract IR         WHAT MUST REMAIN?
                                   │
                                   ▼
                            Rust Design IR        HOW MAY IT WORK?
                                   │
                                   ▼
                               Rust Code
                                   │
                                   ▼
                            Verification IR        HOW DO WE KNOW?
                                   │
                                   ▼
                           Execution Runtime     WHAT ACTUALLY RAN?
                                   │
                                   ▼
                            Evidence Ledger      WHAT WAS OBSERVED?
                                   │
                                   ▼
                              Gate Engine       DO REQUIREMENTS HOLD?
                                   │
                                   ▼
                         Migration Certificate
                                   │
                                   ▼
                           Release Authority
                                   │
                                   ▼
                          Orchestration Layer
                                   │
                                   ▼
                     ┌─────────────┼─────────────┐
                     ▼             ▼             ▼
                   MU-A          MU-B          MU-C
                     │             │             │
                     └─────────────┼─────────────┘
                                   │
                                   ▼
                            Next migration
```

The orchestration layer is deliberately **outside** the semantic trust chain.

That is important:

```text
Scheduler can decide:
    "run this analysis next."

Scheduler cannot decide:
    "therefore the code is correct."
```

---

## 515. The resulting authority model
<!-- source: ORCHESTRATION.md §53 -->

| Layer | Authority |
|-------|-----------|
| LLM/Agent | Propose reasoning, artifacts, hypotheses |
| Semantic analyzer | Produce observations |
| KSIR reconciler | Reconcile observations into semantic facts |
| Contract compiler | Formalize preservation requirements |
| Rust designer | Propose realizations |
| Implementation agent | Modify bounded worktree |
| Execution runtime | Establish what actually executed |
| Evidence ledger | Preserve provenance/integrity |
| Verification engine | Evaluate propositions |
| Gate engine | Evaluate requirements |
| Scheduler | Allocate authorized work |
| Review authority | Review release candidate |
| Release authority | Authorize release |

No single agent controls the entire chain.

---

## 516. Final invariant set
<!-- source: ORCHESTRATION.md §54 -->

At this point I would freeze the following as **RFL-AE Core Invariants**:

```text
RFL-AE-I001  NO EVIDENCE → NO VERIFIED CLAIM
RFL-AE-I002  IMPLEMENTATION AUTHORITY ≠ VERIFICATION AUTHORITY
RFL-AE-I003  EXECUTION RECEIPT ≠ SEMANTIC PROOF
RFL-AE-I004  UNKNOWN ≠ FALSE
RFL-AE-I005  UNKNOWN ≠ PROBABLY SAFE
RFL-AE-I006  CONFLICT → INVESTIGATION, NOT VOTING
RFL-AE-I007  STALE ARTIFACT → NO CURRENT CANONICAL AUTHORITY
RFL-AE-I008  SCOPE MUST BE EXPLICIT
RFL-AE-I009  SNAPSHOT MUST BE EXPLICIT
RFL-AE-I010  CONFIGURATION/ARCHITECTURE VALIDITY MUST BE EXPLICIT
RFL-AE-I011  IMMUTABLE EVIDENCE CANNOT BE OVERWRITTEN
RFL-AE-I012  INVALIDATION PROPAGATES THROUGH DEPENDENCIES
RFL-AE-I013  SCHEDULING DOES NOT CREATE SEMANTIC AUTHORITY
RFL-AE-I014  RELEASE IS DERIVED FROM GATES, NOT AGENT OPINION
RFL-AE-I015  CERTIFICATE CLAIMS ARE BOUNDED BY THEIR DECLARED SCOPE
```

---

## 517. What remains
<!-- source: ORCHESTRATION.md §55 -->

The core architecture is now substantially complete.

The next step should **not** be another conceptual layer. It should be turning the architecture into a **normative protocol specification and repository skeleton**.

Specifically:

```text
RFL-AE v0.1
│
├── PROTOCOL.md
├── ARCHITECTURE.md
├── VERIFICATION.md
├── EXECUTION.md
├── ORCHESTRATION.md
├── EVIDENCE.md
├── schemas/
├── crates/
│   ├── rfl-types
│   ├── rfl-protocol
│   ├── rfl-ksir
│   ├── rfl-contract
│   ├── rfl-design
│   ├── rfl-verification
│   ├── rfl-execution
│   ├── rfl-evidence
│   ├── rfl-gates
│   └── rfl-orchestration
└── tests/
    ├── protocol/
    ├── ksir/
    ├── contract/
    ├── verification/
    ├── execution/
    ├── evidence/
    ├── gates/
    └── orchestration/
```

The first implementation target should be the **protocol kernel plus event-sourced state machine**, not the LLM agents. Once that kernel is executable, the rest of the system can be attached to it without allowing an agent to redefine the rules of its own execution.

---

**Done — see [PROTOCOL-KERNEL.md](PROTOCOL-KERNEL.md)** (§518–§547, source §§1–§30), which turns
the protocol specification into an executable state machine: the trust boundary through the
protocol kernel to the append-only event store and canonical state, the normative
`Command ≠ Event` distinction, the canonical event envelope with both `state_before` and
`state_after`, opaque typed IDs, the transition algebra, `ProtocolState`, the deterministic
reducer, declarative `TransitionSpec` and its eleven preconditions, atomicity with the event as
commit boundary, optimistic concurrency and the CAS boundary, the `EventStore` trait, the event
hash chain, structured `ProtocolError`, rejected command versus authorized operation failure, the
executable migration transition table, the strict verification transition, event-sourced
projections, snapshotting, the three distinct version axes, event evolution, the
`PROTO-001`–`PROTO-020` conformance suite, the `ATTACK-001`–`ATTACK-020` adversarial suite, the
minimal `rfl-protocol` crate, dependency direction without authority recursion, the first
executable vertical slice, the three protocol theorems, and the resulting separation of semantic,
protocol, execution, scheduling and release authority. Same provenance convention as
`VERIFICATION.md`.
