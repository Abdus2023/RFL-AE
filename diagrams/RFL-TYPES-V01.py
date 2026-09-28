#!/usr/bin/env python3
"""Regenerate every ASCII diagram in RFL-TYPES-V01.md.

    python3 diagrams/RFL-TYPES-V01.py [outdir]    # default /tmp/rtvdiag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py RFL-TYPES-V01.md <outdir>

The diagrams in RFL-TYPES-V01.md are NOT verbatim transcriptions: the pasted
source had all of its art collapsed onto single lines, so each diagram was
re-derived. This script is the record of that derivation -- re-running it and
diffing against the committed document proves the diagrams still match.

Collapse rule used throughout: a run of N spaces inside a collapsed block is a
line break followed by N-1 leading spaces; an extra space between two
unindented lines is a blank line. Runs that are clearly intra-line alignment
(the `==` column in §929, the `→` column in §939) are kept as spacing.
Single-space word runs were broken into lines where they are lists (§928,
§929, §938, §940, §942, §944, §946).

Glyph note. `│ ├ └ ─` trees and rules stay box-drawing; `↓` / `→` / `≠` /
`⇒` / `∧` chains stay as they are. No block mixes an ASCII `|` with box
glyphs.

No geometric normalisations were needed: every column below is the source's
own. Where the source's alignment is one column off on a first line (§939,
`kernel changes`), it is kept as the source has it.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/rtvdiag")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import VERT, HORIZ  # noqa: E402

D = {}
BR, TR = "\u2514", "\u251c"      # └ ├
DASH = HORIZ                     # ─
DWN = "\u2193"                   # ↓
ARROW = "\u2192"                 # →
NEQ = "\u2260"                   # ≠
IMPL = "\u21d2"                  # ⇒
AND = "\u2227"                   # ∧


def one(s):
    return [s]


def dchain(items, c):
    """Items at column 0 joined by a ↓ on column c."""
    out = [items[0]]
    for it in items[1:]:
        out += [" " * c + DWN, it]
    return out


def kids(items, col, spaced=False):
    """├── / └── children at `col`; `spaced` puts a │ line before each."""
    out = []
    for i, s in enumerate(items):
        if spaced:
            out.append(" " * col + VERT)
        out.append(" " * col + (BR if i == len(items) - 1 else TR)
                   + DASH * 2 + " " + s)
    return out


# ================================================================ §926
D["P01"] = ["rfl-types", VERT] + kids(
    ["identifiers", "digest", "epoch", "scope", "operation", "authorization",
     "task", "artifact", "evidence", "contract", "gate", "error"], 0)
D["P02"] = ["rfl-types", "   " + VERT] + kids(
    ["no rfl-transition", "no rfl-ledger", "no rfl-evidence", "no rfl-gates",
     "no filesystem/network/LLM/runtime authority"], 3)

# ================================================================ §927
D["P03"] = one(f"TaskId {NEQ} ArtifactId {NEQ} EvidenceId")

# ================================================================ §928
D["P04"] = one("sha256:<64 lowercase hexadecimal characters>")
D["P05"] = one("sha256:9f86d081884c7d659a2feaa0c55ad015"
               "a3bf4f1b2b0b822cd15d6c15b0f00a08")
D["P06"] = ["SHA256(...)", "sha256(...)", "sha-256:..."]

# ================================================================ §929
# `iff  a.kernel` = line break + 1 leading space, which puts every `==` on
# column 18 -- the source's own alignment.
D["P07"] = ["Epoch(a) == Epoch(b) iff",
            " a.kernel         == b.kernel",
            AND + " a.specification == b.specification",
            AND + " a.protocol      == b.protocol",
            AND + " a.generation    == b.generation"]
assert len({l.index("==") for l in D["P07"][1:]}) == 1
D["P08"] = one("request.epoch != authoritative_epoch")

# ================================================================ §930
D["P09"] = one('"linux-7.x"')
D["P10"] = ["KernelSnapshotId(", "    sha256:<commit/tree identity>", ")"]

# ================================================================ §932
D["P11"] = one("scope is data not prose")
D["P12"] = ["repository = linux", "paths       = drivers/foo/**",
            "architecture = x86_64", "configuration = CONFIG_FOO"]

# ================================================================ §933
D["P13"] = ["Authorization", "      + AuthorizationState", "      " + DWN,
            "authorization validity"]

# ================================================================ §934
D["P14"] = one('"kernel/foo.c"')

# ================================================================ §935
D["P15"] = ["Task"] + kids([f"Attempt 0 {ARROW} Failed",
                            f"Attempt 1 {ARROW} Failed",
                            f"Attempt 2 {ARROW} Succeeded"], 1)
D["P16"] = dchain(["Executing", "Failed", "Executing", "Failed", "Executing"],
                  c=1)

# ================================================================ §936
D["P17"] = one(f'"Observed" {NEQ} "Valid"')

# ================================================================ §938
D["P18"] = [f"CanonicalEncode(T) {ARROW} bytes",
            "Digest(T) = SHA256(CanonicalEncode(T))"]
D["P19"] = one("RFC 8785 JCS")
D["P20"] = dchain(["Rust object", "canonical structured representation",
                   "canonical bytes", "digest"], c=3)

# ================================================================ §939
D["P21"] = [f"kernel changes       {ARROW} epoch changes",
            f"specification changes {ARROW} epoch changes",
            f"protocol changes      {ARROW} epoch changes",
            f"generation changes    {ARROW} epoch changes"]

# ================================================================ §940
D["P22"] = one("P1: No stale request can become an accepted transition.")
D["P23"] = ["request.epoch \u2260 state.epoch",
            " " * 8 + IMPL + " \u03b4(state, request) = Reject(EpochMismatch)"]
D["P24"] = ['"same repository"', '"same source"', '"same agent"',
            '"same task"']

# ================================================================ §942
D["P25"] = [f"{i}. {s}" for i, s in enumerate([
    "request identity", "task existence", "epoch", "snapshot",
    "authorization existence", "authorization epoch", "authorization actor",
    "authorization task", "capability", "scope", "expiry/revocation",
    "task state", "dependencies", "duplicate/replay",
    "operation-specific predicates"], start=1)]

# ================================================================ §943
D["P26"] = one("Reject(InvalidTransition)")
D["P27"] = one(f"Succeeded {ARROW} Certified")
D["P28"] = one(f"BuildPassed {ARROW} Verified")

# ================================================================ §944
D["P29"] = [f"A{i:02d} {s}" for i, s in enumerate([
    "stale epoch", "snapshot mismatch", "specification mismatch",
    "expired authorization", "revoked authorization", "missing capability",
    "scope escape", "invalid transition", "duplicate request",
    "forged artifact", "unbound evidence", "self-verification",
    "event tampering", "replay divergence", "failed required gate",
    "blocked required gate", "invalidated dependency",
    "valid complete execution"], start=1)]
assert len(D["P29"]) == 18
D["P30"] = one("expected result + expected rejection reason")

# ================================================================ §945
D["P31"] = ["Task T1"] + kids(["MigrationUnit M1", "Artifact A1",
                               "Contract C1"], 2, spaced=True)
D["P32"] = dchain(["Epoch E1", "Authorize Agent A1", "Generate Artifact A1",
                   "Execute Build", "Evidence EVID1", "Verify",
                   "Gate G1 = Pass", "Certificate C1"], c=3)
D["P33"] = one(f"E1 {ARROW} request E2")
D["P34"] = one("valid evidence + failed gate")
D["P35"] = one("all technical gates pass")
D["P36"] = one("UpstreamAcceptance = Accepted")

# ================================================================ §946
# `↓ FREEZE` (one space) puts FREEZE straight under its arrow; `FREEZE  EXE…`
# and `↓  CONFORMANCE` / `↓  FIRST…` (two spaces) are blank lines.
_arrow = " " * 9 + DWN
D["P37"] = (["CONCEPTUAL", DASH * 10, "architecture", "semantic model",
             "trust model", "verification model", _arrow, "FREEZE", "",
             "EXECUTABLE", DASH * 10, "rfl-types", "rfl-transition",
             "rfl-ledger", "rfl-evidence", "rfl-gates", _arrow, "",
             "CONFORMANCE", _arrow, "", "FIRST REAL MIGRATION UNIT"])

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
