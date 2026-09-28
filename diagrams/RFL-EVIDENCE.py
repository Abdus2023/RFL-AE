#!/usr/bin/env python3
"""Regenerate every ASCII diagram in RFL-EVIDENCE.md.

    python3 diagrams/RFL-EVIDENCE.py [outdir]    # default /tmp/rediag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py RFL-EVIDENCE.md <outdir>

The diagrams in RFL-EVIDENCE.md are NOT verbatim transcriptions: the pasted
source had all of its art collapsed onto single lines, so each diagram was
re-derived. This script is the record of that derivation -- re-running it and
diffing against the committed document proves the diagrams still match.

Collapse rule used throughout: a run of N spaces inside a collapsed block is a
line break followed by N-1 leading spaces; an extra space between two
unindented lines is a blank line. Flat word lists with single spaces
(§877, §893) were broken into lines by meaning.

Glyph note. Box-drawing art stays box-drawing; `↓` / `→` / `↛` / `≠` / `⇒`
chains stay as they are. No block mixes an ASCII `|` with box glyphs.

Normalisations (all geometric, no content change):
  * §892 architecture stack: the arrows between HUMAN AUTHORITY, POLICY / SCOPE
    and the first box sit on column 24, but the source drew each box's ┬
    (and the ▼ under it) on column 23. Every box now puts its ┬ on 24, so the
    whole stack shares one spine, and CERTIFICATE is centred on it. Box widths
    and the label padding inside each box are the source's.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/rediag")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "skills", "ascii-diagram-forge", "scripts"))
from geo import (VERT, DOWN, CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
                 TEE_D, HORIZ, row, marks)  # noqa: E402

D = {}
BR, TR = "\u2514", "\u251c"      # └ ├
DASH = HORIZ                     # ─
DWN = "\u2193"                   # ↓
ARROW = "\u2192"                 # →
NARROW = "\u219b"                # ↛
NEQ = "\u2260"                   # ≠
IMPL = "\u21d2"                  # ⇒


def one(s):
    return [s]


def dchain(items, c):
    """Items at column 0 joined by a ↓ on column c."""
    out = [items[0]]
    for it in items[1:]:
        out += [" " * c + DWN, it]
    return out


def bchain(items, c):
    """Items at column 0 joined by │ / ▼ on column c."""
    out = [items[0]]
    for it in items[1:]:
        out += [marks([(c, VERT)]), marks([(c, DOWN)]), it]
    return out


def kids(items, col):
    return [" " * col + (BR if i == len(items) - 1 else TR) + DASH * 2 + " " + s
            for i, s in enumerate(items)]


def rule(head, tails, glyph, indent):
    """`head` then one indented `glyph tail` line per tail."""
    return [head] + [" " * indent + glyph + " " + t for t in tails]


def groups(items, indent=4):
    out = []
    for i, (h, vals) in enumerate(items):
        if i:
            out.append("")
        out += [h] + [" " * indent + v for v in vals]
    return out


def spine_box(left, inner, label, pad):
    """One-line box at column `left`, `inner` columns wide, label padded by
    `pad`; bottom ┬ at left + 1 + inner // 2 (the geo.cen convention)."""
    s = left + 1 + inner // 2
    assert pad + len(label) <= inner, label
    return ([" " * left + CORNER_TL + DASH * inner + CORNER_TR,
             " " * left + VERT + (" " * pad + label).ljust(inner) + VERT,
             " " * left + CORNER_BL + DASH * (s - left - 1) + TEE_D
             + DASH * (left + inner - s) + CORNER_BR]), s


# ================================================================ §866
D["P01"] = (["crates/rfl-evidence/"] + kids(["Cargo.toml", "src/"], 0)
            + kids(["lib.rs", "record.rs", "binding.rs", "artifact.rs",
                    "execution.rs", "environment.rs", "toolchain.rs",
                    "outcome.rs", "canonical.rs", "validate.rs", "tests/"], 4)
            + kids(["binding.rs", "artifact.rs", "execution.rs",
                    "environment.rs", "adversarial.rs", "canonical.rs"], 8))
D["P02"] = dchain(["rfl-types", "rfl-evidence"], c=4)

# ================================================================ §867
D["P03"] = dchain(["Artifact", "ExecutionRequest", "ExecutionObservation",
                   "EvidenceRecord"], c=3)
D["P04"] = dchain(["EvidenceRecord", "Verification", "VerificationResult"], c=7)

# ================================================================ §869
D["P05"] = bchain(["C source", "semantic analysis", "AI-generated Rust",
                   "human modification", "formatting", "final artifact"], c=3)

# ================================================================ §870
D["P06"] = one('"make test"')

# ================================================================ §871
D["P07"] = one("verified = true")

# ================================================================ §872
D["P08"] = ["Evidence", marks([(3, VERT)])] + kids(
    ["epoch", "task", "artifact", "execution", "inputs", "outputs",
     "environment", "toolchain"], 3)

# ================================================================ §873
D["P09"] = one(f"Failed {NEQ} Blocked")
D["P10"] = one("compiler unavailable")
D["P11"] = one("test failed")
D["P12"] = one("test never ran")

# ================================================================ §874
D["P13"] = one("evidence.subject == artifact.identity.id")
D["P14"] = one("evidence.execution == execution.execution_id")
D["P15"] = one("evidence.epoch == artifact.epoch")
D["P16"] = ["evidence.output_digest", " " * 4 + "matches execution outputs"]

# ================================================================ §875
D["P17"] = groups([("Artifact A", ["digest = AAA"]),
                   ("execute A", []),
                   ("Evidence claims:", ["subject = Artifact B",
                                         "digest = BBB"])])
D["P18"] = dchain(["Artifact mismatch", "EvidenceUnbound"], c=8)

# ================================================================ §876
D["P19"] = (dchain(["Artifact A Epoch E10", "tested", "PASS"], c=3) + [""]
            + dchain(["Artifact A Epoch E11", "source changed"], c=3))
D["P20"] = one(f"old evidence {NEQ} current evidence")
D["P21"] = one("E10 != E11")
D["P22"] = rule("epoch mismatch", ["evidence unusable"], ARROW, 4)

# ================================================================ §877
D["P23"] = ["compiler", "Rust version", "LLVM version", "clang version",
            "architecture", "configuration", "kernel tree", "host OS",
            "target architecture", "feature flags", "environment variables",
            "tool versions"]

# ================================================================ §878
D["P24"] = one("x86_64 + CONFIG_A")
D["P25"] = one("ARM64 + CONFIG_B")
D["P26"] = dchain(["Evidence", "configuration", "architecture", "toolchain",
                   "artifact"], c=4)
D["P27"] = ["ConfigurationCoverage", "ArchitectureCoverage"]

# ================================================================ §879
D["P28"] = one('command = "cargo test"')
D["P29"] = one("command_digest = H(canonical(ExecutionSpec))")

# ================================================================ §880
D["P30"] = dchain(["source artifact", "compiler", "binary artifact"], c=7)
D["P31"] = ["output_artifacts = [", " " * 4 + "ArtifactIdentity(binary_digest)",
            "]"]
D["P32"] = one("build passed")
D["P33"] = one(f"this exact input {ARROW} this exact toolchain {ARROW} this "
               f"exact execution {ARROW} this exact output {ARROW} produced "
               "this observed outcome")

# ================================================================ §881
# Source geometry kept: spine on 3; the closing ↓ on 10 with `Verified`
# centred on it (6..13).
D["P34"] = (["Artifact A", marks([(3, VERT)])]
            + [" " * 3 + TR + DASH * 2 + " " + s for s in
               ("Evidence E1: build passed", "Evidence E2: KUnit passed",
                "Evidence E3: differential test passed")]
            + [marks([(3, VERT)]), marks([(3, DOWN)]), "Verification",
               marks([(3, VERT)])] + kids(["Contract C17"], 3)
            + [" " * 10 + DWN, row([("Verified", 10)])])

# ================================================================ §882
D["P35"] = rule("Evidence", ["Contract satisfaction", "Verification"], NEQ, 3)

# ================================================================ §883
D["P36"] = groups([("Required:", ["build", "KUnit", "ABI", "differential"]),
                   ("Observed:", ["build", "KUnit"])])
D["P37"] = one("Verification = Blocked")
D["P38"] = one("Verification = Failed")

# ================================================================ §884
D["P39"] = ["verification:", " " * 4 + "BLOCKED"]
D["P40"] = rule("NO EVIDENCE", ["NO VERIFIED CLAIM"], ARROW, 4)

# ================================================================ §886
D["P41"] = groups([("Agent:", ["generated artifact"]),
                   ("Agent:", ['generated "test result"']),
                   ("Agent:", ["generated evidence record"]),
                   ("Agent:", ["declares verification"])])
D["P42"] = ["EvidenceRecord", " " * 4 + "requires ExecutionObservation"]
D["P43"] = ["ExecutionObservation", " " * 4 + "requires registered Executor"]

# ================================================================ §887
D["P44"] = ["Artifact"]
for _lab, _nxt in (("digest", "ExecutionRequest"),
                   ("authorization", "ExecutionObservation"),
                   ("output", "EvidenceRecord"),
                   ("contract interpretation", "VerificationResult")):
    D["P44"] += [marks([(3, VERT)]), " " * 3 + VERT + " " + _lab,
                 marks([(3, DOWN)]), _nxt]
D["P44"] += [marks([(3, VERT)]), marks([(3, DOWN)]), "GateResult"]

# ================================================================ §888
D["P45"] = groups([("E100:", ["Build passed"]),
                   ("E101:", ["Toolchain fingerprint discovered corrupt"]),
                   ("E102:", ["E100 invalidated"])])
D["P46"] = one("E100 occurred")
D["P47"] = one("E100 is no longer admissible evidence")
D["P48"] = one(f"history {NEQ} current validity")

# ================================================================ §889
D["P49"] = dchain(["Collected", "Bound", "Validated", "Available",
                   "Used by verification", "May become invalidated"], c=4)
D["P50"] = groups([("Outcome:", ["Passed"]), ("Validity:", ["Invalid"])])

# ================================================================ §890
D["P51"] = rule("ExecutionSuccess", ["EvidenceValid", "ContractSatisfied",
                                     "Verified", "Certified"], NARROW, 4)

# ================================================================ §892
S = 24
D["P52"] = [row([("HUMAN AUTHORITY", S)]), marks([(S, VERT)]),
            marks([(S, DOWN)]), row([("POLICY / SCOPE", S)]),
            marks([(S, VERT)]), marks([(S, DOWN)])]
for _i, (_lab, _pad) in enumerate((("RFL-TYPES", 3), ("RFL-TRANSITION", 1),
                                   ("RFL-LEDGER", 3), ("RFL-EVIDENCE", 2),
                                   ("VERIFICATION", 3), ("RFL-GATES", 4))):
    _b, _s = spine_box(14, 18, _lab, _pad)
    assert _s == S
    D["P52"] += _b + [marks([(S, DOWN)])]
D["P52"] += [row([("CERTIFICATE", S)])]
D["P53"] = dchain(["C source", "C analyzers", "KSIR", "Contracts",
                   "Rust Design IR", "Rust generator", "RFL protocol"], c=3)

# ================================================================ §893
D["P54"] = ["PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE", "INVALIDATED"]
D["P55"] = ["required gate", "optional gate", "conditional gate",
            "dependency gate", "evidence-completeness gate", "scope gate",
            "provenance gate", "semantic-contract gate"]
D["P56"] = (rule("BLOCKED required gate", ["FAILED required gate"], NEQ, 8)
            + [""] + rule("but both", ["NOT CERTIFIABLE"], IMPL, 8))

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
