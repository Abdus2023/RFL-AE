# RFL-AE — `rfl-ledger`: Authoritative, Tamper-Evident History

> **Provenance and numbering.** This document was supplied untitled (the heading above is derived from its content — rename freely), numbered **§39–§61** in the source: the author continued the numbering of [RFL-TRANSITION.md](RFL-TRANSITION.md) (§19–§38), which itself continued [RFL-TYPES.md](RFL-TYPES.md) (§1–§18). It has no unnumbered sections. To keep the corpus contiguous, its sections are renumbered **§843–§865**, continuing directly from `RFL-TRANSITION.md` (which ends at §842). The mapping is the plain **`corpus_section = source_section + 804`** — the same offset as `RFL-TRANSITION.md`, because the author's numbering and the corpus numbering both continue without a gap. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: RFL-LEDGER.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/rfl-ledger/` tree, no `Ledger` trait or backend, no replay engine, no fork detection, and none of the ledger attacks L1–L9 has been written or compiled. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** The pasted source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/RFL-LEDGER.py`](diagrams/RFL-LEDGER.py); re-running it reproduces all 68 diagrams. Box-drawing art stays box-drawing and the two fork diagrams in §855 and §856 stay ASCII `/ \`; no block mixes an ASCII `|` with box glyphs. Three diagrams were normalised geometrically, with no content change: in §856 the branch labels now sit symmetrically under the fork; in §864 the `EVENT VALIDATOR` row was one column wider than its box, so all three boxes were widened by one column, which puts every spine on the same column; in §865 the labels are centred on the box's `┬`. The two LaTeX formulas in §851 and §860 are fenced as `math`. Rust types and the Rust-syntax fragments — `replace_event(old, new)` in §858 and the two `Event` shapes in §860 — are fenced as `rust`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`). Unlike every earlier paste, this one did not end with a "save it as markdown" instruction; it was saved on the same basis as the previous ones.

Next is **`rfl-ledger`**. This is where RFL-AE turns the transition engine's decisions into an authoritative, tamper-evident history.

The key design decision is:

> The ledger is not a log of what agents claim happened. It is the serialized history of protocol transitions.

---

## Contents

- [843. `rfl-ledger`](#843-rfl-ledger)
- [844. Event identity](#844-event-identity)
- [845. Canonical event](#845-canonical-event)
- [846. Chain integrity](#846-chain-integrity)
- [847. Why both are necessary](#847-why-both-are-necessary)
- [848. Ledger API](#848-ledger-api)
- [849. Persistence is not authority](#849-persistence-is-not-authority)
- [850. Replay](#850-replay)
- [851. Replay invariant](#851-replay-invariant)
- [852. Determinism requirement](#852-determinism-requirement)
- [853. Time handling](#853-time-handling)
- [854. Transition context](#854-transition-context)
- [855. Fork detection](#855-fork-detection)
- [856. Why forks matter for agent systems](#856-why-forks-matter-for-agent-systems)
- [857. Canonical branch](#857-canonical-branch)
- [858. No silent history rewriting](#858-no-silent-history-rewriting)
- [859. Correction ≠ erasure](#859-correction--erasure)
- [860. Event immutability](#860-event-immutability)
- [861. Genesis event](#861-genesis-event)
- [862. Ledger validation levels](#862-ledger-validation-levels)
- [863. Adversarial ledger suite](#863-adversarial-ledger-suite)
- [864. The ledger now has a strong security boundary](#864-the-ledger-now-has-a-strong-security-boundary)
- [865. The next major boundary: `rfl-evidence`](#865-the-next-major-boundary-rfl-evidence)

---

## 843. `rfl-ledger`
<!-- source: RFL-LEDGER.md §39 -->

```text
crates/rfl-ledger/
├── Cargo.toml
└── src/
    ├── lib.rs
    ├── ledger.rs
    ├── event.rs
    ├── digest.rs
    ├── append.rs
    ├── replay.rs
    ├── validation.rs
    ├── fork.rs
    └── tests/
        ├── append.rs
        ├── replay.rs
        ├── tamper.rs
        ├── ordering.rs
        ├── duplicate.rs
        └── fork.rs
```

Dependency:

```text
rfl-types
      │
      ▼
rfl-transition
      │
      ▼
rfl-ledger
```

`rfl-ledger` should not execute kernel commands or decide whether a gate passes.

Its responsibility is:

```text
EVENT INTEGRITY + ORDER + APPEND + REPLAY + HISTORY VALIDATION
```

## 844. Event identity
<!-- source: RFL-LEDGER.md §40 -->

The event needs two different identities.

### Logical identity

```rust
pub struct EventId(pub Uuid);
```

### Content identity

```rust
pub struct EventDigest(pub Digest);
```

They must not be conflated.

Two events can have different IDs but identical content.

Conversely, the same ID with different content is a replay conflict.

Therefore:

```text
EventId
    ≠ EventDigest
```

## 845. Canonical event
<!-- source: RFL-LEDGER.md §41 -->

The event should contain everything necessary to reconstruct the transition.

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

But there is an important question:

**What exactly is hashed?**

Never hash the serialized object including `event_digest` itself.

Define:

```text
EventCore
    ↓
canonical encoding
    ↓
Digest
    ↓
Event { ..., event_digest }
```

Conceptually:

```rust
pub struct EventCore {
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
}
```

Then:

```text
event_digest = H(canonical(EventCore))
```

## 846. Chain integrity
<!-- source: RFL-LEDGER.md §42 -->

A simple event sequence:

```text
E0
 │
 ├── sequence = 0
 ├── previous_event = None
 └── digest = D0
       │
       ▼
E1
 │
 ├── sequence = 1
 ├── previous_event = E0
 └── digest = D1
       │
       ▼
E2
 │
 ├── sequence = 2
 ├── previous_event = E1
 └── digest = D2
```

The chain invariant is:

```text
E[n].previous_event == E[n-1].id
```

and:

```text
E[n].previous_state == E[n-1].resulting_state
```

except for the genesis event.

This gives us two independent consistency relationships:

```text
history linkage + state linkage
```

## 847. Why both are necessary
<!-- source: RFL-LEDGER.md §43 -->

Imagine an attacker changes:

```text
E17.resulting_state
```

but leaves:

```text
E18.previous_event
```

unchanged.

The event chain still looks superficially connected.

But:

```text
E18.previous_state != modified(E17.resulting_state)
```

reveals the corruption.

Conversely, changing:

```text
E18.previous_event
```

is caught by the event-chain invariant.

So:

```text
event_digest + previous_event + previous_state
```

form three separate integrity checks.

## 848. Ledger API
<!-- source: RFL-LEDGER.md §44 -->

Keep the public interface small.

```rust
pub trait Ledger {
    fn append(&mut self, event: Event)
        -> Result<(), LedgerError>;

    fn get(&self, id: EventId)
        -> Option<&Event>;

    fn iter(&self)
        -> impl Iterator<Item = &Event>;

    fn head(&self)
        -> Option<&Event>;

    fn replay(&self)
        -> Result<State, ReplayError>;

    fn validate(&self)
        -> Result<(), LedgerError>;
}
```

The actual persistence backend can later be:

```text
MemoryLedger
FileLedger
GitLedger
DatabaseLedger
ContentAddressedLedger
RemoteLedger
```

without changing protocol semantics.

## 849. Persistence is not authority
<!-- source: RFL-LEDGER.md §45 -->

This distinction is important.

A database row does not become authoritative merely because it exists.

The authority chain is:

```text
Transition relation
       ↓
valid Event
       ↓
validated ledger
       ↓
replay
       ↓
authoritative state
```

A corrupted persistence backend must fail validation.

Therefore:

```text
database says Certified
```

is not enough.

The system must establish:

```text
ledger replay
    → state
    → Certified
```

## 850. Replay
<!-- source: RFL-LEDGER.md §46 -->

The replay engine should start from a known genesis state.

```rust
pub fn replay(
    events: &[Event],
    initial: State,
) -> Result<State, ReplayError>
```

For each event:

```text
1. validate event digest
2. validate sequence
3. validate previous_event
4. validate previous_state
5. validate transition
6. apply transition
7. compare resulting state
8. continue
```

The critical point is step 5.

Replay should **re-run the protocol transition semantics**, not simply trust:

```text
event.resulting_state
```

Otherwise an attacker could forge a valid-looking state digest.

## 851. Replay invariant
<!-- source: RFL-LEDGER.md §47 -->

For every valid event:

```math
Apply(S_n,E_{n+1}) = S_{n+1}
```

So:

```text
replay(E0...En)
       == authoritative_state
```

If:

```text
stored resulting_state != recomputed resulting_state
```

then:

```text
ReplayConflict
```

not "best effort recovery."

## 852. Determinism requirement
<!-- source: RFL-LEDGER.md §48 -->

Replay creates a hard requirement:

> The authoritative transition function must be deterministic.

It cannot depend on:

```text
current wall clock
randomness
LLM output
network state
filesystem discovery
environment variables
CPU timing
thread scheduling
```

unless those values are explicitly represented as transition inputs.

This gives:

```text
same State + same Request + same authoritative context
        ↓
same Result
```

This is one reason the protocol kernel must remain separate from probabilistic agents.

## 853. Time handling
<!-- source: RFL-LEDGER.md §49 -->

There are two different kinds of time.

### Protocol time

Used for authorization expiration:

```text
now >= expires_at
```

### Historical time

Recorded as evidence about when something happened.

They must not be confused.

A replay of an event from yesterday must not suddenly fail because:

```text
now > event.authorization.expires_at
```

The replay engine should evaluate the event using its **recorded transition context**, not today's wall clock.

Otherwise historical replay becomes time-dependent.

## 854. Transition context
<!-- source: RFL-LEDGER.md §50 -->

This suggests a useful object:

```rust
pub struct TransitionContext {
    pub protocol_epoch: Epoch,
    pub observed_time: Timestamp,
    pub authorization_state: AuthorizationState,
    pub dependency_state: DependencyState,
}
```

For live execution:

```text
TransitionContext
    ← current authoritative state
```

For replay:

```text
TransitionContext
    ← event-bound historical context
```

This avoids hidden inputs.

## 855. Fork detection
<!-- source: RFL-LEDGER.md §51 -->

A ledger can fork:

```text
             E10
            /   \
           /     \
         E11A   E11B
```

Both may claim:

```text
previous_event = E10
```

but they represent incompatible histories.

RFL-AE must not silently merge them.

Represent:

```rust
pub enum HistoryStatus {
    Linear,
    Forked,
    Corrupt,
}
```

A fork should produce:

```text
ForkDetected
```

and normally block certification.

## 856. Why forks matter for agent systems
<!-- source: RFL-LEDGER.md §52 -->

Suppose two agents independently authorize different implementations:

```text
Agent A: E50 → artifact A

Agent B: E50 → artifact B
```

If both are treated as one history, later evidence can accidentally become ambiguous.

Instead:

```text
                E50
              /     \
             /       \
        branch A   branch B
```

must remain explicit.

Then governance can decide which branch is canonical.

The ledger itself should not use majority voting to decide.

## 857. Canonical branch
<!-- source: RFL-LEDGER.md §53 -->

Introduce:

```rust
pub struct BranchId(pub Uuid);
```

and:

```rust
pub struct BranchHead {
    pub branch: BranchId,
    pub head: EventId,
}
```

Now:

```text
History
 ├── branch A → E73
 └── branch B → E71
```

can coexist without pretending they are one linear history.

Later, a merge operation can be introduced explicitly if the semantics justify it.

Do not add merge semantics now.

## 858. No silent history rewriting
<!-- source: RFL-LEDGER.md §54 -->

The following operation should not exist:

```rust
replace_event(old, new)
```

Instead:

```text
old event
   ↓
immutable

new event
   ↓
new history
```

If a previous decision was wrong:

```text
E31
 ↓
CorrectionRequested
 ↓
E32
```

The history records the correction.

It does not rewrite E31.

This is essential for AI-generated engineering, where mistakes and revisions are expected.

## 859. Correction ≠ erasure
<!-- source: RFL-LEDGER.md §55 -->

Introduce a future event family:

```text
Correction
Invalidation
Supersession
Revocation
```

For example:

```text
E20: VerificationPassed
E21: EvidenceInvalidated
E22: VerificationInvalidated
```

The historical fact:

```text
"E20 happened"
```

remains true.

The derived fact:

```text
"artifact is currently verified"
```

becomes false.

This is exactly the distinction between:

```text
history
```

and:

```text
current canonical state
```

## 860. Event immutability
<!-- source: RFL-LEDGER.md §56 -->

A useful invariant:

```math
EventDigest(E) = H(Core(E))
```

Therefore:

```text
modify Core(E)
     ↓
Digest(E) changes
     ↓
chain validation fails
```

The implementation should make mutation difficult at the type level.

For example, expose:

```rust
pub struct Event(EventCore);
```

with private fields, and require construction through validated constructors.

Avoid:

```rust
pub struct Event {
    pub everything: ...
}
```

where arbitrary callers can construct malformed events.

## 861. Genesis event
<!-- source: RFL-LEDGER.md §57 -->

A ledger needs an explicit genesis.

```rust
pub struct Genesis {
    pub protocol: Digest,
    pub epoch: Epoch,
    pub initial_state: Digest,
}
```

Then:

```text
Genesis
   ↓
E0
   ↓
E1
   ↓
...
```

Genesis itself should be immutable.

The genesis digest establishes the root of the history.

## 862. Ledger validation levels
<!-- source: RFL-LEDGER.md §58 -->

We should distinguish:

```text
STRUCTURAL_VALID
```

from:

```text
SEMANTIC_VALID
```

and:

```text
REPLAY_VALID
```

For example:

```text
Structural:
    hashes correct
    sequence correct
    links correct

Semantic:
    transitions allowed

Replay:
    reconstructed state matches
```

A ledger can therefore report:

```text
Structural = PASS
Semantic    = FAIL
Replay      = BLOCKED
```

rather than collapsing everything into `invalid`.

## 863. Adversarial ledger suite
<!-- source: RFL-LEDGER.md §59 -->

Now expand the earlier 18 tests with ledger-specific attacks.

### L1 — Modify event content

```text
E7.operation:
    Execute → Verify
```

Expected:

```text
DigestMismatch
```

### L2 — Modify resulting state

Expected:

```text
StateChainMismatch
```

### L3 — Modify previous event

Expected:

```text
HistoryLinkMismatch
```

### L4 — Reorder events

```text
E7, E8, E6
```

Expected:

```text
SequenceViolation
```

### L5 — Duplicate event

Expected:

```text
DuplicateEvent
```

### L6 — Duplicate request with different digest

Expected:

```text
ReplayConflict
```

### L7 — Fork

```text
E10 → E11A
E10 → E11B
```

Expected:

```text
ForkDetected
```

### L8 — Forge resulting state

An attacker constructs a syntactically valid event whose state digest claims:

```text
Certified
```

without performing transitions.

Expected:

```text
ReplayConflict
```

### L9 — Historical expiration trap

Replay an event whose authorization expired **after the event occurred**.

Expected:

```text
Replay succeeds
```

This is a particularly important positive test.

## 864. The ledger now has a strong security boundary
<!-- source: RFL-LEDGER.md §60 -->

```text
             REQUEST
                │
                ▼
       ┌─────────────────┐
       │ TRANSITION      │
       │ ENGINE          │
       └────────┬────────┘
                │
         accepted event
                │
                ▼
       ┌─────────────────┐
       │ EVENT VALIDATOR │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │ APPEND-ONLY     │
       │ LEDGER          │
       └────────┬────────┘
                │
                ▼
          REPLAY ENGINE
                │
                ▼
       RECONSTRUCTED STATE
```

This gives us a much stronger property than ordinary agent traces:

```text
trace
    = narrative

ledger
    = executable history
```

## 865. The next major boundary: `rfl-evidence`
<!-- source: RFL-LEDGER.md §61 -->

With transitions and history established, the next problem is:

> How do we establish facts about the outside world without allowing those facts to become self-authenticating?

That is `rfl-evidence`.

The pipeline becomes:

```text
               PROTOCOL
                   │
                   ▼
           OperationRequest
                   │
                   ▼
              Transition
                   │
                   ▼
                 Event
                   │
                   ▼
               Execution
                   │
                   ▼
         External observation
                   │
                   ▼
          ┌─────────────────┐
          │ rfl-evidence    │
          │                 │
          │ artifact        │
          │ input           │
          │ command         │
          │ environment     │
          │ toolchain       │
          │ output          │
          │ outcome         │
          └────────┬────────┘
                   │
                   ▼
             Verification
                   │
                   ▼
                 Gates
```

The crucial next distinction will be:

```text
OBSERVATION
     ≠ EVIDENCE RECORD
     ≠ VERIFICATION
     ≠ CERTIFICATION
```

`rfl-evidence` should therefore be designed around **binding evidence to exact artifacts, exact inputs, exact execution, exact environment, and exact epoch**, rather than around a generic `passed: bool`.

That is the next layer to formalize.

---

**Done — see [RFL-EVIDENCE.md](RFL-EVIDENCE.md)** (§866–§893, source §§62–§89, continuing this
document's own numbering), which specifies **`rfl-evidence`**, the most important external trust
boundary — the ledger records what RFL-AE authorized; evidence establishes what an external
execution system actually observed: immutable artifact identity and provenance; typed execution
requests; execution observations that deliberately carry no `verified = true`; evidence records
bound to epoch, task, artifact, execution, command, inputs, outputs, environment and toolchain;
**Failed ≠ Blocked**; the forged-artifact, stale-evidence and self-generated-evidence attacks;
configuration and architecture scope; evidence completeness (missing evidence gives `BLOCKED`,
not `FAILED`); evidence invalidation without rewriting history; the theorem that execution
success does not imply certification; and `rfl-gates` as the next step. Same provenance
convention as `VERIFICATION.md`.
