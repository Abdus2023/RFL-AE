# 02 — Architecture assessment

Part of the [deep audit](README.md). Original report sections **§4–§9**.

---

## §4. The architecture itself is unusually well separated

The strongest part of RFL-AE is not the list of AI skills.

It is the authority separation.

The documents progressively establish:

```text
C source
   ↓
KSIR
   ↓
Contract IR
   ↓
Rust Design IR
   ↓
Rust implementation
   ↓
Verification IR
   ↓
Execution evidence
   ↓
Gate evaluation
   ↓
Migration certificate
```

And separately:

```text
Scheduler
    ≠
Semantic authority
```

and:

```text
Execution receipt
    ≠
Semantic proof
```

and:

```text
Implementation authority
    ≠
Verification authority
```

Those are exactly the distinctions an AI-based kernel engineering system needs.

The key architecture is spread across `KSIR.md`, `CONTRACTS.md`,
`DESIGN-IR.md`, `VERIFICATION.md`, `GATES.md`, `EXECUTION.md`,
`ORCHESTRATION.md`.

---

## §5. Strongest architectural property: epistemic separation

The RUST-CORE model has:

```rust
pub enum Epistemic<T> {
    Unknown,

    Observed {
        value: T,
        evidence: EvidenceId,
    },

    Derived {
        value: T,
        from: Vec<ArtifactId>,
    },

    Hypothesis {
        value: T,
        basis: Vec<ArtifactId>,
    },
}
```

and separately:

```rust
pub enum VerificationStatus {
    Unverified,
    Provisional,
    PartiallyVerified,
    Verified,
    Blocked,
}
```

That is the correct conceptual direction.

It permits:

```text
Epistemic = Derived
Verification = Unverified
```

rather than turning a model-derived fact into a verified fact.

That distinction is essential for LLM-assisted engineering.

---

## §6. Strongest safety rule: no consensus truth

The repository explicitly rejects:

```text
7 agents say X
3 agents say Y
→ X wins
```

and instead requires:

```text
X observations
Y observations
        ↓
CONFLICT
        ↓
additional evidence
```

That is exactly right for kernel concurrency, lifetime, memory ordering and ABI
questions.

A majority of LLMs is not evidence of kernel semantics.

This is one of the most important design decisions in the entire repository.

---

## §7. Snapshot/epoch model is also strong

The repository correctly recognizes:

```text
Linux S1
    ↓
fact F
```

cannot silently become:

```text
Linux S2
    ↓
same fact F
```

The epoch mechanism then adds:

```text
Epoch 41
    ↓
authorization
    ↓
work
    ↓
contract change
    ↓
Epoch 42
```

with old authorization becoming stale.

That is exactly the mechanism needed for a continuously changing Linux tree.

---

## §8. Execution/Evidence layer is conceptually sound

EXECUTION.md makes a particularly important separation:

```text
ExecutionStatus
        ≠
ProcessOutcome
        ≠
EvidenceStatus
```

For example:

```text
exit code 0
```

doesn't automatically mean:

```text
verification passed
```

The execution layer records what happened.

The verification layer interprets what it means.

The gate layer decides whether that meaning satisfies release policy.

That three-layer distinction is correct.

See `EXECUTION.md` §419–462.

---

## §9. Gate model is also conceptually good

The repository explicitly distinguishes:

```text
PASS
FAIL
BLOCKED
NOT_APPLICABLE
INVALIDATED
```

and states:

```text
FAIL != BLOCKED
```

That is important.

For example:

```text
RCU test failed
```

is materially different from:

```text
RCU test could not execute
because required configuration was unavailable
```

The release predicate is also explicit:

```text
snapshot_valid
AND scope_valid
AND contract_gate_pass
AND design_gate_pass
AND implementation_gate_pass
AND required_verification_gates_pass
AND unsafe_gate_pass
AND ABI_gate_pass
AND regression_gate_pass
AND adversarial_gate_pass
AND evidence_gate_pass
AND no_blocking_unknowns
AND no_unresolved_critical_conflicts
AND no_invalidated_dependencies
```

That is much better than:

```text
score >= 90
```

or:

```text
all_tests_green
```

See `GATES.md`.
