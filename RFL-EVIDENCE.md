# RFL-AE — `rfl-evidence`: The External Trust Boundary

> **Provenance and numbering.** This document was supplied untitled (the heading above is derived from its content — rename freely), numbered **§62–§89** in the source: the author continued the numbering of [RFL-LEDGER.md](RFL-LEDGER.md) (§39–§61), which continued [RFL-TRANSITION.md](RFL-TRANSITION.md) (§19–§38) and [RFL-TYPES.md](RFL-TYPES.md) (§1–§18). It has no unnumbered sections. To keep the corpus contiguous, its sections are renumbered **§866–§893**, continuing directly from `RFL-LEDGER.md` (which ends at §865). The mapping is the plain **`corpus_section = source_section + 804`** — the same offset as `RFL-TRANSITION.md` and `RFL-LEDGER.md`, because the author's numbering and the corpus numbering both continue without a gap. Every heading carries the mapping as a machine-readable comment of the form `<!-- source: RFL-EVIDENCE.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Status note.** Like the rest of this corpus, this document is a **specification**. No `crates/rfl-evidence/` tree, no evidence record, binding validator, executor registry or evidence lifecycle has been written or compiled. The repository status remains `v0.0` — documentation only.

> **Transcription note (derived treatment — delete if unwanted).** The pasted source's ASCII art arrived collapsed onto single lines, so the diagrams were *redrawn* with every glyph position derived by column arithmetic and verified by the box-width, orphan-connector, off-centre and ASCII-substitution checks. The generator is committed at [`diagrams/RFL-EVIDENCE.py`](diagrams/RFL-EVIDENCE.py); re-running it reproduces all 56 diagrams. Box-drawing art stays box-drawing; no block mixes an ASCII `|` with box glyphs. One diagram was normalised geometrically, with no content change: in §892 the source drew the arrows above the first box one column to the right of every box's `┬`, so the whole stack now shares one spine. Two flat word lists arrived with single spaces only and were broken into lines by meaning: in §877, `architecture configuration` was read as two items (`architecture`, `configuration`) because §878 treats configuration and architecture as separate scopes — join them if one item was intended; in §893 the gate kinds split at each `gate`. The §884 evidence-completeness grid is rendered as a markdown table. The three LaTeX formulas in §882 are fenced as `math`. Rust types and the Rust-syntax fragments — the paths `ExecutionOperation::KUnit` (§870) and `EvidenceStatus::Incomplete` (§883), and the function signatures in §891 — are fenced as `rust`; pseudo-assignments such as `verified = true` and `output_artifacts = [ … ]` stay `text`. Rust blocks use the corpus's canonical formatting (4-space indent, single space after `:`).

Now we cross the most important external trust boundary: **`rfl-evidence`**.

The transition/ledger layers establish what RFL-AE authorized and what the protocol says happened. `rfl-evidence` establishes what an external execution system actually observed.

---

## Contents

- [866. `rfl-evidence`](#866-rfl-evidence)
- [867. The fundamental model](#867-the-fundamental-model)
- [868. Artifact identity](#868-artifact-identity)
- [869. Artifact provenance](#869-artifact-provenance)
- [870. Execution request](#870-execution-request)
- [871. Execution observation](#871-execution-observation)
- [872. Evidence record](#872-evidence-record)
- [873. Evidence outcome](#873-evidence-outcome)
- [874. Evidence binding](#874-evidence-binding)
- [875. The forged-artifact attack](#875-the-forged-artifact-attack)
- [876. The stale-evidence attack](#876-the-stale-evidence-attack)
- [877. Environment is part of evidence](#877-environment-is-part-of-evidence)
- [878. Configuration coverage](#878-configuration-coverage)
- [879. Command identity](#879-command-identity)
- [880. Output identity](#880-output-identity)
- [881. Verification remains separate](#881-verification-remains-separate)
- [882. Contract/evidence relation](#882-contractevidence-relation)
- [883. Evidence completeness](#883-evidence-completeness)
- [884. Evidence completeness matrix](#884-evidence-completeness-matrix)
- [885. Independent verification](#885-independent-verification)
- [886. The self-generated evidence attack](#886-the-self-generated-evidence-attack)
- [887. Evidence provenance chain](#887-evidence-provenance-chain)
- [888. Evidence invalidation](#888-evidence-invalidation)
- [889. Evidence lifecycle](#889-evidence-lifecycle)
- [890. This exposes an important theorem](#890-this-exposes-an-important-theorem)
- [891. `rfl-evidence` therefore ends at facts](#891-rfl-evidence-therefore-ends-at-facts)
- [892. The complete architecture is becoming executable](#892-the-complete-architecture-is-becoming-executable)
- [893. Next: `rfl-gates`](#893-next-rfl-gates)

---

## 866. `rfl-evidence`
<!-- source: RFL-EVIDENCE.md §62 -->

```text
crates/rfl-evidence/
├── Cargo.toml
└── src/
    ├── lib.rs
    ├── record.rs
    ├── binding.rs
    ├── artifact.rs
    ├── execution.rs
    ├── environment.rs
    ├── toolchain.rs
    ├── outcome.rs
    ├── canonical.rs
    ├── validate.rs
    └── tests/
        ├── binding.rs
        ├── artifact.rs
        ├── execution.rs
        ├── environment.rs
        ├── adversarial.rs
        └── canonical.rs
```

Its dependency boundary:

```text
rfl-types
    ↓
rfl-evidence
```

It should not depend on:

- an LLM
- a semantic analyzer
- a Rust generator
- a specific CI provider
- GitHub
- Cargo
- clang
- the Linux kernel

Those are evidence producers.

## 867. The fundamental model
<!-- source: RFL-EVIDENCE.md §63 -->

We need four distinct objects:

```text
Artifact
   ↓
ExecutionRequest
   ↓
ExecutionObservation
   ↓
EvidenceRecord
```

And then:

```text
EvidenceRecord
       ↓
Verification
       ↓
VerificationResult
```

Do not skip the intermediate layers.

## 868. Artifact identity
<!-- source: RFL-EVIDENCE.md §64 -->

An artifact must have immutable identity.

```rust
pub struct ArtifactIdentity {
    pub id: ArtifactId,
    pub digest: Digest,
    pub kind: ArtifactKind,
}
```

Possible kinds:

```rust
pub enum ArtifactKind {
    SourceTree,
    SourceFile,
    RustCrate,
    Binary,
    KernelImage,
    Module,
    TestBundle,
    Patch,
    Documentation,
    EvidenceBundle,
}
```

The digest answers:

> Which exact bytes?

It does not answer:

> What do these bytes mean?

That semantic distinction remains important.

## 869. Artifact provenance
<!-- source: RFL-EVIDENCE.md §65 -->

Add:

```rust
pub enum ArtifactOrigin {
    Generated,
    HumanCreated,
    HumanModified,
    MechanicalTransform,
    Merge,
    CherryPick,
    Imported,
}
```

Then:

```rust
pub struct ArtifactRecord {
    pub identity: ArtifactIdentity,
    pub epoch: Epoch,
    pub origin: ArtifactOrigin,
    pub parents: Vec<ArtifactId>,
}
```

This connects directly to the AI-generation provenance architecture.

For example:

```text
C source
   │
   ▼
semantic analysis
   │
   ▼
AI-generated Rust
   │
   ▼
human modification
   │
   ▼
formatting
   │
   ▼
final artifact
```

Every transition should remain visible.

## 870. Execution request
<!-- source: RFL-EVIDENCE.md §66 -->

The execution system should receive a typed request.

```rust
pub struct ExecutionRequest {
    pub id: RequestId,
    pub epoch: Epoch,
    pub task: TaskId,
    pub artifact: ArtifactIdentity,

    pub executor: ExecutorId,

    pub input: InputSet,
    pub operation: ExecutionOperation,
}
```

For example:

```rust
pub enum ExecutionOperation {
    Build,
    UnitTest,
    KUnit,
    Kselftest,
    RuntimeTest,
    StaticAnalysis,
    DifferentialTest,
    ConcurrencyTest,
    AbiCheck,
}
```

Again:

```text
"make test"
```

is not the protocol-level semantic operation.

The adapter can translate:

```rust
ExecutionOperation::KUnit
```

into the actual commands required by a particular environment.

## 871. Execution observation
<!-- source: RFL-EVIDENCE.md §67 -->

The executor returns an observation:

```rust
pub struct ExecutionObservation {
    pub execution_id: ExecutionId,

    pub started_at: Timestamp,
    pub finished_at: Timestamp,

    pub exit_status: Option<i32>,

    pub stdout_digest: Digest,
    pub stderr_digest: Digest,

    pub output_artifacts: Vec<ArtifactIdentity>,

    pub environment: EnvironmentFingerprint,
    pub toolchain: ToolchainFingerprint,
}
```

Notice what is deliberately absent:

```text
verified = true
```

The executor reports observations.

It does not certify them.

## 872. Evidence record
<!-- source: RFL-EVIDENCE.md §68 -->

Now bind the observation to its subject.

```rust
pub struct EvidenceRecord {
    pub id: EvidenceId,

    pub epoch: Epoch,

    pub task: TaskId,
    pub subject: ArtifactId,

    pub execution: ExecutionId,
    pub executor: ExecutorId,

    pub command_digest: Digest,
    pub input_digest: Digest,

    pub output_digest: Digest,

    pub environment: EnvironmentFingerprint,
    pub toolchain: ToolchainFingerprint,

    pub outcome: EvidenceOutcome,
}
```

The important relationship is:

```text
Evidence
   │
   ├── epoch
   ├── task
   ├── artifact
   ├── execution
   ├── inputs
   ├── outputs
   ├── environment
   └── toolchain
```

Evidence without those bindings is weak evidence.

## 873. Evidence outcome
<!-- source: RFL-EVIDENCE.md §69 -->

Keep the outcome deliberately small:

```rust
pub enum EvidenceOutcome {
    Passed,
    Failed,
    Blocked,
    NotApplicable,
}
```

Again:

```text
Failed ≠ Blocked
```

A compiler error is not the same fact as:

```text
compiler unavailable
```

Likewise:

```text
test failed
```

is not:

```text
test never ran
```

## 874. Evidence binding
<!-- source: RFL-EVIDENCE.md §70 -->

This becomes one of the central functions:

```rust
pub fn validate_binding(
    evidence: &EvidenceRecord,
    artifact: &ArtifactRecord,
    execution: &ExecutionObservation,
) -> Result<(), EvidenceError>
```

It should establish:

```text
evidence.subject == artifact.identity.id
```

and:

```text
evidence.execution == execution.execution_id
```

and:

```text
evidence.epoch == artifact.epoch
```

and:

```text
evidence.output_digest
    matches execution outputs
```

and equivalent checks for input/environment/toolchain.

## 875. The forged-artifact attack
<!-- source: RFL-EVIDENCE.md §71 -->

Consider:

```text
Artifact A
    digest = AAA

execute A

Evidence claims:
    subject = Artifact B
    digest = BBB
```

The evidence must be rejected.

```text
Artifact mismatch
        ↓
EvidenceUnbound
```

This sounds obvious, but it is one of the most important boundaries in the whole architecture.

A test result is meaningless if we cannot establish **what was tested**.

## 876. The stale-evidence attack
<!-- source: RFL-EVIDENCE.md §72 -->

Consider:

```text
Artifact A Epoch E10
   ↓
tested
   ↓
PASS

Artifact A Epoch E11
   ↓
source changed
```

Even if the artifact name is unchanged:

```text
old evidence ≠ current evidence
```

because:

```text
E10 != E11
```

The protocol should reject reuse unless an explicit derivation establishes that the old evidence remains applicable.

Default:

```text
epoch mismatch
    → evidence unusable
```

## 877. Environment is part of evidence
<!-- source: RFL-EVIDENCE.md §73 -->

For kernel migration this is essential.

A result may depend on:

```text
compiler
Rust version
LLVM version
clang version
architecture
configuration
kernel tree
host OS
target architecture
feature flags
environment variables
tool versions
```

So:

```rust
pub struct EnvironmentFingerprint {
    pub digest: Digest,
}
```

and:

```rust
pub struct ToolchainFingerprint {
    pub digest: Digest,
}
```

can initially be opaque canonical fingerprints.

Later they can be decomposed.

The first protocol should not prematurely encode every tool.

## 878. Configuration coverage
<!-- source: RFL-EVIDENCE.md §74 -->

This connects directly to semantic verification.

Suppose:

```text
x86_64 + CONFIG_A
```

passes.

That does not establish:

```text
ARM64 + CONFIG_B
```

passes.

Therefore evidence needs scope:

```text
Evidence
    ↓
configuration
    ↓
architecture
    ↓
toolchain
    ↓
artifact
```

Then RFL-AE can later calculate:

```text
ConfigurationCoverage
ArchitectureCoverage
```

without pretending that one successful build proves universal correctness.

## 879. Command identity
<!-- source: RFL-EVIDENCE.md §75 -->

A command must also be bound.

Do not merely store:

```text
command = "cargo test"
```

as free text.

Store a canonical execution specification and its digest:

```rust
pub struct ExecutionSpec {
    pub operation: ExecutionOperation,
    pub arguments: Vec<String>,
    pub working_scope: Scope,
}
```

Then:

```text
command_digest = H(canonical(ExecutionSpec))
```

This lets evidence establish:

> This exact operation was executed.

Not merely:

> Something called a test was run.

## 880. Output identity
<!-- source: RFL-EVIDENCE.md §76 -->

Likewise, stdout is not the artifact.

For a build:

```text
source artifact
       ↓
compiler
       ↓
binary artifact
```

Evidence should bind to the resulting binary:

```text
output_artifacts = [
    ArtifactIdentity(binary_digest)
]
```

Then:

```text
build passed
```

means:

```text
this exact input → this exact toolchain → this exact execution → this exact output → produced this observed outcome
```

That is substantially stronger.

## 881. Verification remains separate
<!-- source: RFL-EVIDENCE.md §77 -->

Now we can define:

```rust
pub struct VerificationResult {
    pub artifact: ArtifactId,
    pub contract: ContractId,
    pub evidence: Vec<EvidenceId>,
    pub method: VerificationMethod,
    pub status: VerificationStatus,
}
```

For example:

```text
Artifact A
   │
   ├── Evidence E1: build passed
   ├── Evidence E2: KUnit passed
   ├── Evidence E3: differential test passed
   │
   ▼
Verification
   │
   └── Contract C17
          ↓
      Verified
```

The verification layer is where evidence is interpreted against a contract.

Evidence alone does not know what constitutes success.

## 882. Contract/evidence relation
<!-- source: RFL-EVIDENCE.md §78 -->

This gives us a useful formal distinction:

```math
Evidence(E)
```

means:

> a bounded observation exists.

Whereas:

```math
Satisfies(E,C)
```

means:

> the evidence is relevant and sufficient to establish contract `C`.

And:

```math
Verified(A,C)
```

means:

> artifact `A` satisfies contract `C` under the declared verification method and evidence.

So:

```text
Evidence
   ≠ Contract satisfaction
   ≠ Verification
```

## 883. Evidence completeness
<!-- source: RFL-EVIDENCE.md §79 -->

A verification system should also be able to say:

```rust
EvidenceStatus::Incomplete
```

rather than manufacture a failure.

For example:

```text
Required:
    build
    KUnit
    ABI
    differential

Observed:
    build
    KUnit
```

Correct result:

```text
Verification = Blocked
```

not:

```text
Verification = Failed
```

because ABI and differential tests were never executed.

This distinction will matter enormously for the final gate.

## 884. Evidence completeness matrix
<!-- source: RFL-EVIDENCE.md §80 -->

We can formalize:

| Required evidence | Available | Result    |
|-------------------|-----------|-----------|
| Build             | yes       | available |
| KUnit             | yes       | available |
| ABI               | no        | missing   |
| Differential      | no        | missing   |

Then:

```text
verification:
    BLOCKED
```

because required evidence is absent.

This is exactly the architecture's principle:

```text
NO EVIDENCE
    → NO VERIFIED CLAIM
```

## 885. Independent verification
<!-- source: RFL-EVIDENCE.md §81 -->

Evidence should identify the executor:

```rust
pub struct ExecutorIdentity {
    pub id: ExecutorId,
    pub kind: ExecutorKind,
}
```

For example:

```rust
pub enum ExecutorKind {
    Human,
    CiRunner,
    BuildSystem,
    TestHarness,
    VerificationService,
}
```

An LLM agent should not be treated as an execution authority merely because it generated a plausible transcript.

## 886. The self-generated evidence attack
<!-- source: RFL-EVIDENCE.md §82 -->

Attack:

```text
Agent:
    generated artifact

Agent:
    generated "test result"

Agent:
    generated evidence record

Agent:
    declares verification
```

The protocol must require a real execution observation.

Therefore:

```text
EvidenceRecord
    requires ExecutionObservation
```

and:

```text
ExecutionObservation
    requires registered Executor
```

The agent cannot simply instantiate an authoritative executor identity.

## 887. Evidence provenance chain
<!-- source: RFL-EVIDENCE.md §83 -->

We can now create:

```text
Artifact
   │
   │ digest
   ▼
ExecutionRequest
   │
   │ authorization
   ▼
ExecutionObservation
   │
   │ output
   ▼
EvidenceRecord
   │
   │ contract interpretation
   ▼
VerificationResult
   │
   ▼
GateResult
```

This is the complete fact-to-decision chain.

## 888. Evidence invalidation
<!-- source: RFL-EVIDENCE.md §84 -->

Evidence must be invalidatable without rewriting history.

Example:

```text
E100:
    Build passed

E101:
    Toolchain fingerprint discovered corrupt

E102:
    E100 invalidated
```

History still says:

```text
E100 occurred
```

Current truth says:

```text
E100 is no longer admissible evidence
```

This is why:

```text
history ≠ current validity
```

must remain explicit.

## 889. Evidence lifecycle
<!-- source: RFL-EVIDENCE.md §85 -->

```text
Collected
    ↓
Bound
    ↓
Validated
    ↓
Available
    ↓
Used by verification
    ↓
May become invalidated
```

Potential statuses:

```rust
pub enum EvidenceValidity {
    Unvalidated,
    Valid,
    Invalid,
    Superseded,
}
```

Keep this separate from outcome:

```text
Outcome:
    Passed

Validity:
    Invalid
```

is perfectly coherent.

A test may genuinely have passed while the evidence later becomes unusable because its artifact binding was discovered to be wrong.

## 890. This exposes an important theorem
<!-- source: RFL-EVIDENCE.md §86 -->

A successful execution does not imply a valid certification.

Formally:

```text
ExecutionSuccess
    ↛ EvidenceValid
    ↛ ContractSatisfied
    ↛ Verified
    ↛ Certified
```

The arrows require additional relations.

This is one of the central protections against **verification theater**.

## 891. `rfl-evidence` therefore ends at facts
<!-- source: RFL-EVIDENCE.md §87 -->

The crate should not contain:

```rust
pub fn certify(...)
```

It should expose:

```rust
pub fn validate_binding(...)
pub fn validate_integrity(...)
pub fn validate_scope(...)
pub fn validate_epoch(...)
pub fn validate_executor(...)
```

and construct validated evidence.

Certification belongs later.

## 892. The complete architecture is becoming executable
<!-- source: RFL-EVIDENCE.md §88 -->

We now have:

```text
                 HUMAN AUTHORITY
                        │
                        ▼
                 POLICY / SCOPE
                        │
                        ▼
              ┌──────────────────┐
              │   RFL-TYPES      │
              └─────────┬────────┘
                        ▼
              ┌──────────────────┐
              │ RFL-TRANSITION   │
              └─────────┬────────┘
                        ▼
              ┌──────────────────┐
              │   RFL-LEDGER     │
              └─────────┬────────┘
                        ▼
              ┌──────────────────┐
              │  RFL-EVIDENCE    │
              └─────────┬────────┘
                        ▼
              ┌──────────────────┐
              │   VERIFICATION   │
              └─────────┬────────┘
                        ▼
              ┌──────────────────┐
              │    RFL-GATES     │
              └─────────┬────────┘
                        ▼
                   CERTIFICATE
```

And only after this kernel is stable should the semantic machinery become a client:

```text
C source
   ↓
C analyzers
   ↓
KSIR
   ↓
Contracts
   ↓
Rust Design IR
   ↓
Rust generator
   ↓
RFL protocol
```

The agents remain outside the authority boundary.

## 893. Next: `rfl-gates`
<!-- source: RFL-EVIDENCE.md §89 -->

The remaining kernel problem is now:

> Given verified evidence and dependencies, under what exact conditions may RFL-AE derive `TechnicalCertification`?

That should **not** be a boolean `ready`.

We need a gate algebra that preserves:

```text
PASS
FAIL
BLOCKED
NOT_APPLICABLE
INVALIDATED
```

and distinguishes:

```text
required gate
optional gate
conditional gate
dependency gate
evidence-completeness gate
scope gate
provenance gate
semantic-contract gate
```

The next step is therefore to formalize **`rfl-gates` and the certification predicate**, including the critical rule:

```text
BLOCKED required gate
        ≠ FAILED required gate

but both
        ⇒ NOT CERTIFIABLE
```

Then we can connect the executable kernel to the **MigrationUnit → KSIR → Contract → Rust Design IR** pipeline without letting the semantic agents bypass the authority machinery.
