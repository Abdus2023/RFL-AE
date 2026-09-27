#!/usr/bin/env python3
"""audit_corpus.py — sweep every specification document in the corpus.

    python3 audit_corpus.py            # from the repo root
    python3 audit_corpus.py --dir ..

Reports, per file: section count, range, fence balance, unclassified code
blocks, comment-in-heading leaks, bold-in-heading leaks, broken links, and
provenance coverage. Then the corpus totals: document count, total sections,
numbering range, duplicates, and gaps.

Gaps are expected to contain exactly the sections the source never defined
(RFL-AE has a deliberate gap at 108). Use --expect-gaps to assert that.
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auditlib as A

EXCLUDE = {"README.md"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=".", help="directory holding the .md files")
    ap.add_argument("--expect-gaps", default="",
                    help="comma-separated section numbers that are allowed to be "
                         "missing (RFL-AE: 108)")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    files = sorted(f for f in os.listdir(a.dir)
                   if f.endswith(".md") and f not in EXCLUDE)
    if not files:
        print(f"no .md files in {a.dir}")
        return 2

    hdr = (f"{'FILE':<22}{'SECS':>5}{'RANGE':>13}{'FENCE':>7}{'UNCL':>6}"
           f"{'CMT':>5}{'LEAK':>6}{'LINK':>6}{'PROV':>13}")
    print("=" * len(hdr))
    print(hdr)
    print("=" * len(hdr))

    all_secs, bad_files, skipped_any = [], [], False
    for f in files:
        path = os.path.join(a.dir, f)
        text = A.read(path)
        secs = [n for n, _t, _i in A.sections(text)]
        all_secs += secs
        fences = A.check_fences(text)
        rd = A.check_render(text)
        links = A.check_links(text, a.dir)
        # offset is DERIVED per file (356/386/418/462 ...), never assumed
        prov = A.check_provenance(text, f)

        if rd["available"]:
            uncl, cmt, leak = rd["unclassified"], rd["cmthead"], rd["leak"]
        else:
            uncl = cmt = leak = "-"
            skipped_any = True
        broken = len(links["broken_anchors"]) + len(links["broken_md"]) \
            + len(links["unresolved_dashed"])
        # provenance is only meaningful for files that actually use it
        has_prov = "<!-- source: " in text
        prov_s = (f"{prov['comments']}/{prov['sections']}"
                  + (f" +{prov['offset']}" if prov["offset"] is not None else " ?off")
                  if has_prov else "n/a")

        rng = f"{min(secs)}-{max(secs)}" if secs else "-"
        print(f"{f:<22}{len(secs):>5}{rng:>13}{fences['total']:>7}"
              f"{str(uncl):>6}{str(cmt):>5}{str(leak):>6}{broken:>6}{prov_s:>13}")

        errs = []
        if not fences["balanced"]:
            errs.append("unbalanced fences")
        if rd["available"]:
            if uncl:
                errs.append(f"{uncl} unclassified code block(s)")
            if cmt:
                errs.append("comment in heading")
            if leak:
                errs.append("** in heading")
        if broken:
            errs.append(f"{broken} broken link(s)")
        if has_prov and not prov["complete"]:
            errs.append("provenance incomplete")
        if errs:
            bad_files.append((f, errs))

    print("=" * len(hdr))
    print(f"documents     : {len(files)}")
    print(f"sections      : {len(all_secs)}")
    print(f"range         : {min(all_secs)} .. {max(all_secs)}")
    dupes = sorted(k for k, v in collections.Counter(all_secs).items() if v > 1)
    print(f"duplicates    : {dupes or 'none'}")
    gaps = [i for i in range(min(all_secs), max(all_secs) + 1) if i not in set(all_secs)]
    print(f"gaps          : {gaps or 'none'}")

    expected_gaps = [int(x) for x in a.expect_gaps.split(",") if x.strip()]
    problems = []
    if dupes:
        problems.append(f"duplicate section numbers: {dupes}")
    if a.expect_gaps and gaps != expected_gaps:
        problems.append(f"gaps {gaps} != expected {expected_gaps}")
    for f, errs in bad_files:
        problems.append(f"{f}: " + ", ".join(errs))

    print()
    if skipped_any and not A.HAVE_MARKDOWN:
        print("NOTE: render checks SKIPPED -- 'markdown' is not installed, so")
        print("      unclassified/cmthead/leak columns are unknown, NOT clean.")
        if a.strict:
            problems.append("render checks could not run")
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        for p in problems:
            print("  - " + p)
        return 1
    print("ALL FILES OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
