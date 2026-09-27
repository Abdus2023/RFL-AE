# RFL-AE — Execution & Evidence Runtime

> **Provenance and numbering.** This document was supplied as *RFL-AE — Execution & Evidence Runtime v0.1*, numbered §1–§44 in the source. To keep the corpus contiguous, its sections are renumbered **§419–§462**, continuing directly from [GATES.md](GATES.md) (which ends at §418). The mapping is **`corpus_section = source_section + 418`**. The original source numbering is preserved on every heading as a machine-readable HTML comment of the form `<!-- source: EXECUTION.md §n -->`, so source traceability is lossless and either numbering can be used to locate a clause.

> **Execution Runtime — authorized execution, exact evidence, immutable provenance**

---

## Contents

- [419. Purpose](#419-purpose)
- [420. The Problem: Execution Without Evidence](#420-the-problem-execution-without-evidence)
- [421. Execution Is Not Just Running a Command](#421-execution-is-not-just-running-a-command)
- [422. Execution Trust Chain](#422-execution-trust-chain)
- [423. Execution Request](#423-execution-request)
- [424. Capability-Based Authorization](#424-capability-based-authorization)
- [425. Scope Binding](#425-scope-binding)
- [426. Command Specification](#426-command-specification)
- [427. Executable Identity](#427-executable-identity)
- [428. Environment Specification](#428-environment-specification)
- [429. Worktree Isolation](#429-worktree-isolation)
- [430. Network Policy](#430-network-policy)
- [431. Execution Lifecycle](#431-execution-lifecycle)
- [432. Execution Status](#432-execution-status)
- [433. Process Outcome](#433-process-outcome)
- [434. Evidence Status](#434-evidence-status)
- [435. Execution Receipt](#435-execution-receipt)
- [436. Execution Artifacts](#436-execution-artifacts)
- [437. Artifact Roles](#437-artifact-roles)
- [438. Immutable Evidence](#438-immutable-evidence)
- [439. Evidence Record](#439-evidence-record)
- [440. Evidence Binder](#440-evidence-binder)
- [441. Evidence Graph](#441-evidence-graph)
- [442. Reverse Provenance](#442-reverse-provenance)
- [443. Replay Support](#443-replay-support)
- [444. Reproducibility Tiers](#444-reproducibility-tiers)
- [445. Nondeterminism Classification](#445-nondeterminism-classification)
- [446. Tool Receipts](#446-tool-receipts)
- [447. Tool Capability Registry](#447-tool-capability-registry)
- [448. Execution Authority vs Semantic Authority](#448-execution-authority-vs-semantic-authority)
- [449. Execution Failures](#449-execution-failures)
- [450. Security Boundary](#450-security-boundary)
- [451. Receipt Signing](#451-receipt-signing)
- [452. Evidence Strength](#452-evidence-strength)
- [453. Evidence Independence](#453-evidence-independence)
- [454. Execution Provenance](#454-execution-provenance)
- [455. Execution Runtime Structure](#455-execution-runtime-structure)
- [456. Acceptance Criteria](#456-acceptance-criteria)
- [457. First Vertical Slice](#457-first-vertical-slice)
- [458. Execution Runtime Adversarial Review](#458-execution-runtime-adversarial-review)
- [459. Execution Trust Theorem](#459-execution-trust-theorem)
- [460. Evidence Loop Closure](#460-evidence-loop-closure)
- [461. Architectural Completeness](#461-architectural-completeness)
- [462. Next Artifact: Orchestrator](#462-next-artifact-orchestrator)

---

## 419. Purpose
<!-- source: EXECUTION.md §1 -->

The Execution Runtime turns an authorized migration action into a reproducible, evidence-producing execution. It guarantees that:

```text
AUTHORIZED REQUEST
         ↓
EXACT EXECUTION
         ↓
CAPTURED OBSERVATION
         ↓
IMMUTABLE RECEIPT
         ↓
EVIDENCE RECORD
```

This is the missing trust boundary. Everything above assumes that an execution receipt is trustworthy.

Without it:

```text
NO EXECUTION RECEIPT
         ↓
NO EXECUTION CLAIM
```

and:

```text
NO BINDING BETWEEN RECEIPT AND ARTIFACT
                    ↓
NO EVIDENCE
```

---

## 420. The Problem: Execution Without Evidence
<!-- source: EXECUTION.md §2 -->

A test may pass on one agent and fail on another without explanation. A migration may be approved based on logs nobody can reconstruct. An LLM may say:

```text
"I executed the test"
```

But what exactly was executed? Against what source? In what environment? With what command? Against what binary? Where are the outputs? Can it be reproduced? Was the receipt bound to the artifacts? Without those, verification is theater.

---

## 421. Execution Is Not Just Running a Command
<!-- source: EXECUTION.md §3 -->

Execution means:

- authorized command
- exact binary/source/tool identity
- isolated environment
- bounded resources
- captured stdout/stderr
- artifact digests
- deterministic receipt
- append-only evidence record
- replay support
- independent verification hooks

---

## 422. Execution Trust Chain
<!-- source: EXECUTION.md §4 -->

```text
                         AGENT
                           │
                           ▼
                   Execution Request
                           │
                           ▼
                  Authorization Layer
                           │
                    ┌──────┴──────┐
                    │             │
                  ALLOW         DENY
                    │             │
                    ▼             ▼
                 Runtime       Ledger
                    │
                    ▼
            Isolated Context
                    │
                    ▼
                Executor
                    │
                    ▼
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
         stdout         stderr        artifacts
            │              │              │
            └──────────────┼──────────────┘
                           │
                           ▼
                    Observation Set
                           │
                           ▼
                   Execution Receipt
                           │
                           ▼
                    Evidence Binder
                           │
                           ▼
                    Evidence Ledger
```

Every stage produces typed evidence.

---

## 423. Execution Request
<!-- source: EXECUTION.md §5 -->

```rust
pub struct ExecutionRequest {
    pub request_id: RequestId,
    pub migration_unit: MigrationUnitId,
    pub requested_by: AgentId,
    pub authorization: CapabilityGrant,
    pub snapshot: SnapshotId,
    pub variant: VariantId,
    pub command: CommandSpec,
    pub environment: EnvironmentSpec,
    pub resource_limits: ResourceLimits,
    pub network_policy: NetworkPolicy,
    pub artifacts_policy: ArtifactPolicy,
    pub evidence_policy: EvidencePolicy,
    pub replay_policy: ReplayPolicy,
    pub timeout: Timeout,
    pub created_at: Timestamp,
}
```

The command is part of the signed/hashed request identity.

If the command changes:

```text
cargo test
```

→

```text
cargo test --features experimental
```

it is a different request.

---

## 424. Capability-Based Authorization
<!-- source: EXECUTION.md §6 -->

Authorization is not:

```text
Agent X is trusted
```

It is:

```text
Agent X may execute this class of command
in this scope
with these resources
under these constraints
until this epoch expires
```

```text
Agent
       ↓
Capability
       ↓
Scope
       ↓
Authorization
       ↓
Execution
```

```rust
pub struct ExecutionCapability {
    pub principal: AgentId,
    pub permitted_actions: Vec<ActionClass>,
    pub snapshot_scope: SnapshotScope,
    pub unit_scope: UnitScope,
    pub repo_scope: RepoScope,
    pub branch_scope: BranchScope,
    pub tool_scope: ToolScope,
    pub resource_limits: ResourceLimits,
    pub network_policy: NetworkPolicy,
    pub epoch: Epoch,
    pub expiry: Option<Timestamp>,
}
```

Without scope binding:

```text
grant to run tests on MU-001
```

could be reused for:

```text
running arbitrary builds on MU-002
```

---

## 425. Scope Binding
<!-- source: EXECUTION.md §7 -->

Each execution request must satisfy:

```rust
authorize(request) -> AuthorizationDecision
```

It must bind:

- snapshot
- migration unit
- repo
- branch
- tool identity
- resource limits
- epoch
- capability expiry

If any mismatch:

```rust
ScopeViolation
```

---

## 426. Command Specification
<!-- source: EXECUTION.md §8 -->

```rust
pub struct CommandSpec {
    pub tool: ExecutableIdentity,
    pub argv: Vec<Arg>,
    pub cwd: WorkdirRef,
    pub env: EnvironmentSpec,
    pub input_manifest: Manifest,
    pub declared_outputs: Vec<OutputSpec>,
    pub determinism: DeterminismClass,
}
```

The command must be canonicalized before hashing.

---

## 427. Executable Identity
<!-- source: EXECUTION.md §9 -->

```rust
pub struct ExecutableIdentity {
    pub name: ToolName,
    pub version: ToolVersion,
    pub digest: Digest,
    pub source: ToolSource,
    pub capability_class: ToolCapabilityClass,
}
```

Without executable digests:

```text
"rustc was run"
```

could hide:

```text
a different rustc
```

---

## 428. Environment Specification
<!-- source: EXECUTION.md §10 -->

```rust
pub struct EnvironmentFingerprint {
    pub os: OsIdentity,
    pub kernel: KernelIdentity,
    pub toolchain: ToolchainDigest,
    pub container: ContainerDigest,
    pub env_vars: BTreeMap<String, EnvRole>,
    pub locale: Locale,
    pub timezone: Timezone,
    pub filesystem: FsIdentity,
    pub network: NetworkIdentity,
}
```

Each variable has a role:

```rust
pub enum EnvironmentRole {
    SemanticInput,
    ReproducibilityInput,
    DiagnosticOnly,
    SecretRedacted,
    Irrelevant,
}
```

Otherwise irrelevant env vars destabilize evidence digests.

---

## 429. Worktree Isolation
<!-- source: EXECUTION.md §11 -->

Execution must occur in an isolated worktree:

```text
/workspaces/
└── MU-004821/
    ├── source/
    ├── build/
    ├── inputs/
    ├── outputs/
    ├── logs/
    └── receipt/
```

This prevents cross-unit contamination.

---

## 430. Network Policy
<!-- source: EXECUTION.md §12 -->

Default:

```text
NETWORK = DENY
```

Only explicitly allowed operations:

```rust
pub enum NetworkPolicy {
    Deny,
    Allowlist { endpoints: Vec<Endpoint>, reasons: Vec<Reason> },
    Proxied { registry: RegistryId },
}
```

Network access becomes evidence:

```rust
pub struct NetworkAccessLog {
    pub execution: ExecutionId,
    pub endpoint: Endpoint,
    pub policy_decision: Decision,
    pub timestamp: Timestamp,
}
```

---

## 431. Execution Lifecycle
<!-- source: EXECUTION.md §13 -->

```text
REQUESTED
    ▼
VALIDATING
    │
    ├── INVALID → REJECTED
    │
    ▼
AUTHORIZED
    ▼
MATERIALIZING
    ▼
READY
    ▼
EXECUTING
    │
    ├── timeout
    ├── resource violation
    ├── executor failure
    └── process failure
    │
    ▼
CAPTURING
    ▼
FINALIZING
    ▼
RECEIPT_CREATED
    ▼
EVIDENCE_BOUND
```

---

## 432. Execution Status
<!-- source: EXECUTION.md §14 -->

```rust
pub enum ExecutionStatus {
    Requested,
    Authorized,
    Materializing,
    Executing,
    Capturing,
    Completed,
    Failed,
    TimedOut,
    ViolatedPolicy,
    Inconclusive,
    Replayed,
}
```

---

## 433. Process Outcome
<!-- source: EXECUTION.md §15 -->

```rust
pub struct ProcessOutcome {
    pub exit_code: Option<i32>,
    pub signal: Option<i32>,
    pub wall_time: Duration,
    pub cpu_time: Duration,
    pub max_rss: Option<Bytes>,
    pub oom: bool,
    pub timeout: bool,
}
```

Important distinction:

```text
exit code 101
```

does **not** mean:

```text
verification obligation failed
```

It may mean:

```text
test process crashed
capture failed
harness broken
```

---

## 434. Evidence Status
<!-- source: EXECUTION.md §16 -->

```rust
pub enum EvidenceStatus {
    Captured,
    Bound,
    Reproducible,
    PartiallyReproducible,
    NonReproducible,
    Invalidated,
    Superseded,
}
```

Execution success ≠ verification success. Verification success ≠ migration approval.

---

## 435. Execution Receipt
<!-- source: EXECUTION.md §17 -->

```rust
pub struct ExecutionReceipt {
    pub receipt_id: ReceiptId,
    pub request: ExecutionRequest,
    pub authorization: AuthorizationDecision,
    pub environment: EnvironmentFingerprint,
    pub tool: ExecutableIdentity,
    pub inputs: InputManifest,
    pub outputs: Vec<ArtifactRef>,
    pub stdout: ArtifactRef,
    pub stderr: ArtifactRef,
    pub process_outcome: ProcessOutcome,
    pub timing: ExecutionTiming,
    pub resource_usage: ResourceUsage,
    pub network_log: Vec<NetworkAccessLog>,
    pub policy_violations: Vec<PolicyViolation>,
    pub receipt_digest: Digest,
    pub created_at: Timestamp,
}
```

The receipt must be canonicalized before digesting.

```text
receipt_digest = digest(canonicalize(receipt))
```

No unordered map ambiguity.

---

## 436. Execution Artifacts
<!-- source: EXECUTION.md §18 -->

```rust
pub struct ExecutionArtifact {
    pub artifact_id: ArtifactId,
    pub role: ArtifactRole,
    pub path: RelativePath,
    pub digest: Digest,
    pub size: u64,
    pub content_type: ContentType,
    pub produced_by: ExecutionId,
    pub bound_to_receipt: ReceiptId,
    pub retention: RetentionPolicy,
    pub redaction: RedactionStatus,
}
```

stdout/stderr are artifacts, not ephemeral logs.

---

## 437. Artifact Roles
<!-- source: EXECUTION.md §19 -->

```rust
pub enum ArtifactRole {
    Stdout,
    Stderr,
    ObjectFile,
    TestBinary,
    CoverageData,
    SanitizerReport,
    DiffReport,
    ProofLog,
    CompilerOutput,
    CoccinelleLog,
    ReplayInput,
    ReplayOutput,
    EvidenceAttachment,
}
```

Without this, "the test printed PASS" becomes untraceable.

---

## 438. Immutable Evidence
<!-- source: EXECUTION.md §20 -->

Once created:

```text
receipt.digest
artifact.digest
evidence_record.id
```

are immutable.

Corrections create:

```text
new artifacts
new receipts
new evidence records
```

and invalidate old ones through dependency rules — never by silent overwrite.

Forbidden:

```text
overwrite evidence.json
```

Required:

```text
append new version
link supersedes
update ledger dependencies
```

---

## 439. Evidence Record
<!-- source: EXECUTION.md §21 -->

```rust
pub struct EvidenceRecord {
    pub evidence_id: EvidenceId,
    pub receipt: ReceiptId,
    pub artifacts: Vec<ArtifactId>,
    pub observations: Vec<Observation>,
    pub interpretations: Vec<Interpretation>,
    pub verification_links: Vec<VerificationResultId>,
    pub gate_links: Vec<GateResultId>,
    pub status: EvidenceStatus,
    pub supersedes: Option<EvidenceId>,
    pub superseded_by: Option<EvidenceId>,
    pub created_at: Timestamp,
}
```

Execution records observation, not meaning.

```rust
Observation {
    "test process exited 0"
}
```

not:

```rust
Interpretation {
    "the test oracle accepted proposition P"
}
```

The latter belongs to the verification layer.

---

## 440. Evidence Binder
<!-- source: EXECUTION.md §22 -->

```rust
bind_evidence(receipt, artifacts) -> EvidenceBinding
```

It must verify:

- receipt digest
- artifact digests
- tool identity
- input manifest
- output manifest
- environment fingerprint
- network policy compliance
- authorization scope
- migration unit binding
- snapshot binding

If any mismatch:

```rust
BindingStatus::Invalid(reason)
```

```rust
pub enum BindingStatus {
    Valid,
    Partial { missing: Vec<MissingLink> },
    Invalid { reason: BindingFailure },
    Unbound,
}
```

Without binding, execution is just an activity.

---

## 441. Evidence Graph
<!-- source: EXECUTION.md §23 -->

```text
              Execution Request
                      │
                      ▼
                Authorization
                      │
                      ▼
                   Receipt
              ┌───────┼───────┐
              ▼       ▼       ▼
           stdout  stderr  outputs
              │       │       │
              └───────┼───────┘
                      │
                      ▼
                 Observation
                      │
                      ▼
               EvidenceRecord
            ┌─────────┼───────────┐
            ▼         ▼           ▼
          KSIR    Contract  Verification
                                  │
                                  ▼
                                Gate
```

---

## 442. Reverse Provenance
<!-- source: EXECUTION.md §24 -->

The runtime must answer:

```text
Why did this gate fail?
```

by walking backward:

```text
Release Gate
    ↓
G-ADVERSARIAL-002 FAIL
    ↓
VO-004821-RCU-007 FAIL
    ↓
Counterexample CE-91
    ↓
Execution EX-774
    ↓
Receipt R-774
    ↓
Binary digest
    ↓
Implementation commit
    ↓
Design obligation
    ↓
Contract invariant
    ↓
KSIR fact
    ↓
source evidence
```

---

## 443. Replay Support
<!-- source: EXECUTION.md §25 -->

```rust
pub struct ReplayManifest {
    pub replay_id: ReplayId,
    pub original_receipt: ReceiptId,
    pub snapshot: SnapshotId,
    pub variant: VariantId,
    pub tool: ExecutableIdentity,
    pub inputs: InputManifest,
    pub environment: EnvironmentFingerprint,
    pub command: CommandSpec,
    pub expected_outputs: Vec<ArtifactDigest>,
}
```

```text
Receipt
   ↓
Replay Manifest
   ↓
Materialize exact inputs
   ↓
Reconstruct environment
   ↓
Execute
   ↓
Compare outputs
```

---

## 444. Reproducibility Tiers
<!-- source: EXECUTION.md §26 -->

```rust
pub enum ReproducibilityTier {
    Exact,
    SemanticallyEquivalent,
    PartiallyReproducible,
    NonDeterministic,
    Unavailable,
}
```

```rust
pub struct ReplayResult {
    pub original_digests: Vec<Digest>,
    pub replay_digests: Vec<Digest>,
    pub matching: Vec<ArtifactId>,
    pub divergent: Vec<ArtifactId>,
    pub divergence_reasons: Vec<DivergenceReason>,
    pub tier: ReproducibilityTier,
}
```

These are evidence properties, not confidence scores.

---

## 445. Nondeterminism Classification
<!-- source: EXECUTION.md §27 -->

```rust
pub enum NondeterminismClass {
    None,
    Timestamps,
    Paths,
    HashSeeds,
    Concurrency,
    Network,
    Toolchain,
    Hardware,
    Unknown,
}
```

Uncontrolled nondeterminism limits what can be claimed but does not invalidate execution.

---

## 446. Tool Receipts
<!-- source: EXECUTION.md §28 -->

Each tool invocation gets its own receipt:

```rust
pub struct ToolReceipt {
    pub tool: ExecutableIdentity,
    pub invocation: CommandSpec,
    pub inputs: InputManifest,
    pub outputs: Vec<ArtifactRef>,
    pub exit_status: ProcessOutcome,
    pub runtime_environment: EnvironmentFingerprint,
    pub receipt_digest: Digest,
}
```

Examples:

- Coccinelle log
- smatch invocation
- rustc invocation
- KUnit harness
- fuzzer corpus state

---

## 447. Tool Capability Registry
<!-- source: EXECUTION.md §29 -->

```rust
pub enum ToolCapabilityClass {
    Transformational,
    Analytical,
    Observational,
    Inferential,
    Untrusted,
}
```

Example:

```text
Coccinelle = OBSERVATIONAL/TRANSFORMATIONAL, cannot establish complete ownership semantics
```

The runtime records capability class so downstream verification cannot overinterpret tool output.

---

## 448. Execution Authority vs Semantic Authority
<!-- source: EXECUTION.md §30 -->

The Execution Runtime is authority over:

```text
what actually executed
```

The Verification IR, KSIR, and Contract layer are authority over:

```text
what it means
```

The Gate Engine is authority over:

```text
whether requirements are satisfied
```

No layer may impersonate another.

---

## 449. Execution Failures
<!-- source: EXECUTION.md §31 -->

```rust
pub enum ExecutionFailure {
    AuthorizationDenied,
    ScopeViolation,
    ToolMissing,
    ToolDigestMismatch,
    InputMissing,
    InputDigestMismatch,
    SandboxViolation,
    NetworkViolation,
    ResourceExceeded,
    Timeout,
    Crash,
    CaptureFailure,
    ArtifactWriteFailure,
    ReceiptSealFailure,
    EvidenceBindingFailure,
    ReplayUnavailable,
    Unknown,
}
```

Critical distinction:

```text
exit code 0 does not mean obligation verified
exit code 101 does not mean verification failed
```

---

## 450. Security Boundary
<!-- source: EXECUTION.md §32 -->

```text
UNTRUSTED AGENT
       ↓
REQUEST VALIDATOR
       ↓
CAPABILITY CHECK
       ↓
SANDBOX
       ↓
EXECUTOR
       ↓
ARTIFACT STORE
```

The runtime must assume:

- agents may be compromised
- inputs may be malicious
- generated code may attempt privilege escalation
- network access may leak data
- artifacts may be tampered with

---

## 451. Receipt Signing
<!-- source: EXECUTION.md §33 -->

```text
receipt
     ↓
canonical encoding
     ↓
digest
     ↓
executor signature
```

```rust
pub struct SignedReceipt {
    pub receipt: ExecutionReceipt,
    pub signer: ExecutorIdentity,
    pub signature: Signature,
    pub signing_epoch: Epoch,
}
```

Signing proves:

```text
the execution authority attests to this recorded execution
```

not:

```text
the executed command was semantically correct
```

---

## 452. Evidence Strength
<!-- source: EXECUTION.md §34 -->

```rust
pub enum EvidenceStrength {
    DirectExecutable,
    DifferentialAgainstBaseline,
    SanitizerBacked,
    ProofAssistantBacked,
    PatternOnly,
    Inferential,
    Insufficient,
}
```

The runtime records strength class — never a numeric confidence.

---

## 453. Evidence Independence
<!-- source: EXECUTION.md §35 -->

```rust
pub struct EvidenceIndependence {
    pub generator: AgentId,
    pub executor: AgentId,
    pub verifier: AgentId,
    pub interpreter: AgentId,
    pub independence_class: IndependenceClass,
    pub conflicts: Vec<IndependenceConflict>,
}
```

```text
                   Implementation Agent
                             │
                             ▼
                         Rust code
                             │
                             ▼
             Independent Verification Runtime
                             │
                             ├── compiler
                             ├── sanitizer
                             ├── differential harness
                             └── adversarial mutation
                             │
                             ▼
                   Independent Evidence
```

Bad independence:

```text
same LLM generates hypothesis → same LLM writes test → same LLM evaluates result
```

This must be detectable structurally.

---

## 454. Execution Provenance
<!-- source: EXECUTION.md §36 -->

```text
         Authorization
               │
               ▼
       Execution Request
               │
     ├────────── Snapshot
     ├────────── Variant
     ├────────── Inputs
     ├────────── Tool
     └────────── Command
               │
               ▼
           Execution
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
 stdout     stderr    artifacts
    │          │          │
    └──────────┼──────────┘
               │
               ▼
            Receipt
               │
               ▼
          Observation
               │
               ▼
           Evidence
               │
               ▼
      Verification Result
               │
               ▼
             Gate
```

Every downstream decision can be traced back to exact execution facts.

---

## 455. Execution Runtime Structure
<!-- source: EXECUTION.md §37 -->

```text
crates/
├── rfl-execution-types/
│   ├── request.rs
│   ├── command.rs
│   ├── environment.rs
│   ├── receipt.rs
│   └── failure.rs
├── rfl-capability/
│   ├── capability.rs
│   ├── authorization.rs
│   ├── scope.rs
│   └── validator.rs
├── rfl-workspace/
│   ├── isolation.rs
│   ├── materialize.rs
│   └── cleanup.rs
├── rfl-executor/
│   ├── process.rs
│   ├── sandbox.rs
│   ├── limits.rs
│   └── network.rs
├── rfl-artifacts/
│   ├── store.rs
│   ├── digest.rs
│   ├── manifest.rs
│   └── capture.rs
├── rfl-receipts/
│   ├── canonical.rs
│   ├── digest.rs
│   ├── sign.rs
│   └── verify.rs
├── rfl-evidence-ledger/
│   ├── record.rs
│   ├── append.rs
│   ├── invalidate.rs
│   ├── dependency.rs
│   └── query.rs
└── rfl-replay/
    ├── manifest.rs
    ├── materialize.rs
    ├── execute.rs
    └── compare.rs
```

---

## 456. Acceptance Criteria
<!-- source: EXECUTION.md §38 -->

The execution runtime is acceptable only if it enforces:

```text
EXE-001  every execution requires an authorized request
EXE-002  command, environment, and tool identity are digest-bound
EXE-003  snapshot, variant, and inputs are manifest-bound
EXE-004  isolated worktree prevents cross-unit contamination
EXE-005  network defaults to deny and every access is logged
EXE-006  process outcome and verification meaning remain separate
EXE-007  stdout/stderr/artifacts become digested evidence
EXE-008  receipts are canonical, digest-bound, and immutable
EXE-009  evidence binding is explicit and validated
EXE-010  ledger is append-only; invalidation supersedes, never deletes
EXE-011  replay manifest supports controlled reproduction
EXE-012  nondeterminism is classified, not hidden
EXE-013  tool capability class prevents overinterpretation
EXE-014  evidence independence is structurally represented
EXE-015  reverse provenance walks from gate to source evidence
```

---

## 457. First Vertical Slice
<!-- source: EXECUTION.md §39 -->

```text
RFL-EXEC-LAB-001
```

```text
Authorized task
      ↓
exact Linux snapshot
      ↓
isolated worktree
      ↓
rustc/cargo invocation
      ↓
capture stdout/stderr
      ↓
capture binary/test artifacts
      ↓
execution receipt
      ↓
artifact digest
      ↓
evidence record
      ↓
verification result
      ↓
single gate
      ↓
certificate
```

Then deliberately corrupt:

```text
input digest
receipt
artifact
snapshot
authorization
```

and prove rejection.

---

## 458. Execution Runtime Adversarial Review
<!-- source: EXECUTION.md §40 -->

```text
EXE-QA-001  can an agent execute without capability?
EXE-QA-002  can a grant leak across units?
EXE-QA-003  can a tool binary be swapped silently?
EXE-QA-004  can env vars alter digest stability?
EXE-QA-005  can outputs be rewritten post hoc?
EXE-QA-006  can receipt and artifacts diverge undetected?
EXE-QA-007  can nondeterminism masquerade as success?
EXE-QA-008  can replay silently drift?
EXE-QA-009  can stdout logs substitute for artifacts?
EXE-QA-010  can invalidation erase history?
EXE-QA-011  can network egress evade logging?
EXE-QA-012  can execution status be conflated with verification truth?
EXE-QA-013  can a tool claim more authority than its capability class?
EXE-QA-014  can one agent fake independence?
EXE-QA-015  can reverse provenance break under partial evidence?
```

---

## 459. Execution Trust Theorem
<!-- source: EXECUTION.md §41 -->

If:

```text
authorization is capability-bound
command is canonical and digest-bound
tool identity is digest-bound
inputs are manifest-bound
environment is fingerprinted
execution is sandboxed
outputs are captured and digested
receipts are canonical and immutable
evidence binding is explicit
ledger is append-only
replay manifests are materializable
reverse provenance is traversable
```

then:

```text
every verification claim above the runtime is grounded in auditable execution facts
```

and:

```text
the system can distinguish "verified," "executed," "failed to execute," and "cannot establish"
```

This theorem must become executable protocol predicates, not documentation.

---

## 460. Evidence Loop Closure
<!-- source: EXECUTION.md §42 -->

```text
            ┌───────────────────────────┐
            │      Linux Snapshot       │
            └─────────────┬─────────────┘
                          ▼
                  Semantic Analysis
                          ▼
                        KSIR
                          ▼
                      Contract
                          ▼
                     Rust Design
                          ▼
                   Implementation
                          ▼
                   Verification IR
                          ▼
                Authorized Execution
                          ▼
                  Evidence Runtime
                          ▼
                   Evidence Ledger
                          ▼
                     Gate Engine
                          ▼
                Migration Certificate
                          │
                          ▼
                       Review
                          │
                          ▼
                       Release
                          │
                          ▼
                 New Kernel Snapshot
                          │
                          ▼
                          └───────────────┐
                                          ▼
                                    Revalidation
```

At this point, evidence becomes the system's primary currency.

---

## 461. Architectural Completeness
<!-- source: EXECUTION.md §43 -->

The architecture now has:

```text
KSIR             semantic source of truth
Contract IR      preservation obligations
Rust Design IR   implementation decisions
Verification IR  obligations → evidence methods
Evidence Runtime authoritative execution and evidence
Gate Engine      deterministic acceptance
Certificate Compiler release artifacts
```

Five IRs. Two deterministic authorities. One execution runtime.

---

## 462. Next Artifact: Orchestrator
<!-- source: EXECUTION.md §44 -->

What remains is orchestration:

```text
discover
   ↓
prioritize without ranking correctness
   ↓
allocate agents
   ↓
lease migration unit
   ↓
execute protocol transitions
   ↓
handle conflicts
   ↓
quarantine failures
   ↓
revalidate stale artifacts
   ↓
schedule independent verification
   ↓
submit release candidate
```

The next artifact should be the **Migration Orchestrator / Scheduler** — leases, dependency-aware scheduling, quarantine/recovery, capability matching, fairness, cancellation, stale-epoch handling, and crash recovery, without turning concurrency into authority confusion, stale work, duplicated effort, or verification theater.

**IR / Question:**

| IR | Question |
|----|----------|
| KSIR | What does the existing kernel actually do? |
| Contract IR | What must remain true? |
| Rust Design IR | What Rust structure can satisfy it? |
| Verification IR | How can preservation be established? |
| Evidence IR / Ledger | What exactly was observed and executed? |

**Authority / Responsibility:**

| Authority | Responsibility |
|-----------|----------------|
| Gate Engine | Does the evidence satisfy the declared requirements? |
| Certificate Compiler | Produce the bounded, immutable migration result |
