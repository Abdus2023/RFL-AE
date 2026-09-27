#!/usr/bin/env python3
"""audit_file.py — audit one markdown document in the corpus.

    python3 audit_file.py ../../EXECUTION.md --range 419-462 \\
        --source-name EXECUTION.md --offset 418 --probes probes/execution.txt

Exit status: 0 clean, 1 problems found, 2 checks could not run (only fatal
under --strict for the render checks).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auditlib as A


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--range", dest="rng", help="expected corpus range, e.g. 419-462")
    ap.add_argument("--source-name", help="name used inside the provenance comment")
    ap.add_argument("--offset", type=int, help="corpus_section - source_section")
    ap.add_argument("--probes", help="file of verbatim source phrases, one per line")
    ap.add_argument("--strict", action="store_true",
                    help="treat SKIPPED checks as failures")
    a = ap.parse_args()

    text = A.read(a.file)
    name = os.path.basename(a.file)
    problems, skipped = [], []
    say = print

    say("=" * 68)
    say(f"AUDIT  {name}")
    say("=" * 68)

    # 1. sections
    exp = None
    if a.rng:
        lo, hi = (int(x) for x in a.rng.split("-"))
        exp = range(lo, hi + 1)
    c = A.check_contiguity(text, exp)
    say(f"sections      : {c['count']}  first={c['first']}  last={c['last']}"
        + (f"  expected={c['expected']}" if exp else ""))
    if not c["contiguous"]:
        problems.append(f"section numbering not contiguous (expected {c.get('expected')})")
    if c["duplicates"]:
        problems.append(f"duplicate section numbers: {c['duplicates']}")

    # 2. fences
    f = A.check_fences(text)
    say(f"fences        : {f['total']}  {'balanced' if f['balanced'] else 'UNBALANCED'}"
        f"  langs={f['langs']}")
    if not f["balanced"]:
        problems.append("unbalanced code fences")

    # 3. rust
    r = A.check_rust_balance(text)
    say(f"rust blocks   : {r['blocks']}  delimiter problems={len(r['problems'])}")
    for p in r["problems"]:
        problems.append(f"rust block {p['block']}: {p['open_n']}{p['open']} vs "
                        f"{p['close_n']}{p['close']}")

    # 4. render
    rd = A.check_render(text)
    if rd["available"]:
        say(f"render        : tables={rd['tables']} h2={rd['h2']} h3={rd['h3']} "
            f"code={rd['code_blocks']} unclassified={rd['unclassified']} "
            f"stray_pipes={rd['stray_pipes']} cmthead={rd['cmthead']} leak={rd['leak']}")
        if rd["unclassified"]:
            problems.append(f"{rd['unclassified']} code block(s) render with no language "
                            f"class -- a placeholder escaped its ```text fence")
        if rd["cmthead"]:
            problems.append("HTML comment leaked into a rendered heading")
        if rd["leak"]:
            problems.append("literal ** leaked into a rendered heading")
        if rd["stray_pipes"]:
            problems.append(f"{rd['stray_pipes']} stray pipe(s) outside <pre>")
    else:
        skipped.append("render (markdown package not installed)")
        say("render        : SKIPPED -- 'markdown' package not installed")
        say("                install with:  python3 -m venv .venv && "
            ".venv/bin/pip install markdown")

    # 5. structural
    blocks = A.text_blocks(text)
    bw = A.check_box_widths(blocks)
    orph = A.check_orphans(blocks)
    offc = A.check_offcentre(blocks)
    ascii_sub = A.check_ascii_substitution(blocks)
    say(f"structure     : text_blocks={len(blocks)} box_width={len(bw)} "
        f"orphans={len(orph)} offcentre={len(offc)} ascii_sub={len(ascii_sub)}")
    for x in bw:
        problems.append(f"box width block {x['block']} row {x['row']}: "
                        f"want {x['want']} got {x['got']}")
    for x in orph:
        problems.append(f"orphaned connector block {x['block']} row {x['row']} "
                        f"col {x['col']}: {x['line']!r}")
    for x in offc:
        problems.append(f"arrow lands on whitespace, block {x['block']} row "
                        f"{x['row']} col {x['col']}: {x['line']!r}")
    for x in ascii_sub:
        problems.append(f"ASCII art mixed into a box-drawing block "
                        f"{x['block']} row {x['row']}: {x['line']!r}")

    # 6. provenance
    if a.source_name and a.offset is not None:
        p = A.check_provenance(text, a.source_name, a.offset)
        say(f"provenance    : {p['comments']}/{p['sections']} comments, "
            f"mapping errors={p['mapping_errors']} (offset {a.offset})")
        if not p["complete"]:
            problems.append(f"provenance incomplete: {p['comments']}/{p['sections']} "
                            f"comments, {p['mapping_errors']} mapping errors")
    else:
        skipped.append("provenance (--source-name/--offset not given)")

    # 7. links
    l = A.check_links(text, os.path.dirname(os.path.abspath(a.file)))
    say(f"links         : anchors={l['anchors']} internal={l['internal']} "
        f"broken_anchors={len(l['broken_anchors'])} md={l['md_links']} "
        f"broken_md={len(l['broken_md'])}")
    if l["broken_anchors"]:
        problems.append(f"broken internal anchors: {l['broken_anchors']}")
    if l["broken_md"]:
        problems.append(f"broken .md links: {l['broken_md']}")
    if l["unresolved_dashed"]:
        problems.append(f"linked heading with dash/arrow whose anchor does not "
                        f"resolve: {l['unresolved_dashed']}")

    # 8. probes
    if a.probes:
        pb = A.check_probes(text, A.load_probes(a.probes))
        say(f"probes        : {pb['total']} phrases, missing={len(pb['missing'])}")
        for m in pb["missing"][:20]:
            problems.append(f"probe missing: {m!r}")
    else:
        skipped.append("probes (--probes not given)")

    say("-" * 68)
    if skipped:
        say(f"SKIPPED ({len(skipped)}): " + "; ".join(skipped))
    if problems:
        say(f"PROBLEMS ({len(problems)}):")
        for p in problems:
            say("  - " + p)
        return 1
    if skipped and a.strict:
        say("FAIL (--strict): checks were skipped, so this run proved nothing")
        return 2
    say("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
