# `rfl-ledger v0.1` — historical authority and replay

> **Provenance and numbering.** This document was supplied as *`rfl-ledger v0.1` — historical authority and replay* (the heading above is the source's own), numbered **§1–§28** in the source, preceded by an unnumbered introduction that is kept as the preamble below and followed by an unnumbered closing section, *Next: `rfl-evidence v0.1`*. Like [RFL-TRANSITION-V01.md](RFL-TRANSITION-V01.md), it restarts the author's numbering at §1. To keep the corpus contiguous, its sections are renumbered **§970–§998**, continuing directly from `RFL-TRANSITION-V01.md` (which ends at §969). The mapping is **`corpus_section = source_section + 969`**, with the unnumbered closing section recorded as source **§29** — the convention already used by `RFL-TYPES-V01.md`, `RFL-GATES.md` and earlier documents. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: RFL-LEDGER-V01.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause. The file is named `RFL-LEDGER-V01.md` because [RFL-LEDGER.md](RFL-LEDGER.md) (§843–§865) already exists; this document freezes that crate's v0.1 semantics.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/rfl-ledger/` source, ledger implementation, replay engine, state projection or test — including the adversarial suite L01–L18 of §994 — has been written or compiled. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** The paste arrived wrapped in a code fence; the fence was treated as transport, not content. The source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/RFL-LEDGER-V01.py`](diagrams/RFL-LEDGER-V01.py); re-running it reproduces all 79 diagrams. One diagram was normalised geometrically, with no content change: in the §995 trust chain, `immutable history` started one column right of the spine that every arrow and both boxes' `┬` sit on, and is now centred on it. **One omission:** the §979 invariant began `id="x1" append(E) = Err ⇒ …` in the source; `id="x1"` is a leaked code-fence attribute, not content, and was dropped — restore it if it was intended. The source mixed heading levels (`## 1.` then `# 2.` onwards, and `## Next:` for the closing section); all numbered sections are `##` here, and the source's `###` sub-headings in §976, §984 and §985 stay `###`. Word lists and stacked lines that arrived with single spaces only were broken into one item per line (§970, §973, §975, §976, §982, §984, §985, §986, §990, §991, §994, §996). Two runs were kept on one line and could instead be split: `H' ≠ H AND Replay(H') fails` (§994) and the one-sentence conclusion in §996. In §974 and §976 the label after a `↓` (`previous_event`, `E0`, `E1`) stays on its arrow line. The standalone questions in the preamble and §992 are rendered as blockquotes. The §987 tamper matrix and the §997 layer table are rendered as markdown tables. Rust declarations and the incorrect `replay()` of §980 are fenced as `rust`; comparisons and assignments such as `sequence == 0` (§973) stay `text`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The ledger is the next critical boundary because it turns accepted transitions into **auditable protocol history**.

The central rule:

> The ledger stores history; replay derives authoritative state from history. Stored state is a cache, not the source of truth.

---

## Contents

- [970. Crate contract](#970-crate-contract)
- [971. Event anatomy](#971-event-anatomy)
- [972. Event identity versus event digest](#972-event-identity-versus-event-digest)
- [973. Genesis](#973-genesis)
- [974. Chain invariant](#974-chain-invariant)
- [975. Why a hash chain alone is insufficient](#975-why-a-hash-chain-alone-is-insufficient)
- [976. Three validation levels](#976-three-validation-levels)
- [977. Ledger API](#977-ledger-api)
- [978. Append protocol](#978-append-protocol)
- [979. Append atomicity](#979-append-atomicity)
- [980. Replay is not `resulting_state`](#980-replay-is-not-resulting_state)
- [981. Replay uses historical context](#981-replay-uses-historical-context)
- [982. Replay purity](#982-replay-purity)
- [983. Forks](#983-forks)
- [984. Fork ≠ corruption](#984-fork--corruption)
- [985. Duplicate events](#985-duplicate-events)
- [986. Request replay](#986-request-replay)
- [987. Tamper matrix](#987-tamper-matrix)
- [988. Ledger errors](#988-ledger-errors)
- [989. Immutable history](#989-immutable-history)
- [990. Invalidation](#990-invalidation)
- [991. State digest](#991-state-digest)
- [992. State projection](#992-state-projection)
- [993. Replay equivalence property](#993-replay-equivalence-property)
- [994. The adversarial suite](#994-the-adversarial-suite)
- [995. The trust chain is now explicit](#995-the-trust-chain-is-now-explicit)
- [996. What `rfl-ledger` still does NOT prove](#996-what-rfl-ledger-still-does-not-prove)
- [997. Resulting architecture](#997-resulting-architecture)
- [998. Next: `rfl-evidence v0.1`](#998-next-rfl-evidence-v01)

---

## 970. Crate contract
<!-- source: RFL-LEDGER-V01.md §1 -->

```text
crates/rfl-ledger/
├── Cargo.toml
└── src/
    ├── lib.rs
    ├── event.rs
    ├── event_core.rs
    ├── ledger.rs
    ├── append.rs
    ├── validation.rs
    ├── replay.rs
    ├── digest.rs
    ├── fork.rs
    └── tests/
        ├── genesis.rs
        ├── append.rs
        ├── ordering.rs
        ├── tamper.rs
        ├── replay.rs
        ├── duplicate.rs
        ├── fork.rs
        └── adversarial.rs
```

Dependency direction:

```text
rfl-ledger
    ├── rfl-types
    └── rfl-transition
```

It must not depend on:

```text
rfl-evidence
rfl-gates
KSIR
Rust-generation logic
LLM infrastructure
```

---

## 971. Event anatomy
<!-- source: RFL-LEDGER-V01.md §2 -->

Separate the event's semantic content from its digest.

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

But `event_digest` must **not** be included in the material being hashed.

Therefore:

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
EventDigest
    = SHA256(
    CanonicalEncode(EventCore)
)
```

This prevents recursive hashing.

---

## 972. Event identity versus event digest
<!-- source: RFL-LEDGER-V01.md §3 -->

Do not collapse:

```text
EventId
```

and:

```text
EventDigest
```

They answer different questions.

```text
EventId
    = identity/reference

EventDigest
    = content integrity
```

Thus:

```text
same EventId + different EventCore
```

is detectable.

Likewise:

```text
different EventId + same EventCore
```

is technically possible unless the protocol explicitly prohibits duplicate semantic events.

That decision belongs to duplicate-event policy, not cryptographic identity.

---

## 973. Genesis
<!-- source: RFL-LEDGER-V01.md §4 -->

The ledger must have an explicit genesis event/state.

Do not infer genesis from:

```text
sequence == 0
```

alone.

Define:

```rust
pub struct Genesis {
    pub event: Event,
    pub initial_state: Digest,
}
```

Genesis invariants:

```text
sequence = 0
previous_event = None
previous_state = initial_state
```

and:

```text
genesis is immutable
```

A ledger with no explicit genesis is not replay-complete.

---

## 974. Chain invariant
<!-- source: RFL-LEDGER-V01.md §5 -->

For every event after genesis:

```text
E[n].sequence = E[n-1].sequence + 1
```

and:

```text
E[n].previous_event = E[n-1].id
```

and:

```text
E[n].previous_state = E[n-1].resulting_state
```

Therefore:

```text
E0
 ↓ previous_event
E1
 ↓
E2
 ↓
E3
```

A modification to any link must become observable.

---

## 975. Why a hash chain alone is insufficient
<!-- source: RFL-LEDGER-V01.md §6 -->

Consider:

```text
E0 → E1 → E2
```

An attacker modifies `E1`.

The chain detects that:

```text
E2.previous_state
```

may no longer match.

But there are actually **three independent integrity questions**:

```text
1. Is the event content intact?
2. Is the event connected to the expected predecessor?
3. Does replay of the event produce the claimed resulting state?
```

Therefore RFL-AE needs three validation layers.

---

## 976. Three validation levels
<!-- source: RFL-LEDGER-V01.md §7 -->

```text
STRUCTURAL_VALID
        ↓
SEMANTIC_VALID
        ↓
REPLAY_VALID
```

### Structural

Checks:

```text
digest
sequence
previous_event
field presence
epoch consistency
```

### Semantic

Checks:

```text
operation legal
actor/task relation
transition legal
authorization relation
```

### Replay

Actually reconstruct:

```text
S0
 ↓ E0
S1
 ↓ E1
S2
```

and compare the derived state with the claimed state.

Only replay validation establishes:

```text
history ⇒ state
```

rather than merely:

```text
history appears internally consistent
```

---

## 977. Ledger API
<!-- source: RFL-LEDGER-V01.md §8 -->

The minimal API:

```rust
pub trait Ledger {
    fn append(&mut self, event: Event) -> Result<(), LedgerError>;

    fn get(&self, id: EventId) -> Option<&Event>;

    fn head(&self) -> Option<&Event>;

    fn iter(&self) -> impl Iterator<Item = &Event>;

    fn validate(&self) -> Result<(), LedgerError>;

    fn replay(&self) -> Result<State, ReplayError>;
}
```

But one important restriction:

`append()` must never simply push into a vector.

It must validate the event against the current head.

---

## 978. Append protocol
<!-- source: RFL-LEDGER-V01.md §9 -->

For a non-genesis event:

```text
candidate
    ↓
validate EventCore digest
    ↓
validate sequence
    ↓
validate previous_event
    ↓
validate previous_state
    ↓
validate epoch
    ↓
validate semantic transition
    ↓
append
```

Any failure:

```text
append(candidate) = Err(...)
```

and:

```text
ledger remains unchanged
```

This gives the ledger atomicity at the logical level.

---

## 979. Append atomicity
<!-- source: RFL-LEDGER-V01.md §10 -->

This is a mandatory invariant:

```text
append(E) = Err ⇒ LedgerAfter == LedgerBefore
```

No partial append.

No:

```text
event inserted then validation failed
```

No mutation before validation completes.

---

## 980. Replay is not `resulting_state`
<!-- source: RFL-LEDGER-V01.md §11 -->

This is probably the most important ledger rule.

Incorrect:

```rust
fn replay(&self) -> State {
    self.head().unwrap().resulting_state
}
```

That merely trusts the event.

Correct conceptually:

```text
initial state
    ↓
apply E0
    ↓
derived state 1
    ↓
apply E1
    ↓
derived state 2
    ↓
...
```

At each step:

```text
digest(derived_state)
        == event.resulting_state
```

If not:

```text
ReplayDivergence
```

---

## 981. Replay uses historical context
<!-- source: RFL-LEDGER-V01.md §12 -->

The replay engine must not consult current mutable authority.

Bad:

```text
replay()
   ↓
current authorization database
```

because current authorization state can differ from historical state.

Instead the event/history must provide the inputs required for historical reconstruction.

Conceptually:

```rust
pub struct HistoricalTransitionContext {
    pub event_time: Timestamp,
    pub authorization_snapshot: AuthorizationSnapshot,
    pub dependency_snapshot: DependencySnapshot,
}
```

The exact serialization of these snapshots can be refined, but the principle is fixed:

```text
replay(H) must depend only on H + immutable protocol rules
```

not on current external state.

---

## 982. Replay purity
<!-- source: RFL-LEDGER-V01.md §13 -->

For a fixed history `H`:

```text
Replay(H)
```

must not depend on:

```text
current_time
randomness
network
filesystem
LLM output
environment variables
current authorization
current Git branch
current CI state
```

Therefore:

```text
Replay(H) = deterministic function
```

This is what makes historical verification meaningful.

---

## 983. Forks
<!-- source: RFL-LEDGER-V01.md §14 -->

A linear ledger:

```text
E0 → E1 → E2 → E3
```

A fork:

```text
          E2a
         /
E0 → E1
         \
          E2b
```

Do not silently choose one.

Represent:

```rust
pub enum HistoryStatus {
    Linear,
    Forked,
    Corrupt,
}
```

And:

```rust
pub struct Branch {
    pub id: BranchId,
    pub head: EventId,
}
```

For v0.1, the safest rule is:

```text
fork detected → ledger not certifiable
```

No automatic merge.

---

## 984. Fork ≠ corruption
<!-- source: RFL-LEDGER-V01.md §15 -->

These must remain distinct.

### Fork

Two internally valid successors exist:

```text
E1 → E2a
E1 → E2b
```

This may be legitimate branching.

### Corruption

An event violates integrity:

```text
E2.previous_event != E1.id
```

or:

```text
digest(E2.core) != E2.event_digest
```

or:

```text
replay(E2) != E2.resulting_state
```

Therefore:

```text
Forked ≠ Corrupt
```

But both should prevent a linear certification path unless an explicit branch-selection policy exists.

---

## 985. Duplicate events
<!-- source: RFL-LEDGER-V01.md §16 -->

There are several different duplicate cases.

### Exact duplicate

```text
same EventId
same EventCore
same digest
```

This should be idempotently recognized where appropriate.

### Same ID, changed content

```text
same EventId
different EventCore
```

→ integrity failure.

### Different ID, same semantic operation

Potentially valid or potentially duplicate depending on protocol semantics.

Do not automatically equate:

```text
same operation
```

with:

```text
same event
```

because two legitimate attempts can perform the same operation.

---

## 986. Request replay
<!-- source: RFL-LEDGER-V01.md §17 -->

This is different from event duplication.

Suppose:

```text
Request R1
```

is submitted twice.

If the digest is identical:

```text
R1 + digest(D)
R1 + digest(D)
```

the second submission should return the historical result.

But:

```text
R1 + digest(D1)
R1 + digest(D2)
```

must produce:

```text
ReplayConflict
```

This prevents request identity from becoming mutable.

---

## 987. Tamper matrix
<!-- source: RFL-LEDGER-V01.md §18 -->

The ledger's adversarial tests should deliberately modify one field at a time.

| Mutation | Expected result |
|---|---|
| event content | `DigestMismatch` |
| event digest | `DigestMismatch` |
| sequence | `SequenceViolation` |
| previous event | `HistoryLinkMismatch` |
| previous state | `StateChainMismatch` |
| resulting state | `ReplayDivergence` |
| event order | `SequenceViolation` |
| duplicate event | `DuplicateEvent` |
| conflicting request | `ReplayConflict` |
| two successors | `ForkDetected` |

This is much stronger than merely testing that “tampering fails.”

---

## 988. Ledger errors
<!-- source: RFL-LEDGER-V01.md §19 -->

Freeze a dedicated taxonomy:

```rust
pub enum LedgerError {
    GenesisMissing,
    GenesisInvalid,

    DigestMismatch,

    SequenceViolation,
    HistoryLinkMismatch,
    StateChainMismatch,

    DuplicateEvent,
    ReplayConflict,

    EpochMismatch,

    SemanticViolation,

    ForkDetected,
    CorruptHistory,

    ReplayDivergence,
}
```

Replay errors can remain separate if useful:

```rust
pub enum ReplayError {
    InvalidHistory(LedgerError),
    UnknownTransition,
    MissingHistoricalContext,
    StateMismatch,
}
```

Do not turn every failure into:

```text
InvalidLedger
```

because diagnosis is part of the evidence architecture.

---

## 989. Immutable history
<!-- source: RFL-LEDGER-V01.md §20 -->

Corrections must never modify an old event.

Suppose:

```text
E17
```

contains a mistaken claim.

Do not:

```text
edit E17
```

Instead:

```text
E17
 ↓
E18 = Correction / Invalidation / Supersession
```

Thus:

```text
history = what happened
```

while:

```text
current state = what is currently authoritative
```

This preserves both.

---

## 990. Invalidation
<!-- source: RFL-LEDGER-V01.md §21 -->

A particularly important case:

```text
E50 → evidence accepted
E51 → later evidence invalidated
```

Do not rewrite E50.

Record:

```text
E51 = Invalidate(E50)
```

Replay therefore reconstructs:

```text
historically:
    E50 existed and was accepted

currently:
    E50 is invalidated
```

That distinction will later become essential for `rfl-evidence` and `rfl-gates`.

---

## 991. State digest
<!-- source: RFL-LEDGER-V01.md §22 -->

The ledger should never hash an arbitrary Rust debug representation.

Define:

```text
StateDigest
    = SHA256(
    CanonicalEncode(StateProjection)
)
```

where `StateProjection` contains only authoritative protocol state.

Do not accidentally include:

```text
HashMap iteration order
memory addresses
timestamps not semantically relevant
debug metadata
filesystem paths
process IDs
```

Canonical state encoding is therefore another release-gate requirement.

---

## 992. State projection
<!-- source: RFL-LEDGER-V01.md §23 -->

A useful separation is:

```text
Full runtime state
        │
        ▼
Authoritative State Projection
        │
        ▼
Canonical encoding
        │
        ▼
StateDigest
```

The projection answers:

> Which facts determine protocol state?

Not:

> What happens to be stored in the implementation?

This avoids implementation details becoming accidental protocol semantics.

---

## 993. Replay equivalence property
<!-- source: RFL-LEDGER-V01.md §24 -->

The strongest v0.1 ledger property:

```text
Given valid history H:

append(H)
       ↓
replay(H)
       ↓
S

and every event Ei contains digest(Si)
```

Then:

```text
digest(Si) == Ei.resulting_state
```

for every event.

Therefore a forged `resulting_state` cannot survive replay.

---

## 994. The adversarial suite
<!-- source: RFL-LEDGER-V01.md §25 -->

The minimum ledger suite should contain:

```text
L01 valid genesis
L02 invalid genesis
L03 valid append
L04 invalid digest
L05 sequence gap
L06 sequence rewind
L07 previous-event corruption
L08 previous-state corruption
L09 resulting-state forgery
L10 reordered history
L11 duplicate event
L12 conflicting request
L13 fork
L14 replay divergence
L15 historical authorization expiration
L16 historical authorization revocation
L17 invalidation event
L18 failed append atomicity
```

And one particularly important metamorphic test:

```text
Take valid H.
Mutate exactly one byte of EventCore.
Replay(H').
```

Expected:

```text
H' ≠ H AND Replay(H') fails
```

---

## 995. The trust chain is now explicit
<!-- source: RFL-LEDGER-V01.md §26 -->

After `rfl-transition` + `rfl-ledger`:

```text
                   AGENT
                     │
                     │ OperationRequest
                     ▼
             ┌───────────────┐
             │ rfl-transition│
             └───────┬───────┘
                     │
               EventProposal
                     │
                     ▼
             ┌───────────────┐
             │   rfl-ledger  │
             └───────┬───────┘
                     │
             immutable history
                     │
                     ▼
                  replay
                     │
                     ▼
            reconstructed State
```

The important direction is:

```text
history → state
```

not:

```text
state → history
```

That is the difference between an auditable protocol and a database with an audit log.

---

## 996. What `rfl-ledger` still does NOT prove
<!-- source: RFL-LEDGER-V01.md §27 -->

A valid ledger does not prove:

```text
the C semantics were correctly reconstructed
the Rust implementation is correct
a test was sufficient
the evidence is relevant
a contract is satisfied
the gate predicate is appropriate
Linux upstream will accept the patch
```

It proves something narrower and valuable:

```text
the protocol history is structurally and semantically coherent, and deterministic replay reconstructs the claimed protocol state.
```

That boundary must remain narrow.

---

## 997. Resulting architecture
<!-- source: RFL-LEDGER-V01.md §28 -->

We now have three distinct authority layers:

```text
rfl-types
    │
    │ vocabulary + canonical identities
    ▼
rfl-transition
    │
    │ admissibility
    ▼
rfl-ledger
    │
    │ historical authority
    ▼
rfl-evidence
    │
    │ execution observation
    ▼
rfl-gates
    │
    │ certification decision
    ▼
certificate
```

Each layer answers a different question:

| Layer | Question |
|---|---|
| `rfl-types` | What does the protocol mean by this object? |
| `rfl-transition` | Is this requested state transition permitted? |
| `rfl-ledger` | What actually belongs to authoritative protocol history? |
| `rfl-evidence` | What was actually observed during execution? |
| `rfl-gates` | Are the certification requirements satisfied? |

That separation is now strong enough to support the next layer.

---

## 998. Next: `rfl-evidence v0.1`
<!-- source: RFL-LEDGER-V01.md §29 -->

The difficult problem there is to prevent the classic chain:

```text
command exited 0
        ↓
"test passed"
        ↓
"artifact verified"
        ↓
"contract satisfied"
```

from becoming an implicit assumption.

Instead we will formalize:

```text
Artifact
   ↓
ExecutionRequest
   ↓
ExecutionObservation
   ↓
EvidenceRecord
   ↓
EvidenceValidity
   ↓
ContractSatisfaction
```

with explicit binding of **artifact digest, input digest, command digest, executor, environment, toolchain, configuration, architecture, and output artifacts**.
