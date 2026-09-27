# 04 — Tooling defects

Part of the [deep audit](README.md). Original report sections **§13, §14, §17,
§18**, grouped here because they all concern `skills/`.

All four findings were re-verified against the branch and all four hold.

---

## §13. Concrete tooling defect — run_all.sh does not actually run all six skills

The README says:

```bash
./skills/run_all.sh
```

and describes it as running everything.

The script does execute six stages, but the actual coverage is:

```text
1. geometry self-test
2. skill validation
3. corpus audit
4. newest-document audit
5. closeout verification
6. negative tests
```

It does not positively execute:

```text
corpus-provenance-numbering/renumber.py
placeholder-splice/splice.py
```

The splice tool is tested only through a deliberately failing negative test.

The numbering tool isn't executed at all.

So:

```text
"all six skills are operationally exercised"
```

is not established.

Classification

```text
PROVED tooling coverage gap.
```

This does not invalidate the skills themselves.

It means:

```text
skill exists
```

is being confused with:

```text
skill has been executed successfully against a positive fixture
```

> **Maintainer note — verified, claim holds.** `renumber.py` is never invoked
> by `run_all.sh`; `splice.py` appears only at the negative-test stage
> (`neg "splice aborts on an unreferenced diagram"`). The report is right that
> existence was being conflated with positive execution. Both tools do work
> when invoked directly — `renumber.py plan` reproduces the shipped
> `ORCHESTRATION.md` provenance blockquote byte-for-byte, and a splice
> round-trip succeeds — but neither was wired into the runner. This is the
> highest-value fix in the report and is now tracked as such.

---

## §14. Concrete tooling defect — validate_skill.py doesn't actually validate that scripts run

Its own docstring says:

```text
validate_skill.py — check a skill is well-formed and its scripts run.
```

But its implementation:

```text
✓ parses frontmatter
✓ checks names
✓ checks descriptions
✓ checks Verification section
✓ byte-compiles *.py
✓ checks referenced files exist
```

It does not execute the scripts.

Therefore:

```text
syntax-valid
```

is being verified, but:

```text
runtime-valid
```

is not.

This is particularly relevant because RFL-AE's philosophy explicitly emphasizes:

> NO EVIDENCE → NO VERIFIED CLAIM

The tooling should obey the same rule.

Recommended distinction

```text
STATIC_VALID
    py_compile succeeds

EXECUTABLE_VALID
    positive invocation succeeds

NEGATIVE_VALID
    known-invalid fixture fails

REPRODUCIBLE
    repeated invocation produces same result
```

> **Maintainer note — verified, claim holds.** `validate_skill.py` imports
> `py_compile` and never imports `subprocess` or invokes anything. The docstring
> overstates what it does: the phrase "and its scripts run" is not backed by the
> implementation. The four-level distinction proposed here
> (`STATIC_VALID` / `EXECUTABLE_VALID` / `NEGATIVE_VALID` / `REPRODUCIBLE`) is a
> better model than the current binary and should be adopted.

---

## §17. Tooling audit itself has a few weaknesses

The Markdown audit is thoughtful and substantially better than a naive regex
checker.

For example, it explicitly detects:

```text
ASCII substitution
box-width errors
orphan connectors
off-centre arrows
unbalanced fences
Rust delimiter imbalance
broken anchors
broken Markdown links
provenance mismatch
```

and it deliberately treats unavailable rendering as:

```text
SKIPPED
```

rather than:

```text
PASS
```

That is good engineering.

But there are limits.

Rust balance checking

It effectively counts:

```text
{
}
(
)
[
]
```

inside Rust code.

That can be fooled by:

```rust
let s = "{";
```

or comments/macros/string literals.

So it is a structural heuristic, not a Rust parser.

That is acceptable for a Markdown corpus audit, but should never be described
as Rust syntax verification.

> **Maintainer note — verified, claim holds.** The implementation is literally
> `if body.count(o) != body.count(c)` over `{}`, `()`, `[]`. It is a heuristic.
> The corpus has never been described as Rust-verified — the Rust toolchain is
> unavailable in the authoring environment and every commit message says the
> blocks were structurally validated only, never compiled — but the audit
> skill's own wording should make that limit explicit.

---

## §18. verify_closeout.py is useful but not cryptographically strong

It checks things such as:

```text
previous document → new document
README → new document
README status
new document → previous document
numbering continuity
```

Good.

But its checks are largely substring/regex based.

For example:

```python
if f"]({a.new})" in readme
```

doesn't establish that the link is the correct README entry.

Likewise:

```python
if a.prev not in new_t
```

doesn't establish that the previous document appears in the correct provenance
block.

Again:

```text
good corpus hygiene tool
```

not:

```text
formal provenance verifier
```

> **Maintainer note — verified, claim holds.** Both quoted expressions appear
> verbatim in the script. `f"]({a.new})" in readme` would be satisfied by a link
> anywhere in the README, including in an unrelated sentence, and
> `a.prev not in new_t` would be satisfied by any incidental mention of the
> previous filename. The tool is correctly scoped as hygiene, not verification,
> and should say so in its own docstring.
