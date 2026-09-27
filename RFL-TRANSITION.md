# RFL-AE — `rfl-transition`: The Executable Protocol Law

> **Provenance and numbering.** This document was supplied untitled (the heading above is derived from its content — rename freely), numbered **§19–§38** in the source: the author continued the numbering of the previous paste, [RFL-TYPES.md](RFL-TYPES.md), whose own sections were §1–§18. It has no unnumbered sections. To keep the corpus contiguous, its sections are renumbered **§823–§842**, continuing directly from `RFL-TYPES.md` (which ends at §822). The mapping is the plain **`corpus_section = source_section + 804`** — the first source in this corpus whose numbering does not start at §1, which is why the offset is not simply the previous file's last section. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: RFL-TRANSITION.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/rfl-transition/` tree, no transition engine, no precondition checks, no rejection taxonomy, no execution adapter, and none of the conformance tests or properties P1–P8 has been written or compiled. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** The pasted source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/RFL-TRANSITION.py`](diagrams/RFL-TRANSITION.py); re-running it reproduces all 44 diagrams. Every diagram in this source is box-drawing art or a `↓` / `→` / `⇒` chain, and stays that way. Two diagrams were normalised geometrically, with no content change: in §838 the chain below `SUCCEEDED` ran one column right of the fork branch that feeds it and now continues on that branch's column; in §842 the spine and labels now sit on the boxes' centre. The two LaTeX formulas in §824 are fenced as `math`, which GitHub renders as typeset mathematics. The transition matrix in §826 arrived as a flattened table and is rendered as a real table. The shell commands in §832 are fenced as `bash` and the artifact metadata in §836 as `json`. Rust types and the Rust-syntax fragments — `fn is_valid(…)` and `validate_request(…)` in §827, `authorization_allows(…)` in §829, and `pub scope: String` in §830 — are fenced as `rust`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

Next, we should formalize **`rfl-transition`**. This is the point where the architecture stops merely describing state changes and starts defining an executable protocol law.

---

## Contents

- [823. `rfl-transition`](#823-rfl-transition)
- [824. The transition relation](#824-the-transition-relation)
- [825. State should distinguish Task and Attempt](#825-state-should-distinguish-task-and-attempt)
- [826. Transition matrix](#826-transition-matrix)
- [827. Preconditions must be compositional](#827-preconditions-must-be-compositional)
- [828. Rejection taxonomy](#828-rejection-taxonomy)
- [829. Authorization checking](#829-authorization-checking)
- [830. Scope needs a real type](#830-scope-needs-a-real-type)
- [831. Typed targets](#831-typed-targets)
- [832. Execution adapter boundary](#832-execution-adapter-boundary)
- [833. Duplicate requests](#833-duplicate-requests)
- [834. Content identity matters](#834-content-identity-matters)
- [835. Epoch invalidation](#835-epoch-invalidation)
- [836. Evidence cannot authorize itself](#836-evidence-cannot-authorize-itself)
- [837. Certificate construction](#837-certificate-construction)
- [838. The first complete state machine](#838-the-first-complete-state-machine)
- [839. Important negative property](#839-important-negative-property)
- [840. Conformance properties](#840-conformance-properties)
- [841. Then comes `rfl-ledger`](#841-then-comes-rfl-ledger)
- [842. One deeper consequence](#842-one-deeper-consequence)

---

## 823. `rfl-transition`
<!-- source: RFL-TRANSITION.md §19 -->

The crate should be intentionally small:

```text
crates/rfl-transition/
├── Cargo.toml
└── src/
    ├── lib.rs
    ├── engine.rs
    ├── preconditions.rs
    ├── transitions.rs
    ├── rejection.rs
    ├── authorization.rs
    ├── replay.rs
    └── tests/
        ├── epoch.rs
        ├── authorization.rs
        ├── transitions.rs
        ├── replay.rs
        └── adversarial.rs
```

Dependency:

```text
rfl-types
    ↓
rfl-transition
```

Nothing above `rfl-transition` should be required to decide whether a protocol transition is valid.

## 824. The transition relation
<!-- source: RFL-TRANSITION.md §20 -->

The normative object is:

```math
\delta : (S,R,\Gamma) \rightarrow (S',E)
```

where:

- `S` = current authoritative state
- `R` = requested operation
- `Γ` = authoritative context
- `S'` = resulting state
- `E` = ledger event

Or, on rejection:

```math
\delta(S,R,\Gamma) \rightarrow Reject(reason)
```

So:

```rust
pub enum TransitionResult {
    Accepted {
        event: EventId,
        resulting_state: StateDigest,
    },
    Rejected {
        reason: RejectionReason,
    },
}
```

There must be **no mutation before all preconditions pass**.

That gives us:

```text
validate
   ↓
authorize
   ↓
check state
   ↓
check epoch
   ↓
check scope
   ↓
construct next state
   ↓
construct event
   ↓
commit
```

Not:

```text
mutate
  ↓
discover violation
  ↓
try to undo
```

The latter creates rollback semantics that are much harder to make trustworthy.

## 825. State should distinguish Task and Attempt
<!-- source: RFL-TRANSITION.md §21 -->

Use:

```rust
pub struct TaskState {
    pub task: TaskId,
    pub epoch: Epoch,
    pub status: TaskStatus,
    pub attempt: Option<AttemptId>,
}
```

with:

```rust
pub enum TaskStatus {
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

And separately:

```rust
pub enum AttemptStatus {
    Created,
    Executing,
    Succeeded,
    Failed,
    Aborted,
}
```

This lets us represent:

```text
Task T1
│
├── Attempt A1 → Failed
│
├── Attempt A2 → Failed
│
└── Attempt A3 → Succeeded
```

without rewriting the historical state of `T1`.

## 826. Transition matrix
<!-- source: RFL-TRANSITION.md §22 -->

The matrix should be normative.

| Current    | Operation | Preconditions              | Result     |
|------------|-----------|----------------------------|------------|
| Created    | Admit     | task valid                 | Admitted   |
| Admitted   | Authorize | authorization valid        | Authorized |
| Authorized | Execute   | capability + scope + epoch | Executing  |
| Executing  | Complete  | valid execution evidence   | Succeeded  |
| Executing  | Fail      | execution recorded         | Failed     |
| Succeeded  | Verify    | independent verification   | Verified   |
| Verified   | Gate      | required gates pass        | Gated      |
| Gated      | Certify   | certification conditions   | Certified  |

Everything else is rejected unless explicitly specified.

That means:

```text
Created → Certified
```

is not "probably okay."

It is simply:

```text
Rejected(InvalidTransition)
```

## 827. Preconditions must be compositional
<!-- source: RFL-TRANSITION.md §23 -->

Do not create one giant function:

```rust
fn is_valid(request, state) -> bool
```

Instead:

```text
check_task(...)
check_epoch(...)
check_snapshot(...)
check_authorization(...)
check_capability(...)
check_scope(...)
check_state(...)
check_dependencies(...)
check_duplicate(...)
```

Each returns a typed result:

```rust
pub enum CheckResult {
    Pass,
    Fail(RejectionReason),
}
```

Then:

```rust
pub fn validate_request(...) -> Result<(), RejectionReason>
```

can compose them.

This is useful for two reasons.

First, every rejection has a machine-readable cause.

Second, tests can target individual invariants.

## 828. Rejection taxonomy
<!-- source: RFL-TRANSITION.md §24 -->

The taxonomy becomes part of the protocol API:

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

Do not return:

```text
"request invalid"
```

as the authoritative result.

That loses information needed for:

- auditing
- replay
- metrics
- adversarial tests
- debugging
- policy analysis

## 829. Authorization checking
<!-- source: RFL-TRANSITION.md §25 -->

Authorization should be checked against **all relevant dimensions**.

Conceptually:

```text
Authorization
 ├── actor
 ├── task
 ├── epoch
 ├── operation
 ├── capability
 ├── scope
 └── expiration
```

Therefore:

```rust
fn authorization_allows(
    authorization: &Authorization,
    request: &OperationRequest,
    now: Timestamp,
) -> Result<(), RejectionReason>
```

must verify:

```text
authorization.actor == request.actor
authorization.task == request.task
authorization.epoch == request.epoch
authorization.capability permits request.operation
authorization.scope contains request.target
now < authorization.expires_at
```

And revocation must be checked against authoritative protocol state.

## 830. Scope needs a real type
<!-- source: RFL-TRANSITION.md §26 -->

This is another place where `String` would be dangerous.

Instead of:

```rust
pub scope: String
```

define a structured scope.

For example:

```rust
pub struct Scope {
    pub repository: Option<RepositoryId>,
    pub paths: Vec<PathScope>,
    pub configurations: Vec<ConfigurationScope>,
    pub architectures: Vec<ArchitectureId>,
}
```

Then a request targeting:

```text
drivers/foo/bar.c
```

can be evaluated against an explicit path scope.

This prevents a particularly dangerous authorization pattern:

```text
authorized for:
    drivers/foo/

actually modifies:
    kernel/sched/
```

The transition engine should reject it before execution.

## 831. Typed targets
<!-- source: RFL-TRANSITION.md §27 -->

Likewise, `Target` should not be an arbitrary shell string.

Start with:

```rust
pub enum Target {
    Source(SourceRegion),
    MigrationUnit(MigrationUnitId),
    Artifact(ArtifactId),
    Contract(ContractId),
    Gate(GateId),
    Evidence(EvidenceId),
    Task(TaskId),
}
```

Later:

```text
ExecutionTarget
BuildTarget
TestTarget
RepositoryTarget
```

can be introduced if needed.

The key rule is:

> Protocol semantics should not be encoded as shell syntax.

Shell commands belong to an execution adapter.

## 832. Execution adapter boundary
<!-- source: RFL-TRANSITION.md §28 -->

Eventually:

```text
RFL protocol
      │
      │ typed execution request
      ▼
Execution Adapter
      │
      ├── Cargo
      ├── LLVM
      ├── clang
      ├── kernel build
      ├── KUnit
      ├── kselftest
      └── other tools
```

The protocol never treats:

```bash
make ...
cargo ...
./script.sh
```

as inherently authoritative.

The adapter returns an evidence-producing execution result.

## 833. Duplicate requests
<!-- source: RFL-TRANSITION.md §29 -->

The protocol needs idempotency.

Suppose:

```text
Request R42
```

arrives twice.

The second request must not silently execute twice.

Use:

```text
RequestId
    ↓
request ledger
    ↓
already accepted?
```

Possible outcomes:

```text
same request + same content
    → return recorded result

same request + different content
    → ReplayConflict
```

This is much stronger than simply saying "duplicate requests aren't allowed."

It defines their exact semantics.

## 834. Content identity matters
<!-- source: RFL-TRANSITION.md §30 -->

A `RequestId` alone is insufficient.

Consider:

```text
R42 → Execute artifact A
```

followed later by:

```text
R42 → Execute artifact B
```

The identifier is identical, but the semantic request differs.

Therefore the ledger should commit:

```text
RequestDigest =
    H(canonical(OperationRequest))
```

Then:

```text
same RequestId AND same RequestDigest
```

means replay/idempotence.

Whereas:

```text
same RequestId AND different RequestDigest
```

means:

```text
ReplayConflict
```

## 835. Epoch invalidation
<!-- source: RFL-TRANSITION.md §31 -->

Epoch should be checked at the transition boundary, not merely when the task begins.

Example:

```text
Epoch E17
   │
   ├── analyze source
   ├── generate Rust
   │
   └── source repository advances
            ↓
         Epoch E18
```

An old authorization from `E17` cannot authorize work against `E18`.

Therefore:

```text
Authorization(E17)
        + Request(E18)
        ↓
EpochMismatch
```

This single rule eliminates a large class of stale-analysis bugs.

## 836. Evidence cannot authorize itself
<!-- source: RFL-TRANSITION.md §32 -->

Another critical invariant:

```text
Evidence
    ↓
supports verification

NOT

Evidence
    ↓
declares itself valid
    ↓
authorizes certification
```

For example, a generated artifact must not contain metadata saying:

```json
{
  "verified": true
}
```

and have that metadata become verification authority.

The protocol must require an independent verification transition producing its own evidence.

## 837. Certificate construction
<!-- source: RFL-TRANSITION.md §33 -->

Certification should therefore look approximately like:

```text
Artifact
   │
   ├── source identity
   ├── semantic contracts
   ├── design mappings
   ├── verification evidence
   ├── required gates
   ├── dependency status
   └── epoch
         │
         ▼
     Certificate
```

Not:

```text
artifact.metadata.certified = true
```

Certification is a **derived protocol fact**, not an artifact-provided property.

## 838. The first complete state machine
<!-- source: RFL-TRANSITION.md §34 -->

We can now write the authoritative lifecycle:

```text
                    ┌──────────────┐
                    │    CREATED   │
                    └──────┬───────┘
                           │ Admit
                           ▼
                    ┌──────────────┐
                    │   ADMITTED   │
                    └──────┬───────┘
                           │ Authorize
                           ▼
                    ┌──────────────┐
                    │ AUTHORIZED   │
                    └──────┬───────┘
                           │ Execute
                           ▼
                    ┌──────────────┐
                    │  EXECUTING   │
                    └──────┬───────┘
                         ┌─┴─┐
                    fail │   │ complete
                         ▼   ▼
                    FAILED  SUCCEEDED
                             │
                             │ Verify
                             ▼
                         VERIFIED
                             │
                             │ Gate
                             ▼
                           GATED
                             │
                             │ Certify
                             ▼
                         CERTIFIED
```

And every arrow has explicit predicates.

## 839. Important negative property
<!-- source: RFL-TRANSITION.md §35 -->

The protocol must **not** guarantee:

```text
Certified
    ⇒ Linux upstream accepts patch
```

Instead:

```text
Certified
    ⇒ RFL-AE technical certification conditions satisfied
```

while:

```text
UpstreamAcceptanceState
    = separate governance state
```

This is necessary because technical correctness and upstream acceptance are different authorities.

## 840. Conformance properties
<!-- source: RFL-TRANSITION.md §36 -->

Beyond the 18 individual tests, define protocol-level properties.

### P1 — No unauthorized execution

```text
¬Authorized(request)
    ⇒ ¬Executing(request)
```

### P2 — No stale execution

```text
request.epoch != state.epoch
    ⇒ Reject(EpochMismatch)
```

### P3 — No scope escape

```text
target ∉ authorization.scope
    ⇒ Reject(ScopeViolation)
```

### P4 — No evidence without execution

```text
Evidence(subject)
    ⇒ corresponding execution exists
```

### P5 — No certification without verification

```text
Certified(task)
    ⇒ Verified(task)
```

### P6 — No certification with blocked required gate

```text
required_gate == Blocked
    ⇒ ¬Certified
```

### P7 — Replay determinism

```text
replay(ledger)
    == authoritative_state
```

### P8 — Immutable history

```text
committed_event
    ⇒ cannot be replaced by later event
```

These become candidates for property-based testing later.

## 841. Then comes `rfl-ledger`
<!-- source: RFL-TRANSITION.md §37 -->

Once the transition engine is deterministic, `rfl-ledger` becomes comparatively straightforward:

```text
Transition
     │
     ▼
Event
     │
     ▼
Hash-chain validation
     │
     ▼
Append-only ledger
     │
     ▼
Replay
     │
     ▼
State reconstruction
```

The important architectural ordering is therefore:

```text
rfl-types
      ↓
rfl-transition
      ↓
rfl-ledger
      ↓
rfl-evidence
      ↓
rfl-gates
```

rather than implementing the ledger first and allowing it to become an unstructured event log.

## 842. One deeper consequence
<!-- source: RFL-TRANSITION.md §38 -->

At this point RFL-AE has acquired something more important than an "agent framework."

It has a **small trusted computing base**:

```text
                RFL-AE TCB

┌─────────────────────────────────────────┐
│ Canonical types                         │
│ Identity / digest semantics             │
│ Epoch semantics                         │
│ Authorization predicates                │
│ Scope predicates                        │
│ Transition relation                     │
│ Event integrity                         │
│ Replay semantics                        │
│ Evidence binding                        │
│ Gate algebra                            │
└─────────────────────────────────────────┘
                     ▲
                     │
      everything else is subordinate
                     │
┌─────────────────────────────────────────┐
│ LLMs                                    │
│ Semantic analyzers                      │
│ Code generators                         │
│ Planners                                │
│ Review agents                           │
│ Build systems                           │
│ Test systems                            │
│ External tools                          │
└─────────────────────────────────────────┘
```

That is the architectural property worth protecting.

**Agents may be wrong. Tools may fail. Generated code may be wrong. Analyses may disagree. But none of them gets to redefine protocol truth.**

The next layer is therefore **`rfl-ledger`**, where we make that authority durable and replayable, then attack it with tampered events, duplicate requests, reordered events, forked histories, and divergent replay.

---

**Done — see [RFL-LEDGER.md](RFL-LEDGER.md)** (§843–§865, source §§39–§61, continuing this
document's own numbering), which specifies **`rfl-ledger`**, where the transition engine's
decisions become an authoritative, tamper-evident history — *the ledger is not a log of what
agents claim happened; it is the serialized history of protocol transitions*: `EventId` versus
`EventDigest`; a canonical `EventCore` that excludes its own digest; history linkage plus state
linkage as independent integrity checks; a small `Ledger` API over interchangeable backends,
because **persistence is not authority**; replay that re-runs transition semantics rather than
trusting stored state; the determinism requirement; protocol time versus historical time and an
explicit `TransitionContext`; fork detection and explicit branches with no majority voting; no
silent history rewriting, and **correction ≠ erasure**; immutable events and an explicit
genesis; structural, semantic and replay validation levels; the adversarial ledger attacks
L1–L9, including the historical-expiration trap that must succeed; and `rfl-evidence` as the
next boundary. Same provenance convention as `VERIFICATION.md`.
