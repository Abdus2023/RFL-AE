#!/usr/bin/env python3
"""verify_closeout.py — confirm the end-of-turn ritual actually happened.

    python3 verify_closeout.py --new ORCHESTRATION.md --prev EXECUTION.md

The close-out for every new document is:
  1. the PREVIOUS document gains a forward link to the new one
  2. README lists the new document with its corpus range
  3. README's Status line states the correct document count and max section
  4. the new document's provenance blockquote names the previous document

Each is cheap to forget and none is caught by the content audit, so they get
their own check.
"""
import argparse
import os
import re
import sys

# auditlib lives in the sibling skill; skills/<this>/scripts -> skills/<that>/scripts
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "markdown-corpus-audit", "scripts"))
import auditlib as A  # noqa: E402


_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven",
         "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
         "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
         "eighty", "ninety"]


def number_word(n: int) -> str:
    """1..99 as the capitalised English word the README Status line uses.

    Compound tens are hyphenated ("Twenty-one"), so the caller's regex must
    accept a hyphen. Anything outside 1..99 falls back to the numeral.
    """
    if 0 <= n < 20:
        return _ONES[n].capitalize()
    if 20 <= n < 100:
        t, o = divmod(n, 10)
        return _TENS[t].capitalize() + ("-" + _ONES[o] if o else "")
    return str(n)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", required=True)
    ap.add_argument("--prev", required=True)
    ap.add_argument("--readme", default="README.md")
    ap.add_argument("--dir", default=".")
    a = ap.parse_args()

    def p(f):
        return os.path.join(a.dir, f)

    new_t = A.read(p(a.new))
    prev_t = A.read(p(a.prev))
    readme = A.read(p(a.readme)) if os.path.exists(p(a.readme)) else ""

    secs = [n for n, _t, _i in A.sections(new_t)]
    prev_secs = [n for n, _t, _i in A.sections(prev_t)]
    problems = []

    # 1. forward link
    if f"]({a.new})" not in prev_t:
        problems.append(f"{a.prev} has no forward link to {a.new}")

    # 2. README bullet
    if f"]({a.new})" not in readme:
        problems.append(f"{a.readme} does not list {a.new}")

    # 3. README status
    all_md = [f for f in os.listdir(a.dir)
              if f.endswith(".md") and f != os.path.basename(a.readme)]
    total_secs, max_sec = 0, 0
    for f in all_md:
        s = [n for n, _t, _i in A.sections(A.read(p(f)))]
        total_secs += len(s)
        if s:
            max_sec = max(max_sec, max(s))
    want_count = number_word(len(all_md))
    # `[\w-]+` not `\w+`: the count is a hyphenated compound past twenty
    # ("Twenty-one"), and `\w` stops at the hyphen so it used to match "one".
    m = re.search(r"([\w-]+) specification documents covering \u00a71\u2013\u00a7(\d+)", readme)
    if not m:
        problems.append("README Status line not found or not in the expected form")
    else:
        if m.group(1).lower() != want_count.lower():
            problems.append(f"README says {m.group(1)} documents, found {len(all_md)} "
                            f"(expected '{want_count}')")
        if int(m.group(2)) != max_sec:
            problems.append(f"README says \u00a71\u2013\u00a7{m.group(2)}, corpus max is "
                            f"\u00a7{max_sec}")

    # 4. blockquote names the previous doc
    if a.prev not in new_t:
        problems.append(f"{a.new} never mentions {a.prev} (provenance blockquote "
                        f"should state what it continues from)")

    print("=" * 68)
    print(f"CLOSE-OUT  {a.prev} -> {a.new}")
    print("=" * 68)
    print(f"prev sections : {len(prev_secs)} (last {prev_secs[-1] if prev_secs else '-'})")
    print(f"new sections  : {len(secs)} "
          f"({secs[0] if secs else '-'}..{secs[-1] if secs else '-'})")
    if prev_secs and secs and secs[0] != prev_secs[-1] + 1:
        problems.append(f"numbering gap: {a.prev} ends at {prev_secs[-1]} but "
                        f"{a.new} starts at {secs[0]}")
    print(f"documents     : {len(all_md)}  corpus max section: {max_sec}")
    print(f"forward link  : {'yes' if f']({a.new})' in prev_t else 'NO'}")
    print(f"README bullet : {'yes' if f']({a.new})' in readme else 'NO'}")
    print(f"README status : {m.group(0) if m else 'MISSING'}")
    print("-" * 68)
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        for x in problems:
            print("  - " + x)
        return 1
    print("CLOSE-OUT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
