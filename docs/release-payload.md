# The release payload: how a world gets the kit without cloning it

**Kit maintenance.** A world author never reads this file; what they need is `meta/conventions/
tooling.md` (which command, when) and `ARCHIVE.md`, which travels inside the archive itself.

## The problem it solves

`tools/sync-tooling.sh` had exactly one dependency on git, and it was the whole of its fetching:

```bash
git clone --branch "$TAG" --depth 1 "$KIT_REPO" "$TMP/kit"
git describe --tags          # only to learn the tag, because a clone arrives with no memory of one
```

Everything downstream reads **a tree**: `$TMP/kit/tools/`, `$TMP/kit/template/meta/conventions/`,
`$TMP/kit/site-theme/`. A world never needed the kit's history, and cloning it cost three things:
a `git` on the machine, a network round trip to a forge, and a payload nobody could inspect — the
domain of what a world receives was defined by which branches of the sync's shell happened to run.

A **release payload** is that tree, published. It is attached to every tag, it is identical on every
download, and its digest is in the release notes.

## What is in it

The kit's own layout, curated to what a world receives — because *keeping* the kit's layout is what
made the change surgical: the sync's placement code, its exclusions, its rails and its re-exec are
untouched, and the archive is interchangeable with a checkout by construction.

| in the payload | a world holds it at | written by |
|---|---|---|
| `tools/` (minus `local/`, `docs/`) | `tools/` | every sync |
| `template/meta/conventions/` | `meta/conventions/` | every sync |
| `template/meta/templates/` | `meta/templates/` | every sync |
| `template/.pi/prompts/` | `.pi/prompts/` | every sync |
| `site-theme/` (minus `public/`, generated output, deploy state) | `site/` | every sync |
| `.github/workflows/{checks,site,tooling-drift}.yml` | `.github/workflows/` | every sync |
| `TOOLING_VERSION` | the pin | every sync |
| `template/example-world/` | `example-world/` | only when asked for |

**Not in it, on purpose.** `tools/local/`, the three site pages, `site/public/`, the world's art and
prompt notes, `site/infra/state.json` — the sync never writes those, so shipping them would hand a
world files nothing places. And none of the kit's own maintenance: `docs/`, `CHANGELOG.md`,
`meta/platform-requests/`. `docs/extraction.md` names the world the kit was extracted from, on every
line; it must not arrive in a world's download even to be discarded.

`template/example-world/` travels for two reasons: `init-world.sh --fetch-example` repairs a deleted
demo world from the kit, and the payload can then prove itself with no checkout at all.

## The invariant, and where it is proved

> A world synced from the payload is byte-identical to a world synced from a checkout of the same
> tag.

`tools/verify-payload.sh` proves the half that can be proved without a second kit, on every commit:

1. the payload passes its own check — members, pin, forbidden paths, execute bits, traversal;
2. a world assembled from its `template/example-world/` and its `tools/` **lints with 0 errors**,
   using the tools it shipped;
3. the sync, run inside that world with nothing but the payload, places every document, template,
   prompt, workflow and pin;
4. a **second** sync changes nothing. This is the assertion that matters: it says the payload's
   layout and the sync's placement still agree, so the archive cannot quietly stop carrying
   something the sync writes — a drift that would otherwise surface in a world, after a release.

The equality itself was checked by hand while building this (two worlds at the previous pin, one
synced from a clone, one from the archive with `WORLDKIT_REPO=https://invalid.invalid/x`, then
`diff -r`): identical, with the world's own `tools/local/` script, landing page, About page and
favicon surviving in both. What makes that a structural claim rather than a lucky one is that both
transports produce `$TMP/kit` and the script never learns which ran.

## Transports, in the order tried

| | when |
|---|---|
| `--archive FILE` | a payload on disk: no network, no git, no curl. An air-gapped machine, a corporate proxy, a burned CD. |
| `WORLDKIT_REPO=<path>` | a local checkout or bare mirror, when that path exists. How the tests and the sync's own documentation exercise it. |
| `--url URL` | a payload by URL (a mirror, a file server). |
| *(default)* | the release asset for the tag. |
| `--from-git` | force the clone: a proxy that blocks release assets, or a kit that is not on GitHub. |

**The asset URL is derived from the tag**, so it needs no API call and no rate limit:

```
https://github.com/curiouslittledroid/mythical-forge-worldkit/releases/download/v3.4.0/worldkit-v3.4.0.tar.gz
```

"The newest tag" is answered without the API too: `/releases/latest` redirects to
`/releases/tag/<tag>`, which a plain `HEAD` can read. **No token is needed**: the kit is public, so
release assets download with `curl` alone — for a world, for CI, and for a reader with no account.
A private fork of the kit would need the credential the sync already supports in `WORLDKIT_REPO`
(`https://x-access-token:<token>@github.com/...`), and the sync strips the userinfo from anything it
prints, because a token in a log line is a token in a transcript.

A tag from before release payloads existed has no asset. That is not an error: `curl` fails, and the
sync says so and falls back to a shallow clone. The twenty tags already published keep working, and
nothing had to be back-filled.

## Determinism, and the digest

`tools/build_payload.py` writes one file: sorted entries, one constant mtime, uid/gid 0, mode
preserved (a shell tool that arrives without its execute bit is the defect that cost a release once),
and a gzip header with no name and no time. The same tree produces the same sha256 — so a release can
be rebuilt and compared, and the digest is a thing worth publishing. It is printed in the release
notes, written beside the asset as `.sha256`, and **checked**:

- `build_payload.py --check` at build time, in CI, and in `release.yml` before attaching;
- `sync-tooling.sh`, before extracting, when `--sha256` is given or a `.sha256` sits beside the file.

An unaccompanied payload is a warning rather than a failure: a hand-built one is a legitimate thing to
sync from while developing the payload itself.

## What the sync refuses, and why each refusal exists

| refusal | the failure it prevents |
|---|---|
| the payload's pin ≠ the tag asked for | an asset attached to the wrong release (a copy-paste on a release page) would pin a world to a version it is not holding. An archive cannot be `checkout`-ed, so the pin is the only witness. |
| the checksum does not match | a truncated download, a corrupted mirror, a replaced asset. |
| an absolute or traversing path | extraction writing outside the temporary directory. |
| not exactly one top-level directory | `find … | head -1` would have half-applied a malformed archive and reported success. |
| the pin's target is not a worldkit (no `TOOLING_VERSION`) | any tarball at all being unpacked over a world. |

## What building this found in the existing script

Three defects, all in the same class: **an argument that is not carried across a re-entry**.

1. **The self re-exec dropped every option.** `exec bash "$0" ${TAG:+"$TAG"}` — `"$@"` was gone, so
   `--force`, `--dry-run` and (new) `--archive` were discarded. Harmless for the two rails, because
   the re-entered run skips them; fatal for an option that carries data, and it fails *quietly and
   successfully* — the first prototype run a world's worth of files from the network while the
   operator believed it was offline.
2. **The deletion preview re-ran the sync without its arguments.** Same shape, worse consequence: an
   offline `--archive` sync would fetch from the network to draw up its deletion preview, compare
   against a different tag, and report files that were never deletions. The recommendation to
   `--force` a false finding is how a reader learns to `--force` the real one. The preview now
   replays the original arguments with `--dry-run` prepended.
3. **`[ -d "$KIT_REPO/.git" ]`** — in the bare-repo-plus-worktree layout these projects use, `.git`
   is a *file*. The documented "local checkout, for testing" route never took the local branch. The
   drift check and `init-world.sh` had already learned `-e, not -d`; this one had not.

Also fixed while there: the parser was `for arg in "$@"`, which cannot consume an option's *value*
(`--archive f` left `f` to be read as the tag); and the help was `sed -n '2,26p'`, a line range that
the first new option to outgrow it silently truncated.

## The trap that the phrase "downloaded into a world" invites

Extracting the payload over a world *appears* to work. Measured: tools updated, `TOOLING_VERSION`
bumped, the world's own landing page untouched. What actually happened:

- the documents landed at `template/meta/conventions/`, where a world does not read them, so the
  world pinned `v9.9.9` while its rules were the previous version's;
- `site-theme/` and `template/` appeared beside the world's own files, which no sync will ever remove
  (they are not in the kit's tree at that path, so `--delete` cannot see them);
- `tools/` was replaced with no rails at all — no dirty-tree check, no deletion preview, no licence
  placement, no protocol re-sync.

So `ARCHIVE.md` begins with "do not extract this over a world", and the payload carries the one file
that knows where everything goes. The archive is applied **by the tools inside it**:

```bash
tools/sync-tooling.sh --archive worldkit-v3.4.0.tar.gz
```

## Getting the option in the first place

`--archive` is a flag of the **new** sync, so the version that introduces it cannot itself be fetched
with it: a world's current script parses the arguments before it fetches anything. The first update
that lands this must be an ordinary one:

```bash
tools/sync-tooling.sh v3.4.0      # once, the old way: network, or WORLDKIT_REPO=<checkout>
```

From the next release on, `--archive` is available to that world. A world with **no** `tools/` at all
is the one case where copying is right, and `ARCHIVE.md` gives the three lines.

## What this deliberately does not do

- **Not a manifest.** `tools/build_payload.py` carries a placement table (`PLACEMENT`) and a
  required-members list, so the archive's contents are data — but `sync-tooling.sh`,
  `export-template.sh` and `tooling-drift.yml` still each keep their own version of the exclusion
  list. That is K15 in `ROADMAP.md`, and the payload is now the natural place to publish the one
  list: the archive is the only artefact that exists at a tag *and* travels.
- **Not `init-world.sh --fetch-example`.** It still clones. The payload now carries the demo world,
  so that fetch can become a payload read; it is a separate change with its own test.
- **Not signed.** The digest is published and checked, which makes a replaced asset *visible*; it
  does not make it impossible. GitHub's build-provenance attestation
  (`actions/attest-build-provenance`, verified with `gh attestation verify`) is the next step if the
  kit ever needs provenance rather than convention.

## Operations

Cutting a release is unchanged (`CONTRIBUTING.md`, Release): bump `TOOLING_VERSION`, add the
`CHANGELOG` entry, tag, push the tag. Pushing a `v*` tag now also:

1. checks that the tag and `TOOLING_VERSION` are the same string;
2. builds the payload;
3. checks it;
4. proves it with `tools/verify-payload.sh`;
5. attaches `worldkit-<tag>.tar.gz` and its `.sha256` to the GitHub release, creating it with the
   digests and the "take it" snippet in the notes.

`ci.yml` runs steps 2–4 on **every** commit, so a tag is not where packaging breaks. To rebuild a tag's
payload by hand:

```bash
python3 tools/build_payload.py --out dist     # from a checkout of that tag
python3 tools/build_payload.py --check dist/worldkit-v3.4.0.tar.gz
tools/verify-payload.sh dist/worldkit-v3.4.0.tar.gz
```
