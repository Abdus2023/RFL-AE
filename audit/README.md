# RFL-AE — Deep Audit

An external deep audit of the `arena/01a0e252-rfl-ae` branch at commit
`952e30029baa371831c419f4b23e110b552d1ff7`, supplied as a single report and
split here into themed documents.

**This is a review of the corpus, not a specification.** It therefore lives
outside the §1–§517 corpus numbering and carries no `<!-- source: … §n -->`
provenance comments. The original report's own section numbers (§1–§27) are
preserved on every section heading so the split remains traceable to it.

## Documents

| file | contents | report sections |
|------|----------|-----------------|
| [01-REPOSITORY-VERIFICATION.md](01-REPOSITORY-VERIFICATION.md) | Corpus structure, provenance, document-chain integrity | §1–§3 |
| [02-ARCHITECTURE-ASSESSMENT.md](02-ARCHITECTURE-ASSESSMENT.md) | Authority separation, epistemic model, snapshot/epoch, execution, gates | §4–§9 |
| [03-SPECIFICATION-DEFECTS.md](03-SPECIFICATION-DEFECTS.md) | `GateStatus`, `SnapshotId`, type closure | §10–§12 |
| [04-TOOLING-DEFECTS.md](04-TOOLING-DEFECTS.md) | `run_all.sh` coverage, `validate_skill.py`, audit limits | §13, §14, §17, §18 |
| [05-INFRASTRUCTURE-GAPS.md](05-INFRASTRUCTURE-GAPS.md) | CI authority, commit authenticity | §15–§16 |
| [06-EXTERNAL-CONTEXT.md](06-EXTERNAL-CONTEXT.md) | Subsystem inventory, upstream Rust, kernel testing, governance, AI provenance | §19–§23 |
| [07-RECOMMENDATIONS.md](07-RECOMMENDATIONS.md) | What to preserve, what to change, next milestone | §24–§26 |
| [08-FINAL-ASSESSMENT.md](08-FINAL-ASSESSMENT.md) | Verdict and gap list | §27 |

## Bottom line

The architecture is substantially stronger than a normal AI-agent design
document. The specification is internally coherent at the architectural level,
but it is not yet an implemented or independently executable verification
system.

The repository itself correctly says:

> `v0.0` — documentation only

and explicitly says there are no Rust crates, JSON schemas, or executable
benchmarks yet. That statement is accurate.

## Classification

| Area | Status |
|------|--------|
| Corpus structure / numbering | PROVED |
| Cross-document architecture | PARTIALLY_VERIFIED |
| Authority model | PARTIALLY_VERIFIED |
| Evidence model | PARTIALLY_VERIFIED |
| Transition model | PARTIALLY_VERIFIED |
| Gate model | PARTIALLY_VERIFIED |
| Scheduler model | PARTIALLY_VERIFIED |
| Skill/tooling source | PARTIALLY_VERIFIED |
| Executable RFL-AE implementation | OPEN |
| Actual Linux→Rust migration capability | OPEN |
| Independent CI verification | BLOCKED / ABSENT |

## Verification of this audit's factual claims

> **Addition by the repository maintainer, not part of the original report.**
> Every checkable assertion in this audit was re-verified against the branch
> before the report was saved. Results:

| report § | claim | verified result |
|---|---|---|
| §1 | 14 documents, 516 sections, range 1–517, only §108 missing, no duplicates | **HOLDS** — `audit_corpus.py` reports exactly this |
| §2 | Provenance offsets +356 / +386 / +418 / +462, no mapping errors | **HOLDS** — offsets re-derived, all `N/N` complete |
| §3 | Every document forward-links to the next; no broken chain edge | **HOLDS** — all 13 edges present |
| §10 | `GateStatus` used but never defined; `GATES.md` defines `GateResult` | **HOLDS** — 11 uses in `TRANSITIONS.md`, no `enum GateStatus` anywhere, `GATES.md:263` |
| §11 | `SnapshotId` referenced but never declared; `KernelSnapshotId` also used | **HOLDS** — no declaration of either; `KernelSnapshotId` used in 8 places across 6 files |
| §12 | `RUST-CORE.md` has exactly 31 public declarations | **HOLDS** — 8 opaque IDs + 23 |
| §12 | Those declarations depend on undeclared types | **PARTLY** — `Uuid`, `Digest`, `GitObjectId`, `ArchitectureId`, `ToolchainFingerprint`, `Timestamp` are undeclared; but `EnvironmentFingerprint` **is** declared (`EXECUTION.md:355`), as are `Scope` (`RUST-CORE.md:323`) and `Epoch` (`TRANSITIONS.md:588`). The closure gap is real; that one list item is not. |
| §13 | `run_all.sh` never positively executes `renumber.py` or `splice.py` | **HOLDS** — `renumber.py` is never invoked; `splice.py` only in a negative test |
| §14 | `validate_skill.py` byte-compiles but never executes scripts | **HOLDS** — `py_compile` only, no subprocess |
| §15 | No CI: no `.github/workflows/` | **HOLDS** — no `.github` directory, no `*.yml`/`*.yaml` |
| §17 | Rust check is naive brace counting, not parsing | **HOLDS** — `body.count(o) != body.count(c)` |
| §18 | `verify_closeout.py` checks are substring-based | **HOLDS** — `f"]({a.new})" in prev_t` and similar |

One correction is recorded inline in
[03-SPECIFICATION-DEFECTS.md](03-SPECIFICATION-DEFECTS.md) at §12.
