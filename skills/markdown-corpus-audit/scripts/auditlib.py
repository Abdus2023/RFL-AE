"""auditlib.py — the RFL-AE markdown corpus audit engine.

Run via audit_file.py (one document) or audit_corpus.py (whole corpus).

Design rule that came from a real incident: **a check that cannot run is never
reported as passing.** If the `markdown` package is missing, every render check
reports SKIPPED and `--strict` turns that into a non-zero exit. The failure mode
this prevents is a green run that verified nothing.

The two structural rules below were each the subject of a false alarm and are
stated precisely:

* Orphaned connectors fire ONLY when an adjacent row actually contains
  connectors and none of them aligns within one column. A `▼` sitting between
  two plain-text label rows is normal (that is what `dchain` produces) and must
  not be reported.
* Off-centre is tested as "does the arrow land on a label character", NOT as
  "is every whitespace-delimited token centred". A multi-word label such as
  `Agent A` tokenises into two columns and would otherwise be flagged.
"""

from __future__ import annotations

import collections
import os
import re
from typing import Dict, List, Optional, Sequence, Tuple

CONN = set("\u2502\u251c\u2514\u250c\u2510\u252c\u2534\u253c\u25bc\u25b2\u2500\u2524")
VERT = "\u2502"
DOWN = "\u25bc"

try:
    import markdown as _markdown
    HAVE_MARKDOWN = True
except ImportError:          # pragma: no cover
    _markdown = None
    HAVE_MARKDOWN = False

SKIP = "SKIPPED"


# ------------------------------------------------------------------ primitives

def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def sections(text: str) -> List[Tuple[int, str, int]]:
    """Return [(number, title, line_index)] for every `## N. Title` heading."""
    out = []
    for i, line in enumerate(text.split("\n")):
        m = re.match(r"^## (\d+)\. (.*)$", line)
        if m:
            out.append((int(m.group(1)), m.group(2), i))
    return out


def fenced_blocks(text: str) -> List[Tuple[str, str]]:
    """Return [(language, body)] for every fenced block, in document order."""
    return [(m.group(1) or "", m.group(2))
            for m in re.finditer(r"^```(\w*)\n(.*?)\n^```", text, re.S | re.M)]


def text_blocks(text: str) -> List[str]:
    return [b for lang, b in fenced_blocks(text) if lang == "text"]


# ------------------------------------------------------------------ structural

def check_contiguity(text: str, expected: Optional[range] = None) -> Dict:
    nums = [n for n, _t, _i in sections(text)]
    res = {"count": len(nums),
           "first": nums[0] if nums else None,
           "last": nums[-1] if nums else None,
           "duplicates": sorted(k for k, v in collections.Counter(nums).items() if v > 1)}
    if expected is not None:
        res["contiguous"] = nums == list(expected)
        res["expected"] = f"{expected.start}..{expected.stop - 1}"
    else:
        res["contiguous"] = nums == list(range(nums[0], nums[-1] + 1)) if nums else True
    return res


def check_fences(text: str) -> Dict:
    langs = collections.Counter(re.findall(r"^```(\w+)", text, re.M))
    n = text.count("```")
    return {"total": n, "balanced": n % 2 == 0, "langs": dict(langs)}


def check_rust_balance(text: str) -> Dict:
    problems = []
    for i, (_lang, body) in enumerate(b for b in fenced_blocks(text) if b[0] == "rust"):
        for o, c in (("{", "}"), ("(", ")"), ("[", "]")):
            if body.count(o) != body.count(c):
                problems.append({"block": i, "open": o, "close": c,
                                 "open_n": body.count(o), "close_n": body.count(c)})
    return {"blocks": sum(1 for l, _ in fenced_blocks(text) if l == "rust"),
            "problems": problems}


def check_box_widths(blocks: Sequence[str]) -> List[Dict]:
    """Every `│`-row inside a box must be exactly as wide as its `┌...┐` border."""
    bad = []
    for bi, b in enumerate(blocks):
        rows = b.split("\n")
        for i, r in enumerate(rows):
            t = r.strip()
            if t.startswith("\u250c") and t.endswith("\u2510"):
                w = len(r.rstrip())
                j = i + 1
                while j < len(rows) and rows[j].strip().startswith(VERT):
                    if len(rows[j].rstrip()) != w:
                        bad.append({"block": bi, "row": j, "want": w,
                                    "got": len(rows[j].rstrip()), "line": rows[j]})
                    j += 1
    return bad


def check_orphans(blocks: Sequence[str]) -> List[Dict]:
    """Connectors with no aligned connector in an adjacent row.

    Fires only when an adjacent row HAS connectors. See module docstring.
    """
    bad = []
    for bi, b in enumerate(blocks):
        rows = b.split("\n")
        for i, r in enumerate(rows):
            for c, ch in enumerate(r):
                if ch not in (VERT, DOWN, "\u25b2"):
                    continue
                adj_has = ok = False
                for j in (i - 1, i + 1):
                    if 0 <= j < len(rows):
                        cc = [k for k, g in enumerate(rows[j]) if g in CONN]
                        if cc:
                            adj_has = True
                            if any(abs(k - c) <= 1 for k in cc):
                                ok = True
                if adj_has and not ok:
                    bad.append({"block": bi, "row": i, "col": c, "line": r})
    return bad


def check_offcentre(blocks: Sequence[str]) -> List[Dict]:
    """Every `▼` in a multi-arrow fan row must land on a character of the next row.

    See module docstring for why this is not a per-token centring test.
    """
    bad = []
    for bi, b in enumerate(blocks):
        rows = b.split("\n")
        for i, r in enumerate(rows):
            cc = [k for k, ch in enumerate(r) if ch == DOWN]
            if len(cc) < 2 or i + 1 >= len(rows):
                continue
            lab = rows[i + 1]
            if not lab.strip() or any(ch in CONN for ch in lab):
                continue
            for c in cc:
                if not any(c + d < len(lab) and lab[c + d].strip() for d in (-1, 0, 1)):
                    bad.append({"block": bi, "row": i + 1, "col": c, "line": lab})
    return bad


def check_ascii_substitution(blocks: Sequence[str]) -> List[Dict]:
    """Flag ASCII art substituted for box-drawing glyphs INSIDE a box-drawing block.

    Scope matters. Several early documents reproduce ASCII art (`|`, `+--`)
    verbatim because their source used ASCII -- 65 such lines exist in the
    corpus and all are correct. The defect this catches is narrower: a block
    that is otherwise box-drawing but contains a stray ASCII pipe or `+--`,
    which is how a single wrong glyph silently breaks a spine.
    """
    bad = []
    boxish = set("\u2502\u250c\u2510\u2514\u2518\u252c\u2534\u253c\u2500\u25bc")
    for bi, b in enumerate(blocks):
        rows = b.split("\n")
        if not any(ch in boxish for r in rows for ch in r):
            continue
        for i, r in enumerate(rows):
            if "|" in r or re.search(r"\+--", r):
                bad.append({"block": bi, "row": i, "line": r})
    return bad


# -------------------------------------------------------------------- render

def check_render(text: str) -> Dict:
    """Render with Python-Markdown and inspect the HTML.

    Returns {"available": False, ...} if the package is missing -- callers must
    surface that as SKIPPED, not as a pass.
    """
    if not HAVE_MARKDOWN:
        return {"available": False}
    md = _markdown.Markdown(extensions=["tables", "fenced_code"])
    html = md.convert(text)
    outside = re.sub(r"<pre><code.*?</code></pre>", "", html, flags=re.S)
    stray = [l for l in outside.split("\n")
             if l.count("|") >= 2 and not re.match(r"^\s*<", l.strip())
             and "<t" not in l]
    return {
        "available": True,
        "tables": html.count("<table>"),
        "h2": html.count("<h2>"),
        "h3": html.count("<h3>"),
        "code_blocks": len(re.findall(r"<pre><code", html)),
        "unclassified": len(re.findall(r"<pre><code>", html)),
        "stray_pipes": len(stray),
        "cmthead": len(re.findall(r"<h[1-6][^>]*>[^<]*<!--", html)),
        "leak": len(re.findall(r"<h[1-6][^>]*>[^<]*\*\*", html)),
        "html": html,
    }


# ---------------------------------------------------------------- provenance

def check_provenance(text: str, source_name: str, offset: Optional[int] = None) -> Dict:
    """Every `## N. Title` must carry `<!-- source: NAME §n -->` with N - offset == n.

    The comment may sit on the line directly beneath the heading OR after a
    single blank line -- both layouts occur in the corpus (VERIFICATION/GATES
    use a blank line, EXECUTION/ORCHESTRATION do not), and both are correct.

    If `offset` is None it is DERIVED from the first heading and then required
    to be constant for every section. That lets the corpus sweep validate
    self-consistency without being told each file's offset.
    """
    lines = text.split("\n")
    pat = re.compile(r"^<!-- source: " + re.escape(source_name) + r" \u00a7(\d+) -->$")
    secs = sections(text)
    pairs: List[Tuple[int, int]] = []
    for n, _t, i in secs:
        src = None
        for j in (i + 1, i + 2):          # next line, or past one blank line
            if j >= len(lines):
                break
            nxt = lines[j].strip()
            if not nxt:
                continue
            m = pat.match(nxt)
            src = int(m.group(1)) if m else None
            break
        if src is not None:
            pairs.append((n, src))
    offsets = {n - src for n, src in pairs}
    derived = min(offsets) if len(offsets) == 1 else None
    want = offset if offset is not None else derived
    mapping_errors = ([{"corpus": n, "source": src, "offset": n - src}
                       for n, src in pairs if n - src != want] if want is not None
                      else [{"corpus": n, "source": src} for n, src in pairs])
    return {"sections": len(secs), "comments": len(pairs),
            "offset": want, "offsets_seen": sorted(offsets),
            "mapping_errors": len(mapping_errors),
            "complete": len(pairs) == len(secs) and not mapping_errors}


# ------------------------------------------------------------------- links

def slug(heading: str) -> str:
    """GitHub (gfm) anchor slug.

    Must match GitHub exactly: downcase, drop apostrophes, strip punctuation
    (anything that is not a word char, hyphen, or space), then replace EACH
    space with a hyphen.

    Do NOT collapse runs of whitespace. A heading like `519. Command \u2260 Event`
    loses the `\u2260` and keeps the two surrounding spaces, so its slug is
    `519-command--event` with a DOUBLE hyphen. Collapsing produces
    `519-command-event`, which does not resolve on GitHub.
    """
    s = heading.lower().replace("'", "")
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def check_links(text: str, base_dir: str) -> Dict:
    headings = re.findall(r"^##+ (.*)$", text, re.M)
    anchors = {slug(h) for h in headings}
    internal = re.findall(r"\]\(#([^)]+)\)", text)
    md_links = re.findall(r"\]\(([^)#]+\.md)\)", text)
    return {
        "anchors": len(anchors),
        "internal": len(internal),
        "broken_anchors": sorted({l for l in internal if l not in anchors}),
        "md_links": len(md_links),
        "broken_md": sorted({m for m in md_links
                             if not os.path.exists(os.path.join(base_dir, m))}),
        # A linked heading containing an em/en dash or arrow is only a defect
        # when its anchor does NOT resolve -- glyph presence alone is not a bug.
        "unresolved_dashed": sorted(
            h for h in headings
            if ("\u2014" in h or "\u2192" in h or "\u2013" in h)
            and slug(h) not in set(internal)
            and any(a.startswith(slug(h)[:8]) for a in internal)),
    }


# ------------------------------------------------------------------- probes

def check_probes(text: str, probes: Sequence[str]) -> Dict:
    missing = [p for p in probes if p not in text]
    return {"total": len(probes), "missing": missing}


def load_probes(path: str) -> List[str]:
    """Probe file: one verbatim phrase per line. `#` starts a comment.

    A phrase that itself begins with `#` -- a `###` heading, a `#[test]` or
    `#[derive(...)]` attribute -- must be written with a leading backslash
    (`\\### Gate`, `\\#[test]`); the backslash is removed. Without it the
    line is a comment and is silently NOT checked, which is how 52 heading
    and attribute probes across seven files went unchecked until corpus §969.

    Probes must be copied from the SOURCE, not from the generated file -- a
    probe written from memory that disagrees with the source produces a phantom
    failure. Grep the source before treating a miss as a defect.
    """
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("\\#"):
                out.append(line[1:])
            elif line.strip() and not line.lstrip().startswith("#"):
                out.append(line)
    return out
