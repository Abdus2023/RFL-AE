# RFL-AE skills

The reusable toolchain distilled from producing this specification corpus —
twenty-seven documents, 841 sections, 1746 text-fenced diagram blocks (619 of them
reproducible from the committed generators in `diagrams/`) — across twenty-seven
consecutive specification pastes.

These are not notes about the process. They are the process, runnable.

## The skills

| skill | what it does |
|---|---|
| [`ascii-diagram-forge`](ascii-diagram-forge/SKILL.md) | Generate box-drawing diagrams from computed column arithmetic. Never hand-type a diagram. |
| [`corpus-provenance-numbering`](corpus-provenance-numbering/SKILL.md) | Renumber a new document into a contiguous corpus while keeping source numbering losslessly recoverable. |
| [`placeholder-splice`](placeholder-splice/SKILL.md) | Substitute generated diagrams via `@@KEY@@` and prove each one landed inside a fence. |
| [`markdown-corpus-audit`](markdown-corpus-audit/SKILL.md) | Audit one document or the whole corpus for the defects that render silently. |
| [`spec-turn-closeout`](spec-turn-closeout/SKILL.md) | The end-of-document ritual: forward link, README, status, continuity, commit. |
| [`skill-creator`](skill-creator/SKILL.md) | Meta-skill: author and validate new skills in this format. |

## The workflow they encode

```
      paste a specification
              │
              ▼
  corpus-provenance-numbering      compute the range, emit the blockquote
              │
              ▼
     write the document            headings + provenance comments + @@KEY@@
              │
              ▼
    ascii-diagram-forge            generate each diagram by column arithmetic
              │
              ▼
       placeholder-splice          substitute, and assert the fenced form
              │
              ▼
     markdown-corpus-audit         per file, then the whole corpus
              │
              ▼
      spec-turn-closeout           forward link, README, commit, push, confirm
```

Each stage's output is the next stage's input, and each stage fails loudly
rather than passing silently.

## The one rule underneath all of them

**A check that cannot run is never reported as a pass.**

Every script here either verifies something or says it could not. Nothing in
this directory exits 0 by default. That rule came from a concrete failure: 37
placeholders were spliced outside their fences, every structural check still
reported success, and the only symptom was a `<pre>` count that disagreed with
the expected number of fence pairs.

Related: **read the checker's coverage before trusting its verdict.** Twice in
this project a reported "defect" was a bug in the check — an over-strict orphan
rule that flagged 17 correct rows, and a patch that dropped a loop variable and
reported 2 phantom failures. Both were resolved by inspecting the rendered block
before changing the diagram.

## Running everything

```bash
# the geometry library's self-test
python3 skills/ascii-diagram-forge/scripts/examples.py

# every skill is well-formed and its scripts compile
python3 skills/skill-creator/scripts/validate_skill.py skills/

# the corpus itself is clean
python3 skills/markdown-corpus-audit/scripts/audit_corpus.py --expect-gaps 108

# the last close-out happened
python3 skills/spec-turn-closeout/scripts/verify_closeout.py \
    --new ORCHESTRATION.md --prev EXECUTION.md
```

`audit_corpus.py` and `audit_file.py` need the `markdown` package for their
render checks:

```bash
python3 -m venv .venv && .venv/bin/pip install markdown
```

Without it they print `SKIPPED` for those columns and fail under `--strict`
rather than pretending to pass.

## Conventions

- Skills live in the repository, not `/tmp`. The entire diagram toolchain was
  lost once when `/tmp` was wiped between sessions.
- Scripts take arguments. A hardcoded path is a note, not a tool.
- Every skill ships a negative test. A checker that has never been shown a
  defect is unverified.
- Traps are recorded with their symptom, because the symptom is what lets
  someone recognise the defect next time.
