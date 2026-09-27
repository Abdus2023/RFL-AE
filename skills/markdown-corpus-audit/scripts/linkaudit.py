"""Cross-corpus link check that reads RENDERED HTML, not raw source.

Renders every .md in the repo root plus README.md, collects every href, and
resolves `path#frag` against the rendered heading anchors of the target file.
Regexing raw source gives false positives from code fences, so this parses the
HTML produced by the same Markdown pipeline GitHub approximates.
"""
import argparse, os, re, sys, collections
import markdown

def slug(h):
    s = h.lower()
    s = re.sub(r"<[^>]+>", "", s)
    out = []
    for ch in s:
        if ch.isalnum() or ch in "-_":
            out.append(ch)
        elif ch == " ":
            out.append("-")
        # everything else (punctuation, symbols) is stripped, GitHub-exact
    return "".join(out)

def anchors_of(html):
    hs = re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", html, re.S)
    return {slug(h) for h in hs}

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--root", default=os.getcwd(),
                help="repository root to walk (default: current directory)")
ap.add_argument("--allow", action="append", default=[],
                help="file (repo-relative) permitted to contain deliberately broken "
                     "example links; its failures are reported but do not fail the run")
args = ap.parse_args()
allow = set(args.allow)
root = args.root

def walk(d):
    for e in sorted(os.listdir(d)):
        if e in {".git", ".venv", "__pycache__"}:
            continue
        p = os.path.join(d, e)
        if os.path.isdir(p):
            yield from walk(p)
        elif e.endswith(".md"):
            yield os.path.relpath(p, root)

files = sorted(walk(root))

rendered, anchors = {}, {}
for f in files:
    text = open(os.path.join(root, f), encoding="utf-8").read()
    html = markdown.markdown(text, extensions=["tables", "fenced_code"])
    rendered[f] = html
    anchors[f] = anchors_of(html)

total = broken = excused = 0
report = collections.Counter()

def note(kind, f, href):
    """Count a defect; return True if it is excused as a documented example."""
    global broken, excused
    if f in allow:
        excused += 1
        print(f"{kind:13} {f} -> {href}   [excused: --allow]")
        return True
    broken += 1
    print(f"{kind:13} {f} -> {href}")
    return False

for f in files:
    for href in re.findall(r'href="([^"]+)"', rendered[f]):
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        total += 1
        path, _, frag = href.partition("#")
        if path:
            # a file reference resolves RELATIVE to the containing file's
            # directory, not the repo root
            relpath = os.path.normpath(os.path.join(os.path.dirname(f), path))
        else:
            relpath = f  # anchor-only link -> this same file
        target = os.path.join(root, relpath)
        if not os.path.exists(target):
            note("MISSING FILE", f, href)
            continue
        if not frag:
            report[f] += 1
            continue
        tname = relpath
        if tname not in anchors:
            note("NO TARGET", f, href)
            continue
        if frag in anchors[tname]:
            report[f] += 1
        else:
            note("BROKEN ANCHOR", f, href)

print(f"\nfiles scanned : {len(files)}")
print(f"local links   : {total}")
print(f"broken        : {broken}")
print(f"excused       : {excused}  (documented examples in: {', '.join(sorted(allow)) or 'none'})")
sys.exit(1 if broken else 0)
