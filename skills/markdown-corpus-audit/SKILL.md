---
name: markdown-corpus-audit
description: Audit one markdown document or a whole numbered corpus for the defects that render silently — escaped placeholders, comments leaking into headings, broken diagram spines, ASCII glyphs mixed into box-drawing, broken anchors, incomplete provenance. Use after any edit to a specification document and before committing, or to sweep an entire corpus for numbering gaps and duplicates.
---

# markdown-corpus-audit

Markdown fails quietly. A diagram with a broken spine, a heading that renders
its own HTML comment, a code block with no language — all of these look fine in
a diff and render wrong or ambiguously. This skill checks for them mechanically.

## When to use

- After editing any document in the corpus, before committing.
- After splicing diagrams (this is what catches an escaped placeholder).
- Before declaring a multi-document corpus consistent.

## When not to use

- Prose-only edits with no headings, fences, or links — though running it costs
  a second and has never produced a false positive on the corpus.

## Quick start

One document, fully checked:

```bash
python3 skills/markdown-corpus-audit/scripts/audit_file.py ORCHESTRATION.md \
    --range 463-517 --source-name ORCHESTRATION.md --offset 462 \
    --probes probes/orchestration.txt --strict
```

Whole corpus:

```bash
python3 skills/markdown-corpus-audit/scripts/audit_corpus.py --expect-gaps 108
```

`markdown` is required for the render checks. On a PEP 668 system:

```bash
python3 -m venv .venv && .venv/bin/pip install markdown
```

Never `pip install --break-system-packages`.

## What is checked

| area | check |
|---|---|
| numbering | contiguity against `--range`, no duplicates |
| fences | even count, language histogram |
| rust | `{}` `()` `[]` balance in every ```rust block |
| render | tables, `<h2>`/`<h3>`, **unclassified code blocks**, comment-in-heading, `**`-in-heading, stray pipes outside `<pre>` |
| structure | box border vs content width, orphaned connectors, arrows landing on whitespace, ASCII mixed into box-drawing |
| provenance | comment on every heading, `corpus − offset == source`, constant offset |
| links | internal anchors resolve, `.md` links exist, dashed headings resolve |
| probes | verbatim source phrases still present |

## The three rules that were each the subject of a false alarm

1. **A check that cannot run is never a pass.** If `markdown` is not installed
   the render checks print `SKIPPED` and `--strict` fails the run. A green run
   that verified nothing is worse than a red one.
2. **Orphaned connectors fire only when an adjacent row has connectors.** A `▼`
   between two plain-text label rows is normal — that is what `dchain` produces
   — and must not be reported. An earlier over-strict version flagged 17
   non-defects in one document. The converse limitation: a connector passes if
   **either** neighbour aligns, so a vertical run is accepted as long as one
   end connects. A run whose top hangs free — like `RFL-TRANSITION.md` §837's
   drop from a whole tree to `Certificate`, which is intended — is never
   reported, and neither would be a genuinely disconnected end. Dump the block.
3. **Off-centre means "the arrow does not land on a label character", not "every
   token is centred".** A multi-word label like `Agent A` tokenises into two
   columns; per-token centring flagged 9 correct rows.

## Traps

1. **Unclassified code blocks.** A `<pre><code>` with no language class means a
   placeholder escaped its fence. This counter must be 0. It is the only
   reliable signal for that defect.
2. **Inline HTML comments leak into headings.** `cmthead` must be 0.
3. **The checker itself can be wrong.** An off-centre rule was patched and the
   patch dropped its `for c in cc` loop, so it compared against a stale variable
   and reported 2 phantom failures. **Read the checker's coverage before
   trusting its verdict** — twice in this project a "failure" was a bug in the
   check.
4. **Dump the block before fixing it.** Every off-centre and orphan report
   should be inspected as rendered text first. Most were correct diagrams.
5. **Grep the source before treating a probe miss as a defect.** A probe written
   from memory (`requires evidence` vs the source's `requiring evidence`)
   produces a phantom failure.
6. **Probe files must come from the source, not the output.** Otherwise they
   restate the file and prove nothing.
7. **A dashed heading is only a defect if its anchor fails to resolve.**
   `## 124. Agent Topology for 10–100 Agents` slugs to
   `124-agent-topology-for-10100-agents` and its link matches. Glyph presence is
   not a bug.
8. **`/tmp` is not durable.** Keep checkers in the repo. The entire toolchain
   was lost once when `/tmp` was wiped between sessions.

## Verification

Positive — the real corpus must be clean and must reproduce known figures:

```bash
python3 skills/markdown-corpus-audit/scripts/audit_corpus.py --expect-gaps 108
```

Expected: 28 documents, 864 sections, range `1 .. 865`, no duplicates,
gaps `[108]`, `ALL FILES OK`, exit 0. Per-file figures to spot-check:
`RFL-LEDGER.md` 168 fences / 23 sections / `23/23 +804` (source §39–§61);
`RFL-TRANSITION.md` 120 fences / 20 sections / `20/20 +804` (source §19–§38).

Links — `audit_file.py` only resolves **same-file** anchors and checks that a
linked `.md` path *exists*; it does not verify that a cross-file anchor
(`OTHER.md#412-foo`) actually resolves, and it regexes raw source. Use the
dedicated checker, which renders every file and parses the HTML:

```bash
python3 skills/markdown-corpus-audit/scripts/linkaudit.py \
    --allow skills/markdown-corpus-audit/SKILL.md
```

Expected: 45 files, 690 local links, `broken: 0`, `excused: 2`, exit 0. The
`--allow` entries are files permitted to carry deliberately broken *example*
links (this document demonstrates one below); they are reported but do not fail
the run. Do not `--allow` a corpus document.

Three bugs this checker had to survive, all of which produced plausible-looking
wrong answers rather than crashes: keys must be repo-relative paths, not
basenames (`README.md` exists at both the root and `audit/`); file references
resolve relative to the *containing* file's directory, not the repo root; and
an anchor-only href must map to the same file rather than being re-joined with
its own directory.

Negative — a deliberately broken fixture must be caught. Build it:

```bash
mkdir -p /tmp/negtest && cat > /tmp/negtest/BROKEN.md <<'EOF'
# Broken specimen

## 1. Good section
<!-- source: BROKEN.md §1 -->

```text
┌──────┐
│  ok  │
└──────┘
```

## 2. Bad heading <!-- source: BROKEN.md §2 -->

## 3. Missing provenance

```
|
v
label
```

## 4. Wrong offset
<!-- source: BROKEN.md §99 -->

```rust
struct X {
    a: u8,
```

Link to [nowhere](#4-does-not-exist) and [nofile](NOPE.md).

## 5. Off-centre fan
<!-- source: BROKEN.md §5 -->

```text
     ┌────┼────┐
     ▼    ▼    ▼
   aaaa      bbbb        cccc
```

## 6. Mixed glyphs
<!-- source: BROKEN.md §6 -->

```text
┌────────────┐
|  mixed in  |
└────────────┘
```
EOF

python3 skills/markdown-corpus-audit/scripts/audit_file.py /tmp/negtest/BROKEN.md \
    --source-name BROKEN.md --offset 0
```

Expected: **8 problems, exit 1** — unbalanced rust braces, 1 unclassified code
block, comment leaked into a heading, 1 arrow landing on whitespace, 1 ASCII
line mixed into a box-drawing block, provenance `4/6` with 1 mapping error, 1
broken internal anchor, 1 broken `.md` link.

Note what is correctly *not* flagged: the pure-ASCII block in section 3. Sixty-
five ASCII-art lines exist in this corpus because their sources used ASCII, and
all are faithful. Only ASCII mixed into box-drawing is a defect.
