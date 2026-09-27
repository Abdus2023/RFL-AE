#!/usr/bin/env bash
# run_all.sh — execute every check the skills provide, in dependency order.
#
#   ./skills/run_all.sh [python]
#
# Pass a python interpreter that has the `markdown` package installed if the
# default does not, e.g.  ./skills/run_all.sh .venv/bin/python
#
# Exits non-zero if any stage fails. Nothing here exits 0 by default.
set -uo pipefail

PY="${1:-python3}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0
stage() {
  echo
  echo "════════ $1 ════════"
  shift
  "$@"
  rc=$?
  if [ $rc -ne 0 ]; then
    echo ">>> stage FAILED (exit $rc)"
    fail=1
  fi
  return 0
}

echo "python : $PY"
echo "repo   : $ROOT"
$PY -c "import markdown; print('markdown:', markdown.__version__)" 2>/dev/null \
  || echo "markdown: NOT INSTALLED -- render checks will be SKIPPED"

echo
echo "════════ 1/7 geometry self-test ════════"
python3 skills/ascii-diagram-forge/scripts/examples.py > /tmp/_geo.log 2>&1
rc=$?
tail -16 /tmp/_geo.log
[ $rc -ne 0 ] && { echo ">>> stage FAILED (exit $rc)"; fail=1; }

stage "2/7 skills are well-formed" \
  $PY skills/skill-creator/scripts/validate_skill.py skills/

# --strict: a render check that could not run must fail the stage, not pass it
stage "3/7 corpus audit (17 documents)" \
  $PY skills/markdown-corpus-audit/scripts/audit_corpus.py --expect-gaps 108 --strict

stage "4/7 every internal link resolves (rendered HTML)" \
  $PY skills/markdown-corpus-audit/scripts/linkaudit.py \
      --allow skills/markdown-corpus-audit/SKILL.md

stage "5/7 last document audited in full" \
  $PY skills/markdown-corpus-audit/scripts/audit_file.py PROTOCOL-P58.md \
      --range 576-610 --source-name PROTOCOL-P58.md --offset 575 --strict \
      --probes skills/markdown-corpus-audit/probes/protocol-p58.txt

stage "6/7 close-out ritual verified" \
  $PY skills/spec-turn-closeout/scripts/verify_closeout.py \
      --new PROTOCOL-P58.md --prev PROTOCOL-IMPL.md

echo
echo "════════ 7/7 negative tests (each MUST fail) ════════"
mkdir -p /tmp/negtest /tmp/negtest_splice/diag
cat > /tmp/negtest/BROKEN.md <<'EOF'
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

neg() {
  desc="$1"; shift
  "$@" > /tmp/_neg.log 2>&1
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "  PASS  $desc  (exit $rc, $(grep -c '^  - ' /tmp/_neg.log) findings)"
  else
    echo "  FAIL  $desc  -- expected a non-zero exit, got 0"
    fail=1
  fi
}

neg "audit catches 8 planted defects" \
  $PY skills/markdown-corpus-audit/scripts/audit_file.py /tmp/negtest/BROKEN.md \
      --source-name BROKEN.md --offset 0
neg "close-out fails with no forward link" \
  $PY skills/spec-turn-closeout/scripts/verify_closeout.py \
      --new PROTOCOL-KERNEL.md --prev ARCHITECTURE.md

printf 'alpha\n  |\n  v\nbeta\n' > /tmp/negtest_splice/diag/DFOO.txt
printf 'unused\n'                > /tmp/negtest_splice/diag/DUNUSED.txt
printf '# F\n\n## 1. First\n\n```text\n@@DFOO@@\n```\n' > /tmp/negtest_splice/T.md
neg "splice aborts on an unreferenced diagram" \
  $PY skills/placeholder-splice/scripts/splice.py /tmp/negtest_splice/T.md \
      /tmp/negtest_splice/diag --dry-run

# BROKEN.md carries `](#4-does-not-exist)` and `](NOPE.md)`; no --allow here,
# so the link checker must fail rather than excuse them.
neg "link checker catches a broken anchor and a missing target" \
  $PY skills/markdown-corpus-audit/scripts/linkaudit.py --root /tmp/negtest

echo
if [ $fail -ne 0 ]; then
  echo "RESULT: FAILURES ABOVE"
  exit 1
fi
echo "RESULT: ALL STAGES PASSED"
