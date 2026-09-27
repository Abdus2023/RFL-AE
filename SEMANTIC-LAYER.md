# RFL-AE — Semantic Reconstruction Layer

> **Provenance and numbering.** This document was supplied as *RFL-AE — Semantic Reconstruction Layer*, numbered §1–§29 in the source plus a final unnumbered *RFL-AE maturity boundary* section. To keep the corpus contiguous, its sections are renumbered **§745–§774**, continuing directly from [PROTOCOL-V01.md](PROTOCOL-V01.md) (which ends at §744). The mapping is **`corpus_section = source_section + 744`**, with the unnumbered closing section recorded as source §30 — the convention already used by `PROTOCOL-KERNEL.md`, `FIRST-MIGRATION.md`, `KSIR-IMPL.md`, `KSIR-SLICE.md`, `KSIR-ANALYZER.md` and `EXECUTABLE-KERNEL.md`. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: SEMANTIC-LAYER.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/` tree, no `rfl-ksir` crate, no `linux/subsystems/` profile, no KSIR type, no reconstruction agent, and no vertical slice has been written or compiled. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** The pasted source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/SEMANTIC-LAYER.py`](diagrams/SEMANTIC-LAYER.py); re-running it reproduces all 86 diagrams. Diagrams that arrive as box-drawing art stay box-drawing (the preamble pipeline, the provenance graph, the agent fan-out, the compilation pipeline, the two-evidence chain and the maturity boundary); those that arrive as ASCII art — `|`, `v`, `+--` — stay ASCII, matching the established corpus pattern. No block mixes an ASCII `|` with box glyphs. The C snippets in §745 and §763 are fenced as `c`, the `unsafe` block in §768 and the Rust types as `rust`, and the subsystem profile in §772 as `yaml`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

The next layer is the actual heart of the Linux C→Rust problem:

```text
C source
          │
          ▼
Observed program facts
          │
          ▼
Semantic Reconstruction
          │
          ▼
Kernel Semantic IR (KSIR)
          │
          ▼
Contracts
          │
          ▼
Rust Design IR
          │
          ▼
Rust implementation
          │
          ▼
Independent verification
```

The important rule is:

> **Do not translate syntax first. Reconstruct semantics first.**

A C function can be mechanically translated into Rust while still being semantically wrong because the important behavior may reside in calling conventions, lock context, RCU rules, interrupt context, ownership conventions, error paths, initialization ordering, macros, generated code, or interactions with other subsystems.

---

## Contents

- [745. The reconstruction problem](#745-the-reconstruction-problem)
- [746. KSIR should become typed](#746-ksir-should-become-typed)
- [747. KSIR top-level object](#747-ksir-top-level-object)
- [748. Source facts versus semantic interpretation](#748-source-facts-versus-semantic-interpretation)
- [749. Provenance graph](#749-provenance-graph)
- [750. The semantic dimensions](#750-the-semantic-dimensions)
- [751. Context is part of semantics](#751-context-is-part-of-semantics)
- [752. Lock semantics](#752-lock-semantics)
- [753. Ownership reconstruction](#753-ownership-reconstruction)
- [754. Lifetime graph](#754-lifetime-graph)
- [755. RCU must be a first-class semantic domain](#755-rcu-must-be-a-first-class-semantic-domain)
- [756. Initialization is a contract](#756-initialization-is-a-contract)
- [757. Teardown deserves equal status](#757-teardown-deserves-equal-status)
- [758. ABI is independent](#758-abi-is-independent)
- [759. Configuration semantics](#759-configuration-semantics)
- [760. Architecture-dependent semantics](#760-architecture-dependent-semantics)
- [761. Generated and macro-expanded behavior](#761-generated-and-macro-expanded-behavior)
- [762. Reconstruction agents become specialized](#762-reconstruction-agents-become-specialized)
- [763. Example](#763-example)
- [764. Conflict is a first-class object](#764-conflict-is-a-first-class-object)
- [765. No majority voting](#765-no-majority-voting)
- [766. Semantic confidence must not become truth](#766-semantic-confidence-must-not-become-truth)
- [767. Rust Design IR](#767-rust-design-ir)
- [768. Unsafe is an obligation ledger](#768-unsafe-is-an-obligation-ledger)
- [769. This gives us a real compilation pipeline](#769-this-gives-us-a-real-compilation-pipeline)
- [770. The crucial invariant](#770-the-crucial-invariant)
- [771. New release criterion](#771-new-release-criterion)
- [772. Subsystem migration profile](#772-subsystem-migration-profile)
- [773. The next implementation milestone](#773-the-next-implementation-milestone)
- [774. RFL-AE maturity boundary](#774-rfl-ae-maturity-boundary)

---

## 745. The reconstruction problem
<!-- source: SEMANTIC-LAYER.md §1 -->

For a C function:

```c
int foo(struct bar *b) {
        ...
}
```

RFL-AE should not immediately ask:

```text
"What is the Rust equivalent?"
```

It should first ask:

```text
What does foo mean?
```

More formally:

```text
C Artifact
    │
    ▼
Observable Facts
    │
    ▼
Control/Data/Concurrency Analysis
    │
    ▼
Semantic Claims
    │
    ▼
Contracts
    │
    ▼
Rust Design
```

This produces two distinct artifacts:

```text
C semantics
       |
       +--------------------+
       |                    |
       v                    v
Semantic Contract       Evidence
       |
       v
Rust Design
```

The contract and evidence remain separate.

---

## 746. KSIR should become typed
<!-- source: SEMANTIC-LAYER.md §2 -->

The existing KSIR concept should become a real intermediate representation.

Not merely Markdown.

Something like:

```text
crates/
└── rfl-ksir/
    └── src/
        ├── lib.rs
        ├── function.rs
        ├── type.rs
        ├── memory.rs
        ├── concurrency.rs
        ├── control.rs
        ├── abi.rs
        ├── lifecycle.rs
        └── provenance.rs
```

The first version does not need to model all of C.

It needs to model the **kernel-relevant semantics that affect a safe Rust reconstruction**.

---

## 747. KSIR top-level object
<!-- source: SEMANTIC-LAYER.md §3 -->

```rust
pub struct SemanticUnit {
    pub id: SemanticUnitId,
    pub epoch: Epoch,

    pub source: SourceRegion,

    pub declarations: Vec<Declaration>,
    pub operations: Vec<Operation>,
    pub invariants: Vec<Invariant>,
    pub contracts: Vec<ContractRef>,

    pub evidence: Vec<EvidenceId>,
}
```

The important field is:

```text
evidence
```

Every nontrivial semantic assertion should be traceable.

For example:

```text
Invariant:
    "lock L protects field x"
Evidence:
    source locations
    call graph
    lock annotations
    runtime observations
    static analysis
```

Without that:

```text
"lock L protects x"
```

is merely an agent assertion.

---

## 748. Source facts versus semantic interpretation
<!-- source: SEMANTIC-LAYER.md §4 -->

This distinction needs to become fundamental.

### Observation

```text
Observed:
    function A calls spin_lock(&L)
```

### Derivation

```text
Derived:
    execution of A enters a region protected by L
```

### Hypothesis

```text
Hypothesis:
    all accesses to field x require L
```

### Verification

```text
Verified:
    the invariant has sufficient independent evidence
```

These must never collapse into one Boolean.

```text
OBSERVED
    ≠ DERIVED
    ≠ HYPOTHESIS
    ≠ VERIFIED
```

This matches one of RFL-AE's strongest existing ideas and should now be enforced by the data model.

---

## 749. Provenance graph
<!-- source: SEMANTIC-LAYER.md §5 -->

Instead of storing only:

```text
claim -> evidence
```

use a graph:

```text
              SOURCE
                 │
                 ▼
            OBSERVATION
                 │
           ┌─────┴─────┐
           ▼           ▼
      DERIVATION  DERIVATION
           │           │
           └─────┬─────┘
                 ▼
               CLAIM
                 │
                 ▼
             CONTRACT
                 │
                 ▼
           VERIFICATION
```

Each edge needs provenance.

For example:

```rust
pub enum DerivationKind {
    CallGraph,
    DataFlow,
    ControlFlow,
    TypeAnalysis,
    LockAnalysis,
    RcuAnalysis,
    LifetimeAnalysis,
    RuntimeObservation,
    DifferentialObservation,
}
```

Now RFL-AE can answer:

> Why does the system believe this contract exists?

rather than merely:

> Which agent said it?

---

## 750. The semantic dimensions
<!-- source: SEMANTIC-LAYER.md §6 -->

For kernel reconstruction, KSIR should explicitly model at least these dimensions:

```text
1. Type
2. Memory
3. Ownership
4. Lifetime
5. Aliasing
6. Initialization
7. Destruction
8. Concurrency
9. Locking
10. RCU
11. Interrupt context
12. Process context
13. Allocation context
14. Error behavior
15. Control flow
16. Data flow
17. ABI
18. Calling convention
19. Side effects
20. Global state
21. CPU locality
22. Preemption
23. Atomicity
24. Ordering
25. Synchronization
26. Configuration
27. Architecture dependencies
28. Generated code
29. Macro behavior
30. External subsystem dependencies
```

Not every function will populate all 30.

But the absence must be explicit:

```text
NOT_OBSERVED
```

rather than silently becoming:

```text
false
```

---

## 751. Context is part of semantics
<!-- source: SEMANTIC-LAYER.md §7 -->

This is particularly important for Linux.

A function's meaning cannot always be inferred from its body alone.

Example conceptual distinction:

```text
foo()
```

called from:

```text
process context
```

may permit:

```text
sleep
```

while the same function called from:

```text
atomic context
interrupt context
```

may not.

Therefore KSIR needs:

```rust
pub enum ExecutionContext {
    Process,
    Atomic,
    Interrupt,
    SoftIrq,
    Nmi,
    RcuReadSide,
    Unknown,
}
```

Potentially with compositional properties rather than a single enum, because contexts can overlap.

For example:

```text
Interrupt + RCU read-side + preemption constraints
```

should not necessarily be flattened into one categorical state.

---

## 752. Lock semantics
<!-- source: SEMANTIC-LAYER.md §8 -->

A Rust migration agent must know more than:

```text
"there is a lock here."
```

It needs:

```text
Lock L
├── protects:
│   ├── field x
│   └── field y
├── acquired:
│   ├── function A
│   └── function B
├── released:
│   ├── function A
│   └── function B
├── ordering:
│   └── L1 -> L2
└── context:
    └── process / atomic / ...
```

Represent:

```rust
pub struct LockContract {
    pub lock: SymbolId,
    pub protected: Vec<MemoryLocation>,
    pub ordering: Vec<LockOrder>,
    pub acquisition: Vec<SourceRegion>,
    pub release: Vec<SourceRegion>,
}
```

Then Rust design can decide whether the appropriate representation is:

```text
Mutex
SpinLock
RwLock
raw lock abstraction
guard
atomic
RCU primitive
```

The AI does not get to choose based on naming similarity.

---

## 753. Ownership reconstruction
<!-- source: SEMANTIC-LAYER.md §9 -->

This is one of the hardest parts.

C often expresses ownership indirectly.

For example:

```text
caller allocates
    │
    ▼
callee stores pointer
    │
    ▼
asynchronous worker consumes it
    │
    ▼
worker releases it
```

The C syntax alone does not say:

```text
"this pointer has transferred ownership."
```

KSIR therefore needs explicit ownership events:

```rust
pub enum OwnershipEvent {
    Create,
    Borrow,
    BorrowMut,
    Transfer,
    Retain,
    Release,
    Destroy,
    Unknown,
}
```

And a relation:

```text
Object O  CREATE
    │
    ▼
OWNED(A)
    │
    ▼
TRANSFER
    │
    ▼
OWNED(B)
    │
    ▼
RELEASE
    │
    ▼
DESTROYED
```

The Rust design can then map this to:

```text
Box
Arc
Rc
Pin
&mut T
&T
kernel-specific ownership wrapper
```

or potentially retain an unsafe boundary where the semantics cannot yet be proven.

---

## 754. Lifetime graph
<!-- source: SEMANTIC-LAYER.md §10 -->

Ownership alone is insufficient.

Kernel objects frequently have asynchronous lifetimes.

Represent:

```text
Object
+-- created at A
+-- published at B
+-- consumed by worker C
+-- removed from lookup at D
+-- grace period E
+-- freed at F
```

This becomes:

```rust
pub struct LifetimeContract {
    pub object: SymbolId,
    pub creation: SourceRegion,
    pub publication: Option<SourceRegion>,
    pub retirement: Option<SourceRegion>,
    pub destruction: Option<SourceRegion>,
    pub dependencies: Vec<LifetimeDependency>,
}
```

This is where constructs such as:

```text
RCU
refcounting
workqueues
timers
callbacks
interrupt handlers
```

become central.

---

## 755. RCU must be a first-class semantic domain
<!-- source: SEMANTIC-LAYER.md §11 -->

Do not represent RCU as merely another lock.

Conceptually:

```text
LOCK
    protects concurrent mutation
RCU
    protects access/lifetime under grace-period semantics
```

The reconstruction model should distinguish:

```text
RCU read-side critical section
RCU publication
RCU replacement
RCU retirement
grace-period synchronization
post-grace reclamation
```

Then a Rust design must preserve those semantics.

A naive transformation:

```text
C pointer
    → Rust reference
```

is not automatically valid.

---

## 756. Initialization is a contract
<!-- source: SEMANTIC-LAYER.md §12 -->

Kernel initialization frequently has ordering semantics.

Represent:

```text
init(A)
    requires:
        B initialized
init(C)
    requires:
        A initialized
```

as a dependency graph:

```text
B
│
▼
A
│
▼
C
```

Then:

```text
C before A
```

is a protocol violation.

This should be checked before code generation.

---

## 757. Teardown deserves equal status
<!-- source: SEMANTIC-LAYER.md §13 -->

Migration systems tend to over-focus on construction.

Kernel correctness frequently depends on teardown:

```text
register
    │
    ▼
publish
    │
    ▼
operate
    │
    ▼
quiesce
    │
    ▼
unregister
    │
    ▼
flush
    │
    ▼
free
```

The Rust design must preserve the ordering.

A generated `Drop` implementation cannot simply be assumed correct.

The semantic contract needs to say:

```text
Drop(X)
    requires:
        workers stopped
        callbacks quiesced
        references released
        publication removed
```

---

## 758. ABI is independent
<!-- source: SEMANTIC-LAYER.md §14 -->

Do not bury ABI inside type conversion.

Create:

```rust
pub struct AbiContract {
    pub symbol: SymbolId,
    pub calling_convention: CallingConvention,
    pub parameter_layout: Layout,
    pub return_layout: Layout,
    pub visibility: Visibility,
    pub linkage: Linkage,
}
```

Then:

```text
C ABI
    |
    v
ABI Contract
    |
    v
Rust ABI Design
```

This is especially important for mixed C/Rust kernel configurations.

---

## 759. Configuration semantics
<!-- source: SEMANTIC-LAYER.md §15 -->

Linux source semantics are configuration-dependent.

Conceptually:

```text
CONFIG_A
    enables X
CONFIG_B
    changes implementation Y
CONFIG_A && CONFIG_B
    activates Z
```

Therefore a semantic unit should carry:

```rust
pub struct ConfigurationContext {
    pub symbols: BTreeMap<ConfigSymbol, ConfigValue>,
}
```

The reconstruction system must distinguish:

```text
behavior proven under CONFIG_X
```

from:

```text
behavior proven for all configurations
```

These are different claims.

---

## 760. Architecture-dependent semantics
<!-- source: SEMANTIC-LAYER.md §16 -->

Likewise:

```text
x86
ARM64
RISC-V
...
```

may expose different implementations.

Therefore:

```text
SemanticContract
+-- universal
+-- architecture-specific
```

A claim such as:

```text
"this operation is safe"
```

must carry its domain.

For example:

```text
ARCH = x86_64
CONFIG = ...
TOOLCHAIN = ...
```

rather than pretending one successful build establishes universal validity.

---

## 761. Generated and macro-expanded behavior
<!-- source: SEMANTIC-LAYER.md §17 -->

This is another place where source-level AI reasoning can fail.

The system should distinguish:

```text
written source
generated source
macro expansion
compiler-generated behavior
architecture-generated behavior
```

Coccinelle is already part of the Linux ecosystem for semantic patching and transformation; RFL-AE should therefore treat existing kernel analysis/transformation infrastructure as an evidence source rather than trying to replace all of it with an LLM.

---

## 762. Reconstruction agents become specialized
<!-- source: SEMANTIC-LAYER.md §18 -->

Now we can define the first useful agent roles.

Not:

```text
Agent 1
Agent 2
Agent 3
```

but semantic responsibilities.

```text
                  Reconstruction Coordinator
                               |
       +-----------------------+-----------------------+
       |                       |                       |
       v                       v                       v
 Control/Data           Memory/Lifetime           Concurrency
   Analyzer                Analyzer                Analyzer
       |                       |                       |
       +-----------------------+-----------------------+
                               |
                               v
                         ABI Analyzer
                               |
                               v
                    Configuration Analyzer
                               |
                               v
                     Contract Synthesizer
```

Each agent produces **claims/proposals**, not truth.

---

## 763. Example
<!-- source: SEMANTIC-LAYER.md §19 -->

Suppose an agent observes:

```c
spin_lock(&foo->lock);
foo->value++;
spin_unlock(&foo->lock);
```

The observation is:

```text
O1:
    foo->value is written while lock is held.
```

Evidence:

```text
source = foo.c:L100-L102
```

A derivation:

```text
D1:
    lock(foo->lock) protects this write.
```

Potential contract:

```text
C1:
    writes to foo->value require foo->lock.
```

But C1 is not automatically verified.

The system searches for:

```text
all writes to foo->value
all reads of foo->value
all paths acquiring foo->lock
all paths accessing foo->value
```

If another path does:

```text
foo->value++;
```

without the lock, then:

```text
C1
```

may be false, incomplete, or conditional.

The AI must not silently "repair" the contradiction.

Instead:

```text
CONFLICT
```

enters the evidence/verification pipeline.

---

## 764. Conflict is a first-class object
<!-- source: SEMANTIC-LAYER.md §20 -->

Add:

```rust
pub struct SemanticConflict {
    pub id: ConflictId,
    pub epoch: Epoch,

    pub claims: Vec<ClaimId>,

    pub conflict_kind: ConflictKind,

    pub status: ConflictStatus,
}
```

For example:

```rust
pub enum ConflictKind {
    Ownership,
    Lifetime,
    Locking,
    Rcu,
    ControlFlow,
    Abi,
    Configuration,
    Architecture,
    Type,
    Initialization,
    Teardown,
}
```

And:

```text
Conflict
    ≠ Failure
```

A conflict means the semantic model is not yet resolved.

Therefore:

```text
unresolved critical conflict
        → release blocked
```

This directly supports the existing release predicate.

---

## 765. No majority voting
<!-- source: SEMANTIC-LAYER.md §21 -->

Suppose:

```text
Agent A: lock protects x
Agent B: lock protects x
Agent C: lock does not protect x
```

The system must **not** calculate:

```text
2 vs 1
```

and choose the majority.

Instead:

```text
Claims
    |
    v
Evidence
    |
    v
Analysis
    |
    v
Verification
```

If evidence remains contradictory:

```text
UNKNOWN / CONFLICT
```

The protocol does not manufacture truth from agreement.

---

## 766. Semantic confidence must not become truth
<!-- source: SEMANTIC-LAYER.md §22 -->

A model might output:

```text
confidence = 0.97
```

That is not verification evidence.

The protocol should permit probabilistic metadata:

```rust
pub struct HeuristicScore {
    pub value: f64,
    pub basis: ScoreBasis,
}
```

but prohibit:

```text
score > 0.95
    → Verified
```

The only route to:

```text
Verified
```

is a defined verification relation.

---

## 767. Rust Design IR
<!-- source: SEMANTIC-LAYER.md §23 -->

Once semantic contracts stabilize, introduce the next IR:

```text
KSIR
    |
    v
Contract IR
    |
    v
Design IR
```

Example:

```rust
pub struct RustDesign {
    pub artifact: ArtifactId,
    pub epoch: Epoch,

    pub types: Vec<RustTypeDesign>,
    pub ownership: Vec<OwnershipDesign>,
    pub concurrency: Vec<ConcurrencyDesign>,
    pub abi: Vec<AbiDesign>,

    pub unsafe_obligations: Vec<UnsafeObligation>,
}
```

The critical field:

```text
unsafe_obligations
```

must not disappear.

---

## 768. Unsafe is an obligation ledger
<!-- source: SEMANTIC-LAYER.md §24 -->

Instead of:

```rust
unsafe {
    ...
}
```

being the end of the reasoning, RFL-AE should require:

```rust
pub struct UnsafeObligation {
    pub id: ObligationId,
    pub location: SourceRegion,
    pub reason: UnsafeReason,
    pub required_invariants: Vec<InvariantId>,
    pub evidence: Vec<EvidenceId>,
    pub status: ObligationStatus,
}
```

So:

```text
unsafe block
    |
    v
UnsafeObligation
    |
    +-- invariant 1
    +-- invariant 2
    +-- invariant 3
    |
    v
verification
```

An unresolved critical unsafe obligation blocks certification.

---

## 769. This gives us a real compilation pipeline
<!-- source: SEMANTIC-LAYER.md §25 -->

The final architecture now looks like:

```text
                    LINUX C
                       │
                       ▼
              ┌───────────────────┐
              │ Source Evidence   │
              │                   │
              └────────┬──────────┘
                       │
                       ▼
              ┌───────────────────┐
              │ KSIR              │
              │ control           │
              │ data              │
              │ memory            │
              │ lifetime          │
              │ ownership         │
              │ locking           │
              │ RCU               │
              │ context           │
              │ ABI               │
              │ config            │
              │ architecture      │
              └────────┬──────────┘
                       │
                       ▼
              ┌───────────────────┐
              │ Contract Model    │
              │                   │
              └────────┬──────────┘
                       │
               contract verified
                       │
                       ▼
                Rust Design IR
                       │
                       ▼
              ┌───────────────────┐
              │ Rust Generator    │
              └────────┬──────────┘
                       │
                       ▼
                 Rust artifact
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
       compile       KUnit       runtime
          │            │            │
          └────────────┬────────────┘
                       ▼
                   Evidence
                       │
                       ▼
                 Verification
                       │
                       ▼
                     Gates
                       │
                       ▼
                  Certificate
```

---

## 770. The crucial invariant
<!-- source: SEMANTIC-LAYER.md §26 -->

This entire pipeline should enforce:

```text
RustArtifact
    cannot become Certified
```

unless there exists a valid chain:

```text
RustArtifact
    │
    ▼
RustDesign
    │
    ▼
SemanticContract
    │
    ▼
KSIR
    │
    ▼
SourceEvidence
```

and independently:

```text
RustArtifact
    │
    ▼
Execution
    │
    ▼
Evidence
    │
    ▼
Verification
    │
    ▼
Gates
```

So certification requires **two independent directions of evidence**:

```text
SOURCE SEMANTICS
                 │
                 ▼
KSIR
                 │
                 ▼
CONTRACT
                 │
                 ▼
RUST DESIGN
                 │
                 ▼
RUST ARTIFACT
                 │
                 ▼
EXECUTION EVIDENCE
                 │
                 ▼
VERIFICATION
```

This is much stronger than either:

```text
C → Rust translation
```

or:

```text
Rust compiles + tests pass
```

alone.

---

## 771. New release criterion
<!-- source: SEMANTIC-LAYER.md §27 -->

For a C→Rust unit `U`:

```text
CERTIFIABLE(U)
```

requires:

```text
source_identity_valid
AND semantic_model_complete_for_required_domains
AND no_unresolved_critical_conflicts
AND required_contracts_verified
AND design_contract_conformant
AND unsafe_obligations_resolved
AND abi_contract_satisfied
AND configuration_scope_satisfied
AND architecture_scope_satisfied
AND execution_evidence_valid
AND verification_gates_pass
AND replay_valid
```

The phrase:

```text
complete_for_required_domains
```

is deliberate.

We should not require every imaginable semantic property for every function.

Instead each subsystem declares its required semantic coverage.

---

## 772. Subsystem migration profile
<!-- source: SEMANTIC-LAYER.md §28 -->

That leads directly to the next artifact:

```text
linux/subsystems/scheduler.yaml
```

should define something like:

```yaml
semantic_requirements:
  type: required
  ownership: required
  lifetime: required
  locking: required
  rcu: required
  interrupt_context: required
  preemption: required
  abi: required
  configuration: required
  architecture: required

verification_requirements:
  build: required
  kunit: required
  runtime: required
  concurrency: required
  differential: conditional
```

A simpler subsystem might have:

```text
rcu: not_applicable
```

but that declaration itself should be evidence-backed.

---

## 773. The next implementation milestone
<!-- source: SEMANTIC-LAYER.md §29 -->

We now have enough architecture to define the first **actual end-to-end vertical slice**.

Do not attempt scheduler migration yet.

Use an intentionally small kernel component and prove:

```text
C source
    │
    ▼
source extraction
    │
    ▼
KSIR
    │
    ▼
contract
    │
    ▼
Rust Design IR
    │
    ▼
Rust
    │
    ▼
test
    │
    ▼
evidence
    │
    ▼
gate
    │
    ▼
certificate
```

The vertical slice becomes the reference implementation of the entire RFL-AE protocol.

Then every subsequent subsystem must conform to the same pipeline.

---

## 774. RFL-AE maturity boundary
<!-- source: SEMANTIC-LAYER.md §30 -->

At this point the project can be divided cleanly:

```text
                     RFL-AE
                        │
       ┌────────────────┴─────────────┐
       │                              │
PROTOCOL KERNEL             RECONSTRUCTION ENGINE
       │                              │
       ├── types                      ├── C analysis
       ├── authorization              ├── KSIR
       ├── transitions                ├── contracts
       ├── event ledger               ├── design IR
       ├── evidence                   └── Rust generation
       ├── verification
       └── gates
```

The **protocol kernel must be deterministic**.

The **reconstruction engine may use AI**.

That separation is fundamental.

The LLM can be uncertain, wrong, inconsistent, or adversarially manipulated. The protocol kernel must still produce the same answer for the same typed state and request.

That is the point where RFL-AE becomes an **AI-assisted verified reconstruction system**, rather than an AI coding swarm with a verification layer attached afterward.
