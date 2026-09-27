#!/usr/bin/env python3
"""splice.py — replace @@KEY@@ placeholders with generated diagram bodies.

    python3 splice.py TARGET.md DIAGDIR [--fence-lang text] [--dry-run]

Every diagram in the corpus is generated into its own file and referenced from
the document as ``@@KEY@@`` **inside a fenced block**. This script performs the
substitution and then proves the result, because a bare placeholder that never
got a fence renders as an unclassified code block and every naive structural
check still passes. That was the most serious defect of the whole project.

Guarantees enforced here:
  * every placeholder key resolves to a diagram file (no missing)
  * every diagram file is referenced (no orphans left on disk)
  * each key occurs exactly once
  * AFTER substitution, each body occurs literally as  ```lang\\n<body>\\n```
  * no ``@@...@@`` remains

Exit 0 only when all of the above hold.
"""
import argparse
import glob
import os
import re
import sys


def load_diagrams(d: str) -> dict:
    out = {}
    for path in sorted(glob.glob(os.path.join(d, "*.txt"))):
        with open(path, encoding="utf-8") as fh:
            out[os.path.basename(path)[:-4]] = fh.read().rstrip("\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("diagdir")
    ap.add_argument("--fence-lang", default="text")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    with open(a.target, encoding="utf-8") as fh:
        text = fh.read()
    diags = load_diagrams(a.diagdir)
    keys = re.findall(r"@@([A-Za-z0-9_]+)@@", text)
    uniq = sorted(set(keys))

    print(f"placeholders  : {len(keys)} occurrences, {len(uniq)} unique")
    print(f"diagrams      : {len(diags)} in {a.diagdir}")

    problems = []
    missing = [k for k in uniq if k not in diags]
    unused = [k for k in sorted(diags) if k not in uniq]
    if missing:
        problems.append(f"placeholders with no diagram file: {missing}")
    if unused:
        problems.append(f"diagram files never referenced: {unused}")
    for k in uniq:
        n = text.count(f"@@{k}@@")
        if n != 1:
            problems.append(f"key {k} occurs {n} times (must be exactly 1)")

    if problems:
        for p in problems:
            print("  - " + p)
        print("SPLICE ABORTED (nothing written)")
        return 1

    if a.dry_run:
        print("dry run OK -- no changes written")
        return 0

    out = text
    for k in uniq:
        out = out.replace(f"@@{k}@@", diags[k])

    # ---- the assertion that matters
    escaped = [k for k in uniq
               if f"```{a.fence_lang}\n{diags[k]}\n```" not in out]
    leftover = re.findall(r"@@[A-Za-z0-9_]+@@", out)
    if escaped:
        print(f"  - NOT inside a ```{a.fence_lang} fence after splicing: {escaped}")
    if leftover:
        print(f"  - unresolved placeholders remain: {leftover}")
    if escaped or leftover:
        print("SPLICE ABORTED (nothing written)")
        return 1

    with open(a.target, "w", encoding="utf-8") as fh:
        fh.write(out)

    blocks = re.findall(r"^```(\w*)\n(.*?)\n^```", out, re.S | re.M)
    gen = {diags[k] for k in uniq}
    in_fence = sum(1 for _l, b in blocks if b in gen)
    unclass = sum(1 for l, _b in blocks if not l)
    print(f"spliced       : {len(uniq)} diagrams")
    print(f"fenced blocks : {len(blocks)} total, {in_fence} are generated diagrams, "
          f"{len(blocks) - in_fence} are source text")
    print(f"unclassified  : {unclass} (fences with no language)")
    if unclass:
        print("WARNING: unclassified fences exist -- audit will fail on these")
        return 1
    print("SPLICE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
