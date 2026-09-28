#!/usr/bin/env python3
"""Regenerate every ASCII diagram in RFL-LEDGER-V01.md.

    python3 diagrams/RFL-LEDGER-V01.py [outdir]    # default /tmp/rldiag

Then re-splice with:

    python3 skills/placeholder-splice/scripts/splice.py RFL-LEDGER-V01.md <outdir>

The diagrams in RFL-LEDGER-V01.md are NOT verbatim transcriptions: the pasted
source had all of its art collapsed onto single lines, so each diagram was
re-derived. This script is the record of that derivation -- re-running it and
diffing against the committed document proves the diagrams still match.

Collapse rule used throughout: a run of N spaces inside a collapsed block is a
line break followed by N-1 leading spaces; an extra space between two
unindented lines is a blank line. In this paste the FIRST line of a block keeps
its leading spaces literally (no newline was folded in front of it): §995's
`AGENT` has 19 leading spaces and centres exactly on the arrow column 21, and
§983's `E2a` sits on column 10 like `E2b`. Single-space word runs were broken
into lines where they are lists or stacked steps (§970, §973, §975, §976, §982,
§984, §985, §986, §990, §991, §994, §996); two-space `↓ label` runs keep the label on
the arrow line (§974, §976) where the next token is a node.

Glyph note. Box-drawing art stays box-drawing; `↓` / `→` / `≠` / `⇒` chains
stay as they are. No block mixes an ASCII `|` with box glyphs.

Normalisations (all geometric, no content change):
  * §995 trust chain: `immutable history` started on column 14, one column
    right of centre on the spine (column 21, where every `│`, `▼` and both
    boxes' `┬` sit); it now starts on 13. Every other label already centred.
Omission (flagged in the document):
  * §979 invariant: the source line began `id="x1" append(E) = ...`. The
    `id="x1"` is a leaked code-fence attribute, not content, and was dropped.
"""
import os
import sys

if len(sys.argv) > 1:
    os.environ["DIAGDIR"] = sys.argv[1]

OUT = os.environ.get("DIAGDIR", "/tmp/rldiag")
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


def labchain(items, c):
    """node, label, node, label, node ...: each ↓ on column c carries a label
    (None for a bare arrow)."""
    out = [items[0]]
    for i in range(1, len(items), 2):
        lab, nxt = items[i], items[i + 1]
        out += [" " * c + DWN + ("" if lab is None else " " + lab), nxt]
    return out


def lchain(items, c):
    """Items at column 0 joined by │ / │ label / ▼ on column c.
    `items` alternates node, label, node, ...; a label of None means none."""
    out = [items[0]]
    for i in range(1, len(items), 2):
        lab, nxt = items[i], items[i + 1]
        out.append(marks([(c, VERT)]))
        if lab is not None:
            out.append(" " * c + VERT + " " + lab)
        out += [marks([(c, DOWN)]), nxt]
    return out


def kids(items, col):
    return [" " * col + (BR if i == len(items) - 1 else TR) + DASH * 2 + " " + s
            for i, s in enumerate(items)]


def groups(items, indent=4):
    out = []
    for i, (h, vals) in enumerate(items):
        if i:
            out.append("")
        out += [h] + [" " * indent + v for v in vals]
    return out


def digest_of(name, arg):
    return [name, "    = SHA256(", "    CanonicalEncode(" + arg + ")", ")"]


# ================================================================ §970
D["P01"] = (["crates/rfl-ledger/"] + kids(["Cargo.toml", "src/"], 0)
            + kids(["lib.rs", "event.rs", "event_core.rs", "ledger.rs",
                    "append.rs", "validation.rs", "replay.rs", "digest.rs",
                    "fork.rs", "tests/"], 4)
            + kids(["genesis.rs", "append.rs", "ordering.rs", "tamper.rs",
                    "replay.rs", "duplicate.rs", "fork.rs", "adversarial.rs"],
                   8))
D["P02"] = ["rfl-ledger"] + kids(["rfl-types", "rfl-transition"], 4)
D["P03"] = ["rfl-evidence", "rfl-gates", "KSIR", "Rust-generation logic",
            "LLM infrastructure"]

# ================================================================ §971
D["P04"] = digest_of("EventDigest", "EventCore")

# ================================================================ §972
D["P05"] = one("EventId")
D["P06"] = one("EventDigest")
D["P07"] = groups([("EventId", ["= identity/reference"]),
                   ("EventDigest", ["= content integrity"])])
D["P08"] = one("same EventId + different EventCore")
D["P09"] = one("different EventId + same EventCore")

# ================================================================ §973
D["P10"] = one("sequence == 0")
D["P11"] = ["sequence = 0", "previous_event = None",
            "previous_state = initial_state"]
D["P12"] = one("genesis is immutable")

# ================================================================ §974
D["P13"] = one("E[n].sequence = E[n-1].sequence + 1")
D["P14"] = one("E[n].previous_event = E[n-1].id")
D["P15"] = one("E[n].previous_state = E[n-1].resulting_state")
D["P16"] = labchain(["E0", "previous_event", "E1", None, "E2", None, "E3"], 1)

# ================================================================ §975
D["P17"] = one(f"E0 {ARROW} E1 {ARROW} E2")
D["P18"] = one("E2.previous_state")
D["P19"] = ["1. Is the event content intact?",
            "2. Is the event connected to the expected predecessor?",
            "3. Does replay of the event produce the claimed resulting state?"]

# ================================================================ §976
D["P20"] = dchain(["STRUCTURAL_VALID", "SEMANTIC_VALID", "REPLAY_VALID"], 8)
D["P21"] = ["digest", "sequence", "previous_event", "field presence",
            "epoch consistency"]
D["P22"] = ["operation legal", "actor/task relation", "transition legal",
            "authorization relation"]
D["P23"] = labchain(["S0", "E0", "S1", "E1", "S2"], 1)
D["P24"] = one(f"history {IMPL} state")
D["P25"] = one("history appears internally consistent")

# ================================================================ §978
D["P26"] = dchain(["candidate", "validate EventCore digest", "validate sequence",
                   "validate previous_event", "validate previous_state",
                   "validate epoch", "validate semantic transition", "append"],
                  4)
D["P27"] = one("append(candidate) = Err(...)")
D["P28"] = one("ledger remains unchanged")

# ================================================================ §979
D["P29"] = one(f"append(E) = Err {IMPL} LedgerAfter == LedgerBefore")
D["P30"] = one("event inserted then validation failed")

# ================================================================ §980
D["P31"] = dchain(["initial state", "apply E0", "derived state 1", "apply E1",
                   "derived state 2", "..."], 4)
D["P32"] = ["digest(derived_state)", "        == event.resulting_state"]
D["P33"] = one("ReplayDivergence")

# ================================================================ §981
D["P34"] = dchain(["replay()", "current authorization database"], 3)
D["P35"] = one("replay(H) must depend only on H + immutable protocol rules")

# ================================================================ §982
D["P36"] = one("Replay(H)")
D["P37"] = ["current_time", "randomness", "network", "filesystem",
            "LLM output", "environment variables", "current authorization",
            "current Git branch", "current CI state"]
D["P38"] = one("Replay(H) = deterministic function")

# ================================================================ §983
D["P39"] = one(f"E0 {ARROW} E1 {ARROW} E2 {ARROW} E3")
_trunk = f"E0 {ARROW} E1"
assert len(_trunk) == 7
D["P40"] = [" " * 10 + "E2a", " " * 9 + "/", _trunk, " " * 9 + "\\",
            " " * 10 + "E2b"]
D["P41"] = one(f"fork detected {ARROW} ledger not certifiable")

# ================================================================ §984
D["P42"] = [f"E1 {ARROW} E2a", f"E1 {ARROW} E2b"]
D["P43"] = one("E2.previous_event != E1.id")
D["P44"] = one("digest(E2.core) != E2.event_digest")
D["P45"] = one("replay(E2) != E2.resulting_state")
D["P46"] = one(f"Forked {NEQ} Corrupt")

# ================================================================ §985
D["P47"] = ["same EventId", "same EventCore", "same digest"]
D["P48"] = ["same EventId", "different EventCore"]
D["P49"] = one("same operation")
D["P50"] = one("same event")

# ================================================================ §986
D["P51"] = one("Request R1")
D["P52"] = ["R1 + digest(D)", "R1 + digest(D)"]
D["P53"] = ["R1 + digest(D1)", "R1 + digest(D2)"]
D["P54"] = one("ReplayConflict")

# ================================================================ §988
D["P55"] = one("InvalidLedger")

# ================================================================ §989
D["P56"] = one("E17")
D["P57"] = one("edit E17")
D["P58"] = dchain(["E17", "E18 = Correction / Invalidation / Supersession"], 1)
D["P59"] = one("history = what happened")
D["P60"] = one("current state = what is currently authoritative")

# ================================================================ §990
D["P61"] = [f"E50 {ARROW} evidence accepted",
            f"E51 {ARROW} later evidence invalidated"]
D["P62"] = one("E51 = Invalidate(E50)")
D["P63"] = groups([("historically:", ["E50 existed and was accepted"]),
                   ("currently:", ["E50 is invalidated"])])

# ================================================================ §991
D["P64"] = digest_of("StateDigest", "StateProjection")
D["P65"] = ["HashMap iteration order", "memory addresses",
            "timestamps not semantically relevant", "debug metadata",
            "filesystem paths", "process IDs"]

# ================================================================ §992
D["P66"] = lchain(["Full runtime state", None, "Authoritative State Projection",
                   None, "Canonical encoding", None, "StateDigest"], 8)

# ================================================================ §993
D["P67"] = (["Given valid history H:", ""]
            + dchain(["append(H)", "replay(H)", "S"], 7)
            + ["", "and every event Ei contains digest(Si)"])
D["P68"] = one("digest(Si) == Ei.resulting_state")

# ================================================================ §994
D["P69"] = ["L01 valid genesis", "L02 invalid genesis", "L03 valid append",
            "L04 invalid digest", "L05 sequence gap", "L06 sequence rewind",
            "L07 previous-event corruption", "L08 previous-state corruption",
            "L09 resulting-state forgery", "L10 reordered history",
            "L11 duplicate event", "L12 conflicting request", "L13 fork",
            "L14 replay divergence", "L15 historical authorization expiration",
            "L16 historical authorization revocation", "L17 invalidation event",
            "L18 failed append atomicity"]
D["P70"] = ["Take valid H.", "Mutate exactly one byte of EventCore.",
            "Replay(H')."]
D["P71"] = one(f"H' {NEQ} H AND Replay(H') fails")

# ================================================================ §995
S, LEFT, INNER = 21, 13, 15
assert LEFT + 1 + INNER // 2 == S


def _box(label):
    return [" " * LEFT + CORNER_TL + DASH * INNER + CORNER_TR,
            " " * LEFT + VERT + label + VERT,
            " " * LEFT + CORNER_BL + DASH * (S - LEFT - 1) + TEE_D
            + DASH * (LEFT + INNER - S) + CORNER_BR]


_b1, _b2 = _box(" rfl-transition"), _box("   rfl-ledger  ")
assert len(_b1[1]) == len(_b1[0]) and len(_b2[1]) == len(_b2[0])
D["P72"] = ([row([("AGENT", S)]), marks([(S, VERT)]),
             " " * S + VERT + " OperationRequest", marks([(S, DOWN)])] + _b1
            + [marks([(S, VERT)]), row([("EventProposal", S)]),
               marks([(S, VERT)]), marks([(S, DOWN)])] + _b2
            + [marks([(S, VERT)]), row([("immutable history", S)]),
               marks([(S, VERT)]), marks([(S, DOWN)]), row([("replay", S)]),
               marks([(S, VERT)]), marks([(S, DOWN)]),
               row([("reconstructed State", S)])])
# the source's own columns for every label except `immutable history`
for _lab, _col in (("AGENT", 19), ("EventProposal", 15), ("replay", 18),
                   ("reconstructed State", 12), ("immutable history", 13)):
    assert any(l.startswith(" " * _col + _lab) for l in D["P72"]), _lab
D["P73"] = one(f"history {ARROW} state")
D["P74"] = one(f"state {ARROW} history")

# ================================================================ §996
D["P75"] = ["the C semantics were correctly reconstructed",
            "the Rust implementation is correct", "a test was sufficient",
            "the evidence is relevant", "a contract is satisfied",
            "the gate predicate is appropriate",
            "Linux upstream will accept the patch"]
D["P76"] = one("the protocol history is structurally and semantically "
               "coherent, and deterministic replay reconstructs the claimed "
               "protocol state.")

# ================================================================ §997
D["P77"] = lchain(["rfl-types", "vocabulary + canonical identities",
                   "rfl-transition", "admissibility", "rfl-ledger",
                   "historical authority", "rfl-evidence",
                   "execution observation", "rfl-gates",
                   "certification decision", "certificate"], 4)

# ================================================================ §998
D["P78"] = dchain(["command exited 0", '"test passed"', '"artifact verified"',
                   '"contract satisfied"'], 8)
D["P79"] = dchain(["Artifact", "ExecutionRequest", "ExecutionObservation",
                   "EvidenceRecord", "EvidenceValidity", "ContractSatisfaction"],
                  3)

for k, v in sorted(D.items()):
    with open(os.path.join(OUT, k + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(v) + "\n")

print(f"wrote {len(D)} diagrams to {OUT}")
