---
name: skill-creator
description: Author, validate, and maintain skills in this repository. Use when creating a new skill from a repeated workflow, restructuring an existing skill, or checking that a skill's scripts actually run and fail loudly. Establishes the SKILL.md format, the scripts/ layout, and the rule that every skill must ship a negative test.
---

# skill-creator

Turn a workflow that has been done by hand into a skill someone else can run
without re-deriving it. A skill is **executable knowledge**: prose that says
what to do, plus scripts that do it and prove they did.

## When to use

- The same multi-step procedure has now been performed at least twice.
- A procedure produced a defect that a check would have caught.
- Knowledge currently exists only in someone's head or in a chat transcript.

Do not create a skill for a one-off. The test is whether the next person could
run it without asking you anything.

## Layout

```
skills/
  <skill-name>/
    SKILL.md          required: frontmatter + the knowledge
    scripts/          optional: runnable tools
    references/       optional: long material loaded on demand
```

`SKILL.md` opens with YAML frontmatter:

```yaml
---
name: lowercase-hyphenated
description: One or two sentences. Say what it does AND when to use it --
  this is the text an agent matches against when deciding whether to load it.
---
```

The description is the discovery surface. A description that only says what the
skill *is* will not get loaded at the right moment; include the trigger.

## The five rules

**1. Scripts must be runnable as given.** No "adapt this to your paths". Take
arguments. If a script hardcodes a path it is a note, not a tool.

**2. A check that cannot run must never report success.** If a dependency is
missing, print `SKIPPED`, say what to install, and exit non-zero under
`--strict`. The worst failure available is a green run that verified nothing.

**3. Ship a negative test.** A checker that has never been shown a defect is
unverified. Every audit skill here is demonstrated against a deliberately
broken fixture, and the expected findings are listed. When you add a check,
add the input that trips it.

**4. Record the trap, not just the rule.** "Use absolute columns" is
forgettable. "The original helper used `out.ljust(col) + text`, which silently
concatenated on overlap and produced the corrupt line `acceptquarantine` while
reporting success" is not. Every trap section in these skills came from a real
defect; keep the symptom, because that is what lets someone recognise it.

**5. Verify against real data before declaring done.** Run the new script on
the actual corpus and confirm it reproduces the numbers that were previously
reported by hand. Agreement with a known-good result is the check. So is
agreement on a *byte-for-byte* artifact, which is stronger — see
`corpus-provenance-numbering`, whose `plan` mode regenerates a shipped
blockquote exactly.

## Creating a skill

```bash
python3 skills/skill-creator/scripts/new_skill.py <skill-name> --description "..."
```

Then fill in `SKILL.md`. Recommended section order:

1. **Purpose** — one paragraph.
2. **When to use / when not to** — the boundary matters more than the summary.
3. **Quick start** — copy-pasteable commands that work.
4. **Invariants** — the rules that must not be violated.
5. **Traps** — numbered, each with symptom, cause, fix.
6. **Verification** — how to prove the skill works, including the negative test.

## Verification

```bash
python3 skills/skill-creator/scripts/validate_skill.py skills/<skill-name>
python3 skills/skill-creator/scripts/validate_skill.py skills/          # all
```

Checks: frontmatter present and well-formed, `name` matches the directory,
description is non-trivial, every `scripts/*.py` compiles, every command quoted
in the SKILL.md that starts with `python3 skills/` actually exists.

## Anti-patterns

- **Documentation dressed as a skill.** No scripts, no verification section.
- **A script that reimplements the thing it checks.** If the checker contains
  its own copy of the logic under test, it verified a stand-in.
- **Checks that pass by construction.** Asserting something the code just
  computed is not a test.
- **Silent fallbacks.** `try: import x except: pass` in a validator is how a
  green run starts meaning nothing.
- **Tools kept in `/tmp`.** `/tmp` does not survive between sessions; the
  entire diagram toolchain was lost once this way. Skills live in the repo.
