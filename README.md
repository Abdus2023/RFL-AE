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

## Status

`v0.0` — documentation only. Fourteen specification documents covering §1–§517 (§108 does not
exist in the source; the gap is preserved); no Rust crates, JSON schemas, or executable
benchmarks have been written yet.
