---
name: corpus-provenance-numbering
description: Renumber a newly pasted specification into a single governed corpus while keeping the original source numbering losslessly recoverable. Use when a document arrives with its own section numbers and must join an existing numbered corpus without collisions, or when you need to verify that a document's provenance comments and offsets are consistent.
---

# corpus-provenance-numbering

Independent documents each numbered from 1 are a pile of files, not a corpus.
Concatenating them loses the original numbering. This skill does both:

```
corpus_section = source_section + offset
offset         = last corpus section of the PREVIOUS document
```

so corpus numbering is contiguous across files, and every heading still records
which source section it came from.

## When to use

- A new specification document is being added to an existing numbered corpus.
- Auditing whether a document's numbering and provenance agree.
- Reconstructing which source section a corpus clause came from.

## When not to use

- A standalone document with no corpus to join.
- When the source has no section numbers to preserve.

## Quick start

Plan a new document (writes nothing):

```bash
python3 skills/corpus-provenance-numbering/scripts/renumber.py plan \
    --source-name ORCHESTRATION.md --sections 55 \
    --prev-last 462 --prev-file EXECUTION.md \
    --title "RFL-AE — Orchestration IR + Deterministic Scheduler v0.1"
```

It prints the corpus range, the provenance blockquote to paste under the title,
a Contents skeleton, and the heading/comment pairs.

Renumber a draft you have already written with source numbering:

```bash
python3 skills/corpus-provenance-numbering/scripts/renumber.py apply DRAFT.md \
    --source-name ORCH.md --offset 462 --out ORCHESTRATION.md
```

## The heading form

```markdown
## 463. Orchestration architecture
<!-- source: ORCHESTRATION.md §1 -->
```

Two deliberate choices, both load-bearing:

1. **The comment goes on its own line, never inline.** Python-Markdown leaks an
   inline `<!-- … -->` into the visible `<h2>` text *and* changes the slug, so
   `## 463. Title <!-- source: … -->` renders the comment to the reader. On its
   own line it is invisible and the slug is clean.
2. **No `§` before the number.** `## 463.` not `## §463.`, so the section regex
   `^## (\d+)\. ` keeps matching across the whole corpus.

A blank line between heading and comment is permitted — two documents in the
corpus use one and two do not. The comment must be the next *non-blank* line.

## Invariants

1. Numbering is **contiguous across the corpus** except where the source itself
   had a gap. RFL-AE has exactly one such gap, at §108, and it is preserved
   deliberately.
2. No section number appears twice, anywhere in the corpus.
3. Every heading carries a provenance comment, and
   `corpus − offset == source` for all of them.
4. The offset is **constant within a file** and differs between files.
5. A provenance blockquote at the top of each renumbered document states the
   corpus range, the source range, the mapping formula, and that source
   numbering is preserved.

## Traps

1. **Colliding with an existing document's range.** Always take the offset from
   the previous document's actual last section — read it, do not remember it.
   `renumber.py plan` asks for it explicitly.
2. **Inline provenance comments.** See above; they leak into rendered headings.
   The audit's `cmthead` counter exists for this.
3. **Assuming the comment is on the immediately following line.** Half the
   corpus has a blank line in between. A checker that only looks at `i+1`
   reports 0 provenance comments for those files — which is what happened when
   this was first automated.
4. **Writing the mapping formula into the blockquote by hand and getting the
   offset wrong.** Generate it. `plan` mode's output has been verified
   byte-for-byte against a shipped blockquote.
5. **Anchors in the Contents that do not resolve.** GitHub strips `§` and
   punctuation and lowercases. Generate the slugs rather than typing them; a
   heading containing an em dash or arrow is only a defect if its anchor does
   not actually resolve.

## Verification

```bash
# plan reproduces the blockquote that shipped in ORCHESTRATION.md exactly
python3 skills/corpus-provenance-numbering/scripts/renumber.py plan \
    --source-name ORCHESTRATION.md --sections 55 --prev-last 462 \
    --prev-file EXECUTION.md \
    --title "RFL-AE — Orchestration IR + Deterministic Scheduler v0.1" \
  | grep '^> \*\*Provenance'
diff <(…as above…) <(grep '^> \*\*Provenance' ORCHESTRATION.md)   # must be empty

# per-file: provenance complete, mapping errors 0
python3 skills/markdown-corpus-audit/scripts/audit_file.py ORCHESTRATION.md \
    --range 463-517 --source-name ORCHESTRATION.md --offset 462

# whole corpus: derived offsets, duplicates, gaps
python3 skills/markdown-corpus-audit/scripts/audit_corpus.py --expect-gaps 108
```

Negative test: change one comment to a wrong source number, or delete one, and
confirm `audit_file.py` reports `provenance incomplete` and exits 1. The
`/tmp/negtest/BROKEN.md` fixture in the audit skill covers this.
