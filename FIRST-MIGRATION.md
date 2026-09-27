# RFL-AE — First End-to-End Migration Unit

> **Provenance and numbering.** This document was supplied as *RFL-AE — First End-to-End Migration Unit*, numbered §1–§29 in the source plus a final unnumbered *Frozen next milestone* clause. To keep the corpus contiguous, its sections are renumbered **§611–§640**, continuing directly from [PROTOCOL-P58.md](PROTOCOL-P58.md) (which ends at §610). The mapping is **`corpus_section = source_section + 610`**, with the unnumbered closing clause recorded as source §30 — the same convention `PROTOCOL-KERNEL.md` uses for its unnumbered *Next artifact*. The original source numbering is preserved on every heading as a machine-readable HTML comment of the form `<!-- source: FIRST-MIGRATION.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `fixtures/lab001/` tree, no C fixture, no Rust crate, and no test has been written. MU-000001 is described here as the target of the first vertical slice, not as something that exists. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** In the pasted source every ASCII diagram arrived collapsed onto a single line. Those diagrams were therefore *redrawn* rather than copied, with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector and off-centre checks — they were not hand-typed. The generator is committed at [`diagrams/FIRST-MIGRATION.py`](diagrams/FIRST-MIGRATION.py); re-running it reproduces all 65 diagrams, so the redraw can be checked rather than trusted. Two further normalisations: the source's design block mixed a C name and an arrow with a Rust struct, and since no `rust` block anywhere in the corpus contains an arrow, it is split into a `text` arrow and a pure `rust` struct; and where a collapsed record's line layout was ambiguous, it was rendered in the aligned form its identifier widths imply. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The architecture is now mature enough to build the first **closed-loop migration unit**.

The goal is not yet to migrate a meaningful Linux subsystem. The goal is to prove that RFL-AE can take **one bounded C unit through the entire authority/evidence pipeline** without bypassing its own protocol.

---

## Contents

- [611. Freeze the vertical slice](#611-freeze-the-vertical-slice)
- [612. Lab fixture](#612-lab-fixture)
- [613. Example semantic fixture](#613-example-semantic-fixture)
- [614. KSIR expected facts](#614-ksir-expected-facts)
- [615. Expected unknowns](#615-expected-unknowns)
- [616. Contract compiler](#616-contract-compiler)
- [617. Contract](#617-contract)
- [618. Contract graph](#618-contract-graph)
- [619. Rust Design IR](#619-rust-design-ir)
- [620. Ownership mapping](#620-ownership-mapping)
- [621. Lock mapping](#621-lock-mapping)
- [622. Callback mapping](#622-callback-mapping)
- [623. Unsafe obligations](#623-unsafe-obligations)
- [624. Verification IR generation](#624-verification-ir-generation)
- [625. Test generation](#625-test-generation)
- [626. Negative corpus](#626-negative-corpus)
- [627. Execution](#627-execution)
- [628. Evidence](#628-evidence)
- [629. Verification](#629-verification)
- [630. Gate](#630-gate)
- [631. Independent verification](#631-independent-verification)
- [632. Deliberate protocol attack](#632-deliberate-protocol-attack)
- [633. Migration certificate](#633-migration-certificate)
- [634. Certificate invariant](#634-certificate-invariant)
- [635. MU-000001 manifest](#635-mu-000001-manifest)
- [636. End-to-end state machine](#636-end-to-end-state-machine)
- [637. Why this is the real milestone](#637-why-this-is-the-real-milestone)
- [638. The first real success criterion](#638-the-first-real-success-criterion)
- [639. Then scale](#639-then-scale)
- [640. Frozen next milestone](#640-frozen-next-milestone)

---

## 611. Freeze the vertical slice
<!-- source: FIRST-MIGRATION.md §1 -->

Define:

```text
RFL-AE-LAB-001
MU-000001
```

Scope:

```text
C source
├── one object type
├── one allocation path
├── one initialization path
├── one refcount/lifetime rule
├── one synchronized mutation
├── one callback
├── one destruction path
└── one C/Rust boundary
```

Do **not** start with:

```text
RCU + workqueues + IRQ + DMA + VFS
```

in the same unit.

The lab needs enough semantic difficulty to exercise the architecture, but not enough complexity to make failures ambiguous.

---

## 612. Lab fixture
<!-- source: FIRST-MIGRATION.md §2 -->

Create a deliberately small kernel-like C fixture.

```text
fixtures/lab001/
├── include/
│   └── lab_object.h
├── c/
│   └── lab_object.c
├── rust/
│   └── lib.rs
├── tests/
│   ├── lifecycle.c
│   └── differential.rs
└── expected/
    ├── ksir.json
    ├── contract.json
    └── obligations.json
```

The C fixture should contain:

```text
allocation
    ↓
initialization
    ↓
publication
    ↓
get()
    ↓
callback registration
    ↓
mutation under lock
    ↓
callback
    ↓
put()
    ↓
destruction
```

The deliberately important part is that **the ownership relationship should not be obvious from syntax alone**.

---

## 613. Example semantic fixture
<!-- source: FIRST-MIGRATION.md §3 -->

Conceptually:

```c
struct lab_object {
    refcount_t refs;
    spinlock_t lock;
    int value;
    struct work_struct work;
};

struct lab_object *lab_get(struct lab_object *obj) {
    refcount_inc(&obj->refs);
    return obj;
}

void lab_put(struct lab_object *obj) {
    if (refcount_dec_and_test(&obj->refs))
        kfree(obj);
}

void lab_update(struct lab_object *obj, int value) {
    spin_lock(&obj->lock);
    obj->value = value;
    spin_unlock(&obj->lock);
}
```

And:

```c
void lab_schedule(struct lab_object *obj) {
    lab_get(obj);
    schedule_work(&obj->work);
}
```

with callback:

```c
void lab_work(struct work_struct *work) {
    struct lab_object *obj =
        container_of(work, struct lab_object, work);

    lab_update(obj, 42);
    lab_put(obj);
}
```

This tiny fixture already forces RFL-AE to reconstruct:

```text
refcount
ownership
callback lifetime
container_of
intrusive embedding
workqueue context
locking
destruction
```

That is sufficient for Lab 001.

---

## 614. KSIR expected facts
<!-- source: FIRST-MIGRATION.md §4 -->

The analyzer should produce semantic facts such as:

```text
OBJ-001      type = lab_object
OWN-001      refs protects object lifetime
OWN-002      lab_get acquires reference
OWN-003      lab_put releases reference
OWN-004      zero reference permits destruction
LOCK-001     lock protects value
CTX-001      lab_work executes in deferred process context
CALL-001     schedule_work → lab_work
LIFE-001     callback requires object to remain alive
INTR-001     work_struct embedded in lab_object
ABI-001      C callback receives work_struct-compatible pointer
```

But importantly:

```text
KSIR fact
    ≠
contract
```

KSIR describes what the analyzer reconstructed.

---

## 615. Expected unknowns
<!-- source: FIRST-MIGRATION.md §5 -->

The fixture should also deliberately produce at least one controlled unknown.

For example:

```text
UNKNOWN-001     exact architecture-independent layout
```

or:

```text
UNKNOWN-002     indirect callback reachability
```

depending on which analyzer capabilities are enabled.

The purpose is to prove:

```text
unsupported analysis
        ↓
UNKNOWN
```

rather than:

```text
unsupported analysis
        ↓
assumed safe
```

---

## 616. Contract compiler
<!-- source: FIRST-MIGRATION.md §6 -->

From KSIR:

```text
KSIR
 │
 ▼
Contract compiler
 │
 ├── ownership
 ├── lifetime
 ├── locking
 ├── context
 ├── callback
 ├── ABI
 └── destruction
```

produces:

```text
contract/MU-000001/
├── contract.json
├── invariants.json
├── temporal.json
├── unknowns.json
└── conflicts.json
```

---

## 617. Contract
<!-- source: FIRST-MIGRATION.md §7 -->

Example normalized contract:

```text
C-001
Subject:
    lab_object
Precondition:
    object initialized
Invariant:
    refs > 0 while object is accessible
Postcondition:
    lab_get increments refs
Invariant:
    value mutation occurs while lock held
Temporal:
    callback object remains valid until callback completion
Postcondition:
    final reference release permits destruction
Context:
    lab_work may execute in deferred process context
```

Each statement gets an evidence reference.

No free-floating prose contract.

---

## 618. Contract graph
<!-- source: FIRST-MIGRATION.md §8 -->

The important relationship is:

```text
                  lab_object
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
     lifetime        value       callback
         │             │             │
         ▼             ▼             ▼
     refcount        lock        workqueue
         │             │             │
         └─────────────┼─────────────┘
                       ▼
                  invariants
```

This graph becomes the source for Rust design obligations.

---

## 619. Rust Design IR
<!-- source: FIRST-MIGRATION.md §9 -->

Now produce a design.

Not code.

```text
Contract
    ↓
Rust Design IR
```

Possible design:

```text
lab_object
    ↓
```

```rust
struct LabObject {
    refs: RefCount,
    lock: SpinLock<State>,
    work: WorkItem<Self>,
}
```

But the design compiler must justify each mapping.

---

## 620. Ownership mapping
<!-- source: FIRST-MIGRATION.md §10 -->

```text
C refcount
    ↓
Rust ownership model
lab_get()
    ↓
acquire reference
lab_put()
    ↓
release reference
zero
    ↓
destruction
```

The critical question:

> What Rust mechanism guarantees that the object remains alive while the deferred callback executes?

That cannot be answered merely by writing:

```text
Arc<LabObject>
```

because the semantics of the kernel refcount and callback lifetime must first be characterized.

The design must prove the mapping.

---

## 621. Lock mapping
<!-- source: FIRST-MIGRATION.md §11 -->

C:

```text
spin_lock
    ↓
mutation
    ↓
spin_unlock
```

Rust candidate:

```text
SpinLock<State>
```

Design obligations:

```text
D-LOCK-001 all mutable accesses represented
D-LOCK-002 no bypass path
D-LOCK-003 locking semantics preserve source behavior
D-LOCK-004 callback context permits primitive
D-LOCK-005 IRQ/preemption semantics preserved
```

If any of those remain unknown:

```text
DESIGN ≠ AUTHORIZED_FOR_IMPLEMENTATION
```

---

## 622. Callback mapping
<!-- source: FIRST-MIGRATION.md §12 -->

This is where the lab becomes useful.

The design must establish:

```text
registration
    ↓
callback reachability
    ↓
object lifetime
    ↓
cancellation/quiescence
    ↓
final release
```

A callback is not merely:

```text
fn callback()
```

It is a temporal contract.

---

## 623. Unsafe obligations
<!-- source: FIRST-MIGRATION.md §13 -->

The design compiler should produce something like:

```text
UO-001 C pointer → Rust reference
Required:
    pointer valid
    aligned
    initialized
    object alive
    correct provenance

UO-002 container_of equivalent
Required:
    embedded field belongs to containing object
    offset/layout exact
    address remains stable

UO-003 FFI callback
Required:
    ABI compatible
    calling convention compatible
    lifetime valid
    context valid
```

These are not comments.

They become verification obligations.

---

## 624. Verification IR generation
<!-- source: FIRST-MIGRATION.md §14 -->

Now:

```text
Contract
+ Design
+ Unsafe Obligations
        ↓
Verification Compiler
        ↓
Verification IR
```

Example:

```rust
VerificationObligation {
    id: UO_002,
    category: AbiLayout,
    proposition: "work field offset matches C layout",
    oracle: AbiLayoutOracle,
    required_variants: [x86_64, ...],
}
```

Another:

```rust
VerificationObligation {
    id: LIFE_001,
    category: ResourceLifecycle,
    proposition: "callback cannot dereference object after final release",
    oracle: LifecycleInvariantOracle,
}
```

---

## 625. Test generation
<!-- source: FIRST-MIGRATION.md §15 -->

The verification compiler should derive tests from obligations.

```text
OBLIGATION
    │
    ├── static check
    ├── compile check
    ├── runtime test
    ├── differential test
    └── adversarial test
```

For `LOCK-001`:

```text
normal mutation
concurrent mutation
callback mutation
lock bypass attempt
```

For `LIFE-001`:

```text
normal callback
callback + release race
cancel + release
duplicate release
callback after teardown
```

---

## 626. Negative corpus
<!-- source: FIRST-MIGRATION.md §16 -->

This is essential.

Create intentionally wrong Rust implementations:

```text
fixtures/lab001/negative/
├── missing_ref.rs
├── double_put.rs
├── use_after_free.rs
├── lock_bypass.rs
├── wrong_layout.rs
├── wrong_callback_context.rs
└── ffi_lifetime_violation.rs
```

The system should demonstrate:

```text
correct implementation      ↓ obligations satisfied
incorrect implementation    ↓ at least one obligation fails
```

This tests the verifier rather than merely the happy path.

---

## 627. Execution
<!-- source: FIRST-MIGRATION.md §17 -->

Only now is code execution authorized.

```text
AUTHORIZED_FOR_TESTING
        ↓
ExecutionRequest
        ↓
capability validation
        ↓
isolated worktree
        ↓
exact command
        ↓
executor
        ↓
ExecutionReceipt
```

Example command identity:

```text
rustc
argv = [...]
cwd = ...
environment = ...
toolchain = ...
```

Every generated test result is attached to the receipt.

---

## 628. Evidence
<!-- source: FIRST-MIGRATION.md §18 -->

The resulting chain:

```text
test
 ↓
stdout/stderr
 ↓
artifact
 ↓
receipt
 ↓
observation
 ↓
evidence
```

For example:

```text
EV-001
    subject = UO-002
    receipt = R-014
    artifact = A-031
    snapshot = S-001
    variant = V-001
    status = OBSERVED
```

The evidence ledger does not itself claim:

```text
UO-002 VERIFIED
```

That remains the verification layer's job.

---

## 629. Verification
<!-- source: FIRST-MIGRATION.md §19 -->

The verifier consumes:

```text
VerificationObligation + Evidence + Oracle
```

and produces:

```rust
VerificationResult {
    obligation: UO_002,
    status: Verified,
    evidence: [EV_001],
    oracle_result: OR_001,
}
```

Only now can the gate engine evaluate the requirement.

---

## 630. Gate
<!-- source: FIRST-MIGRATION.md §20 -->

For Lab 001:

```text
LAB001-GATE = ALL(
    snapshot_valid,
    contract_reconciled,
    design_reconciled,
    no_critical_unknown,
    no_critical_conflict,
    implementation_exists,
    all_required_obligations_verified,
    ABI_verified,
    lifetime_verified,
    concurrency_verified,
    negative_tests_detected,
    independent_verification_completed
)
```

The output:

```text
PASS
FAIL
BLOCKED
```

not a confidence percentage.

---

## 631. Independent verification
<!-- source: FIRST-MIGRATION.md §21 -->

This is the point where the architecture's authority separation becomes testable.

Topology:

```text
              DESIGN AGENT
                    │
                    ▼
               IMPLEMENTER
                    │
                    ▼
                ARTIFACT
                    │
                    ▼
           ┌────────┴────────┐
           ▼                 ▼
    CONTRACT REVIEW    VERIFICATION
           │                 │
           └────────┬────────┘
                    ▼
             ADVERSARIAL QA
                    │
                    ▼
                  GATE
```

The implementation agent cannot approve its own result.

---

## 632. Deliberate protocol attack
<!-- source: FIRST-MIGRATION.md §22 -->

For MU-000001, attempt:

```text
ImplementationAgent
        │
        └── SubmitVerification
```

Expected:

```text
ProtocolError::Authorization
```

Then:

```text
Scheduler
    │
    └── AuthorizeRelease
```

Expected:

```text
ProtocolError::Authorization
```

Then:

```text
Agent
    │
    └── submit stale verification
```

Expected:

```text
ProtocolError::StaleEpoch
```

Then:

```text
Agent
    │
    └── verification using invalidated evidence
```

Expected:

```text
GateStatus::Blocked
```

These are system tests, not merely unit tests.

---

## 633. Migration certificate
<!-- source: FIRST-MIGRATION.md §23 -->

Only after all gates pass:

```text
MU-000001
       │
       ▼
MigrationCertificate
```

Certificate graph:

```text
S-001
 │
 ▼
KSIR-001
 │
 ▼
CONTRACT-001
 │
 ▼
DESIGN-001
 │
 ▼
IMPLEMENTATION-001
 │
 ▼
EXECUTION-001
 │
 ▼
EVIDENCE-001
 │
 ▼
VERIFICATION-001
 │
 ▼
GATE-001
 │
 ▼
CERTIFICATE-001
```

The certificate should contain digests for every node.

---

## 634. Certificate invariant
<!-- source: FIRST-MIGRATION.md §24 -->

The certificate generator should reject:

```text
missing contract
missing design
missing implementation
missing verification
missing evidence
invalid receipt
invalidated evidence
critical unknown
critical conflict
stale snapshot
variant mismatch
failed gate
```

Therefore:

```text
Certificate
    implies all declared certificate prerequisites exist
```

but not:

```text
Certificate
    implies the migrated code is universally correct
```

Scope remains bounded.

---

## 635. MU-000001 manifest
<!-- source: FIRST-MIGRATION.md §25 -->

The complete artifact becomes:

```text
migration/MU-000001/
├── manifest.json
│
├── snapshot.json
├── variant.json
├── scope.json
│
├── ksir/
│   ├── facts.json
│   ├── unknowns.json
│   └── conflicts.json
│
├── contract/
│   ├── contract.json
│   ├── invariants.json
│   └── obligations.json
│
├── design/
│   ├── design.json
│   ├── mappings.json
│   └── unsafe-obligations.json
│
├── implementation/
│   ├── commit.json
│   └── artifacts/
│
├── verification/
│   ├── plan.json
│   ├── results.json
│   ├── oracle-results.json
│   └── counterexamples/
│
├── execution/
│   └── receipts/
│
├── evidence/
│   ├── records/
│   └── dependencies.json
│
├── gates/
│   └── results.json
│
└── certificate/
    └── migration-certificate.json
```

This is effectively a **proof-carrying migration package**.

---

## 636. End-to-end state machine
<!-- source: FIRST-MIGRATION.md §26 -->

The whole unit now has two interacting state machines.

### Migration state

```text
DISCOVERED
 ↓
MAPPED
 ↓
CONTRACTED
 ↓
DESIGNED
 ↓
AUTHORIZED_FOR_IMPLEMENTATION
 ↓
IMPLEMENTED
 ↓
AUTHORIZED_FOR_TESTING
 ↓
VERIFIED
 ↓
ADVERSARIALLY_VERIFIED
 ↓
AUTHORIZED_FOR_REVIEW
 ↓
RELEASE_ELIGIBLE
 ↓
RELEASED
```

### Evidence state

```text
NOT_PRESENT
 ↓
OBSERVED
 ↓
BOUND
 ↓
RECONCILED
 ↓
VERIFICATION_INPUT
 ↓
VERIFIED
```

They must **not** be merged.

---

## 637. Why this is the real milestone
<!-- source: FIRST-MIGRATION.md §27 -->

Before MU-000001, RFL-AE is primarily an architecture.

After MU-000001 passes, it becomes an experimentally demonstrated system.

The critical measurements are no longer:

```text
number of agents
number of prompts
lines of generated Rust
tokens consumed
```

Instead:

| Property | Measurement |
| --- | --- |
| Protocol determinism | replay equivalence |
| Authority isolation | unauthorized transition rejection |
| Evidence integrity | receipt/artifact binding |
| Snapshot discipline | mismatch rejection |
| Unknown handling | unknown preservation |
| Contract coverage | obligations reconstructed |
| Verification | obligations independently evaluated |
| Adversarial robustness | negative corpus |
| Reproducibility | replay execution |
| Auditability | complete provenance chain |

---

## 638. The first real success criterion
<!-- source: FIRST-MIGRATION.md §28 -->

The strongest criterion for this milestone is:

```text
MU-000001
```

must be able to answer, mechanically:

```text
What source snapshot was migrated?
        ↓
What semantic facts were reconstructed?
        ↓
What remains unknown?
        ↓
What contract was derived?
        ↓
What Rust design was authorized?
        ↓
What implementation was produced?
        ↓
What exact commands executed?
        ↓
What actually happened?
        ↓
What evidence supports each observation?
        ↓
Which obligations were verified?
        ↓
Which gates passed?
        ↓
Who had authority for each transition?
        ↓
What exact scope does the certificate cover?
```

If any answer is:

```text
"the agent said so"
```

the vertical slice has failed.

---

## 639. Then scale
<!-- source: FIRST-MIGRATION.md §29 -->

Only after MU-000001 is green should the system move to:

```text
MU-000001
      │
      ▼
MU-000002
      │
      ├── independent migration
      │
      ▼
MU-000003
      │
      ├── shared semantic dependency
      ▼
MU-000004
```

Then test orchestration.

Only later:

```text
10 units
 ↓
100 units
 ↓
1000 units
 ↓
subsystem
 ↓
cross-subsystem migration
```

The architecture should scale **the evidence discipline**, not merely the number of agents.

---

## 640. Frozen next milestone
<!-- source: FIRST-MIGRATION.md §30 -->

```text
RFL-AE-M0
├── Protocol kernel executable
├── Event sourcing deterministic
├── Authorization enforced
├── Evidence ledger connected
├── Verification IR connected
├── Gate engine connected
└── MU-000001 end-to-end
```

After that, the next major task is **not another IR**.

It is to implement **KSIR v0.1 + the semantic reconstruction vertical slice**, feeding real C/compiler observations into MU-000001.

That is where RFL-AE stops being a protocol framework and starts becoming an actual Linux-engineering system.
