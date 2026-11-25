---
description: "Run an image prompt note: compile it, generate candidates, look at each one, score it against the checks, log the round"
argument-hint: "<plate slug> [candidate count]"
---
Run the plate: **$1**. Candidates: ${2:-the note's `n`}.

You are running one round of the image loop. A round is: **compile → generate → look → score → log**. You do not edit the prompt during a run.

## 1. Load

Read `site/image-prompts/$1.md` (or the file whose `slug` matches) and `site/image-prompts/_style.md`.

Assemble the prompt as exactly two parts, joined by one blank line:

1. the text inside the note's ```prompt fence, verbatim;
2. the ```style block named by the note's `style:` field, verbatim.

Append the `## Avoid` list **only** if the note's `avoid_appended` is `true`, or the user asks for it in this run. When appended, compress it to 3–5 items, one sentence, at the end.

## 2. Generate — one call

`generate_image` with:

- `prompt`: the assembled text (your own numbering and prose never enters it);
- `model`, `aspect_ratio`, `resolution`, `n`: from the note unless the user overrides;
- `output_path`: `<note's candidates dir>/v<version>` — the extension adds `-1`, `-2`, … for n > 1;
- `open_in_preview: false` (the user opens what they want).

If the user names a reference image, pass it as `input_references` and say so in the report.

## 3. Look at every candidate

Open each saved file with the read tool. **Judge what is in the picture, never what the prompt asked for.** For each candidate, go down the note's `## Checks` table and mark pass or fail. A check passes only if you can point at the thing in the image.

Then apply `## Must say` as a whole: if a viewer would not come away with the claim, it fails even when every individual check passed.

## 4. Report

A table — one row per candidate — then a recommendation.

| Candidate | Fails | What is actually wrong |
|---|---|---|
| v2-1 | #1, #6 | framed window in the cap; the far lane is lit grey |

Then:

- **Fails common to every candidate:** name the clause that caused it and propose the exact replacement wording. Do not apply it — that is `/image-iterate`'s job.
- **Best candidate**, and the two or three changes that would make it acceptable.
- **Anything that contradicts canon**, raised as a question.

## 5. Log

Append one row per candidate to the note's `## Iteration log`: version, date, model, what changed for this version, `pending user`, and the file paths. Leave the verdict for the user's answer.

## Rules

- One `generate_image` call per invocation unless the user asks for another round.
- Never edit the prompt body to get a better picture: that hides what the prompt actually does.
- Never describe an image you have not opened.
- If the note has no `## Checks` table, stop and say so — the round would have nothing to judge against.
