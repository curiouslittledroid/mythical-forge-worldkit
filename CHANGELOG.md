# Changelog

A world pins the kit by copying its version into `TOOLING_VERSION` and updating with
`tools/sync-tooling.sh`. **A change a world cannot absorb silently is a major bump and gets a
migration note here.**

## 1.0.4 — the check got stricter, and found more

Patch. A world should sync and re-run `tools/verify-world.sh`.

Three changes to `tools/check_citations.py`, each of which found citations that the previous
version accepted:

- **It now reads the site's markdown.** `site/` was skipped wholesale, so the art prompts -- which
  cite section numbers in a checks table -- were never checked. Three of them cited a section of the
  world's site note that does not exist; one cited the palette in the wrong section.
- **A reference to a document this repository does not have is reported, not skipped.** A kit prompt
  legitimately cites a world's atlas register, and in the kit that reference resolved to nothing and
  vanished. That silence is exactly how the `thread` template kept a stale citation until a world ran
  the check (1.0.3). These are printed as NOTES at the end of a run: visible, and not failures.
- **A reference that names a directory no longer falls back to a bare basename match.** `meta/site.md`
  was matching the kit's `docs/site.md`, which made a citation of the world's note look like a
  citation of the kit's -- and the same bug hid the palette citation named above.

Also fixed, all in the kit's own files: `tools/site_export.py`, `site/astro.config.mjs` and
`site/image-prompts/_style.md` cited `meta/site.md` where they meant `docs/site.md`. In a world the
first path is the world's own site note with different numbers.

## 1.0.3 — a template that cited a world note by number

Patch. A world should sync and re-run `tools/verify-world.sh`.

`meta/templates/thread.md` told an author that the thread classes were in a section of a world note.
The kit could not see the problem: that note lives in a world, so in the kit the citation resolved to
nothing and the check passed. In a world it resolved, and the number was wrong -- the note has been
cut back, and that section is no longer there. The classes are the kit's own concept, so the template
now cites the kit's `docs/thread-pattern.md` §6.

The rule this teaches: **a template cites the kit's documents, never a world's.** A template is
copied into a world whose notes are numbered differently or reduced, and the kit's own CI can only
see the citations that resolve inside the kit.

## 1.0.2 — two dozen citations the check found in the kit's own voice

Patch. Nothing a world authors changes; a world should sync and re-run `tools/verify-world.sh`.

The citation check's first findings were not only in a world's notes. Four of the kit's own tools
and docs cited the world's site note (`meta/site.md`) where they meant the kit's (`docs/site.md`) --
a path that resolves to a DIFFERENT document in a world, which is exactly the ambiguity
`docs/conventions.md` §16.1 forbids. In the kit the citation read correctly; in a world it pointed at
a note with different section numbers. Fixed by naming the path, not the basename.

## 1.0.1 — the citation check

Patch: no world's content changes and no section number moves. **Re-run your own proof**
(`tools/verify-world.sh`) — the check below is new, and it will report citations that were already
wrong before this release.

**New: `tools/check_citations.py`.** Every `§N` citation is resolved against the document it names.
It fails when the number does not exist, when the document numbers nothing, and when the document
cannot be found. Renumbering a document is the change it exists to catch: a section that moves takes
every citation of it with it, silently, here and in every world that synced the old numbers. Wired
into `verify-kit.sh`, `verify-world.sh` and CI. The rule it enforces is in `docs/conventions.md`
§16.1.

**Fixed — the check's first findings.** Twelve citations gave the testimony specification its old
document name (`docs/site.md`) although those sections are `docs/testimony.md` §3.4/3.5; the atlas
refresh prompt cited the register's corrections table and its build section by the numbers they had
before a renumbering; and a few citations in the kit's own docs pointed at sections that do not
exist. A world that cites these documents will see the same findings.

**Nothing else changed.** `template: true`, the `example-world` linter exclusion and the sync's
example mirror are groundwork for the world template and land in the next release.

## 1.0.0 — the extraction

The first release: the tooling and the general rules lifted out of the first world
(`hollowfall-codex`), with every world-specific value moved behind `world.config.yaml`.

**If you are migrating a world that predates the kit**, the changes that are not silent:

1. **A `world.config.yaml` is now required at the vault root.** It replaces the values that used to
   be hardcoded in the tools: the world's id, title, its overland entity, its game-ready repository,
   the ids of the notes the tools must find, and the site's navigation. See `docs/conventions.md`
   §2.
2. **`MYTHICAL_FORGE_ROOT` has no default.** It must point at the platform repository (the directory
   holding `packages/authored-content`). Every tool fails loudly and names the variable if it is
   unset; the old default silently produced `Cannot find module 'yaml'`.
3. **Scenarios live with their campaign**, not in `tools/`. `vault.scenarios` names the directory.
4. **`visibility` is gone.** The publish axis is the disclosure class (`open`, `earned`, `sealed`) on
   every lore section, and the site exports the `open` ones. A GM-only note is written in full and
   classified, never omitted.
5. **Spelling is a setting** (`vault.spelling`); the linter checks it. Metric stays mandatory.
6. The documents a world used to hold are now the kit's, cited **by name and section**. A world keeps
   a pointer note for each (see its `meta/campaign-authoring-guide.md` for the pattern).
7. **A world vendors the kit's documents at `tools/docs/`**, written by the sync: the rules are part
   of the tooling, because a tool enforces a rule the world's agent has to be able to read.
8. **`tools/verify-world.sh` replaced `verify-example.sh`**, and it overlays nothing: it runs the
   world's own vault and its own scenarios. A world no longer carries a copy of a fixture it does not
   own — delete `meta/templates/examples/ferryman/` and keep the world's examples in `meta/examples/`.
   `meta/templates/` is now wholly the kit's and is mirrored, so anything a world adds there is
   removed by the next sync.
