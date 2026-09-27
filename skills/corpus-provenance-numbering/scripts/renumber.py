#!/usr/bin/env python3
"""renumber.py — global corpus numbering with lossless source provenance.

The rule, fixed for the whole corpus:

    corpus_section = source_section + offset
    offset         = last corpus section of the PREVIOUS document

so numbering continues across files while the original source numbering stays
recoverable. Every renumbered heading carries a machine-readable comment.

Two modes.

  plan    Compute the range for a new document and emit the provenance
          blockquote, the Contents list, and the heading/comment pairs.
          Nothing is written.

              python3 renumber.py plan --source-name ORCHESTRATION.md \\
                  --sections 55 --prev-last 462

  apply   Rewrite a draft's `## n. Title` headings into corpus numbering and
          insert the provenance comment under each one.

              python3 renumber.py apply DRAFT.md --source-name ORCH.md \\
                  --offset 462 --out ORCHESTRATION.md

Heading form (two deliberate, load-bearing choices):
  * The comment goes on its OWN LINE, never inline. Python-Markdown leaks an
    inline `<!-- ... -->` into the visible <h2> text and changes the slug.
  * The `§` is dropped from the heading number (`## 463.` not `## §463.`) so the
    section regex `^## (\\d+)\\. ` keeps matching.
A blank line between heading and comment is allowed but the comment must be the
next non-blank line.
"""
import argparse
import re
import sys

COMMENT = "<!-- source: {name} \u00a7{n} -->"


def blockquote(name: str, count: int, prev_last: int, prev_file: str,
               doc_title: str) -> str:
    lo, hi = prev_last + 1, prev_last + count
    return (
        f"> **Provenance and numbering.** This document was supplied as "
        f"*{doc_title}*, numbered \u00a71\u2013\u00a7{count} in the source. To keep the "
        f"corpus contiguous, its sections are renumbered "
        f"**\u00a7{lo}\u2013\u00a7{hi}**, continuing directly from "
        f"[{prev_file}]({prev_file}) (which ends at \u00a7{prev_last}). The mapping is "
        f"**`corpus_section = source_section + {prev_last}`**. The original source "
        f"numbering is preserved on every heading as a machine-readable HTML "
        f"comment of the form `{COMMENT.format(name=name, n='n')}`, so source "
        f"traceability is lossless and either numbering can be used to locate a "
        f"clause."
    )


def github_slug(h: str) -> str:
    """GitHub (gfm) slugger. Each space becomes one hyphen; runs are NOT
    collapsed, so a heading whose glyph was stripped between two spaces yields
    a double hyphen."""
    s = h.lower().replace("'", "")
    return re.sub(r"[^\w\- ]", "", s).replace(" ", "-")


def plan(name: str, count: int, prev_last: int, prev_file: str, title: str) -> int:
    lo, hi = prev_last + 1, prev_last + count
    print("=" * 68)
    print(f"NUMBERING PLAN  {name}")
    print("=" * 68)
    print(f"source range  : 1 .. {count}")
    print(f"offset        : +{prev_last}  (last section of {prev_file})")
    print(f"corpus range  : {lo} .. {hi}")
    print()
    print("--- paste this blockquote under the document title ---")
    print()
    print(blockquote(name, count, prev_last, prev_file, title))
    print()
    print("--- Contents (anchor links resolve under GitHub's slugger) ---")
    print()
    for i in range(1, count + 1):
        corpus = prev_last + i
        print(f"- [{corpus}. <title {i}>](#{corpus}-<title-{i}-slugified>)")
    print()
    print("--- heading / comment pairs ---")
    print()
    for i in range(1, min(count, 5) + 1):
        print(f"## {prev_last + i}. <title {i}>")
        print(COMMENT.format(name=name, n=i))
        print()
    if count > 5:
        print(f"... and so on through ## {hi} / {COMMENT.format(name=name, n=count)}")
    return 0


def apply(draft: str, name: str, offset: int, out: str) -> int:
    with open(draft, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    n = 0
    res = []
    for line in lines:
        m = re.match(r"^## (?:\u00a7)?(\d+)\. (.*)$", line)
        if m:
            n += 1
            corpus = n + offset
            res.append(f"## {corpus}. {m.group(2)}")
            res.append(COMMENT.format(name=name, n=n))
        else:
            res.append(line)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(res))
    print(f"renumbered {n} sections: source 1..{n} -> corpus {1 + offset}..{n + offset}")
    print(f"written to {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)

    p = sub.add_parser("plan", help="compute range + emit blockquote and Contents")
    p.add_argument("--source-name", required=True)
    p.add_argument("--sections", type=int, required=True)
    p.add_argument("--prev-last", type=int, required=True)
    p.add_argument("--prev-file", default="")
    p.add_argument("--title", default="")

    q = sub.add_parser("apply", help="renumber a draft's headings in place")
    q.add_argument("draft")
    q.add_argument("--source-name", required=True)
    q.add_argument("--offset", type=int, required=True)
    q.add_argument("--out", required=True)

    a = ap.parse_args()
    if a.mode == "plan":
        prev_file = a.prev_file or "PREVIOUS.md"
        return plan(a.source_name, a.sections, a.prev_last, prev_file,
                    a.title or a.source_name)
    return apply(a.draft, a.source_name, a.offset, a.out)


if __name__ == "__main__":
    sys.exit(main())
