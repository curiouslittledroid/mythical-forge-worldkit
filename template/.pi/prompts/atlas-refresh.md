---
description: Rebuild the atlas from the codex (maps/atlas-features.yaml, the feature tables and the SVG skeletons)
argument-hint: "[section or scope]"
---
Rebuild this world's atlas from the canon. Scope: ${1:-everything}.

You are the map-maker for this codex. The chain of authority is:

```
world/... place notes        canon; the only authored truth
      ↓  this prompt
maps/atlas-features.yaml     authored map data          ← the diff target
      ↓  deterministic tools
maps/atlas-features.md  +  maps/svg/*.svg  +  previews
      ↕
maps/atlas-register.md       the brief you keep true by hand
```

Never edit the rendered files by hand. If a number is wrong, fix the place note first
(if the note is wrong) or the YAML (if only the map position is wrong), then re-render.
The data schema and the commands are the kit's `meta/conventions/atlas.md`; the frames,
the sheets and the drawing rules are this world's, in the register.

## 0. Read first

1. the kit's `conventions.md` (frontmatter, ids, engine blocks) and `meta/canon-digest.md`.
2. `maps/atlas-features.yaml` — the current data. Read it before the notes, so you can recognise
   what has *not* changed. Its `frames:`, `default_frame:` and sections are the contract you extend.
3. `maps/atlas-register.md` — the world's brief: frame rules, sheet plan, drawing rules,
   corrections history, open questions.
4. `maps/_index.md` — what the world says its maps are for.
5. `maps/atlas-features.md` — the last rendered view (a quick read of what the map shows).
6. The notes that own a feature: everything under `world/places/**`, and whatever else the register
   names as a feature-owning note. **Which notes those are is the world's answer, not this prompt's.**
7. `git status` and `git log --oneline -5` — what changed since the last refresh? Use
   `git log --since=<last-atlas-commit> --name-only -- world/ maps/` to bound the work.

Finding facts is your job; changing canon is not. If a coordinate contradicts a note,
**the note wins**; fix the YAML and note the finding.

## 1. Inventory the features

For the section you are refreshing, list the drawable features its owning notes state: name, kind,
geometry, and the fact that places it. A feature already in the YAML probably has no new fact —
if the note still says 390 km and the YAML says 390, leave it alone.

**The sections are the YAML's.** Its list-valued keys (`regions`, `towns`, … whatever this world
declares) are its sections, and its `labels:` and the register say what they mean. Do not add a
section the world has not decided on; if a new kind of feature is needed, ask.

## 2. Update `maps/atlas-features.yaml`

### The contract

- **Schema** `1`. The file declares its own `frames:` (each with `x` and `y` extents in km) and a
  `default_frame:`. A frame may carry a display `name`, a grid `prefix` and a grid `grid_km`.
- **Sections** keep the order they already have. A section is any list-valued top-level key.
- **Entry keys**, in this order: `id`, `name`, `type`, `frame`, geometry (`x` + `y`, or
  `bounds: [x0, y0, x1, y1]`, or `points: "x,y x,y ..."`), then `status`, `source`, and the
  optional fields the world uses (`origin`, `population`, `length_km`, `note`, `draw`, …). A plate
  carries `title` instead of `name`; a route leg carries `from`, `to` and `km`.
- **Geometry** is in the entry's `frame`; every entry's frame must be one the file declares.
- **`status`:** `canon` (a note states it), `proposed` (a map position awaiting canon), or
  `retired` (kept for one refresh so the diff shows the retirement; delete it next time).
- **`source`:** the vault path of the note that owns the fact. The world's register says whether it
  is required; keep it on every entry you touch.
- **No derived values.** No grid references, bearings, distances between features or travel days.
  `tools/atlas_tables.py` computes them. The only distances allowed are the ones a note states as
  canon (`length_km`, and `km` on a route leg).

### Rules that keep the diff meaningful

1. **Ids never change.** Reuse the engine `loc_`/`zone_`/`faction_` id where one exists. A new
   unnamed feature gets a descriptive id (`loc_<kind>_<n>`) and `status: proposed`.
2. **Do not reorder, re-indent or reformat entries you did not change.** Insert new entries at the
   end of their section. A tidy-up is a separate commit.
3. **Change only what the canon changed.**
4. **A new number in a note is a change.** Update the entry, and add a row to the register's
   corrections section explaining what was wrong.
5. **Do not invent coastlines, new towns or new ruins.** A blank space is a plot. If the map needs a
   feature the notes do not have, ask instead of adding it.
6. **Unplaced features stay unplaced.** A feature with no coordinate in canon is absent until a
   note places it.

### Adding and removing

- New place note → add its feature, with `source`.
- Note deleted or place removed from canon → set `status: retired` for one refresh.
- Renamed place → keep the id, change `name`, and put the old form in `also_known_as`.
- A coordinate that moves → change `x`/`y` only; the diff reports the distance moved.

## 3. Validate and render

```bash
python3 tools/atlas_yaml.py maps/atlas-features.yaml   # schema, ids, frames, geometry
python3 tools/atlas_tables.py                          # maps/atlas-features.md
python3 tools/local/make_atlas.py                      # the world's SVGs, if it has a renderer
python3 tools/lint.py                                  # vault lint: must be 0 errors
```

Then refresh the previews if the world keeps any:

```bash
tools/atlas_previews.sh      # needs macOS + Google Chrome
```

Check each preview before you finish: labels legible, nothing drawn outside the neatline, no
feature missing that the diff added. Fix label placement in `tools/local/make_atlas.py`, never in
the YAML.

## 4. Reconcile the register's prose

`maps/atlas-register.md` is authored, not generated. Update only what the change falsifies: the
frame section if a frame changed, the sheet plan if a plate's frame, scale or paper changed, the
drawing rules if a new kind of feature needs one, and the corrections history with a numbered row
for every contradiction you fixed. Do not rewrite sections that are still true.

## 5. Report and commit

```bash
python3 tools/atlas_diff.py            # human-readable changes against HEAD
python3 tools/atlas_diff.py --check    # non-zero if anything changed
```

In the reply, give: the diff summary, the number of features by section, any contradiction found
(with what you did and what still needs a decision), and the files touched. If a decision is needed,
ask it as a numbered question with a recommended answer.

Commit in one commit:

```
maps: refresh the atlas (<n> added, <m> moved, <k> retired)

<one line per section that changed>
```

## 6. Done when

- `atlas_yaml.py` validates, `atlas_tables.py --check` passes, `lint.py` has 0 errors.
- The previews look right (if the world keeps previews), and every GM sheet still registers over
  its plate.
- `atlas_diff.py` shows exactly the changes you intended and nothing else.
- The register's prose is still true, and new open questions are recorded.

## Quick reference

| Tool | Does |
|---|---|
| `tools/atlas_yaml.py` | reads and validates the YAML (stdlib only) |
| `tools/atlas_tables.py` | writes `maps/atlas-features.md`; `--check` for CI |
| `tools/local/make_atlas.py` | the world's own SVG renderer, if it has one |
| `tools/atlas_diff.py` | compares the YAML with HEAD or a file; `--check`, `--section` |
