# 06 — External context

Part of the [deep audit](README.md). Original report sections **§19–§23**.

These sections compare the corpus against the actual state of upstream Linux
and Rust-for-Linux. They are the auditor's external observations and were not
independently re-verified here; they are recorded as supplied.

---

## §19. The core subsystem inventory is good but should become machine-readable

ARCHITECTURE.md has a surprisingly useful inventory:

```text
Foundation
Boot
Memory
Scheduling
Tasks
Synchronization
RCU
Interrupts
Timers
Workqueues
IPC
VFS
Filesystems
Block
Storage
Driver model
DMA
Networking
Security
Credentials
Modules
Firmware
Power
Time
Architecture
Syscalls
Signals
Namespaces
Cgroups
Tracing
Debugging
perf
eBPF
...
```

This is a strong conceptual starting point.

But it remains a Markdown table.

For the actual AI system, this needs to become something like:

```yaml
subsystem_id: mm-slub
family: memory
source_paths:
  - mm/slub.c
  - include/linux/slab.h

semantic_domains:
  - allocation
  - lifetime
  - concurrency
  - architecture

required_capabilities:
  - allocator-analysis
  - atomic-analysis
  - per-cpu-analysis

migration_class:
  - rust-wrapper-first

verification:
  - KUnit
  - KASAN
  - differential
  - stress
```

That would transform the architecture from a document into schedulable data.

---

## §20. External Linux/Rust validation

The architecture is broadly consistent with the actual state of upstream Rust
support.

Current Linux documentation confirms Rust is integrated under `CONFIG_RUST`,
uses Rust 2021, and still involves some unstable Rust features.

The kernel's Rust support is also `no_std` and uses its own `kernel` crate as
the API layer; Rust code should use kernel abstractions rather than bypassing
them with arbitrary C APIs.

That strongly supports RFL-AE's emphasis on:

```text
FFI boundary
Rust kernel abstractions
unsafe obligations
ABI
context
ownership
```

rather than treating translation as ordinary application-level C→Rust
conversion.

---

## §21. Verification architecture matches real kernel testing better than a simple "unit test" model

Current kernel Rust testing includes:

```text
KUnit
#[test] / rusttest
Kselftests
```

and the kernel also has broader testing/instrumentation such as KASAN, KCSAN and
lockdep.

That means RFL-AE's proposed:

```text
static
runtime
differential
concurrency
memory
ABI
adversarial
regression
```

model is directionally appropriate.

But it needs to be grounded in actual kernel commands, configs, artifacts and
failure semantics.

For example, instead of:

```text
ConcurrencyGate = PASS
```

eventually the evidence should identify:

```text
kernel snapshot
.config
architecture
compiler
KCSAN configuration
test command
execution receipt
KTAP/log artifacts
diagnostic artifacts
oracle
```

The kernel already provides concrete testing infrastructure that can become the
execution substrate.

---

## §22. One important missing external constraint: Linux maintainer authority

This is the biggest conceptual gap I would add to the architecture.

Rust-for-Linux explicitly describes subsystem-specific governance: individual
subsystems decide how they want to approach Rust, and duplicate C/Rust drivers
are generally not allowed by default, with exceptions for bootstrapping.

So RFL-AE currently models:

```text
technical authority
```

extremely well.

It models:

```text
kernel project governance
```

less completely.

A real migration unit eventually needs something like:

```text
Technical Contract
        +
Verification Contract
        +
Repository Policy
        +
Subsystem Maintainer Policy
        +
Patch/Review Requirements
        +
Contributor Attestation
```

The scheduler cannot treat:

```text
RELEASE_ELIGIBLE
```

as equivalent to:

```text
ACCEPTABLE FOR UPSTREAM LINUX
```

Those are different predicates.

---

## §23. AI-generated contribution provenance should be explicit

This matters even more because the target is Linux.

Current kernel guidance explicitly discusses tool-generated content, including
chatbot-generated functions, and says tool use that materially contributes to a
patch should be considered as part of the development/review process.

Therefore RFL-AE should eventually contain:

```text
GenerationRecord
├── agent
├── model
├── model/version identity
├── prompt/task identity
├── input artifacts
├── generated artifact
├── human modifications
├── verification evidence
└── final author/attestation
```

Not because an AI-generated patch is inherently invalid, but because the
provenance is part of the engineering process.
