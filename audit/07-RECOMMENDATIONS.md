# 07 — Recommendations

Part of the [deep audit](README.md). Original report sections **§24–§26**.

---

## §24. What I would NOT change

I would preserve these decisions:

```text
NO confidence score as truth
NO majority vote for semantics
NO agent self-attestation
NO scheduler semantic authority
NO execution receipt = proof
NO implicit snapshot scope
NO stale artifact reuse
NO silent conflict resolution
NO UNKNOWN → probably safe
NO certificate = proof of whole kernel
```

Those are foundational.

---

## §25. What I would change immediately

I would make the next implementation commit a specification-hardening commit,
before writing the Rust runtime.

### P0 — Type closure

Create a canonical domain type registry:

```text
SnapshotId
KernelSnapshotId
Digest
GitObjectId
ArchitectureId
ToolchainFingerprint
EnvironmentFingerprint
GateStatus
...
```

Eliminate synonyms.

> **Maintainer note.** Per the correction in
> [03-SPECIFICATION-DEFECTS.md](03-SPECIFICATION-DEFECTS.md),
> `EnvironmentFingerprint` is already declared at `EXECUTION.md:355`. The
> registry should record it as *declared but scattered* rather than missing; the
> genuinely undeclared primitives are `Uuid`, `Digest`, `GitObjectId`,
> `ArchitectureId`, `ToolchainFingerprint`, and `Timestamp`.

### P0 — Gate algebra

Choose one:

```text
GateStatus
```

or:

```text
GateResult
```

and formally define:

```text
atomic gate status
gate evaluation
aggregate gate result
release predicate
```

### P0 — Positive tooling execution

Make:

```text
run_all.sh
```

actually execute:

```text
renumber.py
splice.py
audit
closeout
skill validation
negative tests
```

with positive fixtures.

### P1 — Executable protocol kernel

Start:

```text
rfl-types
rfl-protocol
rfl-transition
rfl-event-ledger
rfl-evidence
```

before LLM integration.

### P1 — CI authority

Add:

```text
.github/workflows/
```

with:

```text
corpus audit
skill execution
negative tests
Rust compile
protocol tests
deterministic replay tests
```

### P1 — Domain-type schemas

Add machine-readable:

```text
schemas/
├── snapshot.schema.json
├── task.schema.json
├── authorization.schema.json
├── artifact.schema.json
├── evidence.schema.json
├── contract.schema.json
├── verification.schema.json
├── gate.schema.json
├── certificate.schema.json
└── orchestration.schema.json
```

### P1 — Linux integration manifest

Add:

```text
linux/
├── subsystem.yaml
├── toolchain.yaml
├── config-matrix.yaml
├── architecture-matrix.yaml
├── verification-backends.yaml
└── maintainer-policy.yaml
```

---

## §26. The actual next architectural milestone

I would not jump directly into an LLM agent swarm.

The next target should be:

```text
RFL-AE-PROTO-001
```

an executable deterministic protocol kernel:

```text
OperationRequest
                       │
                       ▼
                ┌──────────────┐
                │ Validator    │
                └──────┬───────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Scope       Capability     Epoch
       check         check        check
          │            │            │
          └────────────┼────────────┘
                       ▼
                TransitionEngine
                       │
                       ▼
                 Canonical Event
                       │
                       ▼
                  State Digest
                       │
                       ▼
                  Event Ledger
                       │
                       ▼
                 Replay Engine
```

Then adversarially attack it:

```text
stale authorization
cross-snapshot artifact
scope escape
writer collision
self-verification
invalid transition
forged evidence
artifact substitution
event reordering
duplicate operation
replay divergence
```

Only after that kernel passes should the LLM layer be granted access.
