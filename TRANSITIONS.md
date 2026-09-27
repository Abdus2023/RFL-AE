# RFL-AE — Normative Transition System

**Sections 173–203** — `RFL-AE-PROTOCOL-001`.

> Continues the numbering of [ARCHITECTURE.md](ARCHITECTURE.md) (§1–§51),
> [SPECIFICATION.md](SPECIFICATION.md) (§52–§80), [FORMAL-CORE.md](FORMAL-CORE.md)
> (§81–§107), [PROTOCOL.md](PROTOCOL.md) (§109–§135), and [RUST-CORE.md](RUST-CORE.md)
> (§136–§172). §108 does not exist in the source.

We can now formalize the state machine itself.

The goal is not merely to document valid workflows. The goal is:

> ### **An implementation that makes illegal engineering transitions unrepresentable or mechanically rejectable.**

The protocol should therefore have a small deterministic kernel.

## Contents

| Part | Sections |
| --- | --- |
| [I. Transition kernel](#173-rfl-ae-protocol-001-normative-transition-system) | 173–178 |
| [II. Dependencies & semantics](#179-dependency-conditions) | 179–184 |
| [III. Snapshot, epoch, staleness](#185-snapshot-evolution) | 185–191 |
| [IV. Gates & authority](#192-readwrite-authority-matrix) | 192–198 |
| [V. The AI boundary](#199-the-ai-layer-finally-fits) | 199–203 |

<details>
<summary><strong>Full section index</strong></summary>

173. RFL-AE-PROTOCOL-001: Normative Transition System
174. Normative Transition Table
175. Illegal Transitions Are Part of the Specification
176. Transition Predicate
177. Typed Rejection Reasons
178. Critical Unknowns
179. Dependency Conditions
180. Semantic Dependency vs Source Dependency
181. Kernel Semantic Graph
182. Contract Normal Form
183. Contract IDs and Invariants
184. Claim Graph
185. Snapshot Evolution
186. Epochs
187. Stale Artifact Detection
188. Staleness Graph
189. Agent Scheduling with Staleness
190. Concurrency Control
191. Migration-Unit Lease
192. Read/Write Authority Matrix
193. Verification Is Not Binary
194. Verification Matrix Example
195. Gate Algebra
196. No Hidden Gate Logic
197. Protocol Self-Verification
198. Minimal Protocol Proof Obligations
199. The AI Layer Finally Fits
200. LLM Boundary
201. Tool Boundary
202. Example: Agent Investigating an RCU Question
203. What We Should Build Next

</details>

---

# I. Transition kernel

## 173. RFL-AE-PROTOCOL-001: Normative Transition System

```text
     OperationRequest
             │
             ▼
  ┌─────────────────────┐
  │ Identity validation │
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │ Snapshot validation │
  └──────────┬──────────┘
             │
             ▼
   ┌──────────────────┐
   │ Capability check │
   └─────────┬────────┘
             │
             ▼
      ┌─────────────┐
      │ Scope check │
      └──────┬──────┘
             │
             ▼
   ┌──────────────────┐
   │ State transition │
   │ preconditions    │
   └─────────┬────────┘
             │
             ▼
  ┌─────────────────────┐
  │ Evidence validation │
  └──────────┬──────────┘
             │
             ▼
 ┌──────────────────────┐
 │ Emit canonical event │
 └───────────┬──────────┘
             │
             ▼
    New canonical state
```

---

## 174. Normative Transition Table

The migration-unit lifecycle becomes:

| Current | Operation | Required condition | Result |
| --- | --- | --- | --- |
| `DISCOVERED` | map | source/symbol evidence | `MAPPED` |
| `MAPPED` | contract | required semantic dimensions analyzed | `CONTRACTED` |
| `CONTRACTED` | design | contract sufficiently established | `DESIGNED` |
| `DESIGNED` | authorize implementation | authorization gate passes | `AUTHORIZED_FOR_IMPLEMENTATION` |
| `AUTHORIZED_FOR_IMPLEMENTATION` | implement | scoped writer capability | `IMPLEMENTED` |
| `IMPLEMENTED` | authorize testing | implementation artifact exists | `AUTHORIZED_FOR_TESTING` |
| `AUTHORIZED_FOR_TESTING` | verify | required execution evidence | `VERIFIED` or `PARTIALLY_VERIFIED` |
| `VERIFIED` | adversarial verify | adversarial gates pass | `ADVERSARIALLY_VERIFIED` |
| `ADVERSARIALLY_VERIFIED` | review | review authority | `AUTHORIZED_FOR_REVIEW` |
| `AUTHORIZED_FOR_REVIEW` | release gate | all release predicates pass | `RELEASE_ELIGIBLE` |
| `RELEASE_ELIGIBLE` | release | release authority | `RELEASED` |

There should be **no implicit transitions**.

---

## 175. Illegal Transitions Are Part of the Specification

For example:

```text
DISCOVERED
    └── implement           => DENIED

MAPPED
    └── release             => DENIED

DESIGNED
    └── modify_source       => DENIED

IMPLEMENTED
    └── self_verify         => DENIED

VERIFIED
    └── release             => DENIED
          unless release predicates are independently satisfied
```

The negative space is important.

> A secure protocol is defined partly by what it **refuses to do**.

---

## 176. Transition Predicate

Define every transition as a predicate:

```text
Transition(S, O, A, E) -> Result
```

where:

```text
S = current state
O = requested operation
A = authority/capability
E = available evidence
```

For example:

```text
AuthorizeImplementation =
    state == DESIGNED
AND capability contains REQUEST_AUTHORIZATION
AND contract.valid
AND design.valid
AND no_critical_unknowns
AND required_dependencies_satisfied
AND authorization authority is independent
```

The important part is that the LLM never evaluates this predicate authoritatively.

**The protocol does.**

---

## 177. Typed Rejection Reasons

Never return only:

```text
DENIED
```

Return structured failure.

```rust
pub enum ProtocolError {
    UnknownTask,
    UnknownSnapshot,
    SnapshotMismatch,

    CapabilityMissing,
    CapabilityExpired,
    CapabilityScopeViolation,

    InvalidStateTransition,
    MissingArtifact,
    MissingEvidence,
    InvalidEvidence,

    AuthorizationMissing,
    AuthorizationExpired,
    AuthorityConflict,

    CriticalUnknown,
    UnresolvedConflict,

    ConcurrentWriter,
    StaleEpoch,

    ReplayMismatch,
}
```

Then the orchestrator can react deterministically.

Example:

```text
CapabilityScopeViolation  → do not retry blindly
MissingEvidence           → schedule evidence task
CriticalUnknown           → schedule investigation
ConcurrentWriter          → wait/reconcile
ReplayMismatch            → quarantine protocol state
```

---

## 178. Critical Unknowns

Not all unknowns should block everything. Introduce severity:

```rust
pub enum UnknownSeverity {
    Informational,
    Relevant,
    Critical,
}
```

Example:

```text
function comments:
    UNKNOWN
    severity = Informational
```

versus:

```text
callback execution context:
    UNKNOWN
    severity = Critical
```

Then:

```text
Critical Unknown
        +
Affected invariant
        +
Required for current operation
        ↓
      BLOCK
```

This avoids both extremes:

```text
everything unknown → system never moves
```

and:

```text
unknown → ignored
```

---

# II. Dependencies & semantics

## 179. Dependency Conditions

A migration unit should explicitly declare dependencies.

```rust
pub struct MigrationDependencies {
    pub required_contracts: Vec<ContractId>,
    pub required_units: Vec<MigrationUnitId>,
    pub required_apis: Vec<ApiContractId>,
}
```

For example:

```text
MU-041: Rust workqueue callback

depends_on:
    MU-012: work_struct ownership
    MU-018: callback context
    MU-027: worker lifetime
```

The scheduler can then derive:

```text
MU-012 ─────┐
MU-018 ─────┼──> MU-041
MU-027 ─────┘
```

rather than relying on an LLM to remember dependencies.

---

## 180. Semantic Dependency vs Source Dependency

This distinction is critical.

A source dependency:

```text
A.c
  includes B.h
```

does not necessarily mean:

```text
migration(A)
  depends_on migration(B)
```

Conversely, `A` may semantically depend upon `B` through:

- ownership
- lifetime
- locking
- callback ordering
- ABI
- scheduler assumptions
- memory ordering

Therefore RFL-AE needs two graphs:

```text
SOURCE GRAPH
    includes
    calls
    references
    links

SEMANTIC GRAPH
    owns
    borrows
    synchronizes
    publishes
    waits
    reclaims
    depends_on
```

> The semantic graph determines migration readiness.

---

## 181. Kernel Semantic Graph

KSIR should eventually expose relationships like:

```text
Object A
 ├── owns → Object B
 ├── protected_by → Lock L
 ├── published_via → RCU R
 ├── reclaimed_by → Callback C
 ├── accessed_from → SOFTIRQ
 └── allocated_by → Allocator X
```

This is much more informative than a call graph.

Example:

```text
work_struct
    |
    +-- embedded in --> foo
    |
    +-- queued by --> queue_work()
    |
    +-- executed by --> worker
    |
    +-- callback --> foo_work()
    |
    +-- lifetime --> foo
```

A Rust migration must preserve the **relationships**, not merely the function signatures.

---

## 182. Contract Normal Form

To make contracts machine-comparable, normalize them.

Instead of:

```text
"must hold the lock before modifying state"
```

represent:

```text
Precondition:
    lock(L) == HELD_BY_CURRENT_CONTEXT

Operation:
    write(field)

Postcondition:
    field_updated == true
```

Similarly:

```text
RCU:

Pre:
    rcu_read_lock_active()

Access:
    dereference_rcu(P)

Post:
    no reclamation before grace-period completion
```

The exact representation can evolve, but the principle should be fixed:

> ### **Natural-language explanations are views over canonical contract objects.**

---

## 183. Contract IDs and Invariants

Every important invariant receives an identity.

```text
INV-WQ-001
    Work item cannot be concurrently owned by incompatible queue states.

INV-WQ-002
    Callback lifetime extends through required execution period.

INV-WQ-003
    Cancellation waits for relevant execution completion.

INV-WQ-004
    Required synchronization ordering is preserved.
```

Then:

```text
Rust unsafe block
    satisfies:
        INV-WQ-002
        INV-WQ-004
```

Tests can target the same identifiers.

This creates traceability:

```text
C source
   ↓
Invariant
   ↓
Contract
   ↓
Rust design
   ↓
Code
   ↓
Test
   ↓
Evidence
```

---

## 184. Claim Graph

The evidence system should maintain a graph rather than a flat collection.

```text
CLAIM-001
   |
   +-- derived_from --> OBS-011
   |
   +-- supported_by --> TEST-091
   |
   +-- supported_by --> EXEC-144
   |
   +-- contradicted_by --> TEST-102
   |
   +-- invalidated_by --> SNAPSHOT-CHANGE
```

This permits a claim to become invalid without deleting its historical existence.

---

# III. Snapshot, epoch, staleness

## 185. Snapshot Evolution

Suppose `Linux S1` contains `Invariant X`. Then upstream changes code in `Linux S2`.

The system should not silently rewrite X.

Instead:

```text
X@S1
   |
   | superseded_by
   v
X'@S2
```

Therefore:

```text
truth
```

is always interpreted as:

```text
truth within a specified snapshot
```

This is particularly important for kernel work because APIs, locking behavior, generated code,
architecture support, and Rust infrastructure evolve.

---

## 186. Epochs

Introduce a protocol epoch:

```rust
pub struct Epoch(pub u64);
```

Every authorization binds to an epoch.

```text
Epoch 41
    |
    +-- capability A
    +-- authorization B
    +-- worktree W
```

A critical contract change can increment the migration-unit epoch:

```text
41 → 42
```

Old authorizations become invalid.

This prevents:

```text
old design
   ↓
old authorization
   ↓
new source state
```

from being accidentally combined.

---

## 187. Stale Artifact Detection

Every artifact records:

```text
snapshot
task
migration unit
epoch
parents
digest
```

Suppose `Design D1 epoch = 12` and contract changes to `epoch = 13`.

Then D1 becomes:

```text
STALE
```

unless explicitly revalidated.

This is preferable to silently reusing an artifact that was valid under an earlier semantic
state.

---

## 188. Staleness Graph

```text
 Contract C1
      │
      ▼
  Design D1
      │
      ▼
  Patch P1
      │
      ▼
  Tests T1
```

Contract changes:

```text
     C1
      │
      ▼
     C2
```

The system propagates invalidation:

```text
C1
  │
  ▼
invalidates D1
  │
  ▼
invalidates P1
  │
  ▼
invalidates T1
```

The new path becomes:

```text
     C2
      │
      ▼
     D2
      │
      ▼
     P2
      │
      ▼
     T2
```

This prevents one of the most dangerous agent-system failures:

> **Continuing a previously valid plan after its assumptions have changed.**

---

## 189. Agent Scheduling with Staleness

The scheduler should therefore operate on:

```text
READY  STALE  BLOCKED  QUARANTINED
```

rather than just:

```text
TODO  DONE
```

Example:

```text
Design Agent
     ↓
D1 READY

Contract Agent
     ↓
C2 replaces C1

Scheduler:
     D1 → STALE

Implementation Agent:
     ↓
cannot consume D1
```

This makes dependency invalidation explicit.

---

## 190. Concurrency Control

There are actually two concurrency problems.

### Agent concurrency

```text
many agents
```

### Kernel semantic concurrency

```text
many CPUs
interrupts
preemption
RCU
locks
atomics
```

They must not be conflated.

RFL-AE itself needs distributed coordination primitives:

```text
task lease
migration-unit lease
worktree lease
artifact version
epoch
```

The kernel analysis layer separately models:

```text
spinlocks
mutexes
atomics
RCU
interrupt contexts
```

---

## 191. Migration-Unit Lease

A lease prevents simultaneous implementation writers.

```rust
pub struct WriterLease {
    pub migration_unit: MigrationUnitId,
    pub agent: AgentId,
    pub epoch: Epoch,
    pub expires_at: Timestamp,
}
```

Invariant:

```text
max_active_writer_leases(MU) == 1
```

Multiple read-only agents remain unrestricted.

---

# IV. Gates & authority

## 192. Read/Write Authority Matrix

| Operation | Discovery | Design | Implementation | Verification | Review | Release |
| --- | --- | --- | --- | --- | --- | --- |
| Read source | yes | yes | yes | yes | yes | yes |
| Create observation | yes | yes | limited | yes | yes | no |
| Create contract | yes | yes | no | review | yes | no |
| Modify source | no | no | yes | no | no | no |
| Execute tests | optional | optional | yes | yes | optional | no |
| Create verification | no | no | no | yes | yes | no |
| Authorize implementation | no | no | no | no | yes | yes |
| Merge | no | no | no | no | no | yes |
| Release | no | no | no | no | no | yes |

The exact authority assignments can evolve, but the **separation principle** should not.

---

## 193. Verification Is Not Binary

A migration unit may pass:

```text
V0 parsing
V1 compilation
V2 unit tests
V3 integration
```

while failing:

```text
V5 concurrency
```

Therefore `VERIFIED` should not be a vague aggregate.

Represent gate dimensions individually:

```rust
pub struct VerificationMatrix {
    pub compile: GateStatus,
    pub unit: GateStatus,
    pub integration: GateStatus,
    pub runtime: GateStatus,
    pub concurrency: GateStatus,
    pub memory: GateStatus,
    pub abi: GateStatus,
    pub differential: GateStatus,
    pub adversarial: GateStatus,
    pub regression: GateStatus,
}
```

Then the release policy determines which dimensions are mandatory.

---

## 194. Verification Matrix Example

```text
          MU-WQ-001
────────────────────────────────────────
Compile              PASS
Unit                 PASS
Integration          PASS
Runtime              PASS
Concurrency          PASS
Memory               PASS
ABI                  PASS
Differential         PASS
Adversarial          BLOCKED
Regression           PASS

Release:     BLOCKED
```

The system should not convert that into:

```text
90% verified
```

because the missing dimension may be precisely the one that matters.

---

## 195. Gate Algebra

Gates should compose formally.

```text
Gate(A AND B)
Gate(A OR B)
Gate(NOT A)
```

Example:

```text
ImplementationRelease =
    Compile
AND ABI
AND RequiredRuntimeTests
AND RequiredConcurrencyTests
AND Differential
AND Adversarial
AND Regression
```

A gate result should contain the evaluated inputs:

```rust
pub struct GateResult {
    pub gate: GateId,
    pub status: GateStatus,
    pub inputs: Vec<GateEvaluation>,
    pub evidence: Vec<EvidenceId>,
}
```

Thus `RELEASE_ELIGIBLE` is derivable from explicit predicates.

---

## 196. No Hidden Gate Logic

Avoid:

```rust
if confidence > 0.9 {
    approve()
}
```

The release gate should be inspectable.

For example:

```text
GATE-RUST-MU-001:

required:
    compile == PASS
    abi == PASS
    differential == PASS
    concurrency == PASS
    adversarial == PASS
    unresolved_critical_conflicts == 0
    stale_artifacts == 0
```

Now the gate itself can be tested.

---

## 197. Protocol Self-Verification

The system must verify its own control plane.

This produces a recursive but bounded structure:

```text
 RFL-AE protocol
        │
        ▼
  RFL-PROTO-QA
        │
        ▼
protocol evidence
        │
        ▼
protocol release gate
```

Only after that should it control kernel migration experiments.

Otherwise:

```text
unverified orchestrator
       ↓
claims to verify kernel code
```

would undermine the entire architecture.

---

## 198. Minimal Protocol Proof Obligations

Before RFL-AE is allowed to execute a real migration, demonstrate at least:

| ID | Obligation |
| --- | --- |
| P-001 | Cannot mutate without task. |
| P-002 | Cannot mutate outside scope. |
| P-003 | Cannot mutate another migration unit. |
| P-004 | Cannot use stale authorization. |
| P-005 | Implementation agent cannot self-attest. |
| P-006 | Verification requires execution evidence. |
| P-007 | Cross-snapshot evidence is rejected. |
| P-008 | Critical unresolved conflict blocks authorization. |
| P-009 | Replay reconstructs identical state. |
| P-010 | Invalid artifacts cannot enter canonical state. |

These become the first **RFL-PROTO-QA** acceptance criteria.

---

# V. The AI boundary

## 199. The AI Layer Finally Fits

Only now should we define the LLM agent interface.

The LLM does **not** receive:

```text
"Here is the whole repository. Rewrite this."
```

It receives:

```text
Task
Snapshot
Scope
Relevant artifacts
Relevant evidence
Current unknowns
Current conflicts
Available tools
Granted capabilities
Required output schema
```

Its output is constrained to something like:

```rust
enum AgentProposal {
    ObservationProposal(...),
    HypothesisProposal(...),
    ContractProposal(...),
    DesignProposal(...),
    PatchProposal(...),
    TestPlanProposal(...),
    InvestigationRequest(...),
}
```

The protocol then validates the proposal.

---

## 200. LLM Boundary

The architectural boundary becomes:

```text
                TRUSTED
────────────────────────────────────────
Protocol
Ledger
Authorization
Scope enforcement
Artifact hashing
Evidence binding
Gate evaluation
State machine
────────────────────────────────────────
                UNTRUSTED
────────────────────────────────────────
LLM reasoning
LLM-generated code
LLM explanations
LLM hypotheses
LLM prioritization
────────────────────────────────────────
```

This is the correct place to put the model.

> The LLM can be extremely capable without becoming the authority.

---

## 201. Tool Boundary

The same rule applies to tools.

```text
        Agent
          │
          ▼
    Tool Request
          │
          ▼
Capability Validator
          │
          ▼
    Tool Executor
          │
          ▼
  Execution Receipt
          │
          ▼
   Artifact Store
```

A tool result is not trusted merely because an agent requested it.

Its execution context must be recorded.

---

## 202. Example: Agent Investigating an RCU Question

A concurrency agent receives:

```text
MU-042

Question:
    Is object X guaranteed alive during callback Y?
```

It can request:

```text
READ_SOURCE
READ_HISTORY
READ_CALLGRAPH
RUN_STATIC_ANALYSIS
```

It produces:

```text
Hypothesis H17:
    X remains alive until callback completion.
```

The protocol records H17 as:

```text
HYPOTHESIS
```

The agent cannot promote it directly to:

```text
VERIFIED
```

Another worker executes relevant experiments.

Suppose evidence shows:

```text
callback can race with final reference release
```

Then:

```text
H17
   ↓
CONTRADICTED
```

The migration unit enters:

```text
QUARANTINE
```

before Rust implementation.

> That is precisely the behavior we want.

---

## 203. What We Should Build Next

The architecture is now sufficiently constrained to start writing code.

The next concrete artifact should be `rfl-ae/crates/rfl-protocol/` with approximately:

```text
rfl-protocol/
├── src/
│   ├── lib.rs
│   ├── ids.rs
│   ├── snapshot.rs
│   ├── task.rs
│   ├── migration.rs
│   ├── agent.rs
│   ├── capability.rs
│   ├── authorization.rs
│   ├── artifact.rs
│   ├── evidence.rs
│   ├── event.rs
│   ├── conflict.rs
│   ├── gate.rs
│   ├── transition.rs
│   ├── error.rs
│   └── replay.rs
└── tests/
    ├── authorization.rs
    ├── scope.rs
    ├── transitions.rs
    ├── evidence.rs
    ├── stale.rs
    ├── replay.rs
    └── adversarial.rs
```

And the first implementation target should be deliberately narrow:

```text
                 RFL-PROTOCOL-001
                         │
          ┌──────────────┼───────────────┐
          ▼              ▼               ▼
     typed state   authorization      ledger
          │              │               │
          └──────────────┼───────────────┘
                         ▼
                      replay
                         │
                         ▼
                    conformance
```

Once this passes its own adversarial suite, we can attach the first semantic worker:

```text
C source
    ↓
C-semantic agent
    ↓
Observation / KSIR fragment
    ↓
Protocol
    ↓
Evidence
```

That gives us the first real boundary between **AI reasoning** and **engineering authority**.

---

## Next step

The next major step after that is the **KSIR itself**: defining the semantic representation for
C pointers, objects, ownership, lifetimes, aliases, refcounts, locks, RCU, execution contexts,
allocation contexts, atomics, callbacks, DMA/MMIO, ABI boundaries, architecture assumptions,
and invariants.

That is where the system starts becoming specifically capable of understanding why a Linux C
subsystem can or cannot be translated into a safe Rust design.
