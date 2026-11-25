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
maps/atlas-features.md  +  maps/svg/*.svg  +  svg/preview/*.png
      ↕
maps/atlas-register.md       the brief you keep true by hand
```

Never edit the rendered files by hand. If a number is wrong, fix the place note first
(if the note is wrong) or the YAML (if only the map position is wrong), then re-render.

## 0. Read first

1. the kit's `conventions.md` (frontmatter, ids, engine blocks), `meta/canon-digest.md`.
2. `maps/atlas-features.yaml` — the current data. Read it before the notes, so you can
   recognise what has *not* changed.
3. `maps/atlas-register.md` — frame rules, sheet plan, corrections history, open questions.
4. `maps/geography-data.md` — the signpost note; it explains the frame and points back here. There is no second data file.
5. `maps/atlas-features.md` — the last rendered view (a quick read of what the map shows).
6. Every note under `world/places/**` (continents, regions, settlements, sites), and these
   feature-owning notes: `world/cosmology/{leylines,sentinels,the-gate,choir-roots-stages}.md`,
   `world/factions/{the-wandering-hundred,crimson-league,the-highland-holds,the-concert}.md`,
   `world/places/sites/ruin-sites.md`, `world/society/the-quiet-gardens.md`.
7. `git status` and `git log --oneline -5` — what changed since the last refresh? Use
   `git log --since=<last-atlas-commit> --name-only -- world/ maps/` to bound the work.

Finding facts is your job; changing canon is not. If a coordinate contradicts a note,
**the note wins**; fix the YAML and note the finding.

## 1. Inventory the features

For each source note, list the drawable features it owns:

- **Landmasses** — the five continents, their latitude band, area, climate, global extent.
- **Regions** — forest, fae, storm, scrub, coast, warm valley, lee coast, highland, plateau,
  steppe, crater, eddy ring, tundra, ice sheet, jungle, canopy, basin.
- **Seas and lakes** — the Dry Sea basin, the dry gulf, the brine pool, the boiled lake, the
  fossil shoreline.
- **Rivers** — course, length, source, mouth, irrigated strip.
- **Relief** — the Spine (axis, band, length, crest height), passes, glaciers, badlands,
  plateaux, the Breach, the Black Seam.
- **Deserts and plains** — the Ashen Plains, the Southern Marches.
- **Cities, towns and villages** — every settlement with a population.
- **Holds** — dwarven holds, named and unnamed.
- **Ruins and sites** — by `origin` (golden age, war wound, Choir, sentinel; [[ruin-sites]]), plus the sealed cities, wreck-fields and the mega-dungeon.
- **Sentinels** — every site that has a note of its own (the world's index, if it keeps one).
- **Leylines** — lines, remnants, wells, knots, the Gathering wells.
- **Routes** — roads, tracks, the aqueduct, deep-roads, the ruin line, the sea lane.
- **Route legs** — the distances the notes state, with terrain.
- **Holy sites** — one per shrine, grove, forge, stone, battlefield and cup-hall.
- **Territories** — the Hundred's range.
- **GM overlay** — seed-sites, Hushed counts, League Hearths, strongholds, Quiet Trade nodes.

A feature already in the YAML probably has no new fact. Do not restate the whole world.

## 2. Update `maps/atlas-features.yaml`

### The contract

- **Schema** `1`. Sections in this order: `frames`, `plates`, `landmasses`, `regions`,
  `seas_and_lakes`, `rivers`, `relief`, `deserts_and_plains`, `cities`, `towns`, `holds`,
  `ruins`, `sentinels`, `leylines`, `routes`, `route_legs`, `holy_sites`, `territories`,
  `gm_overlay`.
- **Keys per entry**, in this order: `id`, `name`, `type`, `frame`, geometry
  (`x` + `y`, or `bounds: [x0, y0, x1, y1]`, or `points: "x,y x,y ..."`), then optional
  `status`, `origin`, `magic_class`, `god`, `holder`, `population`, `length_km`, `note`,
  `draw`, `source`.
- **Geometry:** `points` is one quoted string of space-separated `x,y` pairs. `bounds` is
  `[x0, y0, x1, y1]`. Both are in the entry's `frame`.
- **`frame`:** `heartland` (default), `far_reach` or `world`. Never mix frames in one entry.
- **`status`:** `canon` (a note states it), `proposed` (a map position awaiting canon), or
  `retired` (kept for one refresh so the diff shows the retirement; delete it next time).
- **`source`:** the vault path of the note that owns the fact. Required on every entry.
- **No derived values.** No grid references, bearings, distances between features or travel
  days. `tools/atlas_tables.py` computes them. The only distances allowed are the ones a
  note states as canon (`length_km`, and `km` on a route leg).

### Rules that keep the diff meaningful

1. **Ids never change.** Reuse the engine `loc_`/`zone_`/`faction_` id where one exists
   (`loc_highwell`, `zone_green_belt`). New unnamed features get a descriptive id
   (`loc_spine_hold_3`) and are listed as `proposed`.
2. **Do not reorder, re-indent or reformat entries you did not change.** Insert new entries
   at the end of their section. A tidy-up commit is a separate commit.
3. **Change only what the canon changed.** If a note still says 390 km and the YAML says 390,
   leave it alone even if you would have phrased it differently.
4. **A new number in a note is a change.** Update the entry, and add a row to the register's
   `maps/atlas-register.md` §14 explaining what was wrong.
5. **Do not invent coastlines, new towns or new ruins.** A blank space is a plot. If the map
   needs a feature the notes do not have, ask instead of adding it.
6. **Unplaced features stay unplaced.** The seven ordinary Silent Cities and any unnamed
   settlement are simply absent until a note places them.

### Adding and removing

- New place note → add its settlement or site, with `source`.
- Note deleted or place removed from canon → set `status: retired` for one refresh.
- Renamed place → keep the id, change `name`, and put the old form in `also_known_as`.
- A coordinate that moves → change `x`/`y` only; the diff reports the distance moved.

## 3. Validate and render

```bash
python3 tools/atlas_yaml.py maps/atlas-features.yaml   # schema, ids, references
python3 tools/atlas_tables.py                          # maps/atlas-features.md
python3 tools/local/make_atlas.py                            # the sixteen SVGs
python3 tools/lint.py                                  # vault lint: must be 0 errors
```

Then refresh the PNG previews:

```bash
tools/atlas_previews.sh      # needs macOS + Google Chrome
```

Check each preview before you finish: labels legible, nothing drawn outside the neatline,
no feature missing that the diff added. Fix label placement in `tools/local/make_atlas.py`
(`LABELS`, `ZONE_LABELS`, `LINE_LABELS`), never in the YAML.

## 4. Reconcile the register's prose

`maps/atlas-register.md` is authored, not generated. Update only what the change falsifies:

- **§3 sheet plan** if a plate's frame, scale or paper changed.
- **§5–§12** (feature register, the plates, the legs) if a section gained a feature that
  needs a drawing instruction, or a plate's frame changed.
- **§13 GM overlay** if a secret site moved.
- **§14 corrections applied** — add a numbered row for every contradiction you fixed, with
  what the notes now say.
- **§15 how it is built** if a sheet file was added or renamed.
- **Open questions** — close what is settled, add what you found.

Keep the voice: concise, British English, tables over prose, recommendations attached.
Do not rewrite sections that are still true.

## 5. Report and commit

```bash
python3 tools/atlas_diff.py            # human-readable changes against HEAD
python3 tools/atlas_diff.py --check    # non-zero if anything changed
```

In the reply, give: the diff summary, the number of features by section, any contradiction
found (with what you did and what still needs a decision), and the files touched. If a
decision is needed, ask it as a numbered question with a recommended answer.

Commit in one commit:

```
maps: refresh the atlas (<n> added, <m> moved, <k> retired)

<one line per section that changed>
```

## 6. Done when

- `atlas_yaml.py` validates, `atlas_tables.py --check` passes, `lint.py` has 0 errors.
- The previews look right, and every GM sheet still registers over its plate.
- `atlas_diff.py` shows exactly the changes you intended and nothing else.
- The register's prose is still true, and new open questions are recorded.

## Quick reference

| Tool | Does |
|---|---|
| `tools/atlas_yaml.py` | reads and validates the YAML (stdlib only) |
| `tools/atlas_tables.py` | writes `maps/atlas-features.md`; `--check` for CI |
| `tools/local/make_atlas.py` | writes the sixteen SVGs |
| `tools/atlas_diff.py` | compares the YAML with HEAD or a file; `--check`, `--section` |
