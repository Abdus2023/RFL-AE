# RFL-AE — `rfl-types v0.1`: Freezing the First Executable API Contract

> **Provenance and numbering.** This document was supplied untitled (the heading above is derived from its content — rename freely). Unlike the four previous `RFL-*` pastes, it **restarts the author's numbering at §1**: it is numbered **§1–§20** in the source, followed by a final unnumbered *The implementation freeze point* section. To keep the corpus contiguous, its sections are renumbered **§926–§946**, continuing directly from [RFL-GATES.md](RFL-GATES.md) (which ends at §925). The mapping is **`corpus_section = source_section + 925`**, with the unnumbered closing section recorded as source **§21** — the convention already used by `RFL-GATES.md`, `PROOF-CARRYING.md` and the `KSIR-*` documents. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: RFL-TYPES-V01.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause. The file is named `RFL-TYPES-V01.md` because [RFL-TYPES.md](RFL-TYPES.md) (§804–§822) already exists; this document freezes that crate's v0.1 API.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/rfl-types/` or `crates/rfl-transition/` source, no unit test and none of the attacks A01–A18 has been written or compiled. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** The paste arrived wrapped in a code fence; the fence was treated as transport, not content. The source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/RFL-TYPES-V01.py`](diagrams/RFL-TYPES-V01.py); re-running it reproduces all 37 diagrams. No diagram needed a geometric normalisation. The source mixed heading levels (`## 1.` then `# 2.` onwards); all numbered sections are `##` here, as in the rest of the corpus, and the source's `###` sub-headings in §936 and §939 stay `###`. Word lists that arrived with single spaces only were broken into one item per line (§928, §929, §940, §944, and the lists in §946). Two runs were kept on one line and could instead be split: `scope is data not prose` (§932) and `expected result + expected rejection reason` (§944). In §946 the two-space gaps after the last two `↓` arrows were read as blank lines, by the same rule used everywhere else. The §943 transition table is rendered as a markdown table. Rust declarations and the Rust-syntax fragments — `same_protocol()` / `same_kernel()` (§929), the field fragments `operation: String`, `valid: bool` and `target: String` (§931, §933, §934), `#[derive(Serialize)]` (§938), the `#[test]` stubs (§939) and `apply()` (§941) — are fenced as `rust`; pseudo-expressions such as `KernelSnapshotId( sha256:<…> )` stay `text`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The next step is to freeze the **first executable API contract**, beginning with `rfl-types v0.1`. No new architectural layer is needed.

---

## Contents

- [926. `rfl-types v0.1` — normative API](#926-rfl-types-v01--normative-api)
- [927. Identifier discipline](#927-identifier-discipline)
- [928. Digest](#928-digest)
- [929. Epoch](#929-epoch)
- [930. `KernelSnapshotId`](#930-kernelsnapshotid)
- [931. Operation algebra](#931-operation-algebra)
- [932. Scope must be structured](#932-scope-must-be-structured)
- [933. Authorization](#933-authorization)
- [934. OperationRequest](#934-operationrequest)
- [935. Task state](#935-task-state)
- [936. Status algebra](#936-status-algebra)
- [937. Rejection taxonomy](#937-rejection-taxonomy)
- [938. Canonical serialization](#938-canonical-serialization)
- [939. `rfl-types` invariants](#939-rfl-types-invariants)
- [940. First security property](#940-first-security-property)
- [941. `rfl-transition v0.1`](#941-rfl-transition-v01)
- [942. Preconditions](#942-preconditions)
- [943. Transition table](#943-transition-table)
- [944. The first 18 protocol attacks](#944-the-first-18-protocol-attacks)
- [945. First vertical conformance scenario](#945-first-vertical-conformance-scenario)
- [946. The implementation freeze point](#946-the-implementation-freeze-point)

---

## 926. `rfl-types v0.1` — normative API
<!-- source: RFL-TYPES-V01.md §1 -->

The crate should be deliberately boring. It contains **domain vocabulary and invariants**, not transition logic, persistence, cryptography orchestration, or policy evaluation.

```text
rfl-types
│
├── identifiers
├── digest
├── epoch
├── scope
├── operation
├── authorization
├── task
├── artifact
├── evidence
├── contract
├── gate
└── error
```

Dependency rule:

```text
rfl-types
   │
   ├── no rfl-transition
   ├── no rfl-ledger
   ├── no rfl-evidence
   ├── no rfl-gates
   └── no filesystem/network/LLM/runtime authority
```

This keeps the bottom of the dependency graph stable.

## 927. Identifier discipline
<!-- source: RFL-TYPES-V01.md §2 -->

Every protocol identity gets its own newtype.

```rust
pub struct TaskId(pub Uuid);
pub struct AgentId(pub Uuid);
pub struct ArtifactId(pub Uuid);
pub struct EvidenceId(pub Uuid);
pub struct ContractId(pub Uuid);
pub struct GateId(pub Uuid);
pub struct AuthorizationId(pub Uuid);
pub struct EventId(pub Uuid);
pub struct RequestId(pub Uuid);
pub struct MigrationUnitId(pub Uuid);
pub struct SemanticModelId(pub Uuid);
pub struct RustDesignId(pub Uuid);
pub struct DesignElementId(pub Uuid);
pub struct ObligationId(pub Uuid);
pub struct GenerationId(pub Uuid);
pub struct AttemptId(pub Uuid);
pub struct CertificateId(pub Uuid);
pub struct ExecutionId(pub Uuid);
pub struct ExecutorId(pub Uuid);
pub struct CapabilityId(pub Uuid);
pub struct BranchId(pub Uuid);
```

The important invariant is:

```text
TaskId ≠ ArtifactId ≠ EvidenceId
```

even though they may use the same underlying representation.

This prevents accidental API interchange.

Bad:

```rust
fn verify(id: Uuid) { ... }
```

Good:

```rust
fn verify(
    artifact: ArtifactId,
    contract: ContractId,
    evidence: &[EvidenceId],
) { ... }
```

## 928. Digest
<!-- source: RFL-TYPES-V01.md §3 -->

Do not use a naked `[u8; 32]`.

```rust
#[derive(Clone, Copy, PartialEq, Eq, Hash)]
pub enum DigestAlgorithm {
    Sha256,
}

#[derive(Clone, Copy, PartialEq, Eq, Hash)]
pub struct Digest {
    pub algorithm: DigestAlgorithm,
    pub bytes: [u8; 32],
}
```

Canonical textual form:

```text
sha256:<64 lowercase hexadecimal characters>
```

Example:

```text
sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
```

The canonical representation must have exactly one serialization.

No:

```text
SHA256(...)
sha256(...)
sha-256:...
```

as protocol identities.

## 929. Epoch
<!-- source: RFL-TYPES-V01.md §4 -->

The epoch is one of the most important anti-staleness mechanisms.

```rust
pub struct Epoch {
    pub kernel: KernelSnapshotId,
    pub specification: Digest,
    pub protocol: Digest,
    pub generation: u64,
}
```

Canonical equality:

```text
Epoch(a) == Epoch(b) iff
 a.kernel         == b.kernel
∧ a.specification == b.specification
∧ a.protocol      == b.protocol
∧ a.generation    == b.generation
```

Do not provide a partial epoch comparison such as:

```rust
same_protocol()
same_kernel()
```

and then accidentally treat that as authorization compatibility.

Compatibility should be explicit:

```rust
pub fn same_epoch(a: &Epoch, b: &Epoch) -> bool {
    a == b
}
```

The protocol should reject:

```text
request.epoch != authoritative_epoch
```

before execution.

## 930. `KernelSnapshotId`
<!-- source: RFL-TYPES-V01.md §5 -->

This resolves the earlier `SnapshotId` ambiguity.

Use:

```rust
pub struct KernelSnapshotId(pub Digest);
```

and eliminate generic `SnapshotId` from the normative vocabulary.

A kernel snapshot is therefore not merely:

```text
"linux-7.x"
```

but an identity bound to an actual snapshot digest.

For example:

```text
KernelSnapshotId(
    sha256:<commit/tree identity>
)
```

The exact snapshot hashing scheme belongs to the source-identity specification, not to `rfl-types`.

## 931. Operation algebra
<!-- source: RFL-TYPES-V01.md §6 -->

Operations are closed.

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

Do not permit arbitrary strings:

```rust
operation: String
```

because then the authorization layer cannot establish a closed-world security property.

Capability:

```rust
pub struct Capability {
    pub id: CapabilityId,
    pub operation: OperationKind,
    pub scope: Scope,
}
```

## 932. Scope must be structured
<!-- source: RFL-TYPES-V01.md §7 -->

Avoid:

```rust
pub struct Scope {
    pub value: String,
}
```

Instead:

```rust
pub struct Scope {
    pub repository: Option<RepositoryScope>,
    pub paths: Vec<PathScope>,
    pub architectures: Vec<Architecture>,
    pub configurations: Vec<ConfigIdentity>,
}
```

The exact fields can evolve, but the key principle is:

```text
scope is data not prose
```

A path scope should not be able to silently mean an architecture scope.

For example:

```text
repository = linux
paths       = drivers/foo/**
architecture = x86_64
configuration = CONFIG_FOO
```

is machine-checkable.

## 933. Authorization
<!-- source: RFL-TYPES-V01.md §8 -->

```rust
pub struct Authorization {
    pub id: AuthorizationId,
    pub epoch: Epoch,
    pub actor: AgentId,
    pub task: TaskId,
    pub capability: CapabilityId,
    pub scope: Scope,
    pub expires_at: Timestamp,
}
```

But authorization validity must also include revocation.

Therefore the authorization object itself should **not** contain a mutable:

```rust
valid: bool
```

Instead:

```text
Authorization
      + AuthorizationState
      ↓
authorization validity
```

For example:

```rust
pub enum AuthorizationState {
    Active,
    Revoked {
        event: EventId,
    },
}
```

This preserves historical truth.

A previously valid authorization remains historically valid for an event that occurred while it was active.

## 934. OperationRequest
<!-- source: RFL-TYPES-V01.md §9 -->

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

`Target` is closed:

```rust
pub enum Target {
    Source(SourceRegion),
    MigrationUnit(MigrationUnitId),
    Artifact(ArtifactId),
    Contract(ContractId),
    Evidence(EvidenceId),
    Gate(GateId),
    Task(TaskId),
}
```

This is preferable to:

```rust
target: String
```

because:

```text
"kernel/foo.c"
```

cannot accidentally be interpreted as an artifact ID.

## 935. Task state
<!-- source: RFL-TYPES-V01.md §10 -->

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

But the critical design rule remains:

**do not encode retries by moving backwards.**

Instead:

```rust
pub struct TaskAttempt {
    pub id: AttemptId,
    pub task: TaskId,
    pub epoch: Epoch,
    pub sequence: u64,
    pub state: AttemptState,
}
```

Thus:

```text
Task
 ├── Attempt 0 → Failed
 ├── Attempt 1 → Failed
 └── Attempt 2 → Succeeded
```

rather than:

```text
Executing
 ↓
Failed
 ↓
Executing
 ↓
Failed
 ↓
Executing
```

The latter destroys useful historical semantics.

## 936. Status algebra
<!-- source: RFL-TYPES-V01.md §11 -->

These must remain separate.

### Gate

```rust
pub enum GateStatus {
    Pass,
    Fail,
    Blocked,
    NotApplicable,
    Invalidated,
}
```

### Verification

```rust
pub enum VerificationStatus {
    Verified,
    PartiallyVerified,
    Failed,
    Blocked,
}
```

### Evidence validity

Do not overload epistemic status with validity.

Use two axes:

```rust
pub enum EvidenceKind {
    Observed,
    Derived,
    Hypothesis,
}
```

and:

```rust
pub enum EvidenceValidity {
    Unvalidated,
    Valid,
    Invalid,
    Superseded,
}
```

This prevents a particularly dangerous semantic collapse:

```text
"Observed" ≠ "Valid"
```

Something can genuinely be observed and subsequently determined to be invalid evidence.

## 937. Rejection taxonomy
<!-- source: RFL-TYPES-V01.md §12 -->

The protocol needs stable machine-readable rejection reasons.

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

Do not initially expose free-form strings as the authoritative reason.

A human-readable explanation can accompany the enum:

```rust
pub struct Rejection {
    pub reason: RejectionReason,
    pub explanation: Option<String>,
}
```

But the enum is normative.

## 938. Canonical serialization
<!-- source: RFL-TYPES-V01.md §13 -->

This is a critical freeze point.

RFL-AE should not rely on:

```rust
#[derive(Serialize)]
```

alone as its canonical identity mechanism.

For every hash-bearing object define:

```text
CanonicalEncode(T) → bytes
Digest(T) = SHA256(CanonicalEncode(T))
```

The canonical encoding should be deterministic.

A suitable initial rule:

```text
RFC 8785 JCS
```

for JSON-compatible protocol objects.

However, there is an important restriction:

**JCS should not become the semantic model itself.**

The layers remain:

```text
Rust object
   ↓
canonical structured representation
   ↓
canonical bytes
   ↓
digest
```

Serialization is representation.

It is not semantics.

## 939. `rfl-types` invariants
<!-- source: RFL-TYPES-V01.md §14 -->

The crate should test these directly.

### ID isolation

```rust
#[test]
fn ids_are_distinct_types() { ... }
```

### Digest canonicality

```rust
#[test]
fn digest_serialization_is_canonical() { ... }
```

### Epoch equality

```rust
#[test]
fn epoch_changes_when_any_component_changes() { ... }
```

Four mutation tests:

```text
kernel changes       → epoch changes
specification changes → epoch changes
protocol changes      → epoch changes
generation changes    → epoch changes
```

### Gate distinction

```rust
#[test]
fn fail_is_not_blocked() { ... }

#[test]
fn blocked_is_not_fail() { ... }
```

### Evidence distinction

```rust
#[test]
fn observed_does_not_mean_valid() { ... }
```

## 940. First security property
<!-- source: RFL-TYPES-V01.md §15 -->

The first executable property should be:

```text
P1: No stale request can become an accepted transition.
```

Formally:

```text
request.epoch ≠ state.epoch
        ⇒ δ(state, request) = Reject(EpochMismatch)
```

No exception for:

```text
"same repository"
"same source"
"same agent"
"same task"
```

Epoch mismatch is sufficient for rejection.

## 941. `rfl-transition v0.1`
<!-- source: RFL-TYPES-V01.md §16 -->

Once `rfl-types` is frozen, `rfl-transition` becomes the first **authority-bearing** crate.

Its API should be approximately:

```rust
pub trait TransitionEngine {
    fn apply(
        &self,
        state: &State,
        request: &OperationRequest,
        context: &TransitionContext,
    ) -> TransitionResult;
}
```

Result:

```rust
pub enum TransitionResult {
    Accepted {
        event: EventId,
        state: StateDigest,
    },
    Rejected {
        rejection: Rejection,
    },
}
```

The important property:

```rust
apply()
```

does not modify state.

It computes a transition.

State mutation belongs to the caller after acceptance, or to an explicitly transactional state machine.

That makes testing substantially easier.

## 942. Preconditions
<!-- source: RFL-TYPES-V01.md §17 -->

Evaluation order should be deterministic.

```text
1. request identity
2. task existence
3. epoch
4. snapshot
5. authorization existence
6. authorization epoch
7. authorization actor
8. authorization task
9. capability
10. scope
11. expiry/revocation
12. task state
13. dependencies
14. duplicate/replay
15. operation-specific predicates
```

This matters because a nondeterministic rejection order creates nondeterministic protocol behavior.

## 943. Transition table
<!-- source: RFL-TYPES-V01.md §18 -->

The first frozen table should be this small:

| Current    | Operation | Result     |
|------------|-----------|------------|
| Created    | Admit     | Admitted   |
| Admitted   | Authorize | Authorized |
| Authorized | Execute   | Executing  |
| Executing  | Complete  | Succeeded  |
| Executing  | Fail      | Failed     |
| Succeeded  | Verify    | Verified   |
| Verified   | Gate      | Gated      |
| Gated      | Certify   | Certified  |

Everything else:

```text
Reject(InvalidTransition)
```

No implicit transitions.

No automatic:

```text
Succeeded → Certified
```

No automatic:

```text
BuildPassed → Verified
```

Those relationships belong to later verification/gate semantics.

## 944. The first 18 protocol attacks
<!-- source: RFL-TYPES-V01.md §19 -->

These become mandatory conformance tests rather than documentation examples.

```text
A01 stale epoch
A02 snapshot mismatch
A03 specification mismatch
A04 expired authorization
A05 revoked authorization
A06 missing capability
A07 scope escape
A08 invalid transition
A09 duplicate request
A10 forged artifact
A11 unbound evidence
A12 self-verification
A13 event tampering
A14 replay divergence
A15 failed required gate
A16 blocked required gate
A17 invalidated dependency
A18 valid complete execution
```

The test suite should explicitly assert both:

```text
expected result + expected rejection reason
```

For example:

```rust
assert_eq!(
    engine.apply(&state, &request, &ctx),
    TransitionResult::Rejected {
        rejection: Rejection {
            reason: RejectionReason::EpochMismatch,
            ..
        }
    }
);
```

Not merely:

```rust
assert!(result.is_err());
```

The latter would allow unrelated failures to masquerade as security enforcement.

## 945. First vertical conformance scenario
<!-- source: RFL-TYPES-V01.md §20 -->

Before touching actual Linux migration semantics, establish this synthetic scenario:

```text
Task T1
  │
  ├── MigrationUnit M1
  │
  ├── Artifact A1
  │
  └── Contract C1
```

Then:

```text
Epoch E1
   ↓
Authorize Agent A1
   ↓
Generate Artifact A1
   ↓
Execute Build
   ↓
Evidence EVID1
   ↓
Verify
   ↓
Gate G1 = Pass
   ↓
Certificate C1
```

And separately prove:

```text
E1 → request E2
```

is rejected.

Likewise:

```text
valid evidence + failed gate
```

must **not** produce a certificate.

And:

```text
all technical gates pass
```

must still not manufacture:

```text
UpstreamAcceptance = Accepted
```

## 946. The implementation freeze point
<!-- source: RFL-TYPES-V01.md §21 -->

At this point the architecture has crossed an important boundary:

```text
CONCEPTUAL
──────────
architecture
semantic model
trust model
verification model
         ↓
FREEZE

EXECUTABLE
──────────
rfl-types
rfl-transition
rfl-ledger
rfl-evidence
rfl-gates
         ↓

CONFORMANCE
         ↓

FIRST REAL MIGRATION UNIT
```

The next artifact should therefore be the **normative `rfl-types v0.1` source-level specification**: exact Rust declarations, derives, visibility, dependency policy, canonical serialization rules, constructor invariants, and the complete unit-test matrix. After that, `rfl-transition` can be specified against a frozen type surface rather than continuing to move underneath it.

---

**Done — see [RFL-TRANSITION-V01.md](RFL-TRANSITION-V01.md)** (§947–§969, source §§1–§23 — the
author restarted at §1 again, so the offset is +946), *`rfl-transition v0.1` — executable
state-machine specification*, which freezes the transition semantics against this document's type
surface: `rfl-transition` decides whether a transition is admissible and never executes it; an
explicit `State` and `TransitionContext` with no hidden inputs; a deterministic δ that returns an
`EventProposal` rather than committed history; **Accepted ≠ Executed ≠ Succeeded ≠ Verified ≠
Certified**; pure precondition functions in a frozen P01–P19 order; the full authorization
relation; capability versus authorization; scope containment; the state-transition matrix and its
invalid transitions; attempts instead of backward moves; `(RequestId, RequestDigest)` idempotency;
self-verification as an open design point; operation policies; replay and the historical-time
rule; invariants T1–T10; property-based tests; and `rfl-ledger` as the next hard point. Same
provenance convention as `VERIFICATION.md`.
