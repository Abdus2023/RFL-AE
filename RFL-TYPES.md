# RFL-AE — `rfl-types` and the Executable Protocol Kernel

> **Provenance and numbering.** This document was supplied untitled (the heading above is derived from its content — rename freely), numbered §1–§18 in the source plus a final unnumbered *The next concrete layer* section. To keep the corpus contiguous, its sections are renumbered **§804–§822**, continuing directly from [PROOF-CARRYING.md](PROOF-CARRYING.md) (which ends at §803). The mapping is **`corpus_section = source_section + 803`**, with the unnumbered closing section recorded as source §19 — the convention already used by `PROTOCOL-KERNEL.md`, `FIRST-MIGRATION.md`, `KSIR-IMPL.md`, `KSIR-SLICE.md`, `KSIR-ANALYZER.md`, `EXECUTABLE-KERNEL.md`, `SEMANTIC-LAYER.md` and `PROOF-CARRYING.md`. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: RFL-TYPES.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/` tree, no `rfl-types` / `rfl-transition` / `rfl-ledger` / `rfl-evidence` / `rfl-gates` crate, no `Cargo.toml`, and none of the 18 conformance tests has been written or compiled. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** The pasted source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/RFL-TYPES.py`](diagrams/RFL-TYPES.py); re-running it reproduces all 29 diagrams. Box-drawing art stays box-drawing and the dependency-direction diagram in §804 stays ASCII `/ | \` with `↓` heads; no block mixes an ASCII `|` with box glyphs. Three diagrams were normalised geometrically, with no content change: §804's lower half was one column right of its upper half and now mirrors it; §821's spine drifted between columns 16 and 17 while its box's `┬` is at 18, and now sits on 18 throughout; §822's two lower labels are now centred on the `↓`. The §804 crate tree keeps the source's `├──` on `rfl-types/` even though it is the only child of `crates/`. The gate-status semantics in §808 and the 18 conformance tests in §820 arrived as flattened tables and are rendered as real tables. Rust types and the Rust-syntax fragments — `fn verify(…)` in §805, `type Digest = String;` in §806, `execute(command: String)` in §812, `Vec<String>` in §813 and the self-verification check in §819 — are fenced as `rust`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The next step is to make the protocol kernel concrete. I would start with **`rfl-types`**, because every other crate depends on its identity, epoch, status, and digest semantics.

---

## Contents

- [804. `rfl-types`: normative kernel](#804-rfl-types-normative-kernel)
- [805. Canonical identifiers](#805-canonical-identifiers)
- [806. Digest must be algorithm-bearing](#806-digest-must-be-algorithm-bearing)
- [807. Epoch becomes a first-class object](#807-epoch-becomes-a-first-class-object)
- [808. Status algebra](#808-status-algebra)
- [809. Verification status](#809-verification-status)
- [810. Operations](#810-operations)
- [811. Authorization](#811-authorization)
- [812. `OperationRequest`](#812-operationrequest)
- [813. MigrationUnit](#813-migrationunit)
- [814. Transition engine](#814-transition-engine)
- [815. Retry semantics](#815-retry-semantics)
- [816. Event ledger](#816-event-ledger)
- [817. Replay is a theorem of the implementation](#817-replay-is-a-theorem-of-the-implementation)
- [818. Evidence boundary](#818-evidence-boundary)
- [819. Self-verification attack](#819-self-verification-attack)
- [820. The 18 conformance tests](#820-the-18-conformance-tests)
- [821. What this gives us](#821-what-this-gives-us)
- [822. The next concrete layer](#822-the-next-concrete-layer)

---

## 804. `rfl-types`: normative kernel
<!-- source: RFL-TYPES.md §1 -->

The crate should have one job:

> Define the canonical data model and invariants shared by every RFL-AE component.

It should **not** execute commands, inspect Git, call an LLM, read the filesystem, or decide policy.

```text
crates/
├── rfl-types/
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── ids.rs
│       ├── digest.rs
│       ├── epoch.rs
│       ├── status.rs
│       ├── task.rs
│       ├── authorization.rs
│       ├── operation.rs
│       ├── artifact.rs
│       ├── evidence.rs
│       ├── contract.rs
│       ├── gate.rs
│       └── error.rs
```

Dependency direction:

```text
                 rfl-types
                /    |    \
               /     |     \
              ↓      ↓      ↓
     rfl-transition  ledger  evidence
              \      |      /
               \     |     /
                   gates
```

No reverse dependency.

## 805. Canonical identifiers
<!-- source: RFL-TYPES.md §2 -->

Do not use naked `String` or `Uuid` throughout the protocol.

The type system should prevent accidental substitution.

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
```

This is deliberately boring.

That is desirable.

A function accepting:

```rust
fn verify(task: TaskId, artifact: ArtifactId)
```

cannot accidentally receive an `EvidenceId`.

The compiler becomes part of the protocol boundary.

## 806. Digest must be algorithm-bearing
<!-- source: RFL-TYPES.md §3 -->

Do not define:

```rust
type Digest = String;
```

Instead:

```rust
pub enum DigestAlgorithm {
    Sha256,
}

pub struct Digest {
    pub algorithm: DigestAlgorithm,
    pub bytes: [u8; 32],
}
```

Later algorithms can be added deliberately.

The canonical textual form can be:

```text
sha256:<64 lowercase hexadecimal characters>
```

For example:

```text
sha256:0123456789abcdef...
```

The important invariant is:

```text
Digest equality
    = same algorithm AND same digest bytes
```

Never compare presentation strings as the semantic identity.

## 807. Epoch becomes a first-class object
<!-- source: RFL-TYPES.md §4 -->

```rust
pub struct Epoch {
    pub kernel: KernelSnapshotId,
    pub specification: Digest,
    pub protocol: Digest,
    pub generation: u64,
}
```

And:

```rust
pub fn same_epoch(a: &Epoch, b: &Epoch) -> bool {
    a == b
}
```

But the real rule belongs in the protocol:

```text
Epoch(a) ≠ Epoch(b)
        ↓
state/evidence/authorization cannot silently cross the boundary
```

This protects against one of the most dangerous migration failures:

```text
Analyze C at snapshot A
        ↓
C changes
        ↓
Generate Rust against snapshot B
        ↓
reuse analysis from A
        ↓
false certification
```

RFL-AE should reject this rather than attempt to reason around it.

## 808. Status algebra
<!-- source: RFL-TYPES.md §5 -->

Several concepts currently risk being collapsed into one enum.

Do not do that.

### Gate status

```rust
pub enum GateStatus {
    Pass,
    Fail,
    Blocked,
    NotApplicable,
    Invalidated,
}
```

Semantics:

| Status          | Meaning                                                               |
|-----------------|-----------------------------------------------------------------------|
| `Pass`          | Predicate evaluated and satisfied                                     |
| `Fail`          | Predicate evaluated and failed                                        |
| `Blocked`       | Cannot validly evaluate because required authority/evidence is absent |
| `NotApplicable` | Gate is outside declared scope                                        |
| `Invalidated`   | Previously valid result no longer applies                             |

The critical distinction:

```text
FAIL ≠ BLOCKED
```

A failed test and an unavailable test are different facts.

## 809. Verification status
<!-- source: RFL-TYPES.md §6 -->

Separate from gates:

```rust
pub enum VerificationStatus {
    Verified,
    PartiallyVerified,
    Failed,
    Blocked,
}
```

And evidence status:

```rust
pub enum EvidenceStatus {
    Observed,
    Derived,
    Hypothesis,
    Verified,
    Invalidated,
}
```

These represent different epistemic layers.

For example:

```text
Evidence:
    Observed

Verification:
    Verified

Gate:
    Pass
```

is coherent.

But:

```text
Evidence:
    Hypothesis

Verification:
    Verified
```

should be structurally impossible unless the verification record explicitly establishes what was verified independently of that hypothesis.

## 810. Operations
<!-- source: RFL-TYPES.md §7 -->

Use a closed enum initially:

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

This matters because:

```text
"run arbitrary shell command"
```

must not become the fundamental authorization primitive.

Instead:

```text
OperationKind
    + typed Target
    + Scope
    + Authorization
    + Epoch
```

defines the permitted operation.

## 811. Authorization
<!-- source: RFL-TYPES.md §8 -->

Capability and authorization remain distinct.

```rust
pub struct Capability {
    pub id: CapabilityId,
    pub operation: OperationKind,
    pub scope: Scope,
}
```

Then:

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

The distinction is:

```text
Capability
    = what this actor/system is capable of doing

Authorization
    = this actor may perform this operation for this task in this scope during this epoch
```

This prevents the classic confused-deputy problem.

## 812. `OperationRequest`
<!-- source: RFL-TYPES.md §9 -->

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

The transition engine receives exactly this kind of request.

Not:

```rust
execute(command: String)
```

## 813. MigrationUnit
<!-- source: RFL-TYPES.md §10 -->

Now the protocol gets its actual semantic object.

```rust
pub struct MigrationUnit {
    pub id: MigrationUnitId,
    pub epoch: Epoch,
    pub source: SourceSet,
    pub ksir: SemanticModelId,
    pub contracts: Vec<ContractId>,
    pub design: RustDesignId,
    pub artifact: Option<ArtifactId>,
}
```

But `SourceSet` must not merely be:

```rust
Vec<String>
```

It needs source identity.

Conceptually:

```text
SourceSet
 ├── repository identity
 ├── commit/object identity
 ├── source paths
 ├── source regions
 └── configuration scope
```

Thus:

```text
MigrationUnit
       │
       ├── source identity
       │
       ├── semantic model
       │
       ├── contracts
       │
       ├── Rust design
       │
       └── artifact
```

The artifact is therefore the **last** thing attached to the unit, not its definition.

## 814. Transition engine
<!-- source: RFL-TYPES.md §11 -->

Once `rfl-types` is frozen, `rfl-transition` can be deterministic.

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

The transition function:

```rust
pub fn transition(
    state: &State,
    request: &OperationRequest,
) -> TransitionResult
```

returns:

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

There is deliberately no:

```text
Maybe
Probably
Best effort
LLM says okay
Confidence = 0.97
```

inside the authoritative transition relation.

## 815. Retry semantics
<!-- source: RFL-TYPES.md §12 -->

A subtle but important correction:

Do **not** make this legal:

```text
Executing
   ↓
Failed
   ↓
Executing
```

as an implicit state rewind.

Instead:

```text
Task
 │
 ├── Attempt #1
 │      └── Failed
 │
 ├── Attempt #2
 │      └── Executing
 │
 └── Attempt #3
        └── Succeeded
```

So:

```rust
pub struct TaskAttempt {
    pub id: AttemptId,
    pub task: TaskId,
    pub epoch: Epoch,
    pub sequence: u64,
    pub state: AttemptState,
}
```

A retry is a **new attempt**, not a historical mutation.

That becomes extremely important for reproducibility.

## 816. Event ledger
<!-- source: RFL-TYPES.md §13 -->

`rfl-ledger` should make state transitions auditable.

```rust
pub struct Event {
    pub id: EventId,
    pub sequence: u64,
    pub epoch: Epoch,
    pub actor: AgentId,
    pub task: TaskId,
    pub request: RequestId,
    pub operation: OperationKind,

    pub previous_event: Option<EventId>,

    pub previous_state: Digest,
    pub resulting_state: Digest,

    pub event_digest: Digest,
}
```

The event digest should commit to canonical event content.

Conceptually:

```text
E0
 │
 │ hash(E0)
 ↓
E1
 │
 │ hash(E1 + previous_event)
 ↓
E2
 │
 ↓
E3
```

Tampering becomes detectable.

## 817. Replay is a theorem of the implementation
<!-- source: RFL-TYPES.md §14 -->

The ledger must support:

```rust
pub fn replay(events: &[Event]) -> Result<State, ReplayError>;
```

and the central invariant becomes:

```text
replay(authoritative_ledger)
        == authoritative_state
```

This is stronger than:

```text
"we logged what happened"
```

because the ledger becomes an executable historical representation.

The conformance test should deliberately mutate:

```text
E17.resulting_state
E17.event_digest
E18.previous_event
E18.sequence
```

and require replay rejection.

## 818. Evidence boundary
<!-- source: RFL-TYPES.md §15 -->

Execution produces evidence.

The agent does not.

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

This creates a crucial distinction:

```text
Agent:
    "I verified it."

        ≠

Execution infrastructure:
    "This exact artifact was built/tested
     under this exact environment,
     producing this exact result."
```

Only the latter is execution evidence.

## 819. Self-verification attack
<!-- source: RFL-TYPES.md §16 -->

One of the first adversarial rules should be:

```text
Generator ≠ sole verifier
```

Suppose:

```text
Agent A
  ↓
generates Rust
  ↓
Agent A
  ↓
claims verification
```

The protocol should reject it if the verification policy requires independence.

Formally:

```rust
if verifier == generator
    && contract.requires_independent_verification {
    reject(SelfVerification);
}
```

This should not be a social convention.

It should be a transition invariant.

## 820. The 18 conformance tests
<!-- source: RFL-TYPES.md §17 -->

The first executable milestone should contain exactly these adversarial cases:

| #  | Attack                   | Expected |
|----|--------------------------|----------|
| 1  | stale epoch              | Reject   |
| 2  | snapshot mismatch        | Reject   |
| 3  | specification mismatch   | Reject   |
| 4  | expired authorization    | Reject   |
| 5  | revoked authorization    | Reject   |
| 6  | missing capability       | Reject   |
| 7  | scope escape             | Reject   |
| 8  | invalid state transition | Reject   |
| 9  | duplicate request        | Reject   |
| 10 | forged artifact          | Reject   |
| 11 | unbound evidence         | Reject   |
| 12 | self-verification        | Reject   |
| 13 | event tampering          | Reject   |
| 14 | replay divergence        | Reject   |
| 15 | required gate failure    | Reject   |
| 16 | required gate blocked    | Reject   |
| 17 | invalidated dependency   | Reject   |
| 18 | complete valid execution | Accept   |

The last test is important.

An adversarial system that only knows how to reject is not useful.

## 821. What this gives us
<!-- source: RFL-TYPES.md §18 -->

After these crates:

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

we have the first genuinely executable RFL-AE kernel:

```text
          UNTRUSTED AGENTS
                  │
                  │ typed request
                  ▼
        ┌───────────────────┐
        │   RFL-AE KERNEL   │
        │                   │
        │ Types             │
        │ Epoch             │
        │ Authorization     │
        │ Transition        │
        │ Ledger            │
        │ Evidence          │
        │ Gates             │
        └─────────┬─────────┘
                  │
                  ▼
          EXECUTION SYSTEM
                  │
                  ▼
              EVIDENCE
                  │
                  ▼
             CERTIFICATE
```

And, critically:

```text
LLM output
    ≠ protocol state

LLM confidence
    ≠ verification

test output
    ≠ contract satisfaction

contract satisfaction
    ≠ upstream acceptance
```

That separation is the foundation on which the later **KSIR → Contracts → Rust Design IR → Rust generation** pipeline can safely sit.

## 822. The next concrete layer
<!-- source: RFL-TYPES.md §19 -->

After freezing `rfl-types`, I would implement **`rfl-transition` first**, including the transition matrix:

```text
Current State × Operation × Preconditions
                    ↓
           Accepted / Rejected
                    ↓
              State + Event
```

and make the **18 attacks executable as conformance tests before adding any LLM/semantic agent code**.

That changes RFL-AE from a specification describing a trustworthy agent architecture into a small, testable **authority kernel** that agents must obey.
