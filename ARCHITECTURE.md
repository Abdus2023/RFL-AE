# RFL-AE — Rust-for-Linux Autonomous Engineering

**Core Kernel Subsystems for a Rust rewrite of the Linux kernel**

> **Developing the skills, tools, and agentic architectures required for an AI system to
> successfully assist in rewriting the Linux kernel in Rust.**

The right target is **not** "an AI that translates Linux C to Rust."

It is an **AI engineering system** capable of acquiring, proving, and maintaining enough
subsystem knowledge to perform **semantics-preserving, kernel-aware Rust rewrites under
Linux's existing contracts**.

The system should treat the Linux kernel as a collection of coupled **trust domains,
execution models, invariants, and compatibility contracts**, rather than as a C codebase.

---

## Contents

| Part | Sections |
| --- | --- |
| [I. Target & landscape](#1-target-system) | 1–2 |
| [II. Competency domains K0–K12](#3-skills-the-ai-must-possess) | 3–15 |
| [III. Agent system design](#16-agent-architecture) | 16–25 |
| [IV. Capability, knowledge & context models](#26-kernel-rewrite-capability-matrix) | 26–33 |
| [V. Benchmarks, memory & governance](#34-benchmark-families) | 34–42 |
| [VI. Migration planning](#43-migration-dependency-planner) | 43–51 |

<details>
<summary><strong>Full section index</strong></summary>

1. Target System
2. Core C Subsystems to Master
3. Skills the AI Must Possess (K0 — Kernel literacy)
4. K1 — C Kernel Semantics
5. K2 — Kernel Memory Model
6. K3 — Ownership Reconstruction
7. K4 — Concurrency Reconstruction
8. K5 — Kernel FFI Engineering
9. K6 — Unsafe Rust
10. K7 — Kernel Build-System Intelligence
11. K8 — Architecture Knowledge
12. K9 — Verification Engineering
13. K10 — Differential Verification
14. K11 — Kernel Archaeology
15. K12 — Patch Engineering
16. Agent Architecture
17. Recommended Agent Roles
18. The Most Important Artifact: Kernel Semantic IR
19. Evidence Model
20. Skill Progression
21. Toolchain
22. Migration Strategy
23. The Rewrite Loop
24. Critical Architectural Rule
25. First Practical Project
26. Kernel Rewrite Capability Matrix
27. Three Separate Knowledge Planes
28. Kernel Knowledge Graph
29. Execution Context Must Be First-Class
30. `may_sleep` Becomes a Type-Level Concept
31. Memory Ownership Model
32. Pointer Classification
33. `container_of()` Is a Major Benchmark
34. Benchmark Families
35. Agent Memory Architecture
36. Belief Tracking
37. Contradiction Engine
38. No-Consensus Safety Rule
39. Rust Design Review Gate
40. Unsafe Budget
41. FFI Budget
42. Rewrite Unit
43. Migration Dependency Planner
44. Subsystem Migration Classes
45. The Core C Subsystem Dependency Problem
46. The "Semantic Cut" Algorithm
47. Training Curriculum for the AI
48. Golden Corpus
49. Agent Training Should Include Failures
50. Final Architecture
51. Next Build Target

</details>

---

# I. Target & landscape

## 1. Target System

```text
                         RUST KERNEL REWRITE AGENT
                                    │
                ┌───────────────────┴───────────────────┐
                │                                       │
        KERNEL KNOWLEDGE                    ENGINEERING CONTROL
                │                                       │
      ┌─────────┼─────────┐                  ┌──────────┼──────────┐
      │         │         │                  │          │          │
    C/ABI   Semantics   Runtime           Evidence    Policy    CI/Gates
                │                                       │
                └───────────────────┬───────────────────┘
                                    │
                          SUBSYSTEM REWRITE
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
             ANALYZE            TRANSLATE            VERIFY
             contracts          Rust design          differential
             invariants         ownership            testing
             call graph         concurrency          KUnit
             lifetime           locking              KASAN/KCSAN
                                unsafe               LKDTM
                                memory               syzkaller
```

The central principle should be:

> ### **C source is evidence of implementation, not the specification.**

The agent has to reconstruct the specification from source, documentation, tests, generated
artifacts, runtime behavior, ABI contracts, architecture assumptions, and historical changes.

---

## 2. Core C Subsystems to Master

For a Linux-to-Rust rewrite program, the kernel organizes into approximately these **core
subsystem families**.

| Domain | Core C subsystem | Rust difficulty |
| --- | --- | --- |
| Foundation | `include/linux/`, compiler abstractions | Extreme |
| Boot | `init/main`, early boot | Extreme |
| Memory | page allocator, buddy allocator | Extreme |
| Memory | SLAB/SLUB | Extreme |
| Memory | `vmalloc` | Extreme |
| Memory | `mm/` VM | Extreme |
| Scheduling | scheduler/core | Extreme |
| Scheduling | scheduler classes | Extreme |
| Tasks | process/thread lifecycle | Extreme |
| Synchronization | spinlocks, mutexes, rwlocks | Extreme |
| RCU | RCU implementation | Extreme |
| Interrupts | IRQ subsystem | Extreme |
| Timers | timer/hrtimer | High |
| Work | workqueues | High |
| IPC | pipes, eventfd, etc. | High |
| VFS | VFS core | Extreme |
| VFS | dentry/inode/path | Extreme |
| Filesystems | generic filesystem infrastructure | Extreme |
| Block | block layer | Extreme |
| Storage | bio/request machinery | Extreme |
| Drivers | driver model | Extreme |
| Devices | device/bus infrastructure | Extreme |
| DMA | DMA mapping | Extreme |
| Networking | socket layer | Extreme |
| Networking | `net/core` | Extreme |
| Networking | packet/buffer (`sk_buff`) | Extreme |
| Networking | routing | Extreme |
| Networking | TCP/IP | Extreme |
| Security | LSM | Extreme |
| Credentials | cred/user namespaces | Extreme |
| Modules | module loader | Extreme |
| Firmware | firmware loading | High |
| Power | PM/suspend/resume | Extreme |
| Time | clocksource/timekeeping | Extreme |
| Architecture | arch abstraction | Extreme |
| Syscalls | syscall infrastructure | High |
| Signals | signal machinery | Extreme |
| Namespaces | namespace infrastructure | Extreme |
| Cgroups | cgroup core | Extreme |
| Tracing | tracepoints/ftrace | High |
| Debugging | printk/console | High |
| Observability | perf | Extreme |
| eBPF | BPF core | Extreme |
| Security | keyrings | High |
| Security | audit | High |

There is an important distinction, however:

> ### **Not all C subsystems should be rewritten directly.**

Some should initially become **Rust-facing contracts around C implementations**.

That produces a migration topology like:

```text
                  ┌─────────────────────┐
                  │      Rust API       │
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐
                  │ Rust implementation │
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐
                  │   FFI / ABI layer   │
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐
                  │ Existing C subsystem│
                  └─────────────────────┘
```

Then progressively:

```text
Phase A   Rust
            │
            ▼ Rust abstraction
            │
            ▼ C implementation

Phase B   Rust
            │
            ├── Rust implementation
            │
            └── C compatibility boundary

Phase C   Rust
            │
            ▼ Rust implementation
            │
            ▼ small C ABI island

Phase D   Rust kernel subsystem
            │
            ▼ minimal legacy C
```

That is much more realistic than attempting a clean-sheet rewrite.

---

# II. Competency domains K0–K12

## 3. Skills the AI Must Possess

Twelve competency domains.

### K0 — Kernel literacy

The agent must understand:

- kernel/user boundary
- execution contexts
- process/thread model
- interrupts
- preemption
- atomicity
- scheduling
- virtual memory
- physical memory
- DMA
- CPU topology
- NUMA
- SMP
- boot
- modules
- syscalls
- VFS
- networking
- device model

This is prerequisite knowledge.

---

## 4. K1 — C Kernel Semantics

Ordinary C competence is insufficient.

The agent needs to understand Linux-specific patterns such as:

```c
container_of()
list_entry()
offsetof()

READ_ONCE()
WRITE_ONCE()
ACCESS_ONCE()

likely()
unlikely()

barrier()
smp_rmb()
smp_wmb()
smp_mb()
```

and patterns involving:

```c
volatile
atomic_t
refcount_t
percpu
__rcu
__user
__iomem
__must_check
__packed
__aligned
__init
__exit
__ro_after_init
```

The agent needs to infer what these annotations and macros mean **semantically**, not merely
syntactically.

---

## 5. K2 — Kernel Memory Model

This deserves its own competency.

The AI must reason about:

```text
CPU
 │
 ├── compiler ordering
 │
 ├── CPU memory ordering
 │
 ├── cache coherence
 │
 ├── atomic operations
 │
 └── synchronization primitives
```

It must distinguish:

```text
Rust ownership  ≠  Linux synchronization  ≠  hardware memory ordering
```

For example, `Arc<T>` cannot automatically replace a Linux reference-counting discipline.

Likewise, `Mutex<T>` does not automatically correspond to every Linux locking context.

The agent must understand **why a synchronization primitive exists and what execution contexts
may hold it**.

---

## 6. K3 — Ownership Reconstruction

This is probably the most important Rust-specific competency.

Given C:

```c
struct foo {
    struct bar *bar;
    struct list_head node;
};
```

the agent must determine:

```text
Who owns foo?
Who owns bar?
Can bar outlive foo?
Can foo outlive bar?
Can another CPU access bar?
Who releases bar?
Can release happen from interrupt context?
Can foo be freed while node remains linked?
```

Only then can it design:

```rust
struct Foo {
    bar: ...,
    node: ...,
}
```

The translation process therefore becomes:

```text
C pointer graph
      │
      ▼
lifetime graph
      │
      ▼
ownership hypothesis
      │
      ▼
aliasing model
      │
      ▼
Rust representation
```

This needs to be an explicit agent capability.

---

## 7. K4 — Concurrency Reconstruction

The AI must build a **concurrency model before translating code**.

For each object:

```text
Object
 │
 ├── readers
 ├── writers
 ├── CPU ownership
 ├── interrupt ownership
 ├── process-context access
 ├── atomic operations
 ├── locks
 ├── RCU protection
 └── lifetime protection
```

Then derive something like:

```text
                ┌──────────────┐
                │ Shared State │
                └──────┬───────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       CPU 0         CPU 1         IRQ
          │            │            │
       lock A      RCU read     atomic X
```

This should become machine-readable evidence.

---

## 8. K5 — Kernel FFI Engineering

Rust cannot eliminate C immediately.

Therefore the agent needs a dedicated **FFI boundary compiler**.

It should generate/validate:

```text
C type
  │
  ├── layout
  ├── alignment
  ├── ABI
  ├── ownership
  ├── nullability
  ├── lifetime
  ├── mutability
  └── concurrency
          │
          ▼
  Rust representation
```

And produce a contract:

```yaml
FFI CONTRACT
  symbol:
    foo_register()
  ABI:
    C
  preconditions:
    ...
  postconditions:
    ...
  ownership:
    ...
  threading:
    ...
  context:
    process-context only
  may_sleep:
    yes
  unsafe rationale:
    ...
```

This should be **proof-carrying FFI**, rather than arbitrary `extern "C"` declarations.

---

## 9. K6 — Unsafe Rust

The goal should **not** be: *eliminate `unsafe`.*

The goal should be:

> **Minimize and localize `unsafe` code, with explicit proof obligations.**

Every unsafe block should have machine-readable obligations:

```text
UNSAFE BLOCK
  │
  ├── pointer validity
  ├── alignment
  ├── initialization
  ├── aliasing
  ├── lifetime
  ├── synchronization
  ├── ABI
  └── hardware assumptions
```

Example:

```rust
// SAFETY:
// - ptr originates from foo_alloc()
// - foo_alloc guarantees alignment
// - object remains alive under lock
// - caller holds foo_lock()
// - no concurrent mutation of field
unsafe {
    (*ptr).field
}
```

The agent should verify as many of those claims as possible.

---

## 10. K7 — Kernel Build-System Intelligence

The agent must understand more than Cargo.

It needs:

```text
Kconfig
Makefiles
Kbuild
scripts/
arch/*/Makefile
generated headers
compile_commands
compiler flags
linker scripts
modpost
symbol exports
vmlinux
modules
initramfs
```

The dependency graph is:

```text
Kconfig
   │
   ▼
configuration
   │
   ▼
Kbuild
   ├── C compilation
   ├── Rust compilation
   ├── generated artifacts
   └── linking
         │
         ▼
      vmlinux
         │
         ├── BTF
         ├── symbols
         └── modules
```

A kernel rewrite agent that only understands source files will fail here.

---

## 11. K8 — Architecture Knowledge

The agent needs architecture-specific models.

At minimum:

- `x86_64`
- `ARM64`
- `RISC-V`

Eventually:

- `x86`
- `ARM`
- `ARM64`
- `RISC-V`
- `PowerPC`
- `s390`
- `MIPS`
- `LoongArch`

Because:

```text
C source  ≠  architecture-independent semantics
```

The agent must reason about:

- calling conventions
- atomics
- barriers
- page tables
- interrupt controllers
- MMU
- cache behavior
- exception handling
- context switching
- linker scripts
- architecture-specific assembly

---

## 12. K9 — Verification Engineering

This should be a first-class capability.

The agent should know how to use:

```text
rustc   cargo   clang   gcc   bindgen   LLVM tools
objdump readelf nm      pahole BTF      DWARF
KUnit   kselftest       LKDTM
KASAN   KMSAN   KCSAN   UBSAN  lockdep  KFENCE
syzkaller ftrace perf bpftrace
QEMU    KVM     GDB     kgdb
```

The key architecture is:

```text
              CLAIM
                │
                ▼
          TEST DESIGN
                │
                ▼
           EXECUTION
                │
                ▼
            RESULT
                │
                ▼
           ARTIFACT
                │
                ▼
           EVIDENCE
                │
                ▼
         VERIFIED CLAIM
```

**Not:**

```text
"I ran the tests"
        ↓
  "therefore it works"
```

---

## 13. K10 — Differential Verification

For a rewrite, this becomes critical. Run:

```text
        C implementation
                │
        ┌───────┴───────┐
        ▼               ▼
    workload A      workload B
        │               │
        ▼               ▼
     trace C         trace C
        │               │
        └───────┬───────┘
                │
                ▼
         semantic model
                ▲
                │
        ┌───────┴───────┐
        │               │
     trace Rust     trace Rust
        ▲               ▲
        │               │
    workload A      workload B
```

The comparison cannot always be byte-for-byte. The agent needs **equivalence classes**:

- observable behavior
- ABI behavior
- state transition behavior
- error behavior
- ordering guarantees
- resource ownership
- security properties
- performance constraints

---

## 14. K11 — Kernel Archaeology

This is often overlooked. Linux contains decades of accumulated reasoning.

The agent needs to understand:

```text
commit history
      │
      ▼
     bug
      │
      ▼
     fix
      │
      ▼
  new invariant
      │
      ▼
later optimization
      │
      ▼
current implementation
```

A suspicious-looking C pattern may exist because of an old race that is not obvious from the
current function.

Therefore:

> ### **Git history becomes part of the semantic input.**

The agent should be able to ask:

```text
Why was this lock introduced?
Why is this memory barrier here?
Why is this pointer RCU-protected?
Why does this function run under preempt_disable()?
Why can't this allocation sleep?
Why does this callback defer freeing?
Why is this field accessed with READ_ONCE()?
```

---

## 15. K12 — Patch Engineering

The final capability is not merely generating Rust. The agent must produce **small, reviewable,
reversible patches**.

```text
analysis
    ↓
design
    ↓
contract
    ↓
implementation
    ↓
tests
    ↓
verification
    ↓
patch
    ↓
review
    ↓
CI
    ↓
evidence
    ↓
merge candidate
```

This should prohibit giant `"rewrite mm/ in Rust"` patches.

Instead:

```text
mm/
 ├── abstraction
 ├── object type
 ├── helper
 ├── isolated subsystem
 └── migration boundary
```

---

# III. Agent system design

## 16. Agent Architecture

Do **not** build one giant "Linux Rust Agent." Use a **multi-agent engineering system**.

```text
                          ORCHESTRATOR
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
KERNEL CARTOGRAPHER      CONTRACT AGENT          EVIDENCE AGENT
       │                       │                       │
       ▼                       ▼                       ▼
  dependency graph         invariants             provenance
  call graph               ABI                    execution
  ownership graph          concurrency            artifacts
       │                       │                       │
       └───────────┬───────────┴───────────┬───────────┘
                   │                       │
                   ▼                       ▼
             RUST DESIGNER          VERIFICATION AGENT
                   │                       │
                   ▼                       ▼
           RUST IMPLEMENTER           TEST EXECUTOR
                   │                       │
                   └───────────┬───────────┘
                               ▼
                          REVIEW AGENT
                               │
                               ▼
                         RELEASE GATE
```

---

## 17. Recommended Agent Roles

### 1. `kernel-cartographer`

Produces:

```text
SubsystemMap  DependencyGraph  CallGraph  DataGraph  ExecutionContextGraph
```

### 2. `c-semantics-agent`

Determines:

```text
C semantics  macro expansion  compiler assumptions
undefined behavior risks  ABI layout
```

### 3. `ownership-agent`

Produces:

```text
OwnershipGraph  LifetimeGraph  AliasGraph  RefcountGraph
```

### 4. `concurrency-agent`

Produces:

```text
LockGraph  RCUGraph  AtomicAccessGraph  ExecutionContextGraph  OrderingConstraints
```

### 5. `kernel-contract-agent`

Extracts:

```text
preconditions  postconditions  invariants
ABI contracts  security contracts  resource contracts
```

### 6. `rust-architect`

Designs:

```text
Rust types  traits  lifetimes  ownership
safe wrappers  unsafe boundaries  FFI
```

### 7. `rust-implementer`

Writes the implementation.

> It should **not** be the authority for whether its implementation is correct.

### 8. `verification-agent`

Runs:

```text
compile  unit tests  KUnit  kselftest  sanitizers
lockdep  QEMU  differential tests
```

### 9. `adversarial-agent`

Attempts to break the rewrite:

```text
race  UAF  double free  deadlock  ABA  refcount overflow
lifetime violation  incorrect ordering  invalid context  ABI mismatch
```

### 10. `historical-agent`

Searches Git history and identifies:

```text
why invariant exists  related bugs  previous regressions
reverted approaches  architecture-specific fixes
```

### 11. `review-agent`

Acts like a hostile kernel maintainer.

### 12. `evidence-agent`

Maintains the immutable evidence ledger.

---

## 18. The Most Important Artifact: Kernel Semantic IR

The centerpiece should be a **Kernel Semantic Intermediate Representation (KSIR)** —
something conceptually like:

```text
KSIR
 │
 ├── Type
 ├── Function
 ├── Symbol
 ├── MemoryRegion
 ├── Ownership
 ├── Lifetime
 ├── Alias
 ├── Lock
 ├── Atomic
 ├── RCU
 ├── ExecutionContext
 ├── InterruptContext
 ├── Allocation
 ├── DMA
 ├── ABI
 ├── ArchitectureConstraint
 ├── SecurityInvariant
 ├── ErrorContract
 └── Evidence
```

Example:

```yaml
function: foo_update

context:
  - process
  - preemptible

may_sleep: true

lock_requirements:
  - foo->lock

ownership:
  reads:
    - foo.state
  writes:
    - foo.state

lifetime:
  foo:
    requirement: alive
    protection: refcount

concurrency:
  state:
    writer: foo->lock
    readers:
      - foo->lock

ffi:
  exported: false

evidence:
  source:
    - kernel/foo.c:120-181
  history:
    - commit: abc123
  tests:
    - kunit/foo_test
```

Then:

```text
 C
 ↓
Parser
 ↓
Static analysis
 ↓
Git archaeology
 ↓
Dynamic instrumentation
 ↓
KSIR
 ↓
Rust design
 ↓
Rust
```

This is substantially more powerful than source-to-source translation.

---

## 19. Evidence Model

The rewrite system must be explicitly **non-self-validating**.

Every capability claim should look like:

```yaml
CAPABILITY
  agent:
    rust-concurrency-agent
  claim:
    Can reconstruct Linux locking contracts
  evidence:
    - test artifact
    - source analysis
    - dynamic trace
    - differential execution
  status:
    PROVED
```

Possible states:

```text
PROVED  PARTIALLY_VERIFIED  PROVISIONAL  OPEN  BLOCKED
```

And evidence strength:

```text
PROOF  OBSERVED  DERIVED  HEURISTIC  UNVERIFIED
```

Crucially:

```text
agent says "correct"
         │
         ✗        ← not evidence
         │
         ▼
external execution
         │
         ▼
     artifact
         │
         ▼
   evidence record
         │
         ▼
       claim
```

---

## 20. Skill Progression

Competency levels:

| Level | Capability |
| --- | --- |
| L0 | Read Rust/C kernel code |
| L1 | Analyze isolated kernel functions |
| L2 | Build subsystem contracts |
| L3 | Implement Rust wrappers around C |
| L4 | Rewrite isolated subsystem components |
| L5 | Maintain cross-subsystem Rust migrations |
| L6 | Perform independent semantic verification |
| L7 | Design new Rust-native kernel subsystem |
| L8 | Coordinate multi-subsystem migration |

But the level should be **earned independently for each competency**. For example:

| | Memory | Concurrency | VFS | Networking |
| --- | --- | --- | --- | --- |
| C semantics | L6 | L7 | L5 | L4 |
| Rust | L5 | L6 | L5 | L4 |
| FFI | L7 | L7 | L6 | L5 |
| Verification | L6 | L7 | L5 | L5 |
| Architecture | L5 | L6 | L3 | L4 |

That is much more informative than `Agent capability = L6`.

---

## 21. Toolchain

The minimum serious tool ecosystem should include:

```text
                    ┌───────────────────┐
                    │   Linux source    │
                    └─────────┬─────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
        Clang                GCC                rustc
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                      Static Analysis
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
           LLVM              BTF             DWARF
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                    Semantic Database
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
       Git                  QEMU                   KUnit
        │                     │                      │
        ▼                     ▼                      ▼
   History DB            Runtime DB               Test DB
                              │
                              ▼
                     Evidence Database
```

And eventually:

```text
Coccinelle  Clang AST  LLVM IR  BTF  DWARF  sparse  smatch
objdump  readelf  pahole  syzkaller  KUnit  kselftest
KASAN  KCSAN  lockdep  KFENCE  QEMU  KVM  GDB  ftrace  perf  eBPF
```

---

## 22. Migration Strategy

The AI should not select subsystems merely by size. Use a **dependency-aware migration graph**:

```text
                      HIGH LEVEL
                           │
                   ┌───────▼────────┐
                   │  Application   │
                   └───────┬────────┘
                           │
                ┌──────────▼──────────┐
                │  syscall / VFS / net │
                └──────────┬──────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       driver             IPC             block
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                   core primitives
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       memory          locking            RCU
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                        arch/boot
```

The bottom layers have enormous fan-out.

Therefore the AI needs a **migration dependency planner**, not simply a task queue.

---

## 23. The Rewrite Loop

Every migration unit should follow:

```text
FREEZE
  ↓
MAP
  ↓
EXTRACT CONTRACT
  ↓
RECONSTRUCT INVARIANTS
  ↓
MODEL OWNERSHIP
  ↓
MODEL CONCURRENCY
  ↓
DESIGN RUST
  ↓
DEFINE FFI
  ↓
IMPLEMENT
  ↓
COMPILE
  ↓
STATIC VERIFY
  ↓
DYNAMIC VERIFY
  ↓
DIFFERENTIAL VERIFY
  ↓
ADVERSARIAL TEST
  ↓
REVIEW
  ↓
CI
  ↓
EVIDENCE
  ↓
RELEASE GATE
  ↓
TAG
```

This is essentially the existing **freeze → formalize → implement → test → release gate → tag**
principle applied to kernel migration.

---

## 24. Critical Architectural Rule

The AI should have **separate authority domains**.

```text
                IMPLEMENTER
                     │
                     │ proposes
                     ▼
               VERIFICATION
                     │
                     │ produces evidence
                     ▼
                 AUDITOR
                     │
                     │ accepts/rejects evidence
                     ▼
                RELEASE GATE
```

The implementer must never be able to produce `implementation + "therefore verified"` from the
same authority domain.

That is particularly important for an AI system, because otherwise the architecture becomes:

```text
LLM generates Rust
        ↓
LLM evaluates Rust
        ↓
LLM declares Rust correct
```

which is essentially **verification theater**.

---

## 25. First Practical Project

Do **not** start with `mm/`, the scheduler, RCU, or networking.

Instead build the infrastructure around a deliberately small kernel subsystem and use it as the
proving ground — something like:

```text
Linux Rust Rewrite Laboratory
repo/
├── kernel-map/
├── ksir/
├── c-analysis/
├── contract-engine/
├── ownership-engine/
├── concurrency-engine/
├── ffi-contract/
├── rust-design/
├── verifier/
├── differential/
├── adversarial/
├── evidence/
├── migration/
├── agents/
│   ├── cartographer/
│   ├── c-semantics/
│   ├── ownership/
│   ├── concurrency/
│   ├── rust-architect/
│   ├── implementer/
│   ├── verifier/
│   ├── adversary/
│   ├── historian/
│   ├── reviewer/
│   └── evidence/
└── schemas/
    ├── ksir.schema.json
    ├── contract.schema.json
    ├── evidence.schema.json
    └── capability.schema.json
```

Then establish a **Kernel Rewrite Conformance Baseline**.

The first milestone is **not**:

> ~~"Rust subsystem successfully rewritten."~~

It **is**:

> **The AI can inspect an existing C subsystem, reconstruct its contracts and invariants,
> produce a Rust design, identify what it does not know, and generate independently verifiable
> evidence for every material claim.**

Only after that should the system receive authority to modify kernel code.

### The deeper goal

The real project is therefore **three systems, not one**:

```text
                        AI KERNEL ENGINEER
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
  KERNEL MODEL          RUST COMPILER          EVIDENCE ENGINE
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
                      MIGRATION AUTHORITY
```

- The **kernel model** answers: *What does Linux actually require?*
- The **Rust system** answers: *How can those requirements be represented safely and
  efficiently in Rust?*
- The **evidence system** answers: *What have we actually demonstrated?*

That separation is what makes an AI-assisted Linux rewrite program potentially serious rather
than merely an automated C-to-Rust translation project.

---

# IV. Capability, knowledge & context models

## 26. Kernel Rewrite Capability Matrix

The agent should not have one generic "Linux skill." It needs a matrix across **kernel domain ×
engineering competency × evidence level**.

| Subsystem | C | Sem | Mem | Concur | Rust | FFI | Verify |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MM | L6 | L7 | L8 | L8 | L7 | L7 | L8 |
| Sched | L6 | L7 | L7 | L8 | L7 | L6 | L8 |
| RCU | L6 | L8 | L7 | L8 | L7 | L7 | L8 |
| VFS | L7 | L7 | L7 | L7 | L7 | L7 | L7 |
| Net | L7 | L7 | L7 | L8 | L7 | L7 | L8 |
| Block | L7 | L7 | L7 | L7 | L7 | L7 | L7 |
| IRQ | L6 | L7 | L7 | L8 | L7 | L7 | L8 |
| Driver | L6 | L6 | L6 | L7 | L7 | L8 | L7 |
| Arch | L7 | L8 | L7 | L8 | L7 | L8 | L8 |

These numbers should be **required competency thresholds**, not a score assigned to an agent.

An agent qualified to modify `mm/` might therefore need demonstrated capability across several
dimensions simultaneously.

---

## 27. Three Separate Knowledge Planes

A particularly important design decision:

```text
                        KERNEL KNOWLEDGE
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
  STRUCTURAL               SEMANTIC                EMPIRICAL
   KNOWLEDGE               KNOWLEDGE               KNOWLEDGE
       │                       │                       │
  call graph              invariants            runtime traces
     types                 ownership                 tests
 dependencies             concurrency               crashes
    configs                   ABI                    perf
```

These must not be conflated. For example:

| Statement | Plane |
| --- | --- |
| `foo->lock` exists | structural knowledge |
| `foo->lock` protects `foo->state` | semantic knowledge |
| A KCSAN execution observed an unsynchronized access when the lock was removed | empirical knowledge |

The agent should preserve all three separately.

---

## 28. Kernel Knowledge Graph

The system needs a graph database or equivalent indexed representation.

```text
Function
   │
   ├── calls ───────────► Function
   ├── accesses ────────► Field
   ├── requires ────────► Lock
   ├── executes_in ─────► Context
   ├── allocates ───────► Object
   └── modifies ────────► State
```

And:

```text
Object
   │
   ├── contains ────────► Field
   ├── owns ────────────► Resource
   ├── referenced_by ───► Function
   ├── protected_by ────► Lock
   ├── lifetime ────────► Refcount/RCU
   └── exposed_by ──────► ABI
```

This graph becomes the foundation for agent reasoning.

---

## 29. Execution Context Must Be First-Class

One of the easiest ways to generate invalid kernel Rust is to ignore execution context.

The system should explicitly model:

```text
EXECUTION_CONTEXT

  PROCESS
   ├── preemptible
   ├── may_sleep
   └── may_allocate

  ATOMIC
   ├── cannot_sleep
   ├── interruptible = false
   └── allocation restrictions

  SOFTIRQ
   ├── cannot_sleep
   └── restricted APIs

  HARDIRQ
   ├── cannot_sleep
   ├── restricted locking
   └── restricted allocation

  NMI
   ├── extremely restricted
   └── special synchronization
```

Then APIs can have contracts:

```yaml
function: kmalloc

allowed_contexts:
  - PROCESS
  - SOFTIRQ
  - HARDIRQ

flags:
  GFP_KERNEL:
    allowed:
      - PROCESS
  GFP_ATOMIC:
    allowed:
      - PROCESS
      - SOFTIRQ
      - HARDIRQ
```

A Rust API should preserve these constraints.

---

## 30. `may_sleep` Becomes a Type-Level Concept

A future Rust kernel agent should be able to reason about something approximately like:

```rust
fn foo<C: ExecutionContext>(ctx: C) {
    ...
}
```

with operations constrained by context. Conceptually:

```text
ProcessContext
  │
  ├── may_sleep()
  ├── blocking_alloc()
  └── mutex_lock()

AtomicContext
  │
  ├── !may_sleep()
  ├── atomic_alloc()
  └── spin_lock()
```

Whether the final Linux implementation uses literal Rust types for all of this is a separate
engineering question.

The **agent's semantic model**, however, should absolutely contain it.

---

## 31. Memory Ownership Model

Linux's C memory model has several different ownership mechanisms:

```text
                     MEMORY LIFETIME
                           │
     ┌─────────────────────┼─────────────────────┐
     │                     │                     │
     ▼                     ▼                     ▼
  explicit             refcount                RCU
  free()                kref             grace period
     │                     │                     │
     ▼                     ▼                     ▼
 single owner       shared ownership          readers
```

Plus these storage classes:

```text
slab   page allocator   percpu   vmalloc   DMA   ioremap
device-managed memory   stack   static   embedded object
```

The agent should classify every object. For example:

```yaml
object: struct foo

storage:
  kind: slab

ownership:
  model: reference_counted
  refcount:
    field: refs

reader_protection:
  rcu: false

mutation_protection:
  lock: foo->lock

free:
  function: foo_free
  free_context:
    process_only: false
```

---

## 32. Pointer Classification

The C parser should classify pointers rather than treating `T *` uniformly.

```text
T *
 │
 ├── owned
 ├── borrowed
 ├── shared
 ├── nullable
 ├── optional
 ├── RCU-protected
 ├── lock-protected
 ├── userspace pointer
 ├── MMIO pointer
 ├── DMA pointer
 ├── self-referential
 ├── intrusive-container pointer
 └── opaque ABI pointer
```

This classification is one of the most important inputs into Rust design.

---

## 33. `container_of()` Is a Major Benchmark

A serious kernel-Rust agent must master Linux's intrusive data structures.

Example:

```c
struct worker {
    int id;
    struct list_head node;
};
```

and:

```c
struct list_head *node;
struct worker *worker;

worker = list_entry(node, struct worker, node);
```

This isn't simply a pointer cast. The agent needs to understand:

```text
node
  │
  ▼
embedded field
  │
  ▼
containing object
  │
  ▼
object lifetime
```

Rust's ownership model and intrusive structures don't naturally map one-to-one.

Therefore **intrusive data structures should be a dedicated competency benchmark**.

---

# V. Benchmarks, memory & governance

## 34. Benchmark Families

The project should have a formal benchmark suite.

### B01 — C comprehension

Given a function `foo()`, recover:

```text
inputs  outputs  side effects  locks  allocation  context  error paths  lifetime
```

### B02 — Macro comprehension

Given `#define X(...)`, determine its semantic effect after relevant expansion.

### B03 — Ownership reconstruction

Given an object graph, determine:

```text
owner  borrowers  release path  possible UAF
```

### B04 — Lock reconstruction

Given code:

```c
spin_lock(&foo->lock);
...
spin_unlock(&foo->lock);
```

determine which fields are actually protected.

### B05 — RCU reconstruction

Determine:

```text
read-side critical section  publication  replacement  grace period  free path
```

### B06 — Context analysis

Determine whether a function may:

```text
sleep  allocate  take mutex  take spinlock  perform I/O
```

### B07 — ABI reconstruction

Determine whether Rust reproduces:

```text
sizeof  alignof  field offsets  calling convention
enum representation  bitfields  packed layout
```

### B08 — Differential behavior

Given C and Rust implementations, determine whether their observable behavior is equivalent for
a defined domain.

### B09 — Adversarial concurrency

Construct schedules capable of exposing:

```text
race  deadlock  ABA  UAF  lost wakeup  refcount bug  ordering violation
```

### B10 — Historical reasoning

Given a function and Git history, explain why the current invariant exists.

> This is particularly important.

---

## 35. Agent Memory Architecture

Do **not** put everything into one vector database. Use separate stores.

```text
                         AGENT MEMORY
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
 SOURCE FACTS           KNOWLEDGE MODEL           EXPERIENCE
       │                       │                       │
 exact source          derived contracts         past attempts
    symbols                 graphs                 failures
  line ranges             invariants                 fixes
    commits              relationships            regressions
```

Then:

```text
MEMORY  ≠  KNOWLEDGE  ≠  BELIEF  ≠  TRUTH  ≠  AUTHORITY
```

This distinction is extremely important for an autonomous engineering system.

---

## 36. Belief Tracking

The AI needs somewhere to say:

```yaml
hypothesis:
  "foo is always protected by foo->lock"

status:
  PROVISIONAL

support:
  - static-analysis-123
  - commit-abc
  - test-456

counterevidence:
  - path-bar.c:81

required_next_test:
  dynamic_lock_trace
```

This prevents the model from silently converting an inference into a fact.

---

## 37. Contradiction Engine

The system should actively search for contradictions. Example:

```text
Agent A:            foo->state protected by lock A
Agent B:            foo->state protected by RCU
Static analyzer:    write occurs without either
Historical:         commit abc says lock A was removed
Runtime:            KCSAN reports race
```

The system should produce:

```text
CONFLICT
  claim-001
  claim-002
  evidence-003

resolution: OPEN
```

**Not** force consensus.

---

## 38. No-Consensus Safety Rule

For kernel engineering:

```text
disagreement
    ↓
do not vote
    ↓
do not average
    ↓
do not majority-decide
    ↓
produce experiment
```

So:

```text
Agent A ─┐
         │
Agent B ─┼──► disagreement ──► experiment
         │
Agent C ─┘
```

rather than:

```text
3 agents say X
2 agents say Y
therefore X
```

The latter is especially dangerous for concurrency and memory safety.

---

## 39. Rust Design Review Gate

Before code generation, the Rust architecture should produce a **Design Artifact**.

```yaml
migration_unit:
  subsystem: example
  symbol: foo

c_semantics:
  contract: ...

ownership:
  model: ...

concurrency:
  locks: ...

execution_context:
  allowed: ...

rust_design:
  types: ...
  lifetimes: ...
  traits: ...

unsafe:
  blocks: ...

ffi:
  symbols: ...

verification:
  required_tests: ...

known_unknowns:
  - ...
```

Only then does the implementation agent receive authorization.

---

## 40. Unsafe Budget

Introduce a measurable migration constraint:

```text
UNSAFE BUDGET
```

For example:

| migration unit | count |
| --- | --- |
| unsafe blocks | 7 |
| raw pointer operations | 12 |
| FFI calls | 4 |
| `transmute` | 0 |
| unresolved safety obligations | 2 |

The release gate should reject:

```text
unresolved safety obligations > 0
```

unless explicitly classified as a temporary migration exception.

---

## 41. FFI Budget

Likewise:

```text
C DEPENDENCY BUDGET
```

| Rust subsystem | count |
| --- | --- |
| C functions imported | 8 |
| C types exposed | 3 |
| C global state | 1 |
| callbacks into C | 2 |
| unresolved ABI assumptions | 0 |

Migration can then objectively move `8 C functions → 5 → 2 → 0` without pretending the subsystem
is fully Rust-native prematurely.

---

## 42. Rewrite Unit

The basic unit shouldn't be a file. It should be a **Migration Unit**.

A migration unit has:

```text
boundary  contract  dependencies  ownership model  concurrency model
execution contexts  ABI  implementation  tests  evidence  rollback strategy
```

Example:

```text
MU-000173

Subsystem:     kernel/workqueue
Boundary:      worker_pool.c::foo_worker()

Dependencies:  spinlock, atomic, list, timer
Contexts:      process, worker

C implementation:    ...
Rust implementation: ...

Verification:  KUnit, differential, KCSAN
Status:        PARTIALLY_VERIFIED
```

---

# VI. Migration planning

## 43. Migration Dependency Planner

Now the AI can construct:

```text
                         MU-173
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
      MU-102             MU-041             MU-087
       list             locking              timer
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                         MU-001
                      core memory
```

Then calculate:

```text
blocked_by  depends_on  risk  verification_cost  FFI_surface  fanout
```

This produces an actual migration DAG.

---

## 44. Subsystem Migration Classes

Every subsystem classifies into one of four migration modes.

### M0 — Leave C

```text
Rust → stable FFI → C
```

### M1 — Rust abstraction

```text
   C implementation
         ▲
   Rust safe interface
```

### M2 — Hybrid

```text
   Rust implementation
         │
         ├── C compatibility
         └── C legacy dependencies
```

### M3 — Rust-native

```text
   Rust implementation
         │
         └── minimal ABI boundary
```

This allows the Linux rewrite to progress without requiring the entire dependency graph to be
Rust first.

---

## 45. The Core C Subsystem Dependency Problem

There is a fundamental asymmetry:

```text
                       scheduler
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
            mm            RCU           IRQ
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                        drivers
```

But:

```text
mm
 │
 ├── scheduler assumptions
 ├── architecture assumptions
 ├── locking
 ├── RCU
 ├── interrupt context
 └── driver/DMA interactions
```

So there is no true linear `1 → 2 → 3 → 4` migration. It is a **strongly coupled graph**.

The AI needs to reason about **cut sets**:

> What is the smallest Rust boundary that allows meaningful migration without rewriting
> everything downstream?

That should become one of the core planning algorithms.

---

## 46. The "Semantic Cut" Algorithm

For a proposed migration of subsystem `S`, calculate:

```text
dependencies(S)
reverse_dependencies(S)
shared_state(S)
ABI_edges(S)
concurrency_edges(S)
lifetime_edges(S)
```

Then search for boundaries that minimize:

```text
C-boundary size + unsafe surface + shared mutable state + verification complexity
```

subject to:

```text
behavioral equivalence
ABI compatibility
kernel build compatibility
runtime constraints
```

This is much closer to the actual problem of incremental kernel rewriting.

---

## 47. Training Curriculum for the AI

The agent should learn in stages.

```text
L0  Linux architecture
      ↓
L1  C kernel idioms
      ↓
L2  kernel memory/concurrency
      ↓
L3  Rust kernel programming
      ↓
L4  FFI + ABI
      ↓
L5  verification
      ↓
L6  subsystem reconstruction
      ↓
L7  small rewrites
      ↓
L8  cross-subsystem migration
```

And **each stage has tests, not just documents**.

---

## 48. Golden Corpus

Build a corpus of deliberately selected Linux examples:

```text
golden/
├── ownership/
├── lifetimes/
├── refcount/
├── rcu/
├── locking/
├── atomics/
├── waitqueues/
├── workqueues/
├── timers/
├── interrupts/
├── memory/
├── dma/
├── vfs/
├── networking/
├── device-model/
├── architecture/
└── abi/
```

Each example should have:

```text
C source
semantic annotations
known invariants
Rust candidate
expected unsafe boundaries
tests
failure cases
historical context
```

This becomes the **kernel engineering benchmark suite**.

---

## 49. Agent Training Should Include Failures

A high-quality dataset isn't `C → correct Rust`.

It should primarily include:

```text
        C
        ↓
   plausible Rust
        ↓
      failure
        ↓
 why failure happened
        ↓
    correct model
        ↓
    fixed Rust
        ↓
  regression test
```

Examples:

```text
wrong ownership          wrong lifetime           wrong lock scope
wrong interrupt context  wrong atomic ordering    wrong ABI
wrong allocation flags   wrong RCU lifetime       wrong refcount semantics
wrong architecture assumption
```

This teaches the agent where **apparently reasonable Rust is kernel-invalid**.

---

## 50. Final Architecture

Putting everything together:

```text
                        RUST-KERNEL ENGINEERING AI
                                    │
      ┌─────────────────────────────┼─────────────────────────────┐
      │                             │                             │
      ▼                             ▼                             ▼
  KNOWLEDGE PLANE             REASONING PLANE              EVIDENCE PLANE
      │                             │                             │
 ┌────┼─────┐                ┌──────┼──────┐              ┌───────┼───────┐
 ▼    ▼     ▼                ▼      ▼      ▼              ▼       ▼       ▼
source git runtime          C     Rust   kernel          CI      test  provenance
graph  graph graph          sem   design model        artifacts
      │                             │
      └──────────────┬──────────────┘
                     ▼
                    KSIR
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ownership    concurrency      ABI
        │            │            │
        └────────────┼────────────┘
                     ▼
             MIGRATION DESIGN
                     │
                     ▼
            RUST IMPLEMENTATION
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     static      dynamic    differential
    analysis     testing    verification
        │            │            │
        └────────────┼────────────┘
                     ▼
              ADVERSARIAL AUDIT
                     │
                     ▼
                EVIDENCE GATE
                     │
          ┌──────────┴──────────┐
          │                     │
       ACCEPT                 BLOCK
          │
          ▼
        PATCH
          │
          ▼
         CI
          │
          ▼
   MIGRATION LEDGER
```

### The project should therefore have three deliverables

**A. Linux Kernel Semantic Engine** — understands the existing C kernel:

```text
C → AST → CFG → call graph → data graph
  → ownership → concurrency → context
  → ABI → historical reasoning
  → KSIR
```

**B. Rust Kernel Engineering Agent**

```text
KSIR
 ↓
Rust architecture
 ↓
FFI design
 ↓
unsafe obligations
 ↓
implementation
 ↓
tests
```

**C. Independent Verification & Evidence System**

```text
claim
 ↓
test specification
 ↓
actual execution
 ↓
artifact
 ↓
evidence record
 ↓
verification status
```

> The **third system** is what prevents the first two from becoming an LLM code-generation loop.

---

## 51. Next Build Target

The natural next step is to turn this into a concrete project specification:

```text
RFL-AE — Rust-for-Linux Autonomous Engineering
 ├── 00-governance
 ├── 01-kernel-indexer
 ├── 02-c-semantic-engine
 ├── 03-ksir
 ├── 04-ownership-engine
 ├── 05-concurrency-engine
 ├── 06-context-engine
 ├── 07-abi-ffi-engine
 ├── 08-rust-design-engine
 ├── 09-migration-engine
 ├── 10-verification-engine
 ├── 11-differential-engine
 ├── 12-adversarial-engine
 ├── 13-git-archaeology
 ├── 14-evidence-ledger
 ├── 15-agent-runtime
 ├── 16-capability-benchmarks
 └── 17-kernel-subsystem-labs
```

The **first subsystem lab** should be chosen specifically to exercise **ownership + locking +
lifetime + FFI + verification**, rather than starting with a headline subsystem like `mm/`.

From there we can define **RFL-AE v0.1 as an implementable repo specification**, including:

- the KSIR schema
- the evidence schema
- agent protocols
- the benchmark corpus
- capability levels
- tool interfaces
- the first end-to-end C→Rust migration experiment

---

**Continues in [SPECIFICATION.md](SPECIFICATION.md)** (§52–§80) — the v0.1 engineering
specification: repository layout, immutable domain model, the contract set, safety obligations,
agent protocol and authorization states, layered verification, subsystem qualification, the
Kernel Invariant Ledger, and the Migration Certificate.
