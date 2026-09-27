#!/usr/bin/env python3
"""new_skill.py — scaffold a skill directory.

    python3 skills/skill-creator/scripts/new_skill.py my-skill \\
        --description "What it does and when to use it."
"""
import argparse
import os
import re
import sys

TEMPLATE = '''---
name: {name}
description: {description}
---

# {name}

## Purpose

<One paragraph. What problem this removes.>

## When to use

- <trigger>

## When not to use

- <boundary -- as important as the triggers>

## Quick start

```bash
python3 skills/{name}/scripts/<tool>.py --help
```

## Invariants

1. <rule that must not be violated>

## Traps

1. **<symptom>.** <cause>. <fix>.

## Verification

```bash
# positive: reproduces the known-good result
# negative: the fixture below MUST produce these findings
```
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--description", required=True)
    ap.add_argument("--root", default="skills")
    a = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.name):
        print(f"invalid skill name {a.name!r}: use lowercase-hyphenated")
        return 1
    if len(a.description) < 40:
        print("description too short -- it is the discovery surface, so it must "
              "say what the skill does AND when to use it")
        return 1

    d = os.path.join(a.root, a.name)
    if os.path.exists(d):
        print(f"{d} already exists; refusing to overwrite")
        return 1
    os.makedirs(os.path.join(d, "scripts"), exist_ok=True)
    with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as fh:
        fh.write(TEMPLATE.format(name=a.name, description=a.description))
    print(f"created {d}/SKILL.md and {d}/scripts/")
    print("next: fill in the sections, add a script, then run")
    print(f"  python3 {a.root}/skill-creator/scripts/validate_skill.py {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
