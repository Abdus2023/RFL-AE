# RFL-AE

**Rust-for-Linux Autonomous Engineering**

Skills, tools, and agentic architectures for an AI system to assist in rewriting the Linux
kernel in Rust — built around a Kernel Semantic IR, an independent evidence plane, and a
non-self-validating release gate.

## Documents

- **[ARCHITECTURE.md](ARCHITECTURE.md)** (§1–§51) — the founding architecture specification:
  core C subsystem landscape, competency domains K0–K12, agent roles, KSIR, the evidence
  model, benchmark families B01–B10, migration planning (M0–M3, semantic cut), and the
  RFL-AE v0.1 module layout.
- **[SPECIFICATION.md](SPECIFICATION.md)** (§52–§80) — the v0.1 engineering specification:
  repository layout, immutable domain model, the contract set (function / ownership /
  concurrency / execution-context / Rust Design IR), safety obligations, agent protocol and
  authorization states, the layered verification pipeline (V0–V10), differential equivalence
  dimensions (E0–E8), subsystem qualification, the Kernel Invariant Ledger, and the Migration
  Certificate.
- **[FORMAL-CORE.md](FORMAL-CORE.md)** (§81–§107) — the frozen formal core: KSIR v0.1, core
  Rust domain types, evidence-carrying values, the two-axis status algebra, the evidence and
  provenance model, the 20-benchmark suite (C01–C10, R01–R05, V01–V05), anti-hallucination and
  contradiction benchmarks, tool authority levels T0–T6, agent separation, the migration
  manifest and commit protocol, subsystem QA (LOCK/RCU/MM/SCHED), and RFL-AE-LAB-001.
- **[PROTOCOL.md](PROTOCOL.md)** (§109–§135) — the multi-agent execution protocol: message
  envelope, capability-based authority and scope, task admission, the migration-unit state
  machine and quarantine, conflict objects, knowledge-state separation, the canonical artifact
  store, immutable event ledger and deterministic replay, execution receipts, agent topology
  and the 63-agent taxonomy, worktree isolation, patch promotion, the readiness predicate, the
  implementation-admission gate, data vs. control plane, and the L0–L13 v0.2 layer stack.
- **[RUST-CORE.md](RUST-CORE.md)** (§136–§172) — the concrete Rust core: 31 declared types
  (opaque IDs, `KernelSnapshot`, `Epistemic<T>`, `VerificationStatus`, `Task`, `Scope`,
  `Capability`, `CapabilityGrant`, `Authorization`, `Artifact`, `Event`, `Evidence`, `Contract`,
  `ContractKnowledge<T>`, `RustDesign`, `UnsafeObligation`, `AgentOutcome`), the
  `TransitionEngine`, protocol invariants P1–P10, the conformance and adversarial protocol
  suites, agent manifests, scheduling, and the PHASE 0–11 development order.
- **[TRANSITIONS.md](TRANSITIONS.md)** (§173–§203) — `RFL-AE-PROTOCOL-001`, the normative
  transition system: the 7-stage validation kernel, the 11-row normative transition table,
  illegal transitions as specification, transition predicates, typed `ProtocolError` rejection
  reasons, unknown severity, dependency conditions, semantic vs. source dependency, contract
  normal form, claim graph, epochs and staleness propagation, writer leases, the read/write
  authority matrix, `VerificationMatrix` and gate algebra, protocol self-verification, proof
  obligations P-001–P-010, and the trusted/untrusted LLM boundary.
- **[KSIR.md](KSIR.md)** (§204–§250) — the Kernel Semantic IR: layering (structural /
  behavioral / contractual), the `Ksir` root, `KsirFunction`, the pointer model with
  `PointerOwnership` / `Nullability` / `AliasingModel`, object and storage-class models, the
  lifetime graph and refcount/RCU contracts, the concurrency graph and sync-primitive taxonomy,
  execution context, sleepability, allocation context, the effects system, callback and
  temporal graphs, memory ordering, architecture dependencies, ABI, FFI, user memory, DMA,
  MMIO, invariants, semantic classification, the query engine and blocker query, failure modes
  F1–F7, acceptance criteria KSIR-001–KSIR-015, and the QA corpus.
- **[RECONSTRUCTION.md](RECONSTRUCTION.md)** (§251–§291) — the semantic reconstruction
  engine: the analysis backend architecture and its authority table, `AnalysisObservation`
  and reproducible backend identity, build variants and configuration domains, compiler
  command fidelity, Linux-specific semantic hazards, the structural pipeline, call graphs
  and indirect-call reachability, effect and execution-context propagation, the context
  lattice, lock and path-sensitive lockset analysis, ownership, refcount, RCU, callback,
  temporal-ownership, alias, memory-region, ABI and architecture reconstruction, the
  reconciliation engine and its states, conflict as data, the no-consensus rule, evidence
  reconciliation, semantic fact vs verified claim, the semantic dependency graph, migration
  dependency extraction, agent decomposition and the worker contract, the critical unknown
  detector, the crate structure, and acceptance criteria SR-001–SR-012.
- **[CONTRACTS.md](CONTRACTS.md)** (§292–§320) — kernel contract reconstruction:
  `KernelContract` and contract status, preconditions and postconditions, invariants and
  invariant preservation, contract normal form, the 17-domain contract surface, temporal /
  concurrency / context contracts, API contract generation, Rust design alternatives, design
  obligations, unsafe boundary generation and the unsafe budget, contract-to-test generation,
  contract differential testing, contract refinement, contract completeness and the
  `G-CONTRACT-001`…`008` gate, the contract compiler, the agent boundary, the contract review
  agent, the counterexample engine, the migration unit contract package, the end-to-end proof
  chain, and the Rust Design IR transition.
- **[DESIGN-IR.md](DESIGN-IR.md)** (§321–§356) — the Rust Design IR: the `RustDesign` root and
  its `source_contract`, design vs implementation, representation mapping, the Rust type
  taxonomy and semantic roles, ownership mapping and transfer events, lifetime design,
  self-referential structures and pinning obligations, synchronization mapping, lock
  encapsulation and ordering, atomic and RCU design mapping, context-preserving API design,
  contract enforcement strength, FFI boundaries and trust classification, ABI-preserving vs
  ABI-breaking migration, architecture mapping, error mapping and error contracts,
  initialization design and typestate candidates, callback design and reentrancy, design
  rejection, search and selection, the design gate, the Rust implementation boundary, generated
  safety obligations, the design-to-verification chain, the complete migration compiler, and the
  three IRs.
- **[VERIFICATION.md](VERIFICATION.md)** (§357–§386, source §§1–§30) — the Verification IR:
  `VerificationPlan`, `VerificationObligation`, the closed `VerificationCategory` taxonomy, the
  `Proposition` algebra, the claim ≠ test ≠ evidence chain, the `OracleKind` model and oracle
  independence, differential verification and normalization, verification scope, the
  configuration and architecture matrices, static and dynamic verification, CI authority,
  concurrency verification, counterexamples and shrinking, mutation verification, verification
  adequacy, the verification state machine, authority separation, the adversarial verifier, the
  verification compiler, the crate architecture, the migration certificate, and the complete
  evidence chain. Section headings carry machine-readable `source: VERIFICATION.md §n`
  provenance comments.
- **[GATES.md](GATES.md)** (§387–§418, source §§1–§32) — the gate engine and migration
  certificate compiler: the gate invariant, the `Gate` model and severity, the constrained
  `GatePredicate` algebra, `GateEvaluation` and `FAIL != BLOCKED`, the gate dependency graph
  and gate families, the snapshot / scope / contract / design / unsafe / ABI / context /
  lifetime / concurrency / verification gates, evidence validity and freshness, gate policy
  versioning, release eligibility and the release predicate, unknown handling, the migration
  certificate compiler and its structure, certificate invalidation, release authority, human
  review, the complete RFL-AE architecture, the four-layer trust architecture, and the
  Execution & Evidence Runtime. Same provenance convention as `VERIFICATION.md`.
- **[EXECUTION.md](EXECUTION.md)** (§419–§462, source §§1–§44) — the Execution & Evidence
  Runtime: the missing trust boundary between "the system says it ran" and "we can prove
  exactly what ran", the execution trust chain, `ExecutionRequest`, capability-based
  authorization and scope binding, canonical `CommandSpec` / `ExecutableIdentity` /
  `EnvironmentFingerprint`, worktree isolation and deny-by-default network policy, the
  execution lifecycle, the three separate dimensions `ExecutionStatus` / `ProcessOutcome` /
  `EvidenceStatus`, canonical content-addressed `ExecutionReceipt`, digested artifacts and
  roles, immutability and append-only invalidation, `EvidenceRecord` and the nine-clause
  binder, the evidence graph and reverse provenance, replay manifests and reproducibility
  tiers, nondeterminism classification, tool receipts and the capability registry, execution
  vs semantic vs gate authority, typed execution failures, the security boundary, receipt
  signing, evidence strength and independence, execution provenance, the runtime crate
  structure, acceptance criteria `EXE-001`–`EXE-015`, the `RFL-EXEC-LAB-001` vertical slice,
  the `EXE-QA-001`–`EXE-QA-015` adversarial suite, the twelve-condition trust theorem, and the
  closed evidence loop. Same provenance convention as `VERIFICATION.md`.
- **[ORCHESTRATION.md](ORCHESTRATION.md)** (§463–§517, source §§1–§55) — the Orchestration IR
  and deterministic scheduler, treated as a **protocol executor** rather than an intelligent
  project manager: `OrchestrationPlan`, the semantic migration graph and why
  `source graph ≠ semantic graph`, migration-unit readiness, scheduling as a state transition
  (`scheduler ≠ state authority`), the agent model, capability as demonstrable evidence rather
  than competence, capability and authority matching, work and worktree leases, epochs and
  stale work, determinism and the scheduling key, fairness quotas, dependency-aware and
  critical-path scheduling, the event-driven scheduler, immutable assignments, agent crash
  recovery, idempotency and at-least-once dispatch, duplicate execution versus independence,
  quarantine and its recovery, conflict resolution without voting, unknowns as scheduling
  dependencies, automatic evidence tasks, the orchestration state machine, deterministic replay
  and logical time, the scheduler event log, restart recovery and external reconciliation,
  resource scheduling and starvation, cancellation, priority inversion, the multi-agent
  verification topology and the no-self-verification rule, orchestration policy, acceptance
  criteria `ORCH-001`–`ORCH-017`, the scheduler crate architecture, the resulting authority
  model, and the frozen **RFL-AE Core Invariants** `RFL-AE-I001`–`I015`. Same provenance
  convention as `VERIFICATION.md`.
- **[PROTOCOL-KERNEL.md](PROTOCOL-KERNEL.md)** (§518–§547, source §§1–§30) — the protocol
  kernel, where the specification becomes an executable state machine: the trust boundary from
  untrusted proposal side through the kernel to the append-only event store and canonical
  state, the normative `Command ≠ Event` distinction, the canonical event envelope carrying
  both `state_before` and `state_after`, opaque typed IDs, the transition algebra,
  `ProtocolState`, the deterministic reducer, declarative `TransitionSpec` with its eleven
  preconditions, atomicity with the event as commit boundary, optimistic concurrency and the
  CAS boundary, the `EventStore` trait, the event hash chain, structured `ProtocolError`,
  rejected command versus authorized operation failure, the executable migration transition
  table, the strict verification transition, event-sourced projections, snapshotting, three
  distinct version axes, event evolution, the `PROTO-001`–`PROTO-020` conformance suite, the
  `ATTACK-001`–`ATTACK-020` adversarial suite, the minimal `rfl-protocol` crate, dependency
  direction without authority recursion, the first executable vertical slice, the three
  protocol theorems, and the separation of semantic, protocol, execution, scheduling and
  release authority. Same provenance convention as `VERIFICATION.md`.
- **[PROTOCOL-IMPL.md](PROTOCOL-IMPL.md)** (§548–§575, source §§1–§28) — the protocol kernel
  as a concrete API and transition implementation: the repository skeleton, `rfl-types` with
  the `typed_id!` macro so `TaskId != AgentId` even though both are UUIDs, the `Digest` type
  and explicit `DigestAlgorithm`, snapshot identity where the immutable digest is
  authoritative, `MigrationState`, `Operation`, `TransitionCommand` and its `ExpectedState`
  optimistic-concurrency contract, explicit `Authorization` and `AuthorityClass`, capability
  kept separate from authorization, `ProtocolState` over `BTreeMap` for deterministic hashing,
  `MigrationRecord` with no confidence score, the `TransitionEngine` and its validation
  ordering, `TransitionPlan`, `ProtocolEvent` and `EventKind`, the deliberately boring reducer
  and what it must never do, the in-memory `EventStore` and its CAS append, `replay` with
  `state_before`/`state_after` divergence detection, the lifecycle / illegal-transition /
  authorization / epoch / tamper tests, the `PROTO-GATE-001` checklist, the frozen crate
  dependency boundary, and the P0–P10 implementation progression. Rust here is specification,
  not a compiled crate. Same provenance convention as `VERIFICATION.md`.
- **[PROTOCOL-P58.md](PROTOCOL-P58.md)** (§576–§610, source §§1–§35) — connecting persistence,
  evidence and gates to the kernel without letting any of them become hidden authority. **P5**
  persistence: the append-only event log, its length-delimited physical record, the locking
  append protocol, explicit `RecoveryStatus` crash semantics with no silent truncation, and the
  rule that `event constructed ≠ event accepted ≠ event durably persisted ≠ operation executed ≠
  claim verified`. **P6** evidence binding: `EvidenceRef` references rather than bytes,
  `EvidenceValidity`, dependency-driven rather than global invalidation, a
  `VerificationSubmission` that cannot merely carry `status: Verified`, per-obligation
  `ObligationResult`, semantic coverage, and `OracleKind` with `ComparisonRelation` so that
  `C output == Rust output` is never a universal rule. **P7** gates: the gate algebra as typed
  predicates and `GateExpr`, the implementation/test/release gates, and `GateStatus` keeping
  `FAIL` distinct from `BLOCKED` because `UNKNOWN ≠ FALSE`. **P8** certificates:
  `MigrationCertificate` as a claim and not release authority, the full source-to-release chain,
  typed `EventPayload`, dependency invalidation, stale versus invalid, epoch advancement as a
  transition, canonical serialization, the frozen lifecycle transition table, the quarantine
  authority-suppression invariant, the protocol QA matrix, and the release boundary. Same
  provenance convention as `VERIFICATION.md`.
- **[FIRST-MIGRATION.md](FIRST-MIGRATION.md)** (§611–§640, source §§1–§29 plus the unnumbered
  *Frozen next milestone*) — the first closed-loop migration unit. The goal is not to migrate a
  meaningful subsystem but to prove RFL-AE can take **one bounded C unit through the entire
  authority/evidence pipeline** without bypassing its own protocol: the frozen
  `RFL-AE-LAB-001 / MU-000001` slice, a small kernel-like C fixture whose ownership relationship
  is deliberately *not* obvious from syntax alone, expected KSIR facts, controlled unknowns that
  prove `unsupported analysis ↓ UNKNOWN` rather than `assumed safe`, the contract compiler and
  its evidence-referenced statements, the contract graph, ownership/lock/callback mappings,
  unsafe obligations `UO-001…003` that become verification obligations rather than comments,
  verification IR and obligation-derived tests, a **negative corpus** that tests the verifier
  rather than the happy path, execution receipts, the evidence chain, `LAB001-GATE` returning
  `PASS / FAIL / BLOCKED` and not a confidence percentage, the independent-verification
  topology, deliberate protocol attacks, the migration certificate and its invariant, the
  proof-carrying `MU-000001` manifest, two state machines that must not be merged, and the
  thirteen questions the unit must answer mechanically — if any answer is *"the agent said so"*,
  the vertical slice has failed. Same provenance convention as `VERIFICATION.md`.
- **[KSIR-IMPL.md](KSIR-IMPL.md)** (§641–§659, source §§1–§18 plus the unnumbered
  *implementation order* clause) — making KSIR **executable against a real C fixture** rather
  than adding another abstraction layer. The frozen v0.1 domain table, in which *unsupported
  analysis must serialize as an explicit limitation, not disappear*; `rfl-types` + `rfl-ksir`
  with `SemanticFact<T>` and an `EpistemicStatus` that deliberately has **no `Verified`
  variant**; `UnknownFact` carrying domain, reason and severity so `UNKNOWN` is actionable
  rather than `null`; an observation layer that refuses to trust analyzer output; the uniform
  `AnalysisBackend` contract that forbids silently selecting another kernel commit, `.config`,
  compiler, header tree or architecture; `BuildManifest` as the root of semantic evidence —
  `No BuildManifest ↓ No authoritative compiler observation ↓ No VERIFIED semantic claim`; the
  compiler-native first backend; `CallTarget` as a **precision lattice, not a confidence
  score**; context and effect reconstruction; ownership and lock reconstruction that must
  surface `CONFLICT` or `UNPROTECTED` rather than repair source semantics by assumption;
  reconciliation with **no agent voting, no majority rule, no confidence aggregation**; KSIR
  synthesis; critical-unknown blocker extraction; the `lab001` corpus treated as a fixture
  specification; acceptance gates `KSIR-001…020`; the end-to-end execution chain; and the fixed
  M0 implementation order. Same provenance convention as `VERIFICATION.md`.
- **[KSIR-SLICE.md](KSIR-SLICE.md)** (§660–§679, source §§1–§19 plus the unnumbered *immediate
  next build target*) — turning that schema into a **minimal compilable implementation**. The
  `rfl-types` / `rfl-ksir` / `rfl-analysis-types` / `rfl-analysis-compiler` split, which is what
  stops the analyzer from becoming the semantic authority; `id_type!` so a typed `ObjectId` is
  protocol identity rather than a descriptive string; a `Digest` that carries its algorithm;
  snapshot identity where `source_tree_digest` is authoritative and `source_version` merely
  descriptive; build variants as separate validity domains; mandatory provenance; a pointer
  model in which `Ownership = RefCounted`, `Aliasing = MutableShared`, `Lifetime = Unknown` is
  valid KSIR and must **not** be "helpfully" converted into `Arc<T>`; lifetime, concurrency,
  context and effect models; an observation schema that says *this backend observed X* and never
  *X is semantically verified*; a reconciler with **no weighted voting**; a compiler-backend
  boundary that cannot write `state.migration = Verified`; the deliberately narrow `A001…A007`
  first analyzer with explicit `SUPPORTED / PARTIALLY_SUPPORTED / OPAQUE / UNKNOWN` capability
  status; the first **deliberate failure**, where the analyzer failing safely is the correct
  result; deterministic KSIR digests; fail-closed snapshot invalidation; `KSIR-GATE-001`
  returning `PASS / FAIL / BLOCKED` and not `87% semantic confidence`; and the
  authority-separation table. Same provenance convention as `VERIFICATION.md`.
- **[KSIR-ANALYZER.md](KSIR-ANALYZER.md)** (§680–§701, source §§1–§21 plus the unnumbered *next
  implementation sequence*) — building the **first real analyzer** rather than another schema.
  The frozen analyzer boundary in which the analyzer *never receives permission to mutate
  canonical protocol state*; `AnalysisArtifact`, so the chain is
  `KSIR fact ↓ Observation ↓ AnalysisArtifact ↓ ExecutionReceipt` rather than
  `"compiler said so"`; a normalization layer keeping compiler-specific structures out of KSIR;
  a reproducible `BackendIdentity` where `executable_digest` and `algorithm_revision` mean an
  algorithm change invalidates derived facts even with the source tree unchanged; build
  invocation driven by a real `BuildManifest` and recorded as the **actual command**; the
  deliberately small `lab001` fixture with a shim so it stays independently buildable; the
  expected structural graph; observed vs. derived vs. unknown facts that must never be
  collapsed; direct-call effect propagation with `DerivedFact` pointing back to both
  observations; versioned `RuleIdentity`; the callback, context, ownership and lifetime rules
  that stop at `UNKNOWN` instead of guessing; a structural KSIR artifact in which `UNKNOWN` is
  useful data; three negative tests (analyzer failure, conflicting observations, snapshot
  substitution) establishing `execution failure ≠ semantic false ≠ verification failure`; the
  first `KSIR-GATE-001` execution, where **BLOCKED is the correct result**; Contract IR with
  `C005 = BLOCKED`; and the two properties that become executable tests. Same provenance
  convention as `VERIFICATION.md`.
- **[EXECUTABLE-KERNEL.md](EXECUTABLE-KERNEL.md)** (§702–§717, source *Current state* plus
  §§1–§14 plus the unnumbered *Immediate implementation sequence*) — stopping the addition of
  conceptual layers and making the invariants executable. A `Current state` table that still
  records the protocol as **PROVISIONAL** and the transition engine, evidence ledger and gate
  engine as **NOT IMPLEMENTED**; the governing principle that **RFL-AE must be able to reject an
  invalid agent action without asking an LLM whether the action is valid**; a `DOMAIN-TYPES.md`
  registry eliminating the `SnapshotId` / `KernelSnapshotId` ambiguity; the three-way gate
  algebra where `Gate ≠ GateStatus ≠ GateResult`; a canonical `Epoch` answered with `REJECT`
  rather than `WARNING`; `rfl-types` as a deliberately boring crate with **domain types and
  invariants only**; `rfl-transition`, where agents **request** transitions and only the engine
  produces authoritative state; a transition relation that is never `"probably okay"`,
  `"LLM believes valid"` or `"majority of agents approved"`; a task state machine that makes
  `FAILED → VERIFIED` and `EXECUTING → CERTIFIED` structurally impossible; seven adversarial
  negative tests; an event ledger whose `previous_state + operation + resulting_state` makes
  replay divergence detectable; evidence bound to objects rather than `"cargo test passed"`;
  `TechnicalCertification` kept separate from `UpstreamAcceptanceState`; the Linux subsystem
  manifest; the inverted agent hierarchy; a one-engine-first milestone with **0 autonomous
  mutation agents**; eleven implementation phases; and a release gate without which RFL-AE v0.1
  cannot be called complete. Same provenance convention as `VERIFICATION.md`.
- **[PROTOCOL-V01.md](PROTOCOL-V01.md)** (§718–§744, source §§1–§27) — the **Protocol Kernel
  Specification v0.1**, freezing the protocol so it is *closed under execution*: every object
  referenced by a transition has a canonical type, every state change has a deterministic rule,
  and every rejection is machine-identifiable. The canonical domain model in which `Task`,
  `Contract`, `Capability` and `Authorization` are **not interchangeable**; opaque newtype IDs so
  code cannot compare `String` with `ArtifactId`; `KernelSnapshotId` resolving the `SnapshotId`
  ambiguity; an `Epoch` with an executable `same_epoch` rule rather than a textual convention;
  structural `Scope` with `contains()` as protocol logic; the absolute **capability ≠
  authorization** distinction; a closed `OperationKind` with no arbitrary shell execution; typed
  `OperationRequest` instead of natural-language instructions; a transition relation with **no
  third state**; a stable `RejectionReason` taxonomy; explicit transition legality where
  `Created -> Certified` yields `InvalidTransition`; `Task` separated from `TaskAttempt` rather
  than allowing state rewinds; an event ledger chained by `previous_event` and `event_digest`;
  the replay invariant `replay(events) == authoritative_state`; evidence strictly downstream of
  execution; `EvidenceOutcome::Passed` **not** implying `Artifact::Verified`; verification as a
  multi-dimensional relation; nine contract classes; the gate non-equivalences; a certificate
  that is `Derive(...)` and never *"Agent says CERTIFIED"*; an executable `RELEASE_ELIGIBLE`
  predicate; a tiny agent API; the proposed repository reorganisation; an 18-row conformance
  matrix where **the negative suite is as important as the positive suite**; the kernel
  verification bridge, where RFL-AE knows *what* evidence means and Linux tools determine
  *whether* the test passed; maintainer authority as a separate plane; and the C→Rust
  reconstruction model, where **the reconstructed semantic contract — not the Rust code — is the
  source of truth**. Same provenance convention as `VERIFICATION.md`.

## Tooling

[`skills/`](skills/README.md) contains the reusable toolchain this corpus was
produced with, packaged as skills. Six of them: `ascii-diagram-forge` (diagrams
generated from column arithmetic, never hand-typed), `corpus-provenance-numbering`
(contiguous corpus numbering with lossless source provenance),
`placeholder-splice` (substitute generated diagrams and prove each landed inside
a fence), `markdown-corpus-audit` (per-file and whole-corpus checks for the
defects that render silently), `spec-turn-closeout` (the end-of-document ritual),
and `skill-creator` (the meta-skill used to author the others).

Run everything:

```bash
./skills/run_all.sh                    # or: ./skills/run_all.sh .venv/bin/python
```

It runs the geometry self-test, validates every skill, audits the corpus and the
newest document, verifies the last close-out, and then runs three negative tests
that must each fail. It exits non-zero if any stage fails, and it refuses to
report a skipped check as a pass.

## Audit

[`audit/`](audit/README.md) contains an external deep audit of this branch at
`952e300`, split into eight themed documents. It is a review of the corpus, not
a specification, so it sits outside the §1–§744 numbering. Every checkable
claim in it was re-verified before being saved; the results, including one
correction to the report, are recorded in
[audit/README.md](audit/README.md#verification-of-this-audits-factual-claims).

Its conclusion is accepted: this is a **specification-level system**, which is
what the status line below already says.

## Status

`v0.0` — documentation only. Twenty-three specification documents covering §1–§744 (§108 does not
exist in the source; the gap is preserved); no Rust crates, JSON schemas, or executable
benchmarks have been written yet.
