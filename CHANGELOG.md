# Changelog

A world pins the kit by copying its version into `TOOLING_VERSION` and updating with
`tools/sync-tooling.sh`. **A change a world cannot absorb silently is a major bump and gets a
migration note here.**

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
