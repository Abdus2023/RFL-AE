# `rfl-transition v0.1` — executable state-machine specification

> **Provenance and numbering.** This document was supplied as *`rfl-transition v0.1` — executable state-machine specification* (the heading above is the source's own), numbered **§1–§23** in the source, preceded by an unnumbered introduction that is kept as the preamble below. Like [RFL-TYPES-V01.md](RFL-TYPES-V01.md), it restarts the author's numbering at §1. To keep the corpus contiguous, its sections are renumbered **§947–§969**, continuing directly from `RFL-TYPES-V01.md` (which ends at §946). The mapping is the plain **`corpus_section = source_section + 946`**; there is no unnumbered closing section. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: RFL-TRANSITION-V01.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause. The file is named `RFL-TRANSITION-V01.md` because [RFL-TRANSITION.md](RFL-TRANSITION.md) (§823–§842) already exists; this document freezes that crate's v0.1 semantics.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/rfl-transition/` source, precondition function, operation policy, replay routine or test — including invariants T1–T10 and the property-based tests of §967 — has been written or compiled. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** The paste arrived wrapped in a code fence; the fence was treated as transport, not content. The source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/RFL-TRANSITION-V01.py`](diagrams/RFL-TRANSITION-V01.py); re-running it reproduces all 74 diagrams. One diagram was normalised geometrically, with no content change: in the §968 authority boundary, four labels were one to four columns off the vertical line that the box's `┬` and every arrow sit on, and are now centred on it. The source mixed heading levels (`## 1.` then `# 2.` onwards); all numbered sections are `##` here, and the source's `###` sub-headings in §960 and §966 stay `###`. Word lists that arrived with single spaces only were broken into one item per line (§947, §950, §952, §954, §964, §965, §967). In §957, `Authorized:  drivers/foo/**` has a blank line between the label and the path, by the usual two-space rule. In §963 each `↓ δ` stays on its arrow line, because δ labels the step. The one-line formulas T1–T8 in §966 were kept on one line each. Rust declarations and the Rust-syntax fragments — the forbidden calls in §950, `OperationKind::Execute` (§952) and the `if` guard in §961 — are fenced as `rust`; the assignment `A0.state = Executing` (§959) stays `text`, as `verified = true` did in `RFL-EVIDENCE.md`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The next layer should now be frozen at the **transition semantics** level.

The key rule is:

> `rfl-transition` decides whether a requested transition is admissible. It does not execute the requested operation.

That distinction prevents the protocol from quietly becoming an execution engine.

---

## Contents

- [947. Crate boundary](#947-crate-boundary)
- [948. State](#948-state)
- [949. Transition context](#949-transition-context)
- [950. Deterministic transition function](#950-deterministic-transition-function)
- [951. Accepted transition](#951-accepted-transition)
- [952. Why `Accepted` does not mean `Executed`](#952-why-accepted-does-not-mean-executed)
- [953. Preconditions](#953-preconditions)
- [954. Deterministic evaluation order](#954-deterministic-evaluation-order)
- [955. Authorization relation](#955-authorization-relation)
- [956. Capability versus authorization](#956-capability-versus-authorization)
- [957. Scope containment](#957-scope-containment)
- [958. State transition matrix](#958-state-transition-matrix)
- [959. Attempt semantics](#959-attempt-semantics)
- [960. Duplicate request semantics](#960-duplicate-request-semantics)
- [961. Self-verification](#961-self-verification)
- [962. Operation-specific predicates](#962-operation-specific-predicates)
- [963. Replay](#963-replay)
- [964. Critical historical-time rule](#964-critical-historical-time-rule)
- [965. Replay attack test](#965-replay-attack-test)
- [966. Transition invariants](#966-transition-invariants)
- [967. Property-based testing](#967-property-based-testing)
- [968. The transition crate's actual authority boundary](#968-the-transition-crates-actual-authority-boundary)
- [969. What comes immediately after](#969-what-comes-immediately-after)

---

## 947. Crate boundary
<!-- source: RFL-TRANSITION-V01.md §1 -->

```text
crates/rfl-transition/
├── Cargo.toml
└── src/
    ├── lib.rs
    ├── engine.rs
    ├── state.rs
    ├── context.rs
    ├── preconditions.rs
    ├── transitions.rs
    ├── rejection.rs
    ├── authorization.rs
    ├── replay.rs
    └── tests/
        ├── admission.rs
        ├── authorization.rs
        ├── execution.rs
        ├── verification.rs
        ├── certification.rs
        ├── epoch.rs
        ├── replay.rs
        └── adversarial.rs
```

Dependency:

```text
rfl-transition
      │
      └── rfl-types
```

Not:

```text
rfl-transition → rfl-ledger
rfl-transition → rfl-evidence
rfl-transition → rfl-gates
```

Those crates consume transition results.

This avoids circular authority.

## 948. State
<!-- source: RFL-TRANSITION-V01.md §2 -->

The transition engine needs an explicit authoritative state.

```rust
pub struct State {
    pub epoch: Epoch,
    pub tasks: TaskStore,
    pub attempts: AttemptStore,
    pub authorizations: AuthorizationStore,
    pub capabilities: CapabilityStore,
    pub dependencies: DependencyState,
}
```

The stores should be deterministic collections.

For v0.1, conceptually:

```rust
pub trait TaskStore {
    fn get(&self, id: TaskId) -> Option<&Task>;
}
```

and equivalent lookup interfaces for other entities.

The transition engine must not fetch missing information from:

- the filesystem
- Git
- the network
- an LLM
- environment variables
- current process state
- arbitrary shell commands

If the engine needs information, it must be present in `State` or `TransitionContext`.

## 949. Transition context
<!-- source: RFL-TRANSITION-V01.md §3 -->

Some facts are needed to evaluate a transition but are not themselves authoritative state.

```rust
pub struct TransitionContext {
    pub observed_time: Timestamp,
    pub authorization_state: AuthorizationState,
    pub dependency_state: DependencyState,
}
```

More importantly:

```text
State
    = authoritative protocol state

Context
    = supplied evaluation context
```

The engine must not silently construct either.

## 950. Deterministic transition function
<!-- source: RFL-TRANSITION-V01.md §4 -->

The core mathematical contract becomes:

```text
δ : (State, OperationRequest, TransitionContext)
      →
    TransitionResult
```

where:

```text
TransitionResult
    =
      Accepted(EventProposal)
    |
      Rejected(Rejection)
```

For the same inputs:

```text
δ(S, R, C) = X
```

must always produce the same `X`.

Therefore this is forbidden inside `apply()`:

```rust
SystemTime::now()
rand::random()
network_call()
llm_call()
read_environment()
read_filesystem()
```

If time matters, it comes through:

```text
context.observed_time
```

## 951. Accepted transition
<!-- source: RFL-TRANSITION-V01.md §5 -->

Do not immediately emit a committed ledger event.

Return a proposal:

```rust
pub struct EventProposal {
    pub event_id: EventId,
    pub epoch: Epoch,
    pub actor: AgentId,
    pub task: TaskId,
    pub request: RequestId,
    pub operation: OperationKind,
    pub previous_state: Digest,
    pub resulting_state: Digest,
}
```

Then:

```text
TransitionEngine
      ↓
EventProposal
      ↓
Ledger validation
      ↓
append
      ↓
authoritative history
```

This gives the ledger the opportunity to reject:

- duplicate events
- broken sequence
- broken previous-event links
- digest mismatch
- forks

The transition engine should not pretend that an accepted *proposal* is already durable history.

## 952. Why `Accepted` does not mean `Executed`
<!-- source: RFL-TRANSITION-V01.md §6 -->

This distinction needs to be explicit.

```text
REQUEST
  ↓
Transition accepted
  ↓
authorization to perform operation
  ↓
actual executor
  ↓
execution result
```

For example:

```rust
OperationKind::Execute
```

being accepted means:

```text
"The protocol permits this execution."
```

It does **not** mean:

```text
"The command ran successfully."
```

That second fact belongs to `rfl-evidence`.

Therefore:

```text
Accepted ≠ Executed
Executed ≠ Succeeded
Succeeded ≠ Verified
Verified ≠ Certified
```

This chain should become a formal invariant across the repository.

## 953. Preconditions
<!-- source: RFL-TRANSITION-V01.md §7 -->

Implement the precondition pipeline as pure functions.

```rust
pub fn check_task(
    state: &State,
    request: &OperationRequest,
) -> Result<(), RejectionReason>;
```

```rust
pub fn check_epoch(
    state: &State,
    request: &OperationRequest,
) -> Result<(), RejectionReason>;
```

```rust
pub fn check_authorization(
    state: &State,
    request: &OperationRequest,
    context: &TransitionContext,
) -> Result<(), RejectionReason>;
```

```rust
pub fn check_scope(
    authorization: &Authorization,
    request: &OperationRequest,
) -> Result<(), RejectionReason>;
```

```rust
pub fn check_task_state(
    task: &Task,
    operation: &OperationKind,
) -> Result<(), RejectionReason>;
```

Then the engine composes them.

## 954. Deterministic evaluation order
<!-- source: RFL-TRANSITION-V01.md §8 -->

Freeze the order.

```text
P01 request identity
P02 task existence
P03 epoch
P04 snapshot
P05 specification
P06 protocol
P07 authorization existence
P08 authorization epoch
P09 authorization actor
P10 authorization task
P11 capability
P12 operation compatibility
P13 scope
P14 expiry
P15 revocation
P16 task state
P17 dependency state
P18 duplicate/replay
P19 operation-specific preconditions
```

This is not merely an implementation convenience.

It makes rejection behavior deterministic.

Given the same invalid request, RFL-AE should not sometimes report:

```text
EpochMismatch
```

and sometimes:

```text
ScopeViolation
```

depending on hash-map iteration order.

## 955. Authorization relation
<!-- source: RFL-TRANSITION-V01.md §9 -->

Authorization validity should be a conjunction:

```text
AUTHORIZED(R,S,C)
 :=
     AuthorizationExists
 ∧   EpochMatches
 ∧   ActorMatches
 ∧   TaskMatches
 ∧   CapabilityExists
 ∧   OperationAllowed
 ∧   ScopeSatisfied
 ∧   NotExpired
 ∧   NotRevoked
```

Therefore:

```text
Authorization exists
```

is insufficient.

And:

```text
Capability exists
```

is insufficient.

And:

```text
Agent possesses capability
```

is insufficient.

The protocol requires the complete relation.

## 956. Capability versus authorization
<!-- source: RFL-TRANSITION-V01.md §10 -->

This deserves an explicit invariant.

```text
Capability
    =
    what an actor may potentially perform

Authorization
    =
    permission to perform one operation
    for one task
    in one epoch
    within one scope
```

Thus:

```text
Capability(Execute, /drivers/foo)
```

does not itself authorize:

```text
Execute(Task-42, /drivers/foo)
```

Authorization must bind the capability to the concrete task and epoch.

## 957. Scope containment
<!-- source: RFL-TRANSITION-V01.md §11 -->

Scope evaluation must be monotonic:

```text
requested_scope ⊆ authorized_scope
```

Never:

```text
authorized_scope ⊆ requested_scope
```

Example:

```text
Authorized:

drivers/foo/**
```

Request:

```text
drivers/foo/bar.c
```

→ permitted.

Request:

```text
drivers/bar/baz.c
```

→ `ScopeViolation`.

Request:

```text
drivers/foo/** + drivers/bar/**
```

→ `ScopeViolation`.

The latter is important because an agent must not enlarge its scope by adding another target.

## 958. State transition matrix
<!-- source: RFL-TRANSITION-V01.md §12 -->

Freeze the protocol state machine:

```text
Created
   │
   │ Admit
   ▼
Admitted
   │
   │ Authorize
   ▼
Authorized
   │
   │ Execute
   ▼
Executing
   ├──────── Complete ────────► Succeeded
   │
   └──────── Fail ────────────► Failed

Succeeded
   │
   │ Verify
   ▼
Verified
   │
   │ Gate
   ▼
Gated
   │
   │ Certify
   ▼
Certified
```

Invalid transitions include:

```text
Created      → Execute
Created      → Verify
Created      → Certify

Admitted     → Execute
Authorized   → Verify
Executing    → Certify
Succeeded    → Certify
Failed       → Verify
Verified     → Execute
Gated        → Execute
Certified    → anything
```

All must reject.

## 959. Attempt semantics
<!-- source: RFL-TRANSITION-V01.md §13 -->

The retry model is:

```text
Task T
│
├── Attempt A0
│     └── Failed
│
├── Attempt A1
│     └── Failed
│
└── Attempt A2
      └── Succeeded
```

A failed attempt is immutable.

Do not mutate:

```text
A0.state = Executing
```

back into execution.

Create:

```text
A1
```

instead.

This provides an important forensic property:

```text
attempt sequence is historical evidence
```

## 960. Duplicate request semantics
<!-- source: RFL-TRANSITION-V01.md §14 -->

`RequestId` alone is not enough.

Define:

```text
RequestDigest = Digest(CanonicalEncode(OperationRequest))
```

Then:

```text
(RequestId, RequestDigest)
```

identifies an exact request instance.

Cases:

### Same ID + same digest

```text
→ return recorded result
```

This gives idempotency.

### Same ID + different digest

```text
→ ReplayConflict
```

This prevents:

```text
RequestId = R1
first meaning  = Execute(foo)
second meaning = Execute(bar)
```

from being interpreted as the same operation.

## 961. Self-verification
<!-- source: RFL-TRANSITION-V01.md §15 -->

The transition layer should explicitly reject self-verification where the same authority chain is attempting to establish its own trust.

Conceptually:

```text
artifact generator
       ↓
verification authority
```

must not collapse into:

```text
artifact generator
       ↓
"verify myself"
```

At minimum:

```rust
if request.actor == artifact.generator {
    reject(SelfVerification)
}
```

But the eventual rule should be stronger than simple actor inequality.

The relevant relation is **independence of authority**, not merely different identifiers.

This should remain an explicit open design point until the verification-authority model is frozen.

## 962. Operation-specific predicates
<!-- source: RFL-TRANSITION-V01.md §16 -->

The generic state machine should not contain Linux-specific semantics.

Instead:

```rust
pub trait OperationPolicy {
    fn check(
        &self,
        state: &State,
        request: &OperationRequest,
    ) -> Result<(), RejectionReason>;
}
```

Then:

```text
generic transition engine
          │
          ├── generic authorization
          ├── generic epoch
          ├── generic scope
          └── operation policy
```

This allows:

```text
Execute
```

to have additional requirements without contaminating the core transition algebra.

## 963. Replay
<!-- source: RFL-TRANSITION-V01.md §17 -->

Replay must reconstruct state from history.

Not:

```text
stored_state
    +
    stored_events
    =
    "probably valid"
```

Instead:

```text
Genesis
   ↓
Event 1
   ↓ δ
State 1
   ↓
Event 2
   ↓ δ
State 2
   ↓
...
```

Formally:

```text
replay(E₀...Eₙ) = Sₙ
```

and:

```text
stored resulting_state == digest(replay-derived state)
```

must hold.

If they disagree:

```text
ReplayDivergence
```

## 964. Critical historical-time rule
<!-- source: RFL-TRANSITION-V01.md §18 -->

Suppose:

```text
09:00 authorization active
09:05 Execute accepted
09:10 authorization expires
```

At 09:20, historical replay must **not** reject the 09:05 event because the authorization is now expired.

Otherwise historical truth becomes dependent on present state.

Therefore replay needs historical context:

```text
Event
 ├── event timestamp
 ├── authorization snapshot/reference
 ├── epoch
 └── transition inputs
```

The principle is:

```text
current validity ≠ historical validity
```

Later revocation is represented as another event.

History is never rewritten.

## 965. Replay attack test
<!-- source: RFL-TRANSITION-V01.md §19 -->

Construct:

```text
E0: authorization active
E1: Execute accepted
E2: authorization revoked
```

Then replay all three.

Expected:

```text
E1 = valid historical transition
E2 = valid revocation transition
```

Not:

```text
E1 = invalid because authorization is currently revoked
```

This test is essential.

## 966. Transition invariants
<!-- source: RFL-TRANSITION-V01.md §20 -->

The v0.1 crate should establish at least these:

### T1 — stale epoch rejection

```text
request.epoch != state.epoch ⇒ reject
```

### T2 — unauthorized operation rejection

```text
¬AUTHORIZED(request) ⇒ reject
```

### T3 — scope monotonicity

```text
requested_scope ⊄ authorized_scope ⇒ reject
```

### T4 — invalid transition rejection

```text
(state, operation) ∉ TransitionTable ⇒ reject
```

### T5 — no state mutation on rejection

```text
apply(S,R,C) = Reject ⇒ S' = S
```

### T6 — deterministic result

```text
δ(S,R,C) = X ⇒ repeated δ(S,R,C) = X
```

### T7 — duplicate idempotency

```text
same RequestId + same RequestDigest ⇒ same historical result
```

### T8 — conflicting replay rejection

```text
same RequestId + different RequestDigest ⇒ ReplayConflict
```

### T9 — historical replay stability

```text
past valid transition
```

must remain valid when later authorization state changes.

### T10 — no certification shortcut

```text
Verified
```

cannot directly imply:

```text
Certified
```

without the gate transition.

## 967. Property-based testing
<!-- source: RFL-TRANSITION-V01.md §21 -->

This is where RFL-AE should stop relying solely on hand-written examples.

Generate arbitrary invalid requests and assert:

```text
∀ R:
    epoch mismatch
    ⇒ never Accepted
```

Likewise:

```text
∀ R:
    unauthorized scope
    ⇒ never Accepted
```

And:

```text
∀ S,R,C:
    rejected transition
    ⇒ state unchanged
```

For replay:

```text
∀ valid histories H:
    replay(H) == recorded_final_state
```

Then mutate:

```text
event digest
previous event
state digest
sequence
request digest
```

and require replay failure.

## 968. The transition crate's actual authority boundary
<!-- source: RFL-TRANSITION-V01.md §22 -->

At this point the architecture becomes very clean:

```text
             HUMAN / POLICY
                    │
                    ▼
            OperationRequest
                    │
                    ▼
        ┌───────────────────────┐
        │   rfl-transition      │
        │                       │
        │ epoch                 │
        │ authorization         │
        │ capability            │
        │ scope                 │
        │ state                 │
        │ dependencies          │
        │ transition table      │
        └───────────┬───────────┘
                    │
                Accepted
                    │
                    ▼
              EventProposal
                    │
                    ▼
               rfl-ledger
                    │
                    ▼
              authoritative
                 history
```

The executor is deliberately outside this box.

That is the trust-boundary decision that prevents RFL-AE from turning into an opaque agent runtime.

## 969. What comes immediately after
<!-- source: RFL-TRANSITION-V01.md §23 -->

Once this transition specification is frozen, the next implementation sequence should be:

```text
rfl-types
   │
   ▼
rfl-transition
   │
   ▼
rfl-ledger
   │
   ├── append
   ├── hash-chain validation
   ├── replay
   ├── fork detection
   └── tamper tests
   │
   ▼
rfl-evidence
   │
   ▼
rfl-gates
```

The **next genuinely difficult point is `rfl-ledger`**, because that is where the protocol moves from a pure transition relation to durable historical authority.

The key question there is not “how do we store events?” It is:

```text
What exactly makes a historical event authoritative, and how do we prove that replay of that history reconstructs the same protocol state without trusting the stored state itself?
```

That should be the next layer we freeze.

---

**Done — see [RFL-LEDGER-V01.md](RFL-LEDGER-V01.md)** (§970–§998, source §§1–§28 plus the
unnumbered closing section as §29 — the author restarted at §1 again, so the offset is +969),
*`rfl-ledger v0.1` — historical authority and replay*, which answers the question this document
closes on: the ledger stores history and replay derives authoritative state from it, stored state
being only a cache. It freezes the event anatomy (`Event` versus the hashed `EventCore`), event
identity versus event digest, an explicit genesis, the chain invariant, structural / semantic /
replay validation, the `Ledger` API and its atomic append protocol, replay that never trusts
`resulting_state`, historical context and replay purity, forks versus corruption, duplicate events
versus request replay, the tamper matrix, the `LedgerError` taxonomy, immutable history and
invalidation, state projection and digest, the replay-equivalence property, the adversarial suite
L01–L18, and the explicit `history → state` trust chain. Same provenance convention as
`VERIFICATION.md`.
