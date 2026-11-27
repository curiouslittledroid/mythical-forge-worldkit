---
description: "Iterate an image prompt: bump the version, apply only the named change, regenerate, compare against the last version, log the diff"
argument-hint: "<plate slug> <change to apply> [reference candidate]"
---
Iterate the plate: **$1**.

Change to apply: **$2**
Reference image (optional): ${3:-none}

One version is **one named change**. If the change is really three changes, split it into three versions — otherwise the log stops telling you what worked.

## 1. Read

The note, its last two log rows, and the style block it names. If a reference candidate is given, open it so you know what to preserve.

## 2. Decide the edit

State it before making it, in this form:

```
v<N>  old: "<clause that exists>"
      new: "<clause that replaces it>"
      reaches: checks #…
```

Then edit:

- **Only that clause.** Do not reorder the body, do not tighten other sentences, do not "improve" the parts that already passed.
- **Never name a forbidden object.** If the fix is "the post looks like a lamp", remove the lamp vocabulary and describe what *is* there instead.
- **A fix that needs a canon fact** stops here: raise it, get the decision, record it in the canon note (`## Checks` source column), then continue.
- If the fix belongs to the medium rather than the content, it goes in `_style.md`, not the plate — and it affects every plate, so say so.

## 3. Bump

`version: <N>` in the frontmatter. The previous body is in git history; do not keep dead prompt text in the note.

## 4. Generate

Same as `/image-run`: body + style tail, `model`, `aspect_ratio`, `resolution`, `n` from the note. Output to `candidates/<slug>/v<N>`. Pass the reference candidate as `input_references` when one was given — that keeps the composition while the words change.

## 5. Compare

Open the new candidates and the previous version's best. Score both against the `## Checks` table and report what **moved**:

| Check | v<N-1> | v<N> | Note |
|---|---|---|---|
| #1 slot, not window | fail | pass | the framed window is gone |
| #6 dark past the last post | fail | fail | still a grey lane |

Keep the comparison honest in both directions: a fix that breaks a passing check is a regression, and it goes in the report.

## 6. Log

Append a row: version, date, model, the old → new clause (verbatim, short), the verdict (`pending user`, or `accept`/`reject` if the user says so in this run), the files.

## Rules

- **One change per version**, always logged.
- **Never regenerate at the same version number.** Version numbers are cheap; a silently changed prompt is not.
- **Stop after the report.** The next version waits for the user's read of the images.
