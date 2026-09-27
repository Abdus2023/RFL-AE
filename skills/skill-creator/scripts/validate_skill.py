#!/usr/bin/env python3
"""validate_skill.py — check a skill is well-formed and its scripts run.

    python3 skills/skill-creator/scripts/validate_skill.py skills/ascii-diagram-forge
    python3 skills/skill-creator/scripts/validate_skill.py skills/          # all

Checks performed:
  * SKILL.md exists and has YAML frontmatter with name + description
  * `name` matches the directory name
  * description says when to use the skill (not just what it is)
  * every scripts/*.py byte-compiles
  * every `python3 skills/.../x.py` command quoted in SKILL.md points at a file
    that exists
  * the SKILL.md has a Verification section (rule 3 of skill-creator)

Exit 0 only if everything passes.
"""
import os
import py_compile
import re
import sys
import tempfile


def parse_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).split("\n"):
        if ":" in line and not line.startswith((" ", "\t")):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def validate(path: str, repo_root: str) -> list:
    errs = []
    name = os.path.basename(os.path.normpath(path))
    sk = os.path.join(path, "SKILL.md")
    if not os.path.isfile(sk):
        return [f"{name}: no SKILL.md"]
    text = open(sk, encoding="utf-8").read()

    fm = parse_frontmatter(text)
    if fm is None:
        errs.append(f"{name}: SKILL.md has no YAML frontmatter")
        return errs
    if fm.get("name") != name:
        errs.append(f"{name}: frontmatter name={fm.get('name')!r} != directory")
    desc = fm.get("description", "")
    if len(desc) < 40:
        errs.append(f"{name}: description too short ({len(desc)} chars)")
    if not re.search(r"\b(use|when|before|after)\b", desc, re.I):
        errs.append(f"{name}: description never says WHEN to use it")
    if not re.search(r"^## Verification", text, re.M):
        errs.append(f"{name}: no '## Verification' section (skill-creator rule 3)")

    scripts = os.path.join(path, "scripts")
    if os.path.isdir(scripts):
        for f in sorted(os.listdir(scripts)):
            if not f.endswith(".py"):
                continue
            fp = os.path.join(scripts, f)
            try:
                with tempfile.TemporaryDirectory() as td:
                    py_compile.compile(fp, cfile=os.path.join(td, "x.pyc"),
                                       doraise=True)
            except py_compile.PyCompileError as e:
                errs.append(f"{name}: scripts/{f} does not compile: {e.msg}")

    # commands quoted in the SKILL.md must point at real files
    for m in re.finditer(r"python3 (skills/[^\s`\"]+\.py)", text):
        rel = m.group(1)
        if not os.path.isfile(os.path.join(repo_root, rel)):
            errs.append(f"{name}: SKILL.md references missing {rel}")
    return errs


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    target = sys.argv[1]
    # repo root = the directory containing 'skills'
    repo_root = os.path.dirname(os.path.abspath(target)) \
        if os.path.basename(os.path.abspath(target)) != "skills" \
        else os.path.dirname(os.path.abspath(target))
    while repo_root != "/" and not os.path.isdir(os.path.join(repo_root, "skills")):
        repo_root = os.path.dirname(repo_root)

    targets = []
    if os.path.basename(os.path.abspath(target)) == "skills":
        targets = [os.path.join(target, d) for d in sorted(os.listdir(target))
                   if os.path.isdir(os.path.join(target, d))]
    else:
        targets = [target]

    all_errs = []
    for t in targets:
        errs = validate(t, repo_root)
        label = os.path.basename(os.path.normpath(t))
        print(f"{'FAIL' if errs else 'ok  '}  {label}")
        for e in errs:
            print("        - " + e)
        all_errs += errs
    print()
    if all_errs:
        print(f"{len(all_errs)} problem(s)")
        return 1
    print(f"{len(targets)} skill(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
