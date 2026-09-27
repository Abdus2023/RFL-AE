---
name: placeholder-splice
description: Substitute generated diagram bodies into a markdown document via @@KEY@@ placeholders and then prove each one landed inside a fenced block. Use after generating diagrams with ascii-diagram-forge and before auditing, whenever a document references diagrams by placeholder rather than embedding them by hand.
---

# placeholder-splice

Generated diagrams are written to their own files and referenced from the
document as `@@KEY@@` **inside a fenced block**:

````markdown
```text
@@D43@@
```
````

This keeps the document readable before the diagrams exist, lets a diagram be
regenerated without touching prose, and — the reason it matters — makes an
unspliced or unfenced placeholder detectable.

## When to use

- After `ascii-diagram-forge` has produced a directory of diagram files.
- Any time a document embeds generated content by reference.

## When not to use

- A one-off diagram you are pasting once and will never regenerate.

## Quick start

```bash
# check that everything lines up without writing anything
python3 skills/placeholder-splice/scripts/splice.py DOC.md diagrams/ --dry-run

# perform the substitution
python3 skills/placeholder-splice/scripts/splice.py DOC.md diagrams/
```

`--fence-lang` is retained for compatibility but no longer drives the assertion,
which is now per-block and language-agnostic.

## What it guarantees

The script refuses to write unless all of these hold:

1. every `@@KEY@@` in the document has a matching diagram file;
2. every diagram file is referenced (nothing orphaned on disk);
3. each key occurs **exactly once**;
4. **after** substitution, each body is the *exact content* of a fenced block
   that carries a language — any language, since a document may mix ```` ```text ````
   diagrams with ```` ```json ```` records;
5. no `@@…@@` remains;
6. no fenced block is left without a language.

Guarantee 4 is the one that matters. It used to test for `` ```text\n<body>\n``` ``
against a single hardcoded language, which wrongly rejected a document that fenced
three JSON records as ```` ```json ````. The current form is both language-agnostic
and stricter: it requires a whole-block match rather than a substring, so a body
that merely *appears* somewhere inside a larger block no longer passes.

## Traps

1. **Bare placeholders that never got a fence — the most serious defect of the
   whole project.** 37 diagrams were written unwrapped, every structural check
   still "passed", and the only symptom was a `<pre>` count that disagreed with
   the expected number of fence pairs plus 3 blocks rendering with no language
   class. **Fix:** assert the fenced form literally after substitution, and
   require `unclassified == 0` in the render audit.
2. **A placeholder inside the wrong fence.** ```` ```rust ```` around a diagram
   still renders, but syntax highlighting mangles it and the language histogram
   no longer means anything.
3. **Two diagrams with the same key.** The replacement is global; the second
   occurrence silently gets the first's body. The script's "occurs exactly once"
   rule exists for this.
4. **A diagram file left over from a previous document.** If `diagrams/` is
   reused, an unreferenced file looks like success. The script reports
   unreferenced files as an error.
5. **Trusting a splice that printed a count.** A count of replaced placeholders
   says nothing about fences. Check the fenced form.

## Verification

Round-trip on a fixture:

```bash
mkdir -p /tmp/st/diag
printf 'alpha\n  |\n  v\nbeta\n' > /tmp/st/diag/DFOO.txt
printf '# F\n\n## 1. First\n\n```text\n@@DFOO@@\n```\n' > /tmp/st/T.md

python3 skills/placeholder-splice/scripts/splice.py /tmp/st/T.md /tmp/st/diag --dry-run
python3 skills/placeholder-splice/scripts/splice.py /tmp/st/T.md /tmp/st/diag
grep -A4 '```text' /tmp/st/T.md            # body must be inside the fence
```

Negative test — an unreferenced diagram file must abort with exit 1:

```bash
printf 'unused\n' > /tmp/st/diag/DUNUSED.txt
python3 skills/placeholder-splice/scripts/splice.py /tmp/st/T.md /tmp/st/diag --dry-run
echo $?     # 1
```

Then run the audit on the real document and confirm `unclassified: 0`.
