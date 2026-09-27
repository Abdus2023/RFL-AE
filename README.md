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

## Status

`v0.0` — documentation only. Eight specification documents covering §1–§291 (§108 does not
exist in the source; the gap is preserved); no Rust crates, JSON schemas, or executable
benchmarks have been written yet.
