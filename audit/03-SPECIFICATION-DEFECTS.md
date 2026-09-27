# 03 — Specification defects

Part of the [deep audit](README.md). Original report sections **§10–§12**.

All three findings in this document were independently re-verified against the
branch. Two hold exactly; the third holds in substance with one list item
corrected.

---

## §10. Concrete specification defect #1 — GateStatus is undefined

This is the first real defect I found.

TRANSITIONS.md defines:

```rust
pub struct VerificationMatrix {
    pub compile: GateStatus,
    pub unit: GateStatus,
    pub integration: GateStatus,
    pub runtime: GateStatus,
    pub concurrency: GateStatus,
    pub memory: GateStatus,
    pub abi: GateStatus,
    pub differential: GateStatus,
    pub adversarial: GateStatus,
    pub regression: GateStatus,
}
```

and later:

```rust
pub struct GateResult {
    pub gate: GateId,
    pub status: GateStatus,
    ...
}
```

But the corpus does not define:

```text
enum GateStatus
```

The later GATES.md instead defines:

```rust
enum GateResult {
    Pass,
    Fail,
    Blocked,
    NotApplicable,
    Invalidated,
}
```

So there is an unresolved type-level question:

```text
GateStatus
    ?
    ├── same thing as GateResult?
    ├── different aggregate status?
    └── obsolete name?
```

Classification

```text
PROVED specification gap.
```

Required correction

Define one canonical gate status algebra, e.g.:

```rust
pub enum GateStatus {
    Pass,
    Fail,
    Blocked,
    NotApplicable,
    Invalidated,
}
```

and then eliminate or rename GateResult, or explicitly distinguish:

```text
GateStatus
    = atomic status

GateEvaluation
    = evaluated gate artifact

GateResult
    = aggregate result
```

At present the boundary is ambiguous.

> **Maintainer note — verified, claim holds.** `GateStatus` appears 11 times,
> all in `TRANSITIONS.md` (lines 859–868 and 933). There is no `enum GateStatus`
> anywhere in the corpus. `GATES.md:263` defines `enum GateResult` with exactly
> the five variants quoted above. Note there is a second, separate collision the
> report implies but does not name explicitly: `TRANSITIONS.md` also has a
> `pub struct GateResult` while `GATES.md` has an `enum GateResult`, so the name
> is overloaded as well as `GateStatus` being undefined.

---

## §11. Concrete specification defect #2 — SnapshotId is referenced but not declared

RUST-CORE.md declares:

```rust
pub struct KernelSnapshot {
    pub snapshot_id: SnapshotId,
    ...
}
```

but the 31 explicitly declared public core types do not include:

```text
SnapshotId
```

I checked the repository's Rust-core definitions and the corpus has no:

```text
pub struct SnapshotId
```

declaration.

The architecture uses both:

```text
SnapshotId
```

and, elsewhere in the newer execution architecture:

```text
KernelSnapshotId
```

This needs normalization.

Classification

```text
PROVED specification gap.
```

Recommended resolution

Use one canonical identifier:

```rust
pub struct KernelSnapshotId(pub Uuid);
```

and consistently use it everywhere.

Do not allow:

```text
SnapshotId
KernelSnapshotId
```

to become accidental synonyms.

> **Maintainer note — verified, claim holds.** No `struct SnapshotId`,
> `struct KernelSnapshotId`, `type SnapshotId`, or `type KernelSnapshotId`
> exists in any document. `KernelSnapshotId` is used in 8 places across
> `CONTRACTS.md`, `DESIGN-IR.md`, `GATES.md`, `ORCHESTRATION.md`,
> `RECONSTRUCTION.md`, and `VERIFICATION.md` (3×), while `SnapshotId` is used
> in `RUST-CORE.md` (6×) and elsewhere. Both names are live; neither is
> declared.

---

## §12. Concrete specification defect #3 — the repository's "31 types" claim is true, but their dependency closure is not complete

I verified that RUST-CORE.md contains exactly 31 explicit public Rust
declarations:

```text
8 opaque IDs
KernelSnapshot
Epistemic
VerificationStatus
Task
TaskState
Scope
Capability
CapabilityGrant
Authorization
AuthorizedOperation
Artifact
ArtifactHeader
Event
TransitionEngine
Evidence
EvidenceSource
EvidenceStatus
Contract
ContractKnowledge
RustDesign
UnsafeObligation
SafetyObligation
AgentOutcome
```

So the "31 declared types" claim is correct.

However, those declarations depend on additional undeclared types such as:

```text
SnapshotId
Uuid
Digest
GitObjectId
Architecture
ToolchainFingerprint
EnvironmentFingerprint
...
```

That is fine if they are explicitly declared as external/domain primitives.

At the moment, the specification doesn't establish that closure cleanly enough.

Required next step

Create:

```text
DOMAIN-TYPES.md
```

or a normative appendix containing every dependency of the core types.

Then the protocol can have a genuine closed type graph:

```text
RFL-AE domain
     │
     ├── identifiers
     ├── digests
     ├── timestamps
     ├── snapshots
     ├── artifacts
     ├── authorization
     ├── events
     ├── evidence
     └── gates
```

> **Maintainer note — verified, claim holds in substance with one correction.**
> `RUST-CORE.md` contains exactly 31 `pub struct|enum|type|trait` declarations:
> the 8 opaque IDs (`TaskId`, `AgentId`, `ArtifactId`, `EvidenceId`, `EventId`,
> `MigrationUnitId`, `CapabilityId`, `AuthorizationId`) plus the 23 listed. That
> part is exact.
>
> **Correction:** `EnvironmentFingerprint` is *not* undeclared — it is declared
> at `EXECUTION.md:355`. Likewise `Scope` (`RUST-CORE.md:323`) and `Epoch`
> (`TRANSITIONS.md:588`) are declared. The closure gap is nonetheless real, and
> larger than the report suggests for the primitives it did not list:
>
> | type | declared | uses |
> |------|----------|------|
> | `Uuid` | no | 8 |
> | `Digest` | no | 22 |
> | `GitObjectId` | no | 1 |
> | `ArchitectureId` | no | 4 |
> | `ToolchainFingerprint` | no | 4 |
> | `Timestamp` | no | 16 |
> | `EnvironmentFingerprint` | **yes** (`EXECUTION.md:355`) | 8 |
> | `Scope` | **yes** (`RUST-CORE.md:323`) | 26 |
> | `Epoch` | **yes** (`TRANSITIONS.md:588`) | 19 |
>
> So the `DOMAIN-TYPES.md` recommendation stands; only the membership of the
> undeclared list needs correcting.
