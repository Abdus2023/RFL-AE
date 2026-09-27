# 01 — Repository-level verification

Part of the [deep audit](README.md). Original report sections **§1–§3**.

---

## §1. Repository-level verification

The branch root contains:

```text
ARCHITECTURE.md
SPECIFICATION.md
FORMAL-CORE.md
PROTOCOL.md
RUST-CORE.md
TRANSITIONS.md
KSIR.md
RECONSTRUCTION.md
CONTRACTS.md
DESIGN-IR.md
VERIFICATION.md
GATES.md
EXECUTION.md
ORCHESTRATION.md
README.md
skills/
.gitignore
```

There are 14 specification documents.

I programmatically inspected the section headings from the remote contents:

```text
ARCHITECTURE       1–51
SPECIFICATION     52–80
FORMAL-CORE       81–107
                  108  ← intentional gap
PROTOCOL         109–135
RUST-CORE        136–172
TRANSITIONS      173–203
KSIR             204–250
RECONSTRUCTION   251–291
CONTRACTS        292–320
DESIGN-IR        321–356
VERIFICATION     357–386
GATES            387–418
EXECUTION        419–462
ORCHESTRATION    463–517
```

Result:

```text
documents:       14
sections:       516
range:          1–517
missing:        §108 only
duplicates:     none
```

That is a strong result.

The §108 gap is not an accidental numbering defect; the repository explicitly
preserves it because the source corpus skipped it.

> **Maintainer note — verified.** `audit_corpus.py --expect-gaps 108 --strict`
> reports `documents: 14`, `sections: 516`, `range: 1 .. 517`,
> `duplicates: none`, `gaps: [108]`, `ALL FILES OK`. Claim holds exactly.

---

## §2. Corpus provenance is actually implemented

The later documents have machine-readable provenance:

```html
<!-- source: VERIFICATION.md §1 -->
<!-- source: GATES.md §1 -->
<!-- source: EXECUTION.md §1 -->
<!-- source: ORCHESTRATION.md §1 -->
```

and the offsets are correct:

```text
VERIFICATION:
    corpus = source + 356

GATES:
    corpus = source + 386

EXECUTION:
    corpus = source + 418

ORCHESTRATION:
    corpus = source + 462
```

I checked the entire heading/comment mapping rather than merely checking that
the comments exist.

No mapping errors were found.

That part of the repository is genuinely reproducible.

> **Maintainer note — verified.** The offsets above are not assumed by the
> checker; `audit_corpus.py` derives each file's offset from its own headings
> and requires it to be constant, reporting `30/30 +356`, `32/32 +386`,
> `44/44 +418`, `55/55 +462`. Zero mapping errors. Claim holds.

---

## §3. Document-chain integrity

Every document has a forward link to the next specification:

```text
ARCHITECTURE
    ↓
SPECIFICATION
    ↓
FORMAL-CORE
    ↓
PROTOCOL
    ↓
RUST-CORE
    ↓
TRANSITIONS
    ↓
KSIR
    ↓
RECONSTRUCTION
    ↓
CONTRACTS
    ↓
DESIGN-IR
    ↓
VERIFICATION
    ↓
GATES
    ↓
EXECUTION
    ↓
ORCHESTRATION
```

I checked those relationships directly.

No broken document-chain edge was found.

That matters because the corpus is large enough that manual numbering/linking
is itself an error surface.

> **Maintainer note — verified.** All 13 edges
> `ARCHITECTURE → … → ORCHESTRATION` are present; broken chain edges: none.
> Claim holds.
