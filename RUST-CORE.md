# RFL-AE — Concrete Rust Core

**Sections 136–172** — the typed protocol substrate.

> Continues the numbering of [ARCHITECTURE.md](ARCHITECTURE.md) (§1–§51),
> [SPECIFICATION.md](SPECIFICATION.md) (§52–§80), [FORMAL-CORE.md](FORMAL-CORE.md)
> (§81–§107), and [PROTOCOL.md](PROTOCOL.md) (§109–§135). §108 does not exist in the source.

The deterministic substrate should now become an actual typed protocol.

The key design decision is:

> ### **The protocol owns state transitions; agents only propose operations.**

An agent must never directly mutate the canonical state machine.

## Contents

| Part | Sections |
| --- | --- |
| [I. Protocol core](#136-rfl-ae-protocol-concrete-rust-core) | 136–140 |
| [II. Tasks, capabilities, authorization](#141-task-type) | 141–146 |
| [III. Artifacts, events, transitions](#147-artifact-model) | 147–153 |
| [IV. Evidence & contracts](#154-evidence-object) | 154–159 |
| [V. Protocol guarantees](#160-protocol-invariants) | 160–164 |
| [VI. Orchestration & roadmap](#165-scheduling) | 165–172 |

<details>
<summary><strong>Full section index</strong></summary>

136. RFL-AE Protocol: Concrete Rust Core
137. Core Type System
138. Snapshot Identity
139. Epistemic Types
140. Verification State
141. Task Type
142. Task Scope
143. Capability Model
144. Capability Binding
145. Authorization Must Be Separate
146. Authorization Object
147. Artifact Model
148. Artifact Immutability
149. Event Model
150. Event Sourcing
151. State Transition Authority
152. Transition Example
153. Illegal Transition Tests
154. Evidence Object
155. Evidence Status
156. Contract Ledger
157. Unknowns Become Contract Members
158. Rust Design IR
159. Unsafe Obligation Registry
160. Protocol Invariants
161. Conformance Suite
162. Adversarial Protocol Tests
163. Agent Manifest
164. Agent Self-Model
165. Scheduling
166. Agent Failure Is a First-Class State
167. Agent Replacement
168. Human Intervention
169. What This Gives Us
170. The First End-to-End Demonstrator
171. Development Order
172. Immediate Next Specification

</details>

---

# I. Protocol core

## 136. RFL-AE Protocol: Concrete Rust Core

```text
         Agent
           │ OperationRequest
           ▼
┌─────────────────────┐
│ Protocol Validator  │
│                     │
│ capability          │
│ task state          │
│ scope               │
│ artifact provenance │
│ transition rules    │
└──────────┬──────────┘
           │
       accepted?
      /          \
     NO         YES
      │          │
      ▼          ▼
  REJECTED     Event
                 │
                 ▼
         Canonical Ledger
                 │
                 ▼
             New State
```

This means the protocol itself becomes the first thing that must be trustworthy.

---

## 137. Core Type System

Start with opaque identifiers.

```rust
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct TaskId(pub Uuid);

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct AgentId(pub Uuid);

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct ArtifactId(pub Uuid);

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct EvidenceId(pub Uuid);

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct EventId(pub Uuid);

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct MigrationUnitId(pub Uuid);

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct CapabilityId(pub Uuid);

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct AuthorizationId(pub Uuid);
```

Do not use raw strings for these identifiers.

This prevents accidental interchange such as:

```text
TaskId <- ArtifactId
```

at compile time.

---

## 138. Snapshot Identity

A kernel migration cannot operate against an ambiguous source tree.

```rust
pub struct KernelSnapshot {
    pub snapshot_id: SnapshotId,

    pub linux_commit: GitObjectId,
    pub repository_digest: Digest,

    pub architecture: Architecture,
    pub config_digest: Digest,

    pub compiler: ToolchainFingerprint,

    pub generated_artifacts: Vec<ArtifactDigest>,

    pub analysis_environment: EnvironmentFingerprint,
}
```

The snapshot identity should therefore be approximately:

```text
S =
    Linux tree
  + commit
  + architecture
  + configuration
  + generated artifacts
  + toolchain
  + analysis environment
```

A claim tied to snapshot `S1` must not silently become a claim about `S2`.

---

## 139. Epistemic Types

Avoid one universal `confidence` field. Use typed epistemic states.

```rust
pub enum Epistemic<T> {
    Unknown,

    Observed {
        value: T,
        evidence: EvidenceId,
    },

    Derived {
        value: T,
        from: Vec<ArtifactId>,
    },

    Hypothesis {
        value: T,
        basis: Vec<ArtifactId>,
    },
}
```

This prevents:

```rust
confidence: 0.92
```

from pretending to answer: *Why should this statement be believed?*

Instead:

```text
Observed  Derived  Hypothesis  Unknown
```

carry different semantics.

---

## 140. Verification State

Keep verification independent.

```rust
pub enum VerificationStatus {
    Unverified,
    Provisional,
    PartiallyVerified,
    Verified,
    Blocked,
}
```

Therefore:

```text
Epistemic:
    DERIVED

Verification:
    UNVERIFIED
```

is perfectly valid.

Likewise:

```text
Epistemic:
    OBSERVED

Verification:
    VERIFIED
```

can represent an executed observation.

> The two axes should never be collapsed.

---

# II. Tasks, capabilities, authorization

## 141. Task Type

```rust
pub struct Task {
    pub id: TaskId,

    pub snapshot: SnapshotId,
    pub migration_unit: Option<MigrationUnitId>,

    pub scope: Scope,
    pub objective: Objective,

    pub authority: TaskAuthority,
    pub state: TaskState,

    pub created_by: AgentId,
    pub parent: Option<TaskId>,
}
```

Possible states:

```rust
pub enum TaskState {
    Proposed,
    Intake,
    SnapshotBound,
    ScopeBound,
    Authorized,
    Ready,
    Running,
    Blocked,
    Quarantined,
    Completed,
    Rejected,
    Cancelled,
}
```

---

## 142. Task Scope

Scope must be machine-readable.

```rust
pub struct Scope {
    pub subsystem: Option<Subsystem>,
    pub files: BTreeSet<PathBuf>,
    pub symbols: BTreeSet<SymbolId>,
    pub migration_units: BTreeSet<MigrationUnitId>,

    pub architectures: BTreeSet<Architecture>,

    pub allow_source_mutation: bool,
    pub allow_execution: bool,
}
```

This prevents the classic agent failure:

```text
Task:
    migrate function X

Agent discovers:
    interesting dependency Y

Agent modifies:
    X + Y + Z + unrelated cleanup
```

The protocol should reject this unless scope is explicitly expanded.

---

## 143. Capability Model

Capabilities should be explicit enums rather than arbitrary strings.

```rust
pub enum Capability {
    ReadKernel,
    ReadHistory,
    ReadKsir,

    DeriveSemanticModel,
    ProposeContract,
    ProposeRustDesign,

    ModifyWorktree,
    CreatePatch,

    ExecuteBuild,
    ExecuteTests,
    ExecuteAnalysis,

    CreateEvidence,
    CreateVerification,

    RequestAuthorization,
}
```

Critically, `CreateVerification` does **not** imply `AuthorizeRelease`.

---

## 144. Capability Binding

A capability needs scope.

```rust
pub struct CapabilityGrant {
    pub id: CapabilityId,

    pub agent: AgentId,
    pub capability: Capability,

    pub task: TaskId,
    pub snapshot: SnapshotId,
    pub migration_unit: Option<MigrationUnitId>,

    pub path_scope: Vec<PathPattern>,

    pub issued_by: AuthorizationId,
    pub valid_epoch: Epoch,
    pub expires_at: Option<Timestamp>,
}
```

A capability therefore answers:

```text
WHO?
WHAT?
WHERE?
FOR WHICH TASK?
AGAINST WHICH SNAPSHOT?
UNTIL WHEN?
WHO AUTHORIZED IT?
```

---

## 145. Authorization Must Be Separate

Do not let `CapabilityGrant` also mean `Authorization`. They are different concepts.

**Capability** means: *This agent is permitted to perform this class of operation.*

**Authorization** means: *This particular operation is permitted for this particular migration
state.*

Example:

```text
Agent capability:
    CREATE_PATCH

Current migration state:
    CONTRACTED

Result:
    DENIED
```

because implementation authorization has not yet occurred.

---

## 146. Authorization Object

```rust
pub struct Authorization {
    pub id: AuthorizationId,

    pub task: TaskId,
    pub migration_unit: MigrationUnitId,

    pub operation: AuthorizedOperation,

    pub required_contracts: Vec<ContractId>,
    pub required_gates: Vec<GateId>,

    pub issued_by: Authority,
    pub snapshot: SnapshotId,
    pub epoch: Epoch,
}
```

Possible operations:

```rust
pub enum AuthorizedOperation {
    BeginAnalysis,
    ModifyWorktree,
    RunVerification,
    PromoteArtifact,
    MergePatch,
    Release,
}
```

---

# III. Artifacts, events, transitions

## 147. Artifact Model

Everything substantial becomes an artifact.

```rust
pub enum Artifact {
    Observation(Observation),
    SemanticModel(KsirFragment),
    Hypothesis(Hypothesis),
    Contract(Contract),
    RustDesign(RustDesign),
    Patch(Patch),
    TestPlan(TestPlan),
    ExecutionResult(ExecutionResult),
    VerificationResult(VerificationResult),
    Conflict(Conflict),
    GateResult(GateResult),
}
```

Every artifact has common metadata:

```rust
pub struct ArtifactHeader {
    pub id: ArtifactId,
    pub task: TaskId,
    pub snapshot: SnapshotId,

    pub producer: AgentId,

    pub parents: Vec<ArtifactId>,

    pub digest: Digest,

    pub schema_version: SchemaVersion,
}
```

---

## 148. Artifact Immutability

An artifact should never be edited in place.

**Wrong:**

```text
Contract C42
     ↓ edit
     ↓
Contract C42
```

**Correct:**

```text
Contract C42 v1
       │
       ▼
Contract C42 v2

with:

supersedes(C42v2, C42v1)
```

This preserves history.

---

## 149. Event Model

The ledger records state transitions.

```rust
pub struct Event {
    pub id: EventId,

    pub sequence: u64,

    pub task: TaskId,
    pub actor: AgentId,

    pub operation: Operation,

    pub parents: Vec<EventId>,

    pub input_artifacts: Vec<ArtifactId>,
    pub output_artifacts: Vec<ArtifactId>,

    pub authorization: Option<AuthorizationId>,
    pub evidence: Vec<EvidenceId>,

    pub resulting_state: StateDigest,
}
```

The `sequence` is local to the canonical ledger.

The parent references establish causality.

---

## 150. Event Sourcing

The canonical state can be reconstructed:

```text
Initial State
      │
     E1
      │
     E2
      │
     E3
      │
     ...
      │
     En
      │
Current State
```

Therefore:

```text
state = fold(events)
```

Conceptually:

```rust
for event in ledger.events() {
    state.apply(event)?;
}
```

If replay produces a different state:

```text
REPLAY_MISMATCH
```

becomes a hard evidence failure.

---

## 151. State Transition Authority

The critical function:

```rust
pub trait TransitionEngine {
    fn apply(
        &self,
        state: &SystemState,
        request: OperationRequest,
    ) -> Result<Transition, ProtocolError>;
}
```

The agent cannot call:

```rust
state.migration_unit.state = Verified;
```

It must submit:

```rust
OperationRequest::RequestVerification(...)
```

The transition engine decides whether the transition is legal.

---

## 152. Transition Example

Suppose a migration unit is `DESIGNED`. An implementation request arrives.

The protocol checks:

```text
snapshot matches
scope matches
capability exists
design exists
required contract exists
critical unknowns acceptable
implementation authorization exists
```

Only then:

```text
DESIGNED
    ↓
AUTHORIZED_FOR_IMPLEMENTATION
```

and subsequently:

```text
AUTHORIZED_FOR_IMPLEMENTATION
    ↓
IMPLEMENTED
```

after an implementation artifact is actually produced.

---

## 153. Illegal Transition Tests

These should become protocol conformance tests.

| Current state | Operation | Result |
| --- | --- | --- |
| `DESIGNED` | `release()` | DENIED |
| `CONTRACTED` | `modify_source()` | DENIED |
| `IMPLEMENTED` | `mark_verified()` | DENIED |
| `VERIFIED` | `release()` | DENIED, unless release gates satisfied |

The protocol should make these **impossible** rather than relying on agent instructions.

---

# IV. Evidence & contracts

## 154. Evidence Object

```rust
pub struct Evidence {
    pub id: EvidenceId,

    pub snapshot: SnapshotId,

    pub collector: AgentId,

    pub source: EvidenceSource,
    pub observation: Observation,
    pub execution: Option<ExecutionReceipt>,

    pub digest: Digest,

    pub status: EvidenceStatus,
}
```

Evidence source could be:

```rust
pub enum EvidenceSource {
    KernelSource,
    KernelHistory,
    Compiler,
    StaticAnalyzer,
    Runtime,
    Test,
    DifferentialTest,
    AdversarialTest,
    HumanReview,
}
```

---

## 155. Evidence Status

Use the existing epistemic vocabulary consistently:

```rust
pub enum EvidenceStatus {
    Observed,
    Derived,
    Corroborated,
    Contradictory,
    Invalidated,
}
```

A contradictory evidence item must remain in the ledger.

It must not be deleted because the final conclusion changed.

> That is essential for scientific-style reconstruction.

---

## 156. Contract Ledger

A contract should be composed from separate dimensions.

```rust
pub struct Contract {
    pub id: ContractId,

    pub function: FunctionId,

    pub preconditions: Vec<InvariantId>,
    pub postconditions: Vec<InvariantId>,

    pub ownership: OwnershipContract,
    pub lifetime: LifetimeContract,

    pub concurrency: ConcurrencyContract,
    pub context: ExecutionContextContract,

    pub allocation: AllocationContract,
    pub abi: AbiContract,

    pub error: ErrorContract,
    pub security: SecurityContract,

    pub evidence: Vec<EvidenceId>,
}
```

This prevents a vague statement like:

> "The function is safe."

from being treated as a contract.

---

## 157. Unknowns Become Contract Members

Example:

```rust
pub enum ContractKnowledge<T> {
    Established(T),

    Partial {
        known: T,
        unknowns: Vec<UnknownId>,
    },

    Unknown(Vec<UnknownId>),
}
```

Then:

```text
RCU lifetime:
    PARTIAL

Lock nesting:
    ESTABLISHED

NMI behavior:
    UNKNOWN
```

The implementation gate can explicitly say:

```text
NMI behavior required?
    YES

NMI behavior:
    UNKNOWN

=> BLOCKED
```

---

## 158. Rust Design IR

The design phase should produce a representation before source code.

```rust
pub struct RustDesign {
    pub types: Vec<RustType>,
    pub traits: Vec<RustTrait>,

    pub ownership: Vec<OwnershipMapping>,
    pub lifetimes: Vec<LifetimeMapping>,

    pub synchronization: Vec<SyncMapping>,

    pub ffi_boundaries: Vec<FfiBoundary>,

    pub unsafe_regions: Vec<UnsafeObligation>,
}
```

This creates a useful distinction:

```text
C semantics
     ↓
   KSIR
     ↓
Kernel Contract
     ↓
Rust Design IR
     ↓
Rust source
```

The LLM should not jump directly from `C source` to `Rust source`.

---

## 159. Unsafe Obligation Registry

Every unsafe region gets an explicit record.

```rust
pub struct UnsafeObligation {
    pub id: ObligationId,

    pub source_location: SourceLocation,
    pub reason: UnsafeReason,

    pub obligations: Vec<SafetyObligation>,

    pub evidence: Vec<EvidenceId>,

    pub verification: VerificationStatus,
}
```

Possible obligations:

```rust
pub enum SafetyObligation {
    PointerValid,
    PointerAligned,
    Initialized,
    ObjectAlive,
    AliasingControlled,
    SynchronizationHeld,
    RefcountValid,
    RcuProtectionActive,
    InterruptContextValid,
    ArchitectureAssumption,
    AbiCompatible,
}
```

This turns `unsafe { ... }` into an explicit verification target.

---

# V. Protocol guarantees

## 160. Protocol Invariants

Now the protocol itself needs invariants.

| ID | Invariant | Statement |
| --- | --- | --- |
| P1 | Snapshot integrity | Every migration artifact belongs to exactly one snapshot. |
| P2 | Authorization integrity | No mutation without valid authorization. |
| P3 | Capability integrity | Authorization cannot exceed agent capability. |
| P4 | Evidence integrity | VERIFIED requires evidence. |
| P5 | Authority separation | Implementation authority cannot self-attest verification. |
| P6 | Immutable history | Committed artifacts and events are never silently rewritten. |
| P7 | Scope integrity | An operation cannot modify outside its authorized scope. |
| P8 | Replay integrity | Ledger replay must reconstruct canonical state. |
| P9 | Conflict integrity | Unresolved critical conflicts block authorization. |
| P10 | Snapshot isolation | Evidence from S1 cannot silently verify a claim about S2. |

These are now candidates for **machine-checkable protocol properties**.

---

## 161. Conformance Suite

The protocol needs its own QA system.

```text
RFL-PROTO-QA
├── identity
├── snapshot
├── capability
├── authorization
├── scope
├── state-machine
├── artifact
├── evidence
├── conflict
├── event-ledger
├── replay
├── isolation
└── adversarial
```

Especially important:

```text
authorization bypass tests
scope escape tests
replay divergence tests
stale capability tests
cross-snapshot contamination tests
self-verification tests
artifact substitution tests
```

---

## 162. Adversarial Protocol Tests

Before trusting the AI layer, attack the control plane.

```text
Agent A:
    valid READ capability

attempt:
    MODIFY_SOURCE

expected:
    DENIED
```

```text
Agent A:
    MODIFY_SOURCE for file X

attempt:
    modify file Y

expected:
    DENIED
```

```text
Agent A:
    implementation authority

attempt:
    authorize own verification

expected:
    DENIED
```

```text
Agent A:
    capability from snapshot S1

attempt:
    operate on S2

expected:
    DENIED
```

```text
Agent A:
    stale epoch

attempt:
    execute old authorization

expected:
    DENIED
```

These tests are arguably more important than early LLM benchmarks.

---

## 163. Agent Manifest

Every agent should declare its capabilities.

```toml
[agent]
id = "ownership-analyst"
role = "semantic-analysis"

[capabilities]
read_kernel = true
read_ksir = true
derive_ownership = true
propose_contract = true

modify_source = false
authorize = false
verify = false
release = false
```

The runtime should validate the manifest against the issued grants.

An agent cannot simply claim:

```toml
role = verifier
```

and acquire verifier authority.

---

## 164. Agent Self-Model

The earlier CSML-style self-model fits here, but it must remain distinct from authority.

```text
Agent self-model:

capability:
    DERIVE_OWNERSHIP

demonstrated:
    refcount
    intrusive-list

unknown:
    RCU callbacks

limitations:
    PREEMPT_RT
    architecture-specific atomics
```

This is useful for scheduling.

But:

```text
self_model.capability  ≠  protocol.authorization
```

The agent's assertion about itself is not permission.

---

# VI. Orchestration & roadmap

## 165. Scheduling

The orchestrator can then construct a dependency DAG.

Example:

```text
           Source Mapping
                  │
       ┌──────────┼──────────────┐
       ▼          ▼              ▼
   Ownership   Context          ABI
       │          │              │
       └──────────┼──────────────┘
                  ▼
             Concurrency
                  │
                  ▼
              Contract
                  │
                  ▼
             Rust Design
                  │
                  ▼
           Implementation
                  │
                  ▼
       ┌──────────┼──────────────┐
       ▼          ▼              ▼
     Build     Runtime     Differential
       \          |              /
        \         |             /
                  ▼
             Adversarial
                  │
                  ▼
                Gate
```

Agents become workers attached to DAG nodes.

---

## 166. Agent Failure Is a First-Class State

Agents will fail. The protocol should represent:

```rust
pub enum AgentOutcome {
    Completed,
    Blocked,
    Contradiction,
    Timeout,
    ToolFailure,
    EvidenceFailure,
    CapabilityDenied,
    Quarantined,
}
```

Not:

```text
agent disappeared
```

or:

```text
LLM generated nothing
```

The orchestrator can then retry, replace, or escalate without corrupting state.

---

## 167. Agent Replacement

A useful property:

```text
Agent A
   ↓
produces Artifact X
```

Another agent, `Agent B`, should be able to continue from X.

Therefore the system should not depend on hidden conversational state.

```text
Artifact + Evidence + Task state + Protocol state = continuation point
```

This is the difference between an **agent workflow** and an **agent-dependent workflow**.

---

## 168. Human Intervention

Human intervention should also use the protocol.

Not:

```text
human edits database
```

but:

```text
Human Review
     ↓
Review Artifact
     ↓
  Evidence
     ↓
Authorization / Rejection
     ↓
   Event
```

Humans therefore become another authority class.

```text
DISCOVERY  DESIGN  IMPLEMENTATION  VERIFICATION  REVIEW  RELEASE
```

The exact privileges can be separately defined.

---

## 169. What This Gives Us

At this point RFL-AE has three independently testable systems:

```text
                RFL-AE
                   │
        ┌──────────┼───────────┐
        ▼          ▼           ▼
    SEMANTIC    CONTROL    EVIDENCE
     ENGINE      PLANE       PLANE
        │          │           │
      KSIR       Tasks     Receipts
    Contracts    Auth       Claims
     Design      Gates    Provenance
```

And importantly:

```text
Semantic engine can be wrong
        ↓
Evidence catches / exposes it


Agent can be wrong
        ↓
Control plane limits authority


Verification can be incomplete
        ↓
Gate prevents release
```

---

## 170. The First End-to-End Demonstrator

The first real RFL-AE implementation should now be a deliberately tiny migration — something
like `RFL-AE-LAB-001` — with:

```text
C object
   |
   +-- intrusive linkage
   +-- reference count
   +-- lock
   +-- callback
   +-- lifetime rule
   +-- one FFI boundary
   |
   v
  KSIR
   |
   v
Contract
   |
   v
Rust Design IR
   |
   v
Rust implementation
   |
   +-- unit tests
   +-- concurrency tests
   +-- differential test
   +-- deliberate incorrect implementation
   |
   v
Evidence Bundle
   |
   v
Release Gate
```

The deliberate incorrect implementation is important.

The system must demonstrate not only:

```text
correct implementation → accepted
```

but:

```text
incorrect implementation → detected → blocked
```

That is the first meaningful proof that the architecture is doing something beyond generating
code.

---

## 171. Development Order

Freeze the implementation sequence here:

```text
PHASE  0  Protocol types
    ↓
PHASE  1  State machine
    ↓
PHASE  2  Capability + authorization
    ↓
PHASE  3  Immutable event ledger
    ↓
PHASE  4  Artifact/evidence store
    ↓
PHASE  5  Replay engine
    ↓
PHASE  6  KSIR minimum implementation
    ↓
PHASE  7  Contract engine
    ↓
PHASE  8  Rust Design IR
    ↓
PHASE  9  Lab migration
    ↓
PHASE 10  Adversarial protocol QA
    ↓
PHASE 11  LLM agents
```

The ordering matters.

> ### **LLM agents come late.**

Otherwise the system risks spending most of its engineering effort making an
intelligent-looking agent operate a protocol that has never itself been proven to enforce its
invariants.

---

## 172. Immediate Next Specification

The next document should therefore be:

```text
RFL-AE-PROTOCOL-001
"Deterministic Agent Execution Protocol"
```

with these normative sections:

1. Scope
2. Terminology
3. Kernel Snapshot Identity
4. Task Model
5. Migration Unit Model
6. Agent Identity
7. Capability Model
8. Authorization Model
9. Artifact Model
10. Evidence Model
11. Event Model
12. State Machines
13. Transition Rules
14. Conflict Protocol
15. Quarantine Protocol
16. Replay Semantics
17. Scope Enforcement
18. Authority Separation
19. Failure Semantics
20. Conformance Requirements
21. Adversarial Requirements
22. Serialization / Canonicalization
23. Versioning
24. Compatibility
25. Security Model

---

## Next step

Then the next implementation artifact should be the **normative transition table**.

For every state transition we should specify:

```text
CURRENT STATE
  + OPERATION
  + ACTOR CAPABILITY
  + REQUIRED ARTIFACTS
  + REQUIRED EVIDENCE
  + REQUIRED AUTHORIZATION
  + PRECONDITIONS
        ↓
NEW STATE
  + EMITTED EVENT
```

That table is where the architecture stops being descriptive and becomes **mechanically
enforceable**.

---

**Done — see [TRANSITIONS.md](TRANSITIONS.md)** (§173–§203), which specifies that table: the
7-stage validation kernel, the 11-row normative transition table, illegal transitions,
transition predicates, typed rejection reasons, staleness propagation, the read/write authority
matrix, gate algebra, proof obligations P-001–P-010, and the trusted/untrusted LLM boundary.
