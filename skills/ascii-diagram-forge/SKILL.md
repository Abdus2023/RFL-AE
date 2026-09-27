---
name: ascii-diagram-forge
description: Generate box-drawing and flow diagrams deterministically from computed column arithmetic instead of typing them by hand. Use whenever a specification document needs an ASCII/Unicode diagram, a tree, a fan-out, a boxed chain, or a column-aligned table-like block. Ships geo.py, the geometry library every diagram in the RFL-AE corpus was built with.
---

# ascii-diagram-forge

Hand-typed diagrams drift. A column that is one space off in row 7 breaks the
spine, and nothing about the file looks wrong. This skill replaces typing with
arithmetic: **every glyph position is computed from named column constants**, so
a diagram is either structurally correct everywhere or fails loudly.

Across fourteen specification documents this produced ~200 diagrams with a
handful of defects, every one of them caught by the checks in
`markdown-corpus-audit`.

## When to use

- Redrawing a diagram whose source arrived with collapsed whitespace.
- Any tree, chain, fan-out, boxed stage, or aligned block in a document.
- Fixing a diagram where a spine or border has drifted.

## When not to use

- A block that is genuinely just text (a list of identifiers, an enum body, a
  command line). Fencing it as-is is more faithful than redrawing it.
- Anything where the *source* is the authority on spacing. Reproduce it.

## Quick start

```bash
python3 skills/ascii-diagram-forge/scripts/examples.py
```

That prints a worked example of every pattern and runs the self-test. Import
`geo` from your own generator:

```python
import sys; sys.path.insert(0, "skills/ascii-diagram-forge/scripts")
from geo import row, marks, bar, flow, box, boxfix, dchain, tree, align, colbox

C = 25                     # the spine's absolute column
out = [row([("Migration Unit", C)]), marks([(C, "\u2502")])]
out += flow(C)             # ["│", "▼"]
out.append(row([("Independent Verifier", C)]))
print("\n".join(out))
```

Write each diagram to its own file (`D<NAME>.txt`) and reference it from the
document as a placeholder — see the `placeholder-splice` skill.

## The helpers

| helper | use |
|---|---|
| `cen(w, c)` | start column that centres `w` on `c` |
| `row([(text, col), …])` | centre several labels on one row; **raises on overlap** |
| `marks([(col, glyph), …])` | place single glyphs at absolute columns |
| `bar([(col, glyph), …])` | same, filling gaps with `─` — borders and fans |
| `hjoin([(col, segment)])` | compose pre-rendered lines; **column first** |
| `box(lines, C)` | bordered box, returns `(rows, left, right)` |
| `boxfix(lines, C, G)` | box with a forced interior gutter `G` |
| `flow(C)` | the two-row spine continuation `│` then `▼` |
| `dchain(items, c)` | vertical chain joined by `↓` |
| `tree(name, kids)` | `├──`/`└──` child list |
| `align(pairs, gap)` | two-column alignment from the widest label |
| `colbox(lines, cols)` | several boxes side by side |

## Invariants

1. **One coordinate space.** All columns are absolute. Never compute a position
   relative to a previously emitted string's length.
2. **Name your constants.** `C`, `L`, `R`, `A/B/C` for fan columns. Hardcoding a
   number that should equal a constant is how drift enters.
3. **Re-emit the spine in every row a fork spans.** If a branch passes through
   a row, that row must still carry the vertical bar.
4. **`row()` must raise on overlap.** See trap 1.
5. **Box glyphs are box glyphs.** `│` is U+2502, never the ASCII pipe.

## Traps

1. **Two labels merged into one word (`acceptquarantine`).** The original
   `row()` did `out.ljust(col) + text`; when a computed start fell inside
   already-emitted text, `ljust` did nothing and the strings concatenated. The
   generator exited 0 and the corrupt diagram shipped. **Fix:** `row()` now
   computes all spans first and raises `ValueError("OVERLAP: …")`. If you write
   a variant, keep that.
2. **The first glyph lost its leading spaces.** `bar`/`marks` emitted the first
   glyph with no `" " * col` prefix, so every border rendered at column 0 while
   content rows stayed indented. Caught only by running the examples.
3. **`hjoin` argument order.** It is `(col, segment)`. Reversed, you get
   `TypeError: '<' not supported between instances of 'str' and 'int'`.
4. **Box width off by one.** For `boxfix(lines, C, G)` the right border is at
   `left + G + 3` (content is `G+4` wide). A box built directly as
   `│ + " " + text.ljust(G-1) + │` is a *different* construction whose right
   border is at `G + 1`. Conflating the two formulas is a known defect; the
   self-test pins the first.
5. **ASCII pipe substituted for `│`.** One row of an otherwise box-drawing
   diagram used `|`, so the spine vanished for that row. The audit flags ASCII
   mixed into a box-drawing block.
6. **A dropped spine in a fork.** A row emitted `▼` on one branch without `│`
   on the sibling branch, so the sibling's spine disappeared for one row.
   Always emit every branch that is still live.
7. **Even-width centring is one column left.** `cen` uses integer division. This
   is deliberate and consistent; do not "fix" individual diagrams or they will
   disagree with their neighbours.
8. **f-strings cannot contain backslashes** (on older Pythons). Hoist regex
   patterns to a module-level `re.compile` instead of inlining them.
9. **Merging two source blocks into one diagram.** If the source has two
   separate code spans, they are two diagrams. Dump the source block boundaries
   before drawing anything.

## Verification

```bash
# positive: every pattern renders and the geometry self-tests pass
python3 skills/ascii-diagram-forge/scripts/examples.py
```

Expected tail: `all self-tests passed`, exit 0. The self-test asserts that
`row()` raises on overlap and on a negative start column, that `hjoin` raises on
overlap, that box borders align with their content rows, that `boxfix`'s right
border sits at `G+3`, that no box border contains an ASCII pipe, and that
`dchain`/`tree`/`padc` have the lengths they claim.

Then audit the document the diagrams went into:

```bash
python3 skills/markdown-corpus-audit/scripts/audit_file.py DOC.md
```

`box_width`, `orphans`, `offcentre`, and `ascii_sub` must all be 0.
