# RFL-AE — Executable Protocol Kernel

> **Provenance and numbering.** This document was supplied as *Next: RFL-AE → executable protocol kernel*, numbered §1–§14 in the source, preceded by an unnumbered *Current state* section and followed by an unnumbered *Immediate implementation sequence* section. To keep the corpus contiguous, its sections are renumbered **§702–§717**, continuing directly from [KSIR-ANALYZER.md](KSIR-ANALYZER.md) (which ends at §701).
>
> **Note the offset here is +702, not +701.** Because the source's *first* section is unnumbered and precedes its §1, it is recorded as source **§0** so that the mapping **`corpus_section = source_section + 702`** stays constant across the whole file: §702 ← §0, §703–§716 ← §1–§14 exactly as the source numbers them, §717 ← the unnumbered closing section recorded as §15. Recording *Current state* as §15 instead would have preserved the constant offset but broken document order, and shifting the source numbers would have lost the source's own numbering. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: EXECUTABLE-KERNEL.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/` tree, no `rfl-types` / `rfl-transition` / `rfl-event-ledger` / `rfl-evidence` / `rfl-gates` crate, no `linux/` manifest tree, no `DOMAIN-TYPES.md`, and no conformance test has been written or compiled. The repository status remains `v0.0` — documentation only, and §702's own table still describes the protocol, transition engine, evidence ledger and gate engine as not executable.

> **Transcription note (derived treatment — delete if unwanted).** The pasted source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/EXECUTABLE-KERNEL.py`](diagrams/EXECUTABLE-KERNEL.py); re-running it reproduces all 57 diagrams. Six of them (the epoch fan-out, the transition-request flow, the task state machine, the replay divergence, the agent hierarchy and the BAD/GOOD chains) are laid out with ASCII art — `|`, `v`, `+--`, `+--------+` — because the source used ASCII and earlier corpus documents do the same; they are kept in ASCII rather than converted to box-drawing glyphs, and no block mixes the two character sets. The subsystem record in §714 is fenced as `yaml` and the naive `GateStatus` enum in §704 as `rust`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The repository has crossed an important boundary: the architecture is sufficiently mature to stop adding conceptual layers and start making its invariants executable.

The external Linux/Rust environment reinforces this direction. Rust in Linux is `no_std`, uses kernel-specific abstractions over C bindings, and currently still depends on some unstable Rust features; subsystem maintainers remain the relevant authority for accepting Rust changes.

---

## Contents

- [702. Current state](#702-current-state)
- [703. Freeze the semantic vocabulary](#703-freeze-the-semantic-vocabulary)
- [704. Define the gate algebra](#704-define-the-gate-algebra)
- [705. Introduce a canonical `Epoch`](#705-introduce-a-canonical-epoch)
- [706. Build `rfl-types`](#706-build-rfl-types)
- [707. Then build `rfl-transition`](#707-then-build-rfl-transition)
- [708. Formal transition relation](#708-formal-transition-relation)
- [709. State machine](#709-state-machine)
- [710. Negative transitions become first-class tests](#710-negative-transitions-become-first-class-tests)
- [711. Add the event ledger before agents](#711-add-the-event-ledger-before-agents)
- [712. Evidence must bind to objects, not claims alone](#712-evidence-must-bind-to-objects-not-claims-alone)
- [713. Separate technical certification from upstream acceptance](#713-separate-technical-certification-from-upstream-acceptance)
- [714. Linux subsystem manifest](#714-linux-subsystem-manifest)
- [715. Agent architecture comes after this](#715-agent-architecture-comes-after-this)
- [716. Do not start with a swarm](#716-do-not-start-with-a-swarm)
- [717. Immediate implementation sequence](#717-immediate-implementation-sequence)

---

## 702. Current state
<!-- source: EXECUTABLE-KERNEL.md §0 -->

| Layer | Status | Meaning |
| --- | --- | --- |
| Architecture | **PARTIALLY_VERIFIED** | Strong conceptual separation |
| Corpus numbering/provenance | **VERIFIED** | Structural audit passed |
| Specification | **PARTIALLY_VERIFIED** | Several undefined/cross-document types remain |
| Protocol | **PROVISIONAL** | Not executable |
| Transition engine | **NOT IMPLEMENTED** | No authoritative state machine |
| Evidence ledger | **NOT IMPLEMENTED** | No replayable evidence authority |
| Gate engine | **NOT IMPLEMENTED** | Gates are specified, not enforced |
| Agent execution | **NOT AUTHORIZED** | Correct decision at this stage |
| Linux integration | **NOT IMPLEMENTED** | No machine-readable subsystem inventory |
| CI authority | **OPEN** | Repository has no authoritative CI execution layer |

The critical principle now becomes:

> **RFL-AE must be able to reject an invalid agent action without asking an LLM whether the action is valid.**

---

## 703. Freeze the semantic vocabulary
<!-- source: EXECUTABLE-KERNEL.md §1 -->

The first implementation artifact should be a canonical type registry.

I would add:

```text
DOMAIN-TYPES.md
```

with a single authoritative definition for every cross-document primitive.

For example:

```text
SnapshotId
KernelSnapshotId
TaskId
AgentId
ArtifactId
EvidenceId
ContractId
GateId
AuthorizationId
EventId

Digest
GitObjectId

ArchitectureId
SubsystemId
ToolchainFingerprint
EnvironmentFingerprint

GateStatus
VerificationStatus
EvidenceStatus
ExecutionStatus
ProcessOutcome
```

The existing ambiguity around:

```text
SnapshotId
KernelSnapshotId
```

must be resolved before implementation.

Do not permit two identifiers to coexist merely because they sound semantically similar.

A good rule:

```text
KernelSnapshotId
    identifies a Linux source snapshot
SnapshotId
    SHOULD NOT exist unless it means something
    materially different from KernelSnapshotId
```

If they are equivalent, eliminate one.

---

## 704. Define the gate algebra
<!-- source: EXECUTABLE-KERNEL.md §2 -->

The `GateStatus` problem is more important than it initially appears.

Do not simply add:

```rust
enum GateStatus {
    Pass,
    Fail,
    Blocked,
    NotApplicable,
    Invalidated,
}
```

Instead distinguish three concepts.

### Gate condition

What the gate requires.

```rust
pub struct Gate {
    pub id: GateId,
    pub scope: Scope,
    pub predicate: GatePredicate,
}
```

### Gate evaluation

What happened when the predicate was evaluated.

```rust
pub enum GateStatus {
    Pass,
    Fail,
    Blocked,
    NotApplicable,
    Invalidated,
}
```

### Gate result

The immutable evidence-bearing result.

```rust
pub struct GateResult {
    pub gate_id: GateId,
    pub status: GateStatus,
    pub evidence: Vec<EvidenceId>,
    pub evaluated_against: SnapshotId,
}
```

This prevents an important semantic collapse:

```text
Gate
  ≠ GateStatus
  ≠ GateResult
```

That distinction should become normative.

---

## 705. Introduce a canonical `Epoch`
<!-- source: EXECUTABLE-KERNEL.md §3 -->

The existing snapshot/epoch idea should become an actual protocol primitive.

```rust
pub struct Epoch {
    pub snapshot: KernelSnapshotId,
    pub specification_digest: Digest,
    pub protocol_version: String,
    pub generation: u64,
}
```

Every authorization, artifact, evidence record and task execution should be bound to an epoch.

Conceptually:

```text
                   EPOCH
                     |
        +------------+------------+
        |            |            |
      TASK     AUTHORIZATION  ARTIFACT
        |            |            |
        +------------+------------+
                     |
                 EVIDENCE
                     |
                   GATES
                     |
                CERTIFICATE
```

This gives RFL-AE a strong stale-state invariant:

```text
artifact.epoch == authorization.epoch
artifact.epoch == task.epoch
evidence.epoch == artifact.epoch
gate.epoch == evidence.epoch
```

Otherwise:

```text
REJECT
```

not:

```text
WARNING
```

---

## 706. Build `rfl-types`
<!-- source: EXECUTABLE-KERNEL.md §4 -->

The first actual Rust crate should therefore be deliberately boring.

```text
crates/
└── rfl-types/
    ├── Cargo.toml
    └── src/
        ├── lib.rs
        ├── ids.rs
        ├── snapshot.rs
        ├── task.rs
        ├── authorization.rs
        ├── artifact.rs
        ├── evidence.rs
        ├── contract.rs
        ├── verification.rs
        ├── gate.rs
        └── errors.rs
```

```text
No LLM dependency.
No async runtime.
No network.
No filesystem authority.
No agent framework.
No plugin system.
```

The crate should contain **domain types and invariants only**.

---

## 707. Then build `rfl-transition`
<!-- source: EXECUTABLE-KERNEL.md §5 -->

The second crate becomes the actual protocol authority.

```text
crates/
├── rfl-types/
└── rfl-transition/
    ├── Cargo.toml
    └── src/
        ├── lib.rs
        ├── machine.rs
        ├── transition.rs
        ├── preconditions.rs
        ├── authorization.rs
        ├── scope.rs
        └── errors.rs
```

The important design constraint:

> Agents do not transition state.
>
> They **request** transitions.

```text
Agent
  |
  | TransitionRequest
  v
Protocol Engine
  |
  +-- validate epoch
  +-- validate task
  +-- validate authority
  +-- validate capability
  +-- validate scope
  +-- validate preconditions
  +-- validate artifact
  |
  v
Transition
```

Only the transition engine produces the new authoritative state.

---

## 708. Formal transition relation
<!-- source: EXECUTABLE-KERNEL.md §6 -->

The protocol should expose something conceptually equivalent to:

```text
δ : (State, Request) → Result
```

where:

```text
Result =
    Accepted(NewState, Event)
  | Rejected(Reason)
```

Never:

```text
Result = "probably okay"
```

Never:

```text
Result = "LLM believes valid"
```

Never:

```text
Result = "majority of agents approved"
```

This aligns with the architecture's existing rejection of consensus as semantic truth.

---

## 709. State machine
<!-- source: EXECUTABLE-KERNEL.md §7 -->

Start with the smallest useful state machine.

```text
TASK
CREATED
   |
   v
ADMITTED
   |
   v
AUTHORIZED
   |
   v
EXECUTING
   |
   +--------+
   |        |
   v        v
SUCCEEDED  FAILED
   |
   v
VERIFIED
   |
   v
GATED
   |
   v
CERTIFIED
```

But importantly:

```text
FAILED ──X──> VERIFIED
```

and:

```text
AUTHORIZED ──X──> CERTIFIED
```

and:

```text
EXECUTING ──X──> CERTIFIED
```

The protocol should make those impossible rather than relying on agent discipline.

---

## 710. Negative transitions become first-class tests
<!-- source: EXECUTABLE-KERNEL.md §8 -->

This is where RFL-AE becomes genuinely interesting.

The first conformance suite should deliberately attack the protocol.

### Test A — stale authorization

```text
authorize(epoch=10)
snapshot changes
execute(epoch=10)
```

Expected:

```text
REJECT(STALE_EPOCH)
```

### Test B — cross-snapshot artifact

```text
artifact.snapshot = A
authorization.snapshot = B
```

Expected:

```text
REJECT(SNAPSHOT_MISMATCH)
```

### Test C — scope escape

```text
authorized:
    drivers/net/foo.c
requested:
    kernel/sched/core.c
```

Expected:

```text
REJECT(SCOPE_VIOLATION)
```

### Test D — self-verification

```text
agent produces artifact
same authority declares:
    artifact verified
```

Expected:

```text
REJECT(SELF_VERIFICATION)
```

### Test E — forged evidence

```text
Evidence {
    claim: PASS
    artifact: nonexistent
}
```

Expected:

```text
REJECT(EVIDENCE_NOT_BOUND)
```

### Test F — duplicate operation

```text
execute(operation_id=42)
execute(operation_id=42)
```

Expected:

```text
first
 -> ACCEPTED
second
 -> REJECT(DUPLICATE_OPERATION)
```

### Test G — replay divergence

```text
    events[0..N]
          |
          v
      replay()
          |
          v
       state_A

 original execution
          |
          v
       state_B
```

Invariant:

```text
state_A == state_B
```

If not:

```text
REPLAY_FAILURE
```

---

## 711. Add the event ledger before agents
<!-- source: EXECUTABLE-KERNEL.md §9 -->

This is the next architectural pivot.

```text
rfl-types
  ↓
rfl-transition
  ↓
rfl-event-ledger
```

An event should be immutable:

```rust
pub struct Event {
    pub id: EventId,
    pub epoch: Epoch,
    pub sequence: u64,
    pub actor: AgentId,
    pub operation: Operation,
    pub previous_state: Digest,
    pub resulting_state: Digest,
    pub timestamp: Timestamp,
}
```

The important property is not the timestamp.

It is:

```text
previous_state_hash
        + operation
        + resulting_state_hash
```

This makes replay divergence detectable.

---

## 712. Evidence must bind to objects, not claims alone
<!-- source: EXECUTABLE-KERNEL.md §10 -->

The evidence model should reject:

```text
"cargo test passed"
```

as sufficient evidence.

Instead:

```text
Evidence
├── subject
│   └── artifact
├── operation
├── command
├── environment
├── toolchain
├── input digest
├── output digest
├── exit status
└── timestamp
```

For example:

```text
EvidenceRecord {
    subject: ArtifactId,
    source: ExecutionId,
    environment: EnvironmentFingerprint,
    toolchain: ToolchainFingerprint,
    input_digest: Digest,
    output_digest: Digest,
    outcome: PASS,
}
```

This matters particularly for kernel work because the Rust toolchain itself is a meaningful part of the build environment. Current kernel documentation explicitly describes minimum Rust requirements and `rustc`-dependent build configuration.

---

## 713. Separate technical certification from upstream acceptance
<!-- source: EXECUTABLE-KERNEL.md §11 -->

This is a major addition I recommend.

RFL-AE currently has something close to:

```text
RELEASE_ELIGIBLE
```

But Linux has another authority dimension.

A technically verified Rust subsystem does **not** automatically mean:

```text
acceptable upstream patch
```

Current Rust-for-Linux policy explicitly places Rust integration within normal subsystem maintainer authority, and Rust changes generally involve both the relevant subsystem maintainers/reviewers and the Rust subsystem.

Therefore introduce:

```text
TechnicalCertification
```

and separately:

```text
UpstreamAcceptanceState
```

For example:

```text
TechnicalCertification
    UNVERIFIED
    VERIFIED
    INVALIDATED
```

```text
UpstreamAcceptanceState
    NOT_SUBMITTED
    UNDER_REVIEW
    REVIEWED
    ACCEPTED
    REJECTED
    SUPERSEDED
```

Do **not** allow:

```text
VERIFIED
        = UPSTREAM_ACCEPTED
```

They are different propositions.

---

## 714. Linux subsystem manifest
<!-- source: EXECUTABLE-KERNEL.md §12 -->

Once the protocol kernel exists, the Linux-specific layer should become machine-readable.

```text
linux/
├── subsystems/
│   ├── scheduler.yaml
│   ├── memory.yaml
│   ├── rcu.yaml
│   ├── workqueue.yaml
│   ├── vfs.yaml
│   ├── block.yaml
│   ├── networking.yaml
│   └── ...
├── architectures/
├── toolchains/
├── configurations/
├── verification/
└── maintainers/
```

A subsystem record could look like:

```yaml
id: scheduler
family: core
source_paths:
  - kernel/sched/
semantic_domains:
  - tasks
  - scheduling
  - locking
  - cpu-topology
migration_class:
  - semantic_reconstruction
  - unsafe_boundary
  - concurrency_sensitive
verification_backends:
  - compile
  - kunit
  - lockdep
  - kasan
  - kcsan
  - runtime
  - differential
maintainer_authority:
  required: true
```

This is where the architecture stops being a generic agent framework and becomes a **Linux reconstruction system**.

---

## 715. Agent architecture comes after this
<!-- source: EXECUTABLE-KERNEL.md §13 -->

The agent hierarchy should therefore be:

```text
                  HUMAN / MAINTAINER
                           |
                   POLICY AUTHORITY
                           |
                    RFL-AE PROTOCOL
                           |
        +------------------+------------------+
        |                  |                  |
 RECONSTRUCTION         DESIGN          VERIFICATION
     AGENTS             AGENTS             AGENTS
        |                  |                  |
        +------------------+------------------+
                           |
                    ARTIFACT STORE
                           |
                    EVIDENCE LEDGER
                           |
                      GATE ENGINE
                           |
                 TECHNICAL CERTIFICATE
                           |
                 UPSTREAM REVIEW STATE
```

The critical inversion is:

```text
BAD:
LLM
 |
 v
code
 |
 v
tests
 |
 v
"verified"
```

versus:

```text
GOOD:
LLM
 |
 | proposal
 v
RFL-AE
 |
 | authorized operation
 v
artifact
 |
 v
independent execution
 |
 v
evidence
 |
 v
gate engine
 |
 v
certificate
```

---

## 716. Do not start with a swarm
<!-- source: EXECUTABLE-KERNEL.md §14 -->

For the first executable milestone, I would intentionally use:

```text
1 protocol engine
1 event ledger
1 evidence engine
1 gate engine
0 autonomous mutation agents
```

Then prove:

```text
determinism
replay
authorization
scope
epoch isolation
evidence binding
gate semantics
```

Only then introduce:

```text
Agent-1: C semantic reconstruction
Agent-2: Rust design
Agent-3: implementation
Agent-4: verification
Agent-5: adversarial review
```

The agents become **clients of the protocol**, not the protocol itself.

---

## 717. Immediate implementation sequence
<!-- source: EXECUTABLE-KERNEL.md §15 -->

```text
PHASE 0  ─ Freeze
          DOMAIN-TYPES.md
          GateStatus
          SnapshotId
          authority vocabulary
PHASE 1  ─ rfl-types
          canonical Rust domain model
PHASE 2  ─ rfl-transition
          deterministic state machine
PHASE 3  ─ rfl-event-ledger
          append-only events
          deterministic replay
PHASE 4  ─ rfl-evidence
          execution/evidence binding
PHASE 5  ─ rfl-gates
          PASS/FAIL/BLOCKED/INVALIDATED
PHASE 6  ─ conformance
          adversarial negative suite
PHASE 7  ─ CI
          authoritative execution
PHASE 8  ─ Linux manifests
          subsystem/config/arch/toolchain model
PHASE 9  ─ agents
          proposal-only first
PHASE 10 ─ controlled execution
          capability-granted mutation
PHASE 11 ─ kernel reconstruction
          subsystem by subsystem
```

### The first release gate

I would make **RFL-AE v0.1 Protocol Kernel** impossible to call complete unless all of these hold:

```text
[ ] all referenced domain types defined
[ ] no undefined GateStatus
[ ] no undefined SnapshotId
[ ] transition relation executable
[ ] illegal transitions rejected
[ ] authorization is epoch-bound
[ ] artifacts are epoch-bound
[ ] scope enforcement executable
[ ] duplicate operations rejected
[ ] replay deterministic
[ ] evidence bound to execution
[ ] self-verification rejected
[ ] gate state machine executable
[ ] negative tests exist
[ ] CI executes the authoritative suite
[ ] execution evidence is persisted
[ ] release certificate derives from evidence
```

**Only after that should RFL-AE be trusted to supervise an AI system working on Linux kernel C→Rust reconstruction.**

The next concrete step is therefore to write the **`rfl-types` normative type system + state-transition algebra**, rather than adding more agent roles.

---

**Done — see [PROTOCOL-V01.md](PROTOCOL-V01.md)** (§718–§744, source §§1–§27), which freezes the
Protocol Kernel Specification v0.1 and makes the protocol **closed under execution**: the
canonical domain model in which `Task`, `Contract`, `Capability` and `Authorization` are **not
interchangeable**; opaque newtype IDs so code cannot compare `String` with `ArtifactId`;
`KernelSnapshotId` resolving the `SnapshotId` ambiguity; an `Epoch` with an executable
`same_epoch` rule rather than a textual convention; structural `Scope` with `contains()` as
protocol logic; the absolute **capability ≠ authorization** distinction; a closed
`OperationKind` with no arbitrary shell execution; typed `OperationRequest` instead of
natural-language instructions; a transition relation with **no third state**; a stable
`RejectionReason` taxonomy; explicit transition legality where `Created -> Certified` yields
`InvalidTransition`; `Task` separated from `TaskAttempt` rather than allowing state rewinds; an
event ledger chained by `previous_event` and `event_digest`; the replay invariant
`replay(events) == authoritative_state`; evidence strictly downstream of execution;
`EvidenceOutcome::Passed` **not** implying `Artifact::Verified`; verification as a
multi-dimensional relation; nine contract classes; the gate non-equivalences; a certificate that
is `Derive(...)` and never *"Agent says CERTIFIED"*; an executable `RELEASE_ELIGIBLE` predicate;
a tiny agent API; the proposed repository reorganisation; an 18-row conformance matrix where
**the negative suite is as important as the positive suite**; the kernel verification bridge
where RFL-AE knows *what* evidence means and Linux tools determine *whether* the test passed;
maintainer authority as a separate plane; and the C→Rust reconstruction model where **the
reconstructed semantic contract, not the Rust code, is the source of truth**. Same provenance
convention as `VERIFICATION.md`.
