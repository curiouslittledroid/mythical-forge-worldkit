# Changelog

A world pins the kit by copying its version into `TOOLING_VERSION` and updating with
`tools/sync-tooling.sh`. **A change a world cannot absorb silently is a major bump and gets a
migration note here.**

## 1.1.2 — the rails cried wolf about the site's generated directories

Patch. A world should sync.

The site's `src/data/` and `src/content/` are the exporter's, and exist in any world that has built
its site and nowhere in the kit — so the theme rsync deleted them on every sync, and 1.1.0's new
deletion preflight therefore refused **every published world**. Excluding `data/generated` was not
enough; the parents have to go too.

This is the third release in a row where the same shape of bug appeared: a path that exists in a
world and not in the kit (or the reverse) being mistaken for a difference. The tests now cover both
cases — a world's rules in `tools/docs/`, and the generated directories — because a false alarm from
a rail is worse than no rail: it teaches everybody to pass `--force`, and then the real one is missed.

## 1.1.1 — the sync was deleting the world's rules

Patch. A world should sync.

**The bug:** the kit keeps `docs/` as a *sibling* of `tools/`; a world keeps it at `tools/docs/`. The
`tools/` rsync therefore found `docs/` in the world and not in the kit, and **deleted it on every
run** — and the next line re-created it from the kit's `docs/`. The end state was always correct, so
it never showed. But a run that stopped between those two lines left a world with **no rules at all**,
and 1.1.0's new refusals made that reachable, because a refusal is a stop. `docs/` is excluded from
that rsync now: the vendored docs are copied, and never removed.

This is the same asymmetry 1.0.11 had to fix in the drift check. It has now cost two releases, which
is why it is stated in the sync's own comments rather than left to be rediscovered.

**The ordering:** 1.1.0's refusals ran again after the script re-executed itself mid-upgrade, and
refused a tree its own first half had just changed. They run once now, at the start, on the tree the
user chose — never in the re-executed second half.

**Both were found by testing the rails on a throwaway copy of a real world, which is also how the
1.1.0 release was tested.** A rail nobody has watched fire is a rail that does not work.

## 1.1.0 — the sync has safety rails (K10)

Minor, and it can refuse. A world should sync: `tools/sync-tooling.sh` is replaced. Read the two
refusals before your next sync, because they can stop one.

Vendoring's whole safety argument is *the diff is reviewable*. Three ways it was not:

- **A dirty tree.** Syncing onto uncommitted work mixes the tooling upgrade with whatever the world
  was in the middle of, in one diff nobody can attribute. The sync now refuses when the world has
  uncommitted changes **in the paths it replaces** — `tools/`, `meta/templates/`, `site/src/`,
  `.pi/prompts/`, the workflows — and passes cleanly over the paths that are the world's own:
  `tools/local/`, its three site pages, its art, its deploy state. (`--force` overrides.)
- **A deletion nobody was shown.** `rsync --delete` on `tools/` silently removes a file a world put
  there, which is how a world's own script disappears. The sync now re-runs itself in dry-run mode
  first, lists what it *would* delete, and refuses — with the remedies: move it to `tools/local/`, or
  `--force` and let it go.
- **No rehearsal.** `--dry-run` prints every change and writes nothing: no rsync, no `cp`, no
  `TOOLING_VERSION`, no protocol re-sync.

The two refusals cost one extra fetch and one extra rsync pass, and they are the rails the
extraction's own evaluation asked for after a rehearsal found the failure mode by hand.

## 1.0.13 — the extraction's record moves here

Patch: a new document, and four open items. A world should sync — `docs/extraction.md` arrives with
the rest of `tools/docs/` — and a world with a `ROADMAP-EXTRACTION.md` of its own can now delete it.

The first world carried the extraction's plan as a temporary file, to be deleted when its last phase
landed. It has. What was worth keeping moves here:

- **`docs/extraction.md`** — the decisions (D1–D42) as they were taken, and **the evaluation**, which
  was written after the kit was built and asks which decisions survived contact, which are weaker
  than they read, and which were simply wrong. The plan's remaining open items are in `ROADMAP.md`
  now, where the work lives.
- Pointers follow: the kit's `tools/README.md` and `tools/lint.py` referred to a world's temporary
  file for their own design reasoning, which is the same defect in miniature as the citations 1.0.1
  to 1.0.7 kept finding.
- **K11–K14** are the four items the extraction left OPEN: the unchecked prose path reference, the
  codex index's tag line (chrome that wants a world's voice), a fork's missing Open Graph image, and
  the fact that the strongest proof of all — the engine pipeline — is still the most manual.

## 1.0.12 — a comment that told a small lie

Patch. A world should sync: `tools/verify-world.sh` is replaced.

The comment above the copy said the transform writes `codex-threads.yaml` into the vault, and that
this is why the checks run on a copy. It does not: it writes into the Game Ready Repository. The
copy is still right — a check should not be able to modify the world it is checking — but the reason
is now the real one rather than a plausible-sounding one. Nobody would have caught this by reading
the code; it was caught by grepping for the write the comment promised.

## 1.0.11 — the drift check failed on every world

Patch, and a lesson in shipping a check you have not run. `tooling-drift.yml` compared the kit's
`tools/` with a world's `tools/` — but a world keeps the kit's `docs/` at `tools/docs/`, inside
`tools/`, while in the kit it is a sibling. So the byte comparison reported "Only in tools: docs" on
every world, every run: an alarm that is always on is an alarm nobody reads. The comparison excludes
`docs` now, and compares `kit/docs` with `tools/docs/` as its own case, which it already did.

Found by running the check's own logic against a real world before trusting it — the same discipline
as the mutation test on the site exporter, and the reason both bugs were found by the tool rather
than by a user.

## 1.0.10 — the CI a world needed, shipped and synced

Minor: two new workflow files reach every world through the sync. A world should sync.

**`checks.yml`** runs on every push: the suites, the linter, the citation check, the disclosure check
and the guide check. Everything it runs needs neither the platform repository nor the engine, which
is why it can be CI at all. `tools/verify-world.sh` proves more and stays the local pre-commit step.

**`tooling-drift.yml`** answers the question vendoring makes easy to get wrong: is the pin behind the
kit, and do the vendored files still match the pin? Vendoring means a world commits the kit's files
as ordinary files, so a hand-edit to one is invisible until the next sync silently reverts it. The
check clones the pinned tag and diffs `tools/`, `tools/docs/` and `meta/templates/` against it, and
names the files that differ. A world that deliberately pins an older version can set the repository
variable `WORLDKIT_ALLOW_DRIFT=true` and get a warning instead of a failure. It reaches the kit over
HTTPS; a private kit needs a `WORLDKIT_TOKEN` secret, and if the kit cannot be reached the job warns
and passes rather than failing for the wrong reason.

**`template-fork.yml`** is the kit's own, and is not shipped: on a change to the machinery it fetches
the published template, syncs the newest kit tag into it, initialises a throwaway world with
`init-world.sh`, and runs the checks and the site build on the result. That is T12 run as a job
instead of by hand: the question "can somebody start a new world from the template today?" answered
on every release. It needs the template to be reachable; it warns and passes if it is not.

## 1.0.9 — a new world could not pass its own proof

Patch. A world should sync: `tools/verify-world.sh` is replaced.

`verify-world.sh` exited 2 with "no scenarios: name some, or set `vault.scenarios`" on a world that had
written no scenarios yet — which is every world for its first eleven steps, and the exact state the
template hands to a new author. The proof script now says so plainly and passes, and only when there
is genuinely nothing to run: if scenario files exist and the config does not name them, the
simulator's own error still fires.

The distinction matters because the template's promise is "fork it and the pipeline is green". A
green that requires inventing a fake campaign first is not a green.

## 1.0.8 — a prompt came from one world, and a check that never read the prompts

Patch. A world should sync: `.pi/prompts/` is replaced.

Six places in the kit's own prose referred to files that do not exist, or to the FIRST world's files
as if they were the kit's:

- **`.pi/prompts/new-creature.md` was one world's creature rules**, not a process: the water-hole
  rule, well-wyrms, the Grown, the Lineage, a closed list naming that world's peoples. It is now the
  generic sequence — read the world's own rules first (`world/creatures/_index.md`, usually), propose,
  interview, write, check — and it says plainly that the world's rules outrank it. Nothing was lost:
  every rule in the old version is in that world's notes, which is where a world's rules belong.
- `docs/campaign-authoring-guide.md` cited `tools/verify-example.sh`, which was replaced by
  `tools/verify-world.sh` in 1.0.0; `ROADMAP.md` and `CHANGELOG.md` now mark the old name as historic.
- `site/image-prompts/README.md` documented the first world's plate files as if they were the kit's.
  It documents the shape now; a world's plates are the world's.
- `docs/conventions.md`'s example filename, `CONTRIBUTING.md`'s example tool name and
  `world.config.yaml`'s note about the template's config all named something that does not exist
  (`world.config.example.yaml`) or something of the first world's.

**The identity gate did not read `.pi/prompts/`.** That is why a file of one world's monster rules
sat in the kit through eight releases. It does now. `site/` is still excluded, deliberately, until K6
settles whether the theme ships the first world's art direction as its default.

## 1.0.7 — the image prompts cited a world's note

Patch. A world should sync and re-run `tools/verify-world.sh`.

`.pi/prompts/image-accept.md` and `image-prompt.md` sent an author to `meta/site.md` section 6 for
the image deliverables and the colour rule. That path is the WORLD's own site note: in the first
world it numbers its sections, and in a new world it need not -- so the citation dangled in a
template and warned in every world that does not number its notes. The rules are the kit's, and they
are in the kit's `docs/site.md` §6.

This is the third variant of the same mistake (1.0.2, 1.0.3, here): a kit file citing a world's
document by path or number. The convention is in `docs/conventions.md` §16.1 -- a kit document cites
the kit's documents -- and the check reports the rest as NOTES.

## 1.0.6 — the re-exec guard never fired

Patch. No world needs to do anything, but a world more than one release behind should take this
one: it is what makes every later release safe.

`sync-tooling.sh` re-executes itself when a release replaces the running script, because bash keeps
executing the text it started with: without it, a release that adds a sync step does not run that
step when a world takes the release. **The guard could never fire.** It compared the kit's copy with
the world's copy -- and the rsync three lines earlier had just made those identical, so the test was
always false. It now compares a copy of the running script, saved before the copy, with the file
that replaces it. Three tests drive a fake kit and assert that a step added upstream really runs.

Two smaller fixes found while testing it:

- the re-exec runs the script through `bash`, so it works even if the copy on disk lost its execute
  bit. That was this script's first defect, and a re-exec that fails on permissions would be worse
  than no re-exec;
- the shell tools are `chmod +x` after the copy, and the kit's `docs/` copy is guarded like the
  others: a kit without a `docs/` directory no longer kills the run.

## 1.0.5 — the sync can now bootstrap a repository

Patch. No world needs to do anything.

`tools/sync-tooling.sh` assumed its destinations existed: it rsynced into `meta/templates/`,
`site/src/`, `.pi/prompts/` and `.github/workflows/` without creating them first. A world always has
those directories, so this never showed -- and the first repository that did not (the world template,
which is meant to start nearly empty) failed on its very first sync with

    rsync: mkdir ".../meta/templates" failed: No such file or directory

Every destination is now created with `mkdir -p` before anything is written into it, and
`example-world/` gets its three subdirectories for the same reason. Found by bootstrapping the
template through the sync rather than by copying files around it, which is the point of the template
existing at all.

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
