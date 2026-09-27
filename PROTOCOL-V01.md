# RFL-AE — Protocol Kernel Specification, v0.1

> **Provenance and numbering.** This document was supplied as *RFL-AE — Protocol Kernel Specification, v0.1*, numbered §1–§27 in the source with no unnumbered sections. To keep the corpus contiguous, its sections are renumbered **§718–§744**, continuing directly from [EXECUTABLE-KERNEL.md](EXECUTABLE-KERNEL.md) (which ends at §717). The mapping is the plain **`corpus_section = source_section + 717`**. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: PROTOCOL-V01.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/` tree, no `rfl-types` / `rfl-transition` / `rfl-ledger` / `rfl-evidence` / `rfl-verification` / `rfl-gates` crate, no `schemas/`, no `linux/` manifest tree, no `conformance/` suite, and no `.github/workflows` has been written or compiled. The repository status remains `v0.0` — documentation only. §740 describes a *proposed* reorganisation of the repository into `docs/`, `crates/`, `schemas/`, `linux/` and `conformance/`; that reorganisation has **not** been carried out and this document still sits at the repository root alongside the other corpus files.

> **Transcription note (derived treatment — delete if unwanted).** The pasted source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/PROTOCOL-V01.py`](diagrams/PROTOCOL-V01.py); re-running it reproduces all 63 diagrams. One deliberate normalisation: the maintainer-authority diagram in §743 used box-drawing characters for its two forks but ASCII `|` for its spines, and an ASCII pipe inside an otherwise box-drawing block is exactly the defect the corpus's ASCII-substitution check exists to catch, so those spines are now `│`. ASCII `v` arrowheads are kept throughout, matching §718's domain-model diagram, and no block mixes an ASCII `|` with box glyphs. Where the source's inter-token spacing was ambiguous, line breaks follow the meaning rather than a mechanical space count — the clearest case is §736, whose four `!=` statements are kept on one line each. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The key change now is to make the protocol **closed under execution**: every object referenced by a transition must have a canonical type, every state change must have a deterministic rule, and every rejection must be machine-identifiable.

This is also compatible with the actual Linux Rust environment: kernel Rust is `no_std`; the kernel's shared `kernel` crate is the intended abstraction layer rather than bypassing it; KUnit already provides Rust-facing test infrastructure.

---

## Contents

- [718. Canonical domain model](#718-canonical-domain-model)
- [719. IDs are opaque](#719-ids-are-opaque)
- [720. Snapshot identity](#720-snapshot-identity)
- [721. Epoch](#721-epoch)
- [722. Scope](#722-scope)
- [723. Capability ≠ authorization](#723-capability--authorization)
- [724. Operation model](#724-operation-model)
- [725. Request](#725-request)
- [726. Deterministic transition function](#726-deterministic-transition-function)
- [727. Rejection taxonomy](#727-rejection-taxonomy)
- [728. Transition legality](#728-transition-legality)
- [729. Failed state semantics](#729-failed-state-semantics)
- [730. Event model](#730-event-model)
- [731. Replay invariant](#731-replay-invariant)
- [732. Evidence is downstream of execution](#732-evidence-is-downstream-of-execution)
- [733. Evidence provenance](#733-evidence-provenance)
- [734. Verification becomes a relation](#734-verification-becomes-a-relation)
- [735. Contract classes](#735-contract-classes)
- [736. Gate algebra](#736-gate-algebra)
- [737. Certificate](#737-certificate)
- [738. The release predicate](#738-the-release-predicate)
- [739. Agent authority boundary](#739-agent-authority-boundary)
- [740. Proposed repository transition](#740-proposed-repository-transition)
- [741. First conformance matrix](#741-first-conformance-matrix)
- [742. Kernel-specific verification bridge](#742-kernel-specific-verification-bridge)
- [743. Maintainer authority becomes a separate plane](#743-maintainer-authority-becomes-a-separate-plane)
- [744. The next hard problem](#744-the-next-hard-problem)

---

## 718. Canonical domain model
<!-- source: PROTOCOL-V01.md §1 -->

I would freeze the foundational model as:

```text
                    ┌──────────────────────┐
                    │    KernelSnapshot    │
                    └──────────┬───────────┘
                               │
                               v
                    ┌──────────────────────┐
                    │        Epoch         │
                    └──────────┬───────────┘
                               │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              v                 v                 v
            Task            Contract         Capability
              │                 │                 │
              └─────────────────┼─────────────────┘
                               v
                         Authorization
                               │
                               v
                       OperationRequest
                               │
                               v
                       TransitionEngine
                               │
                    ┌──────────┴──────────┐
                    │                     │
                 Reject                Accept
                    │                     │
                    v                     v
                 Reason                 Event
                                          │
                                          v
                                  Artifact/Evidence
                                          │
                                          v
                                        Gates
                                          │
                                          v
                                     Certificate
```

The important point is that **`Task`, `Contract`, `Capability`, and `Authorization` are not interchangeable**.

---

## 719. IDs are opaque
<!-- source: PROTOCOL-V01.md §2 -->

Every externally meaningful identifier should be opaque.

Do not let code accidentally compare:

```text
String
```

with:

```text
ArtifactId
```

or:

```text
TaskId
```

with:

```text
SnapshotId
```

Use newtypes:

```text
pub struct TaskId(pub Uuid);
pub struct AgentId(pub Uuid);
pub struct ArtifactId(pub Uuid);
pub struct EvidenceId(pub Uuid);
pub struct ContractId(pub Uuid);
pub struct GateId(pub Uuid);
pub struct AuthorizationId(pub Uuid);
pub struct EventId(pub Uuid);
```

For content identity:

```rust
pub struct Digest {
    pub algorithm: DigestAlgorithm,
    pub bytes: [u8; 32],
}
```

and:

```rust
pub enum DigestAlgorithm {
    Sha256,
}
```

The algorithm must be part of the identity rather than an undocumented assumption.

---

## 720. Snapshot identity
<!-- source: PROTOCOL-V01.md §3 -->

Resolve the existing `SnapshotId` ambiguity by making the Linux source snapshot explicit:

```rust
pub struct KernelSnapshotId {
    pub git: GitObjectId,
}
```

Then:

```rust
pub struct KernelSnapshot {
    pub id: KernelSnapshotId,
    pub source_digest: Digest,
    pub tree_digest: Digest,
}
```

If RFL-AE later needs a broader snapshot concept, introduce:

```text
pub struct ProtocolSnapshotId(...);
```

rather than overloading `SnapshotId`.

Recommended invariant:

```text
KernelSnapshotId != ProtocolSnapshotId
```

unless there is an actual formal reason for them to be identical.

---

## 721. Epoch
<!-- source: PROTOCOL-V01.md §4 -->

An epoch is the protocol's anti-staleness boundary.

```rust
pub struct Epoch {
    pub kernel: KernelSnapshotId,
    pub specification: Digest,
    pub protocol: Digest,
    pub generation: u64,
}
```

Define:

```text
pub fn same_epoch(a: &Epoch, b: &Epoch) -> bool;
```

with:

```text
same_epoch(a,b)
    iff a.kernel       == b.kernel
      && a.specification == b.specification
      && a.protocol      == b.protocol
      && a.generation   == b.generation
```

This gives us an executable rule rather than a textual convention.

---

## 722. Scope
<!-- source: PROTOCOL-V01.md §5 -->

Scope needs to be structural.

Do not model it merely as:

```rust
pub struct Scope {
    pub path: String,
}
```

because:

```text
kernel/sched/
```

versus:

```text
kernel/sched/core.c
```

requires semantics.

Instead:

```rust
pub struct Scope {
    pub roots: Vec<ScopeRoot>,
}

pub enum ScopeRoot {
    RepositoryPath(RepoPath),
    Subsystem(SubsystemId),
    Artifact(ArtifactId),
}
```

Then define the relation:

```text
contains(scope, target)
```

as protocol logic.

This gives:

```text
authorized:
    subsystem=scheduler
requested:
    kernel/sched/core.c
   => ACCEPT
```

while:

```text
authorized:
    subsystem=scheduler
requested:
    fs/open.c
   => REJECT(SCOPE_VIOLATION)
```

---

## 723. Capability ≠ authorization
<!-- source: PROTOCOL-V01.md §6 -->

This distinction should be absolute.

A capability says:

```text
what an actor is potentially allowed to do
```

Authorization says:

```text
whether that actor is authorized to perform this specific operation at this epoch, on this target, within this scope.
```

Therefore:

```rust
pub struct Capability {
    pub id: CapabilityId,
    pub operation: OperationKind,
    pub scope: Scope,
}
```

while:

```rust
pub struct Authorization {
    pub id: AuthorizationId,
    pub epoch: Epoch,
    pub actor: AgentId,
    pub task: TaskId,
    pub capability: CapabilityId,
    pub scope: Scope,
    pub expires_at: Option<Timestamp>,
}
```

This prevents:

```text
"I have write capability"
```

from becoming:

```text
"I may modify anything."
```

---

## 724. Operation model
<!-- source: PROTOCOL-V01.md §7 -->

Define a closed operation enum initially:

```rust
pub enum OperationKind {
    Observe,
    Extract,
    Analyze,
    Propose,
    Generate,
    Modify,
    Execute,
    Verify,
    Review,
}
```

Do not initially expose arbitrary shell execution as an operation.

Instead:

```rust
pub enum ExecutionTarget {
    KernelBuild,
    KernelTest,
    Kunit,
    RustTest,
    StaticAnalysis,
    DifferentialTest,
}
```

A future privileged operation such as:

```text
ShellCommand
```

must be introduced deliberately because it massively expands the authority surface.

---

## 725. Request
<!-- source: PROTOCOL-V01.md §8 -->

The fundamental protocol input becomes:

```rust
pub struct OperationRequest {
    pub request_id: RequestId,
    pub epoch: Epoch,
    pub task: TaskId,
    pub actor: AgentId,
    pub operation: OperationKind,
    pub target: Target,
    pub authorization: AuthorizationId,
}
```

The engine receives only this.

Not:

```text
"Please modify scheduler code."
```

Not:

```text
natural-language instruction
```

The LLM's natural-language output must first be converted into a typed request.

---

## 726. Deterministic transition function
<!-- source: PROTOCOL-V01.md §9 -->

The central API:

```rust
pub trait TransitionEngine {
    fn apply(
        &mut self,
        request: OperationRequest,
    ) -> TransitionResult;
}
```

with:

```rust
pub enum TransitionResult {
    Accepted {
        event: EventId,
        state: StateDigest,
    },

    Rejected {
        reason: RejectionReason,
    },
}
```

No third state.

No:

```text
maybe probably needs LLM judgment
```

---

## 727. Rejection taxonomy
<!-- source: PROTOCOL-V01.md §10 -->

This deserves its own stable enum.

```rust
pub enum RejectionReason {
    UnknownTask,
    UnknownActor,
    UnknownAuthorization,

    EpochMismatch,
    SnapshotMismatch,
    SpecificationMismatch,
    ProtocolMismatch,

    AuthorizationExpired,
    AuthorizationRevoked,
    CapabilityMissing,

    ScopeViolation,

    InvalidTaskState,
    InvalidTransition,

    ArtifactMissing,
    ArtifactMismatch,

    EvidenceMissing,
    EvidenceUnbound,

    SelfVerification,

    DuplicateOperation,
    ReplayConflict,

    GateFailure,
    GateBlocked,
    DependencyInvalidated,

    PolicyDenied,
}
```

The distinction between these reasons is important for automated diagnosis.

For example:

```text
BLOCKED
```

must not be represented as:

```text
FAIL
```

because the repository's architecture already correctly treats those as different conditions.

---

## 728. Transition legality
<!-- source: PROTOCOL-V01.md §11 -->

Represent state transitions explicitly.

```rust
pub enum TaskState {
    Created,
    Admitted,
    Authorized,
    Executing,
    Succeeded,
    Failed,
    Verified,
    Gated,
    Certified,
}
```

Then define:

```text
Created   -> Admitted
Admitted   -> Authorized
Authorized   -> Executing
Executing   -> Succeeded
  -> Failed
Succeeded   -> Verified
Verified   -> Gated
Gated   -> Certified
```

Everything else is rejected.

For example:

```text
Created -> Certified
```

must produce:

```text
InvalidTransition
```

---

## 729. Failed state semantics
<!-- source: PROTOCOL-V01.md §12 -->

One subtlety needs formal treatment.

Should:

```text
Failed -> Executing
```

be legal?

The answer should **not** be hard-coded as a universal rule.

Instead distinguish:

```text
TaskAttempt
```

from:

```text
Task
```

A task may have multiple attempts while the task's semantic identity remains stable.

```text
Task
 |
 +-- Attempt 1 -> FAILED
 |
 +-- Attempt 2 -> EXECUTING
 |
 +-- Attempt 3 -> SUCCEEDED
```

Therefore:

```text
Task
    !=
TaskAttempt
```

This is cleaner than allowing arbitrary state rewinds.

---

## 730. Event model
<!-- source: PROTOCOL-V01.md §13 -->

Every accepted transition generates exactly one authoritative event.

```rust
pub struct Event {
    pub id: EventId,
    pub sequence: u64,

    pub epoch: Epoch,

    pub actor: AgentId,
    pub task: TaskId,
    pub request: RequestId,

    pub operation: OperationKind,

    pub previous_state: Digest,
    pub resulting_state: Digest,
}
```

The sequence must be monotonic:

```text
0 1 2 3 ...
```

But sequence numbers alone are insufficient.

Add:

```text
pub previous_event: Option<EventId>,
pub event_digest: Digest,
```

Then the ledger forms a chain:

```text
E0
 |
 v
E1
 |
 v
E2
 |
 v
E3
```

---

## 731. Replay invariant
<!-- source: PROTOCOL-V01.md §14 -->

The replay engine should expose:

```rust
pub fn replay(
    events: &[Event],
) -> Result<State, ReplayError>;
```

And the fundamental invariant becomes:

```text
replay(events) == authoritative_state
```

The stronger property:

```text
 execute(requests)
         |
         v
      events
  replay(events)
         |
         v
      state'

state' == execution_state
```

This is one of the most important tests in the entire project.

---

## 732. Evidence is downstream of execution
<!-- source: PROTOCOL-V01.md §15 -->

Do not permit an agent to manufacture its own verification evidence.

Correct:

```text
operation
    |
    v
execution authority
    |
    v
raw result
    |
    v
EvidenceRecord
```

Not:

```text
agent
 |
 +--> code
 +--> "tests passed"
```

The kernel itself already has established test infrastructure such as KUnit, which can run tests and produce structured KTAP results; RFL-AE should treat those external execution systems as evidence producers rather than letting an agent assert the result itself.

---

## 733. Evidence provenance
<!-- source: PROTOCOL-V01.md §16 -->

Minimum:

```rust
pub struct EvidenceRecord {
    pub id: EvidenceId,

    pub epoch: Epoch,

    pub subject: ArtifactId,

    pub executor: ExecutorId,

    pub command_digest: Digest,

    pub input_digest: Digest,

    pub output_digest: Digest,

    pub environment: EnvironmentFingerprint,

    pub toolchain: ToolchainFingerprint,

    pub outcome: EvidenceOutcome,
}
```

And:

```rust
pub enum EvidenceOutcome {
    Passed,
    Failed,
    Blocked,
    NotApplicable,
}
```

Critically:

```text
EvidenceOutcome::Passed
```

does **not** itself imply:

```text
Artifact::Verified
```

A gate must establish that implication under the appropriate verification contract.

---

## 734. Verification becomes a relation
<!-- source: PROTOCOL-V01.md §17 -->

Define:

```text
Verify(Artifact, Contract, EvidenceSet)
        -> VerificationResult
```

where:

```rust
pub enum VerificationResult {
    Verified {
        evidence: Vec<EvidenceId>,
    },

    PartiallyVerified {
        satisfied: Vec<ContractId>,
        missing: Vec<ContractId>,
    },

    Failed {
        violations: Vec<ContractViolation>,
    },

    Blocked {
        reasons: Vec<VerificationBlocker>,
    },
}
```

This prevents a dangerous simplification:

```text
one test passed
      = verified
```

For kernel reconstruction, verification must be multidimensional.

---

## 735. Contract classes
<!-- source: PROTOCOL-V01.md §18 -->

The contract system should distinguish at least:

```text
SemanticContract
SafetyContract
ConcurrencyContract
ABIContract
BuildContract
RuntimeContract
CompatibilityContract
PerformanceContract
MigrationContract
```

Example:

```text
scheduler/core.c
```

might have:

```text
Semantic:
    scheduling decisions preserved
Concurrency:
    lock ordering preserved
Safety:
    ownership/lifetime invariants preserved
ABI:
    exported interfaces preserved
Runtime:
    scheduler behavior valid under test matrix
```

No single test can discharge all five.

---

## 736. Gate algebra
<!-- source: PROTOCOL-V01.md §19 -->

Now the gate engine can consume verification results.

```rust
pub enum GateStatus {
    Pass,
    Fail,
    Blocked,
    NotApplicable,
    Invalidated,
}
```

Define the non-equivalences:

```text
PASS  != NOT_APPLICABLE
FAIL  != BLOCKED
BLOCKED  != PASS
INVALIDATED  != FAIL
```

Especially:

```text
BLOCKED
```

means:

> insufficient authority/evidence to decide.

Whereas:

```text
FAIL
```

means:

> the required condition was evaluated and did not hold.

That distinction should propagate all the way into release certification.

---

## 737. Certificate
<!-- source: PROTOCOL-V01.md §20 -->

The final technical certificate should therefore be a derived object:

```rust
pub struct TechnicalCertificate {
    pub artifact: ArtifactId,
    pub epoch: Epoch,

    pub contract_results: Vec<ContractResult>,
    pub verification_results: Vec<VerificationResult>,
    pub gate_results: Vec<GateResult>,

    pub certificate_digest: Digest,
}
```

And:

```text
Certificate
    =
    Derive(
        Artifact,
        Contracts,
        Evidence,
        Verification,
        Gates
    )
```

It must never be:

```text
Agent says "CERTIFIED"
```

---

## 738. The release predicate
<!-- source: PROTOCOL-V01.md §21 -->

The release predicate can now become executable:

```text
RELEASE_ELIGIBLE(a, e)
```

iff:

```text
epoch_valid(a,e)
AND scope_valid(a)
AND contracts_satisfied(a)
AND verification_satisfied(a)
AND all_required_gates_pass(a)
AND no_required_gate_blocked(a)
AND no_required_gate_failed(a)
AND no_dependency_invalidated(a)
AND evidence_complete(a)
AND replay_valid(a)
```

This is the first point at which the architecture's release language becomes something a machine can actually enforce.

---

## 739. Agent authority boundary
<!-- source: PROTOCOL-V01.md §22 -->

The agent API should intentionally be tiny:

```rust
trait Agent {
    fn observe(&self, request: ObserveRequest) -> Proposal;
}
```

Then:

```text
Agent
  |
  v
Proposal
  |
  v
Protocol validation
  |
  v
OperationRequest
  |
  v
Authorization
  |
  v
Execution
```

An agent never directly calls:

```text
git commit
git push
rm
cargo publish
```

unless those operations have explicitly become authorized protocol operations.

---

## 740. Proposed repository transition
<!-- source: PROTOCOL-V01.md §23 -->

The RFL-AE tree should evolve from:

```text
RFL-AE/
├── ARCHITECTURE.md
├── SPECIFICATION.md
├── ...
├── VERIFICATION.md
├── GATES.md
├── EXECUTION.md
├── ORCHESTRATION.md
└── skills/
```

toward:

```text
RFL-AE/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SPECIFICATION.md
│   ├── FORMAL-CORE.md
│   ├── PROTOCOL.md
│   ├── RUST-CORE.md
│   ├── TRANSITIONS.md
│   ├── KSIR.md
│   ├── RECONSTRUCTION.md
│   ├── CONTRACTS.md
│   ├── DESIGN-IR.md
│   ├── VERIFICATION.md
│   ├── GATES.md
│   ├── EXECUTION.md
│   └── ORCHESTRATION.md
├── crates/
│   ├── rfl-types/
│   ├── rfl-transition/
│   ├── rfl-ledger/
│   ├── rfl-evidence/
│   ├── rfl-verification/
│   └── rfl-gates/
├── schemas/
│   ├── epoch.schema.json
│   ├── task.schema.json
│   ├── authorization.schema.json
│   ├── artifact.schema.json
│   ├── evidence.schema.json
│   ├── verification.schema.json
│   ├── gate.schema.json
│   └── certificate.schema.json
├── linux/
│   ├── subsystems/
│   ├── architectures/
│   ├── configurations/
│   ├── toolchains/
│   ├── verification/
│   └── maintainers/
├── conformance/
│   ├── positive/
│   ├── negative/
│   ├── replay/
│   ├── authorization/
│   └── adversarial/
├── skills/
└── .github/
    └── workflows/
```

---

## 741. First conformance matrix
<!-- source: PROTOCOL-V01.md §24 -->

The initial suite should not test whether the architecture *looks* correct.

It should attack the invariants.

| ID | Attack | Expected |
| --- | --- | --- |
| C-001 | stale epoch | reject |
| C-002 | snapshot mismatch | reject |
| C-003 | specification mismatch | reject |
| C-004 | expired authorization | reject |
| C-005 | revoked authorization | reject |
| C-006 | missing capability | reject |
| C-007 | scope escape | reject |
| C-008 | invalid transition | reject |
| C-009 | duplicate request | reject |
| C-010 | forged artifact | reject |
| C-011 | unbound evidence | reject |
| C-012 | self-verification | reject |
| C-013 | event tampering | reject |
| C-014 | replay divergence | reject |
| C-015 | failed required gate | reject |
| C-016 | blocked required gate | reject |
| C-017 | invalidated dependency | reject |
| C-018 | valid complete execution | accept |

The **negative suite is as important as the positive suite**.

---

## 742. Kernel-specific verification bridge
<!-- source: PROTOCOL-V01.md §25 -->

Once this protocol is working, its evidence adapters can map onto real kernel validation:

```text
RFL-AE
  |
  +-- rustc
  +-- rustfmt
  +-- clippy
  +-- rustdoc/rusttest
  +-- KUnit
  +-- kselftest
  +-- KASAN
  +-- KCSAN
  +-- lockdep
  +-- build matrix
  +-- architecture matrix
  +-- runtime/differential tests
```

The Linux Rust documentation explicitly describes `rustfmt`, `clippy`, `rustdoc`, and Rust testing support, while KUnit provides a kernel-native test framework and machine-readable KTAP output.

The important architectural distinction is:

```text
RFL-AE knows
    WHAT evidence means
Linux tools determine
    WHETHER the underlying test actually passed
```

That prevents RFL-AE from becoming another test-result hallucination layer.

---

## 743. Maintainer authority becomes a separate plane
<!-- source: PROTOCOL-V01.md §26 -->

This should be added now, not later.

Current Rust-for-Linux guidance explicitly says subsystem policy varies, the normal kernel maintainer model applies, and Rust patches should involve both relevant subsystem maintainers/reviewers and the Rust side.

Therefore:

```text
             TECHNICAL PLANE
                    │
       ┌────────────┴────────────┐
       │                         │
 Verification                  Gates
       │                         │
       └────────────┬────────────┘
                    │
          Technical Certificate
                    │
                    v
           REVIEW / GOVERNANCE
                    │
       ┌────────────┴────────────┐
       │                         │
 subsystem maintainer     Rust maintainer
       │                         │
       └────────────┬────────────┘
                    │
             Upstream State
```

This prevents the protocol from making the category error:

```text
technically verified
        = socially/upstream accepted
```

---

## 744. The next hard problem
<!-- source: PROTOCOL-V01.md §27 -->

Once the above is frozen, the next difficult layer is **not the agent swarm**.

It is the C→Rust semantic reconstruction model.

We need to represent:

```text
C source
  |
  v
C semantic evidence
  |
  +-- types
  +-- ownership
  +-- lifetime
  +-- aliasing
  +-- locking
  +-- interrupt context
  +-- RCU context
  +-- allocation context
  +-- error behavior
  +-- ABI
  +-- initialization
  +-- teardown
  +-- concurrency
  |
  v
Semantic Contract
  |
  v
Rust Design IR
  |
  v
Rust implementation
```

That is where **KSIR + RECONSTRUCTION + CONTRACTS + DESIGN-IR** need to be connected into an actual compiler-like pipeline.

The crucial invariant will be:

> **Rust code is not the source of truth for what the C subsystem means. The reconstructed semantic contract is.**

That gives RFL-AE a defensible architecture for the actual Linux C→Rust problem rather than merely an elaborate agent orchestration system.

---

**Done — see [SEMANTIC-LAYER.md](SEMANTIC-LAYER.md)** (§745–§774, source §§1–§29 plus the unnumbered
*RFL-AE maturity boundary*), which specifies the layer at the heart of the Linux C→Rust problem
and whose first rule is **do not translate syntax first — reconstruct semantics first**: the
`SemanticUnit` whose `evidence` field makes every nontrivial assertion traceable; the
`OBSERVED ≠ DERIVED ≠ HYPOTHESIS ≠ VERIFIED` distinction enforced by the data model; a
provenance graph so the system can answer *"why does the system believe this contract exists?"*
rather than *"which agent said it?"*; thirty explicit semantic dimensions where absence is
`NOT_OBSERVED` and never silently `false`; execution context, lock, ownership, lifetime, RCU,
initialization and teardown models; independent ABI and configuration/architecture scopes; the
specialized reconstruction agents that produce **claims/proposals, not truth**; `SemanticConflict`
as a first-class object with **no majority voting**; `HeuristicScore` permitted as metadata but
prohibited from becoming `Verified`; the Rust Design IR whose `unsafe_obligations` must not
disappear; unsafe as an obligation ledger; the full compilation pipeline; the crucial invariant
that certification requires **two independent directions of evidence**; the
`CERTIFIABLE(U)` predicate with `complete_for_required_domains` deliberate; subsystem migration
profiles; the first end-to-end vertical slice; and the maturity boundary where the **protocol
kernel must be deterministic** and the **reconstruction engine may use AI**. Same provenance
convention as `VERIFICATION.md`.
