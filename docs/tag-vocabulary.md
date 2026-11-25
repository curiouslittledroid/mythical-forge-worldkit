# Tag Vocabulary

**Summary:** What a `tags:` entry may be, the five rules that keep a world's tag set a **vocabulary**
rather than an index trail, how the linter enforces it, and how the site's published themes are chosen
from it.

**This is the kit's mechanism.** The *vocabulary itself* — the tags, the families they fall in, the
merge and retirement decisions — is a world's, and lives in the world's own note. The rules, the
lint codes and the shape of the machine-readable block are fixed here.

## What a tag is for


A tag is a **facet**: the answer to "show me everything about X", across folders and kinds. It is not a
copy of what another field already says, and it is not a note-type marker.

| Rule | Statement |
|---|---|
| **R1 — A facet carries mass** | A facet tag appears on **≥3 notes**. One- and two-note tags are noise: the note's own links do the job. |
| **R2 — Classes are closed** | A tag drawn from a list the lore already defines is kept at any count: the **8 relic categories**, the **5 magic traditions**, the **leyline magic classes**, the **Choir vocabulary** and the **Choir root stages**. |
| **R3 — A name tag names its home** | A place or power tag is the slug of a note of that kind (minus a leading `the-`): `seam` → `the-seam`, `bloom` → `the-bloom`. A people tag is a `race_`/peoples note slug. |
| **R4 — One spelling per concept** | Variants merge to the canonical form: plural peoples, singular classes. |
| **R5 — No duplicate statements** | A tag goes when `kind`, the folder, `era:` or another tag on the same note already says it, and an NPC's people tag goes once `race:` records it. (Duplicates of `groups:` and `home:` are *not* removed yet — see open question 4.) |

**R2, R3 and R4 are the world's to satisfy**, not the kit's: which lists the lore already defines
(closed classes), which note a naming tag resolves to, and which spelling is canonical are decisions a
world makes once and records in its own note.

## The machine-readable block

The linter reads a fenced `tags-vocabulary` block in the note the world's config names in
`vault.notes` (and `site_export.py` reads it for the published set). Shape:

```tags-vocabulary
<family>: [tag, tag, ...]      # one line per family; the family is a label, not a rule
gm_only: [tag, ...]            # facets that must never reach a published page
homes:                         # a naming tag -> the note it must resolve to
  <tag>: <note-slug>
```

- A tag not listed in the block is a **lint error**; a vault with no block is not checked at all, so
  the linter's fixtures still work.
- A **naming** tag (one that names people, powers or places) must resolve to a real note, through its
  `homes:` entry, its own slug, or `the-<tag>`.
- The **published set** is a separate list, in the site's vocabulary (see `docs/site.md` §3.3): it is a
  subset of the world's tags, never a new vocabulary. A published tag that no note carries is a build
  failure, so a theme cannot rot.

## Publishing

A site publishes a **subset**, drawn from the vocabulary, of tags that cross sections and mean
something to a reader. The mechanism — the vocabulary block, the audit's `withheld_tags` and
`empty_tags`, the deny-by-default rule — is `docs/site.md` §3.3. The rule of thumb for a world: if a theme
lives in one section it is a worse copy of that section, and a sealed keystone is never a theme.

## Enforcing it

`tools/lint.py` enforces the block, so the vocabulary stays true instead of decaying:

| Code | Level | Rule |
|---|---|---|
| `TG001` | ERROR | a tag is not in the vocabulary |
| `TG002` | WARN | a naming tag (peoples, powers, places) resolves to no note, via its `homes:` entry, its own slug, or `the-<tag>` |

## How to reduce a tag set

A world that starts from a messy field (one world began with 214 distinct tags, 94 of them used once)
does the reduction **once**, and records it in its own note:

1. **Count.** `grep` the frontmatter, or let the linter's error list do it: `TG001` names every tag
   that is not in the vocabulary.
2. **Classify** each into a family, a variant to merge, or a retirement. R1–R5 decide.
3. **Write the merge table** (variant → canonical) and the **retirement table** (tag → why). Both are
   the record that stops the same argument being had twice.
4. **Apply it mechanically**, then re-run the linter until it is clean. Tags are outside a site's
   changelog hash: refiling a note is not a lore revision.
5. **Choose the published set** afterwards, not during: publishing is a different question from
   vocabulary.

## Links

- `docs/site.md` §3.3 — the published set, the audit fields and the deny-by-default rule
- `conventions.md` — the `tags:` field and the frontmatter contract
- a world's own tag note — its families, its vocabulary block, its merge and retirement tables
