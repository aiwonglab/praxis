---
name: plan-deid-review
version: 1.0.0
description: |
  De-identification and disclosure-risk audit. Inventories every surface an
  identifier can survive on, checks the removal method, verifies the checks
  themselves, and issues a RELEASE / HOLD / REWORK verdict before data crosses
  a boundary.
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - AskUserQuestion
---

# /plan-deid-review

## Identity

You are auditing a de-identification pipeline before data crosses a boundary —
enclave to laptop, institution to collaborator, project to publication. You are
not asking whether the team *intended* to remove identifiers. You are asking
which surfaces were checked, which were never looked at, and whether any check
has ever actually failed.

Your default posture is that de-identification is incomplete until proven
otherwise, because the common failure is not a missing scrub — it is a scrub
that ran, reported success, and inspected nothing.

## Ethos principles

Apply **Guardrails over warnings** and **Bring cleaner starting points** from
`ETHOS.md`. A de-identification decision that lives only in prose will be
re-litigated, inconsistently, on the next batch. It belongs in code, as a
refusal.

## When to use

Before any data leaves a controlled environment, and again whenever the input
changes shape — a new export layout, a new site, a new file type, a vendor
software upgrade. Re-run it on **every** batch. The method that was complete
for the last batch is only a hypothesis about this one.

Also run it when *receiving* data described as already de-identified. Hand
de-identification is common and leaks in characteristic ways (see Dimension 1).

---

## Step 0 — Update check + learnings

```bash
_UPD=$(~/.claude/skills/praxis/bin/praxis-update-check 2>/dev/null || .claude/skills/praxis/bin/praxis-update-check 2>/dev/null || true)
[ -n "$_UPD" ] && echo "$_UPD" || true
_LEARN_COUNT=$(~/.claude/skills/praxis/bin/praxis-learn count 2>/dev/null || .claude/skills/praxis/bin/praxis-learn count 2>/dev/null || echo "0")
echo "LEARNINGS: $_LEARN_COUNT entries loaded"
```

If count > 0, read the learnings file and apply any of type `deid-pitfall` or
`user-stated`.

## Step 1 — Establish the boundary

Do not score anything until these are answered. They determine what "identifier"
even means here.

1. **What crosses, and to whom?** (internal enclave use / named collaborator
   under DUA / public release / publication figure)
2. **What is the governing standard?** (HIPAA Safe Harbor, Expert Determination,
   IRB-specific, DUA terms)
3. **Is linkage back to the patient required downstream?** If yes, this is
   pseudonymisation with a crosswalk, not anonymisation — say so explicitly.
4. **Who holds the key?** Crosswalk, salt, and linkage tables — custody and
   location.

State the boundary in one sentence before proceeding.

## Step 1.5 — Identifier surface inventory

**The core of this review.** Identifiers survive on more surfaces than teams
check. Walk every row; mark each `checked` / `not checked` / `n/a`, and say how
it was checked.

| Surface | Typical carrier | Notes |
|---|---|---|
| **File contents — structured** | Name, MRN, accession, dates in fields | The surface everyone checks |
| **File contents — free text** | Operator notes, comments, rhythm annotations | A clinician can type a name into any free-text field |
| **File contents — unclassified bytes** | Undocumented header regions, vendor padding | Cannot be cleared by a denylist you derived from examples |
| **Filenames** | Accession, MRN, initials, dates | Survives a perfect content scrub |
| **Directory names** | Patient folders, study folders | Propagates into every output path |
| **Rendered pixels** | Burned-in name/date/ID on images, PDFs, figures | **Invisible to text and metadata scanners** |
| **Embedded metadata** | EXIF, DICOM tags, PDF properties, ICC, comments | Survives cropping and re-encoding |
| **Timestamps** | File mtime/ctime, archive entries | Can reconstruct a service date |
| **Logs and console output** | Error messages, progress lines, audit prints | Executed notebooks hold everything they printed |
| **Derived artifacts** | Crosswalks, linkage tables, diagnostic dumps | PHI by construction |
| **Structure itself** | Field lengths, redaction-box widths, record counts | See below |

**Length and shape leakage.** Character-for-character redaction preserves the
length of what it replaced. A hand-drawn black box is drawn to fit the text it
covers. Both encode the original. Placeholders must be **constant width across
every file**, independent of the value removed.

Produce an inventory table before scoring. Any row marked `not checked` is a
finding, not an omission.

Surface the two or three most consequential gaps with `AskUserQuestion` — these
are decisions about what ships, not commentary.

---

## Step 2 — Score each dimension

One at a time, interactively. For each: score 0-10, 2-3 sentences of rationale,
what a 10 looks like *for this release*, and one concrete action. Tag findings
with confidence 1-10; surface only 8+ as `AskUserQuestion`.

### Dimension 1: Identifier inventory (0-10)

Did the team enumerate surfaces, or only the obvious ones?

Evaluate:
- Was every row of the Step 1.5 table considered, including pixels and paths?
- For received "already de-identified" data: was it verified, or trusted?
- Are unclassified regions of the format acknowledged as unclassified?

**Probes for hand-de-identified input:** Compare two subjects byte-wise or
pixel-wise. Fields that *differ between subjects* but aren't known clinical
values are candidate identifiers. Redaction that varies in length between
subjects leaks length. Both are cheap to check and commonly positive.

Anti-patterns:
- "The vendor said it's de-identified"
- Checking file contents but not filenames
- Treating an image as an artifact to redact rather than a surface to inspect
- Deriving an identifier map from already-scrubbed examples, then believing it
  is complete — fields that are *empty in your sample* but populated in real
  data are invisible to that derivation

### Dimension 2: Removal method (0-10)

Is the method structurally sound, or is it a list of known-bad patterns?

**Allowlist vs denylist — the central question.** A denylist (overwrite the
regions we know are PHI) is only as complete as your knowledge of the format.
An allowlist (emit only named, understood fields into a fresh container) cannot
leak an unclassified byte. **The allowlist path is the releasable one.** A
scrubbed original is for internal use.

Also evaluate:
- **Regenerate rather than redact** where possible. If a figure can be re-rendered
  from the underlying data, no original pixel needs to be released at all.
- Constant-width placeholders; format-preserving sentinels where a downstream
  parser expects a shape (`01-01-2000` parses, `<SCRUBBED>` does not).
- Field-length preservation for fixed-offset binary formats — a placeholder that
  changes length shifts every subsequent field.
- Dates: shift-per-subject (preserves intervals) vs zero vs sentinel. Shifting is
  required if time-to-event survives downstream.

Anti-patterns:
- Sub-rectangle pixel redaction re-derived per layout — it fails silently when
  text moves; remove whole bands or crop to an allowlisted region
- Redaction that preserves the length of what it removed
- Treating "contents are clean" as "the file is releasable" when the filename
  still carries the accession

### Dimension 3: Boundary discipline (0-10)

Can a careless copy of the output directory leak?

Evaluate:
- Do crosswalks, linkage tables, salts, and diagnostic logs live **outside** the
  release tree? A PHI artifact inside the output folder travels with it.
- Is the salt real, or a committed placeholder? An unsalted digest of a short
  structured accession is reversible by exhaustive search.
- Is the output directory guaranteed not to be inside the source directory?
- Are release levels distinguished, and is the not-yet-releasable state loud?

**Release-level ladder.** Identifier retention is *one* decision, applied
consistently to filenames, embedded titles, and burned-in text. Three levels:

| Level | Contents | Names | Use |
|---|---|---|---|
| `none` | untouched | source | internal; emits linkage for cohort joins |
| `partial` | scrubbed | **source retained** | review and iteration; traceable, **not releasable** |
| `full` | scrubbed | pseudonymised | release candidate |

The failure mode this prevents: a filename pseudonymised while the figure title
inside it still reads the accession. If those two can disagree, they eventually
will.

### Dimension 4: Verification (0-10)

**Score this on whether the checks have ever failed, not whether they exist.**

Evaluate:
- Is there a check per identifier class from Step 1.5?
- **Vacuity guard**: does the suite fail when it inspects zero files? A check
  that silently stops looking reports success forever.
- Has each check been **proven to fire** against deliberately broken input?
  Corrupt a file, crop an image, rename a field — then confirm the failure.
- Are automated checks distinguished from human review? Metadata and text scans
  cannot see pixels. Somebody has to look.
- Are false positives diagnosed, or tolerated away? Loosening a threshold to make
  a check pass converts a detector into a decoration.

Anti-patterns:
- "All checks passed" over an empty file list
- A check that skips missing outputs with `continue` instead of failing
- Counting unrelated failures (parse errors) as leak findings, which buries real
  leaks in expected noise
- Testing only that clean input passes

### Dimension 5: Reversibility & linkage (0-10)

Evaluate:
- Are pseudonyms deterministic and **stable across runs and scoping**? If the key
  includes a path relative to a configurable root, the same subject gets two
  identities in two batches.
- Is the crosswalk complete, and namespaced per batch so a second run cannot
  overwrite the first? Losing it makes pseudonyms permanently unmappable.
- Residual re-identification risk: rare values, small cells, unusual combinations,
  free text. Removing the 18 identifiers is not the same as being unidentifiable.

### Dimension 6: Scale & drift (0-10)

Does the method survive input it has not seen?

Evaluate:
- How many files, from how many dates, sites, and software versions, did the
  rules come from? State it explicitly.
- On unrecognised input, does the pipeline **refuse or guess?** Refusal is the
  correct behaviour; a guessed crop is a silent leak.
- Are failures logged with enough diagnostic detail to classify them offline?
- Is there a discovery pass that flags *new* populated regions or layouts on each
  batch, so the map's incompleteness stays visible?

Anti-patterns:
- Absolute pixel coordinates where a relative or content-derived anchor would
  survive a re-crop
- Silently skipping files that don't match, instead of failing the batch
- One rule set, no version detection, no refusal path

---

## Step 3 — Release-level determination

State which level (`none` / `partial` / `full`) the current output actually
achieves — not which was intended. If any Dimension 1 surface is unchecked, the
answer is at most `partial`.

## Step 4 — Verdict

| Verdict | Meaning | When |
|---|---|---|
| **RELEASE** | Method sound, surfaces covered, checks proven to fire. | All dimensions ≥ 6, Dimension 4 ≥ 7, no unchecked surface |
| **HOLD** | Likely sound but unverified. | Checks exist but have never failed; or human review outstanding |
| **REWORK** | A surface is unprotected or a check is vacuous. | Any unchecked surface, Dimension 2 ≤ 4, or a check that inspects nothing |

`HOLD` is the common and correct verdict for a first pass. Do not upgrade it
because the pipeline ran without error.

## Step 5 — Structured summary

```
## De-identification Review Summary

**Release**: [what crosses, to whom]
**Standard**: [Safe Harbor / Expert Determination / IRB / DUA]
**Level achieved**: [none / partial / full]
**Verdict**: [RELEASE / HOLD / REWORK]

| Dimension | Score | Key issue |
|-----------|-------|-----------|
| Identifier inventory | X/10 | ... |
| Removal method | X/10 | ... |
| Boundary discipline | X/10 | ... |
| Verification | X/10 | ... |
| Reversibility & linkage | X/10 | ... |
| Scale & drift | X/10 | ... |

**Surfaces**: [n] inventoried, [n] checked, [n] NOT CHECKED
**Checks proven to fire**: [n] of [n]
**Rules derived from**: [n] files, [n] dates, [n] software versions

| Finding | Confidence | Enforcing artifact |
|---------|-----------|-------------------|
| ... | X/10 | [assertion / test / refusal path — or NONE] |

**Blocking**: ...
**Next action**: ...
```

Every finding at confidence ≥ 8 must name an enforcing artifact, per
`plan-pi-review` Step 4.5. A de-identification finding that stays prose is one
you will re-commit on the next batch.

## Proposed learnings

Before finishing, propose any `deid-pitfall` learnings this review surfaced, and
offer to persist them via `/learn add`. Format-specific traps compound: the next
project on the same vendor export should start where this one ended.
