---
name: spec-turn-closeout
description: The end-of-document ritual for a specification corpus — forward link from the previous document, README entry and status bump, numbering continuity, commit, push, and verification that all of it actually happened. Use after a new specification document has been written and audited and before declaring the turn complete.
---

# spec-turn-closeout

Writing the document is about 80% of the work. The remainder is what makes the
corpus navigable, and every step of it is easy to forget and none of it is
caught by the content audit.

## When to use

After a new document has been written, spliced, and audited clean — before
committing.

## When not to use

Edits to an existing document. (Though the README status check is still worth
running if the section count changed.)

## The ritual

1. **Forward link.** The *previous* document gains a closing
   `**Done — see [NEW.md](NEW.md)** (§a–§b, source §§1–§n), which specifies …`
   paragraph summarising what the new document covers.
2. **README entry.** A bullet with the corpus range, the source range, and a
   one-paragraph summary, in corpus order.
3. **README status.** Bump the document count and the `§1–§max` range.
4. **Provenance blockquote** at the top of the new document, naming the previous
   document and stating the offset (see `corpus-provenance-numbering`).
5. **Commit** with a message stating both ranges: source and corpus.
6. **Push** to the working branch, then **confirm** the remote SHA equals the
   local one.

## Quick start

```bash
python3 skills/spec-turn-closeout/scripts/verify_closeout.py \
    --new ORCHESTRATION.md --prev EXECUTION.md
```

Checks all four content conditions plus numbering continuity
(`prev.last + 1 == new.first`), and derives the expected document count and
corpus maximum from the directory rather than trusting the README.

## Invariants

1. The new document's first section is exactly `previous last + 1`.
2. Every document is reachable from the README.
3. The README's stated document count and maximum section agree with the corpus
   as it exists on disk.
4. The commit message names both numberings, so history can be read in either.

## Traps

1. **Editing the README by hand and getting the count wrong.** The check derives
   the count from the directory and the spelled-out word from `number_word()`,
   so "Thirteen" after a fourteenth file lands is caught. Past twenty the word
   is a hyphenated compound ("Twenty-one"), and the status regex must accept a
   hyphen — `(\w+)` matches only the tail and reports "one". Both the table and
   the regex were wrong at twenty-one; `number_word()` now generates 1..99.
2. **Forgetting the forward link.** The previous document is the one nobody is
   looking at when the new one is written.
3. **Assuming a push succeeded.** `git push` can fail on auth or a non-fast-
   forward. Compare `git rev-parse HEAD` against
   `git ls-remote origin refs/heads/<branch>`.
4. **A sandbox reset between sessions.** In this project the local checkout was
   rolled back to the initial commit while the remote kept every commit. Before
   doing anything destructive, fetch and compare the working tree against the
   remote branch blob-for-blob; if they match, `git reset --hard` to the remote
   is safe. Never assume local history is the only copy.
5. **Committing generated scratch.** Diagram files, venvs, and probe fixtures
   stay out of the repo. Only the documents and the skills are committed.
6. **Declaring done without running the project's own check.** Run the audit and
   the close-out check, and say what they returned. A clean exit code is not a
   pass if the output is wrong.

## Verification

```bash
# positive: the real turn-14 close-out passes
python3 skills/spec-turn-closeout/scripts/verify_closeout.py \
    --new ORCHESTRATION.md --prev EXECUTION.md
```

Expected: `CLOSE-OUT OK`, exit 0, with `documents : 25`, `corpus max section:
803`, forward link `yes`, README bullet `yes`, and status
`Twenty-five specification documents covering §1–§803`.

Negative tests — each must exit 1:

```bash
# a previous document with no forward link
python3 skills/spec-turn-closeout/scripts/verify_closeout.py \
    --new ORCHESTRATION.md --prev ARCHITECTURE.md
# a document that is not listed in the README
python3 skills/spec-turn-closeout/scripts/verify_closeout.py \
    --new README.md --prev ORCHESTRATION.md
```
