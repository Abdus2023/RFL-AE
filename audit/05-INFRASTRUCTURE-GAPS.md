# 05 — Infrastructure gaps

Part of the [deep audit](README.md). Original report sections **§15–§16**.

---

## §15. The current repository has no CI authority

The remote branch reports:

```text
protected: false
required status checks: off
```

and the commit-specific workflow query returned:

```text
workflow_runs: []
```

The repository root also contains no `.github/workflows/` tree.

Therefore there is currently no remote execution authority establishing:

```text
branch HEAD
    ↓
CI
    ↓
artifact
    ↓
verified
```

This is especially important because one of RFL-AE's own principles is:

```text
CI is execution authority;
local inspection is evidence for diagnosis,
not evidence of execution.
```

At present the repository describes that principle better than it enforces it.

Classification

```text
PROVED infrastructure gap.
```

> **Maintainer note — verified, claim holds.** There is no `.github` directory
> in the working tree and no `*.yml` or `*.yaml` file anywhere in the
> repository. Branch protection and required-checks state were reported by the
> auditor from the GitHub API and were not independently re-queried here, but
> the absence of any workflow definition is confirmed locally. The observation
> that the corpus states the "CI is execution authority" principle while having
> no CI is correct and is the sharpest self-consistency finding in the report.

---

## §16. Commit authenticity

The current HEAD commit reports:

```text
verification:
    verified: false
    reason: unsigned
```

That isn't inherently a defect for an ordinary Git repository.

But for this particular architecture, it becomes relevant.

RFL-AE wants:

```text
artifact
→ digest
→ provenance
→ authority
→ evidence
```

Eventually the repository should probably distinguish:

```text
developer commit
AI-generated artifact
CI-produced evidence
release certificate
```

with cryptographic provenance where required.

Otherwise the project's own evidence model stops one layer below Git
provenance.

> **Maintainer note.** The unsigned-commit observation is consistent with how
> this branch was produced: commits were made through the sandbox's configured
> GitHub authentication with no signing key available, so
> `verification.verified: false` is expected rather than anomalous. The
> architectural point stands independently of that: the corpus specifies
> receipt signing and content-addressed digests for execution evidence
> (`EXECUTION.md` §451, §435) but nothing equivalent for its own artifacts.
