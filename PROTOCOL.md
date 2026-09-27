# RFL-AE — Multi-Agent Execution Protocol

**Sections 109–135** — the operational protocol layer.

> Continues the numbering of [ARCHITECTURE.md](ARCHITECTURE.md) (§1–§51),
> [SPECIFICATION.md](SPECIFICATION.md) (§52–§80), and [FORMAL-CORE.md](FORMAL-CORE.md)
> (§81–§107).
>
> **Numbering note:** the source document begins at §109. There is no §108; the gap is
> preserved as-is rather than renumbered.

The next layer turns RFL-AE from an architecture into an **operational protocol**.

The central rule is:

> ### **Agents exchange typed artifacts and evidence, not authority through conversation.**

A 10–100-agent system should therefore behave more like a distributed engineering system than
a group chat.

## Contents

| Part | Sections |
| --- | --- |
| [I. Protocol foundations](#109-multi-agent-execution-protocol) | 109–114 |
| [II. Migration unit lifecycle](#115-migration-unit-as-the-atomic-engineering-object) | 115–123 |
| [III. Agent topology](#124-agent-topology-for-10100-agents) | 124–130 |
| [IV. Gates & planes](#131-migration-readiness-function) | 131–135 |

<details>
<summary><strong>Full section index</strong></summary>

109. Multi-Agent Execution Protocol
110. Protocol Envelope
111. No Freeform Authority
112. Capability-Based Agent Authority
113. Capability Scope
114. Task Admission
115. Migration Unit as the Atomic Engineering Object
116. Migration Unit State Machine
117. Conflict Object
118. Knowledge-State Separation
119. Canonical Artifact Store
120. Immutable Event Ledger
121. Deterministic Replay
122. Execution Evidence
123. Evidence Chain
124. Agent Topology for 10–100 Agents
125. Suggested Agent Taxonomy
126. Agent Count Should Follow Dependency Width
127. One Writer per Migration Unit
128. Worktree Isolation
129. Patch Promotion
130. The Kernel Rewrite Becomes a Dependency DAG
131. Migration Readiness Function
132. The Most Important Gate
133. RFL-AE Control Plane
134. Proposed RFL-AE v0.2 Architecture
135. The First Executable Prototype

</details>

---

# I. Protocol foundations

## 109. Multi-Agent Execution Protocol

```text
             ┌──────────────────────┐
             │ Kernel Snapshot      │
             │ SHA + .config + arch │
             └───────────┬──────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │ Task Admission        │
             │ scope + authorization │
             └───────────┬───────────┘
                         │
                         ▼
            ┌────────────┴────────────┐
            ▼                         ▼
     ┌─────────────┐             ┌─────────┐
     │ Observation │             │ History │
     │ Agents      │             │ Agents  │
     └─────────────┘             └─────────┘
            │                         │
            └────────────┬────────────┘
                         ▼
                ┌────────────────┐
                │ KSIR           │
                │ semantic model │
                └────────┬───────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
  ┌───────────┐   ┌─────────────┐    ┌────────┐
  │ Ownership │   │ Concurrency │    │ ABI    │
  │ Agents    │   │ Agents      │    │ Agents │
  └───────────┘   └─────────────┘    └────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                ┌─────────────────┐
                │ Contract Ledger │
                └────────┬────────┘
                         │
                         ▼
                ┌────────────────┐
                │ Rust Design IR │
                └────────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │ Implementation │
                │ Agent(s)       │
                └────────┬───────┘
                         │
                         ▼
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
  ┌───────────┐   ┌────────────┐ ┌─────────────────┐
  │ Static QA │   │ Runtime QA │ │ Differential QA │
  └───────────┘   └────────────┘ └─────────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                ┌────────────────┐
                │ Adversarial QA │
                └────────┬───────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Evidence Bundle │
                └────────┬────────┘
                         │
                         ▼
                 ┌──────────────┐
                 │ Release Gate │
                 └──────────────┘
```

---

## 110. Protocol Envelope

Every inter-agent operation should use a canonical envelope.

Conceptually:

```rust
struct AgentMessage {
    protocol_version: ProtocolVersion,
    message_id: MessageId,
    task_id: TaskId,
    migration_unit: MigrationUnitId,

    snapshot: SnapshotId,

    sender: AgentId,
    receiver: AgentId,

    capability: Capability,
    operation: Operation,

    sequence: SequenceNumber,
    parent_events: Vec<EventId>,

    artifact: ArtifactRef,

    evidence: Vec<EvidenceRef>,

    authorization: AuthorizationRef,

    payload_digest: Digest,

    created_at: Timestamp,
    expires_at: Option<Timestamp>,
}
```

The important fields are **not** the timestamps. The important fields are:

```text
snapshot
task_id
migration_unit
sender
capability
operation
parent_events
artifact
evidence
authorization
digest
```

They make the operation **auditable and replayable**.

---

## 111. No Freeform Authority

An agent saying:

> "The lock is probably held here."

must never change system state.

Instead:

```text
Agent
  │
  │ proposes hypothesis
  ▼
Hypothesis Artifact
  │
  │ requires evidence
  ▼
Experiment / Source Analysis
  │
  ▼
Evidence
  │
  ▼
Derived Contract
  │
  ▼
Verification Gate
  │
  ▼
Authorization
```

Therefore:

```text
LLM output  ≠  engineering fact
```

and:

```text
agent agreement  ≠  verification
```

This is particularly important when 20 agents independently converge on the same incorrect
interpretation.

Consensus is useful for **prioritization**. It is not proof.

---

## 112. Capability-Based Agent Authority

Each agent receives a restricted capability set.

Example:

```text
Agent: ownership-analyst-17

Allowed:
    READ_KERNEL
    READ_KSIR
    DERIVE_OWNERSHIP
    CREATE_HYPOTHESIS
    CREATE_CONTRACT_PROPOSAL

Denied:
    MODIFY_SOURCE
    MERGE_PATCH
    AUTHORIZE_IMPLEMENTATION
    MARK_VERIFIED
    RELEASE
```

An implementation agent might have:

```text
READ_KERNEL
READ_KSIR
READ_CONTRACT
READ_DESIGN_IR
CREATE_PATCH
RUN_LOCAL_TESTS
CREATE_EXECUTION_RESULT
```

but not:

```text
ATTEST_VERIFICATION
AUTHORIZE_RELEASE
```

The verification agent receives:

```text
READ_SOURCE
READ_PATCH
READ_CONTRACT
RUN_TESTS
RUN_STATIC_ANALYSIS
RUN_DIFFERENTIAL_TESTS
CREATE_VERIFICATION_RESULT
```

but cannot modify the implementation under verification.

This gives:

```text
Implementation authority
        ≠
Verification authority
        ≠
Release authority
```

That separation should be enforced **mechanically**.

---

## 113. Capability Scope

Capabilities should be scoped along several dimensions.

```text
Capability
├── operation
├── repository
├── kernel snapshot
├── architecture
├── subsystem
├── migration unit
├── files
├── artifact classes
├── execution permissions
└── expiration
```

For example:

```text
MODIFY_SOURCE {
    repository: linux-rfl
    snapshot: 6f83...
    arch: x86_64
    subsystem: kernel/workqueue.c
    migration_unit: workqueue_cancel_001
    files:
        kernel/workqueue.c
        rust/kernel/workqueue.rs
    expires: epoch 142
}
```

An agent cannot turn this into permission to modify:

```text
mm/  net/  fs/  arch/
```

simply because it discovers something interesting there.

That prevents **scope creep through reasoning**.

---

## 114. Task Admission

The system needs an explicit admission phase.

```text
             NO_TASK
                │ task submitted
                ▼
            PROPOSED
                │
             INTAKE
                │
                ├ ── invalid ──────> REJECTED
                │
                ▼
         SNAPSHOT_BOUND
                │
                ▼
           SCOPE_BOUND
                │
                ▼
           AUTHORIZED
                │
                ▼
              READY
```

And the critical invariant:

```text
NO_TASK  ========  NO_CHANGE
```

No admitted task means:

- no source modification
- no generated patch
- no migration-unit mutation
- no authorization
- no release state transition

Agents may still perform explicitly permitted **read-only reconnaissance**, if the system
defines that as outside migration execution.

---

# II. Migration unit lifecycle

## 115. Migration Unit as the Atomic Engineering Object

The migration unit should become the fundamental unit of work.

Not:

```text
rewrite workqueue.c
```

but:

```text
MU-WQ-CANCEL-001

Scope:
    cancel_work_sync()

Inputs:
    struct work_struct
    worker_pool state
    pending/running state

Contracts:
    ownership
    synchronization
    execution context
    cancellation semantics
    memory ordering
    ABI

Outputs:
    Rust implementation
    FFI boundary
    tests
    differential evidence
```

A migration unit should be small enough that its correctness can be established
independently.

---

## 116. Migration Unit State Machine

```text
           DISCOVERED
                ▼
             MAPPED
                ▼
           CONTRACTED
                ▼
            DESIGNED
                ▼
  AUTHORIZED_FOR_IMPLEMENTATION
                ▼
           IMPLEMENTED
                ▼
     AUTHORIZED_FOR_TESTING
                ▼
             TESTED
                ▼
      DIFFERENTIAL_VERIFIED
                ▼
      ADVERSARIAL_VERIFIED
                ▼
      AUTHORIZED_FOR_REVIEW
                ▼
        RELEASE_ELIGIBLE
                ▼
            RELEASED
```

Any serious contradiction can transition to:

```text
               ┌────────────┐
               │ QUARANTINE │
               └──────┬─────┘
                      │
        ┌─────────────┼───────────────┐
        ▼             ▼               ▼
    MORE DATA    EXPERIMENT     HUMAN REVIEW
        │             │               │
        └─────────────┼───────────────┘
                      ▼
                  REANALYZE
```

> Quarantine is not failure of the architecture. It is one of its safety mechanisms.

---

## 117. Conflict Object

Agents will disagree. **Do not resolve disagreement by voting.** Represent it:

```rust
struct Conflict {
    conflict_id: ConflictId,
    task_id: TaskId,

    subject: ArtifactRef,

    propositions: Vec<Proposition>,

    supporting_evidence: Vec<EvidenceRef>,
    contradicting_evidence: Vec<EvidenceRef>,

    affected_invariants: Vec<InvariantId>,

    severity: ConflictSeverity,

    required_resolution: ResolutionMethod,
}
```

Possible resolution methods:

```text
SOURCE_INSPECTION    HISTORY_INSPECTION    STATIC_ANALYSIS
BUILD_EXPERIMENT     RUNTIME_EXPERIMENT    CONCURRENCY_TEST
ARCHITECTURE_TEST    DIFFERENTIAL_TEST     HUMAN_REVIEW
```

Example:

```text
Agent A:
    callback may execute in process context.

Agent B:
    callback can execute from softirq context.

System:
    CONFLICT

Required:
    execution-context experiment
```

The system should not produce:

```text
A: 7 agents
B: 4 agents
=> A wins
```

Instead:

```text
DISAGREEMENT
     ↓
  EXPERIMENT
     ↓
 OBSERVATION
     ↓
CONTRACT UPDATE
```

---

## 118. Knowledge-State Separation

The earlier distinction between:

```text
MEMORY  KNOWLEDGE  BELIEF  CONSENSUS  TRUTH  AUTHORITY  CANON  HISTORY
```

should become actual protocol objects rather than terminology.

A useful relationship is:

```text
     HISTORY
        │
        ▼
   OBSERVATION
        │
        ▼
    KNOWLEDGE
        │
        ├────────────────┐
        ▼                ▼
     BELIEF         HYPOTHESIS
        │                │
        └───────┬────────┘
                ▼
           EXPERIMENT
                │
                ▼
            EVIDENCE
                │
                ▼
              CLAIM
                │
                ▼
          VERIFICATION
                │
                ▼
              CANON
```

`AUTHORITY` is orthogonal:

```text
CANON  ≠  AUTHORITY
```

Something can be canonical without granting an agent permission to modify it.

---

## 119. Canonical Artifact Store

Agents should not pass large semantic objects through prompts. Instead:

```text
             ┌────────────────────┐
             │   Artifact Store   │
             ├────────────────────┤
             │ KSIR               │
             │ Contracts          │
             │ Evidence           │
             │ Hypotheses         │
             │ Designs            │
             │ Patches            │
             │ Test Results       │
             │ Conflicts          │
             │ Gate Results       │
             └──────────┬─────────┘
                        │
            ┌───────────┼───────────┐
            ▼           ▼           ▼
         Agent A     Agent B     Agent C
```

Messages carry references:

```text
artifact_id  digest  version  snapshot_id
```

rather than duplicating the artifact.

This reduces:

- context drift
- accidental mutation
- prompt truncation
- contradictory copies
- provenance loss

---

## 120. Immutable Event Ledger

Every meaningful transition becomes an event.

```text
E0001 TASK_CREATED
E0002 SNAPSHOT_BOUND
E0003 SCOPE_BOUND
E0004 OBSERVATION_CREATED
E0005 KSIR_UPDATED
E0006 CONTRACT_PROPOSED
E0007 CONFLICT_CREATED
E0008 EXPERIMENT_EXECUTED
E0009 CONFLICT_RESOLVED
E0010 DESIGN_AUTHORIZED
E0011 PATCH_CREATED
E0012 BUILD_EXECUTED
E0013 TEST_EXECUTED
E0014 DIFFERENTIAL_VERIFICATION
E0015 ADVERSARIAL_VERIFICATION
E0016 RELEASE_GATE
```

Each event references its parents:

```text
E0010
 ├── parent: E0009
 ├── contract: C0041
 ├── design: D0023
 └── authorization: A0018
```

Therefore the engineering history becomes a DAG.

```text
                    E0001
                      │
                    E0002
                      │
              ┌───────┴───────┐
              ▼               ▼
            E0003           E0004
              │               │
              └───────┬───────┘
                      ▼
                    E0005
                      │
                    E0006
                      │
              ┌───────┴───────┐
              ▼               ▼
            E0007           E0008
                  \       /
                   \     /
                      ▼
                    E0009
```

Replay then becomes possible.

---

## 121. Deterministic Replay

The system should eventually support:

```text
replay(task_id, snapshot_id)
```

and reconstruct:

```text
what did the system know?
what did it believe?
what evidence existed?
which agents acted?
what permissions did they have?
which commands executed?
which artifacts changed?
why did the gate pass?
```

This is much stronger than an agent transcript.

A transcript answers: *What did the agents say?*

A replay ledger should answer:

> **What state transitions actually occurred, based on which artifacts and execution
> evidence?**

---

## 122. Execution Evidence

Every executable verification operation should generate an execution record.

Conceptually:

```rust
struct ExecutionReceipt {
    execution_id: ExecutionId,

    task_id: TaskId,
    snapshot_id: SnapshotId,

    actor: AgentId,

    command: String,
    working_tree: Digest,
    environment: EnvironmentFingerprint,
    toolchain: ToolchainFingerprint,

    started_at: Timestamp,
    finished_at: Timestamp,
    exit_code: i32,

    stdout_digest: Digest,
    stderr_digest: Digest,

    artifacts: Vec<ArtifactRef>,
}
```

The crucial distinction:

```text
Agent says:
    cargo test passed

        ≠

ExecutionReceipt:
    command executed
    exit_code = 0
    artifact digest = ...
```

This directly enforces:

> **NO EVIDENCE → NO VERIFIED CLAIM**

---

## 123. Evidence Chain

A verification claim should have a traceable chain.

Example:

```text
CLAIM:
    Rust implementation preserves cancellation semantics
       │
       ├── Contract C42
       │
       ├── Rust Design D17
       │
       ├── Commit P91
       │
       ├── Test T88
       │
       ├── Execution E144
       │
       ├── Differential Result DR19
       │
       └── Adversarial Result AR07
```

The release gate consumes this graph. **Not an LLM-generated summary.**

---

# III. Agent topology

## 124. Agent Topology for 10–100 Agents

Do not create a fully connected agent mesh.

A 100-agent system with unrestricted peer-to-peer communication becomes difficult to reason
about. Prefer **bounded coordination**:

```text
                  ORCHESTRATOR
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      Discovery     Contracts   Verification
        Pool          Pool          Pool
         /|\           /|\           /|\
        / | \         / | \         / | \
       A  B  C       D  E  F       G  H  I
                         ...
```

Within each pool:

```text
specialized agents
         ↓
   typed artifacts
         ↓
  pool coordinator
         ↓
canonical artifact store
```

Cross-pool communication occurs through artifacts. **Not arbitrary conversations.**

---

## 125. Suggested Agent Taxonomy

### Discovery

```text
kernel-cartographer   symbol-indexer     include-tracer
callgraph-agent       config-agent       architecture-agent
history-agent         generated-code-agent
```

### Semantic reconstruction

```text
c-semantics-agent   ownership-agent   lifetime-agent  alias-agent
refcount-agent      context-agent     allocation-agent
```

### Concurrency

```text
lock-agent      atomic-agent    rcu-agent        waitqueue-agent
workqueue-agent irq-agent       timer-agent      preempt-rt-agent
```

### Kernel contracts

```text
mm-contract-agent      vfs-contract-agent   net-contract-agent
driver-contract-agent  dma-contract-agent   security-contract-agent
abi-agent
```

### Rust design

```text
type-design-agent      lifetime-design-agent  trait-design-agent
unsafe-boundary-agent  ffi-agent              pin-init-agent
sync-abstraction-agent
```

### Implementation

```text
rust-implementation-agent  ffi-implementation-agent
test-generation-agent      build-integration-agent
```

### Verification

```text
compile-agent          static-analysis-agent  runtime-agent
concurrency-agent      miri-agent             kasan-agent
lockdep-agent          differential-agent     abi-verification-agent
```

### Adversarial

```text
race-attacker      lifetime-attacker   refcount-attacker
deadlock-attacker  uaf-attacker        abi-attacker
architecture-attacker  error-path-attacker
```

### Governance

```text
evidence-agent  provenance-agent  gate-agent  review-agent  release-agent
```

---

## 126. Agent Count Should Follow Dependency Width

The system should **not** attempt to maximize agent count.

For a migration unit:

```text
10 agents
    ↓
parallel analysis
    ↓
contract synthesis
    ↓
1 canonical contract
    ↓
3 design agents
    ↓
1 design gate
    ↓
1 implementation agent
    ↓
many verification agents
```

A useful principle is:

```text
parallelism during discovery
        +
serialization at authority boundaries
```

For example, ownership and concurrency analysis can happen simultaneously.

But authorization of implementation should have one deterministic gate.

---

## 127. One Writer per Migration Unit

A particularly useful invariant:

```text
ONE ACTIVE IMPLEMENTATION WRITER
        PER MIGRATION UNIT
```

Multiple analysts can inspect it. Multiple verification agents can test it. But source
mutation should be serialized.

```text
                 ┌── ownership
                 ├── concurrency
                 ├── ABI
                 ├── history
                 └── architecture
                        │
                        ▼
                CANONICAL DESIGN
                        │
                        ▼
                   IMPLEMENTER
                        │
                        ▼
                    WORKTREE
```

This avoids multi-agent patch races.

---

## 128. Worktree Isolation

For parallel implementation experiments:

```text
linux/
├── canonical/
├── task-MU001/
├── task-MU002/
├── task-MU003/
└── adversarial/
```

Each worktree binds to:

```text
snapshot
task
migration unit
authorization
agent
```

No agent can accidentally modify another migration unit's worktree.

---

## 129. Patch Promotion

A patch should not go directly from:

```text
IMPLEMENTER
     ↓
    main
```

Instead:

```text
IMPLEMENTER
     ↓
candidate patch
     ↓
format / compile
     ↓
unit tests
     ↓
integration tests
     ↓
static analysis
     ↓
concurrency verification
     ↓
differential verification
     ↓
adversarial verification
     ↓
human/reviewer authority
     ↓
release gate
     ↓
canonical branch
```

Each stage creates evidence.

---

## 130. The Kernel Rewrite Becomes a Dependency DAG

This is the important scaling property.

A kernel subsystem is not a flat list of files. It becomes:

```text
                core types
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       locking    memory     context
          │          │          │
          └───┬──────┴──────┬───┘
              ▼             ▼
             RCU          refs
                  \       /
                   \     /
                     ▼
                workqueues
                     │
                     ▼
                  drivers
                     │
                     ▼
                    VFS
                     │
                     ▼
                filesystems
```

Migration order can therefore be derived from **contract dependencies**, rather than arbitrary
directory order.

---

# IV. Gates & planes

## 131. Migration Readiness Function

A migration unit should have an explicit readiness predicate.

Conceptually:

```text
READY(MU) =
    snapshot_bound
AND scope_bound
AND dependencies_known
AND ownership != UNKNOWN
AND critical_lifetimes != UNKNOWN
AND concurrency_contract != UNKNOWN
AND execution_context != UNKNOWN
AND ABI_contract != UNKNOWN
AND unsafe_obligations_defined
AND verification_plan_exists
AND authorization_exists
```

Not every field needs to be completely known. But unknowns must be **explicitly classified**.

For example:

```text
ownership:
    PARTIALLY_VERIFIED

architecture_dependency:
    OPEN

ABI:
    VERIFIED

execution_context:
    VERIFIED
```

That is much more useful than:

```text
confidence = 87%
```

---

## 132. The Most Important Gate

Before implementation:

```text
       ┌──────────────────────────┐
       │ IMPLEMENTATION ADMISSION │
       └─────────────┬────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    Contract     Ownership   Concurrency
      known        known        known
        │            │            │
        └────────────┼────────────┘
                     ▼
               Context known
                     │
                     ▼
                 ABI known
                     │
                     ▼
            Unsafe obligations
                 explicit
                     │
                     ▼
             Verification plan
                  exists
                     │
                     ▼
                AUTHORIZED
```

If a critical contract is unknown:

```text
STOP  QUARANTINE  INVESTIGATE
```

Not:

```text
LLM guesses
     ↓
 code anyway
```

---

## 133. RFL-AE Control Plane

At this point the architecture naturally separates into two planes.

### Data Plane

```text
Linux source
     ↓
  analysis
     ↓
   KSIR
     ↓
 contracts
     ↓
   Rust
     ↓
  tests
     ↓
execution artifacts
```

### Control Plane

```text
tasks
     ↓
authorization
     ↓
capabilities
     ↓
state transitions
     ↓
gates
     ↓
evidence
     ↓
release authority
```

This separation is fundamental.

```text
Data plane determines:
    what exists

Control plane determines:
    what the system is permitted to do
```

---

## 134. Proposed RFL-AE v0.2 Architecture

The current system can now be frozen into these major layers:

| Layer | Name |
| --- | --- |
| L0 | Kernel Snapshot |
| L1 | Repository / Symbol Index |
| L2 | Semantic Extraction |
| L3 | KSIR |
| L4 | Contract Ledger |
| L5 | Rust Design IR |
| L6 | Implementation |
| L7 | Verification |
| L8 | Differential Verification |
| L9 | Adversarial Verification |
| L10 | Evidence / Provenance |
| L11 | Agent Control Plane |
| L12 | Authorization / Gates |
| L13 | Release / Canon |

With one invariant crossing all layers:

```text
              NO EVIDENCE
                    │
                    ▼
          NO VERIFIED CLAIM
```

And another:

```text
           NO AUTHORIZATION
                    │
                    ▼
              NO MUTATION
```

---

## 135. The First Executable Prototype

The next implementation target should be **not an AI agent**.

Build the deterministic kernel of RFL-AE first:

```text
rfl-ae/
├── crates/
│   ├── rfl-types/
│   ├── rfl-protocol/
│   ├── rfl-ledger/
│   ├── rfl-evidence/
│   ├── rfl-snapshot/
│   ├── rfl-ksir/
│   └── rfl-gates/
├── schemas/
│   ├── task.schema.json
│   ├── event.schema.json
│   ├── artifact.schema.json
│   ├── evidence.schema.json
│   ├── contract.schema.json
│   ├── authorization.schema.json
│   └── conflict.schema.json
├── agents/
│   └── manifests/
├── fixtures/
└── tests/
    ├── protocol/
    ├── ledger/
    ├── authorization/
    ├── evidence/
    └── replay/
```

The first executable milestone should demonstrate:

```text
create task
     ↓
bind kernel snapshot
     ↓
issue scoped capability
     ↓
create observation
     ↓
create contract
     ↓
create implementation authorization
     ↓
execute command
     ↓
record execution receipt
     ↓
create verification claim
     ↓
verify evidence chain
     ↓
release gate
```

**No LLM is required for this.** That is deliberate.

Once this deterministic substrate exists, an LLM becomes a replaceable **reasoning worker**
sitting behind the protocol.

That gives RFL-AE the property we actually want:

```text
        LLM failure
             ↓
     bounded artifact
             ↓
         evidence
             ↓
           gate
             ↓
        contained
```

rather than:

```text
        LLM failure
             ↓
      plausible code
             ↓
  plausible explanation
             ↓
     merged kernel
             ↓
         unknown
```

---

## Next step

The next layer should be the **actual Rust protocol implementation**: concrete `Task`, `Agent`,
`Capability`, `Artifact`, `Event`, `Evidence`, `Authorization`, `Conflict`, and `Gate` types,
their state-transition rules, and the conformance tests that make the protocol mechanically
enforceable.

---

**Done — see [RUST-CORE.md](RUST-CORE.md)** (§136–§172), which specifies those types
concretely: 31 Rust type declarations, the `TransitionEngine`, protocol invariants P1–P10, the
conformance and adversarial protocol suites, and the PHASE 0–11 development order.
