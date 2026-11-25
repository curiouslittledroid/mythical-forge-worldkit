# Testimony

**Summary:** The site's one first-person device: a passage of reported speech from a named person who
was there, written inside the note it describes. This document is both the **specification** (what the
pipeline does with an account, §3.4–§3.5 below) and the **procedure** (how to write one, from Part 1
on). The mechanism is the kit's; the *object* — the book an account is quoted from, and the cast of
tellers — is a world's, and the world's own note names it.

**One home per fact.** A note's Summary and Details state what is true. A testimony does not restate
them: it says what one person **saw**, in their own voice, and gets one thing *wrong*. If you find
yourself summarising the Details above it, stop (Part 5).

## The specification

### 3.4 Testimony (the Reader's account)

Some pages carry an **account**: a first-person passage, reported speech from a named person who was there, three paragraphs long or more. **To write one, follow [[testimony-guide]]** — that is the procedure; this section is the specification. It is not the page's voice and not a Folklore (a Folklore is what a *region* believes, one or two sentences, unattributed).

- **It is canon, and it lives in the note.** A `## Testimony` section in the note it describes, marked `**Disclosure:** open`. One home per account. Its home, its cast and its authoring rules are [[the-readers-book]].
- **The first line is the entry heading, in the Reader's own voice** — he is the one writing, so it says **me**, not "him": `**CY 649, in the BLAZE.** **Sabel Cray**, at the slips in Dustport — told to me.` Its order is fixed and it is his: **the date first** (he never omits it and never puts it elsewhere), **then the person**, **then the place**, then how the account reached him (`copied from her letters`, `told to me`, `my own eyes`). This line is load-bearing: it tells the exporter who is speaking, when, and therefore which volume of the book the account belongs in.
- **`**Quote:**` on the next line is optional.** It is the pull-quote. Without one, the opening sentence is used.
- **The exporter lifts the section out of the body** into `testimony:` frontmatter (`teller`, `transmission`, `heading`, `quote`, `taken`, `paragraphs`). The layout shows the **pull-quote at the head with the byline `CY <year> · <teller>`** — date first, because the date is the entry's identity — and the **whole account after the body** under *From the Reader's book*, with his heading quoted as his words. A testimony that is `earned` or `sealed` is dropped like any other section; an attribution with no account under it is dropped and logged as `testimony without an account`.
- **The book runs to four volumes over seventy-five years**, and each volume has its own page. A volume asks for its accounts with **`testimony_index: <first>-<last>`** in frontmatter; its page assembles the accounts taken in those years, **oldest first**, each under the title of the page that owns it. Every account falls in exactly one volume — the first whose range holds its year. `testimony_index: true` collects everything, undated accounts included. The account keeps its one home; a volume page is a reading order, assembled the way a tag page is.
- **An account with no `CY` year is a defect**, because it silently claims to describe the present. It is not placed in any volume and is listed in the audit as `testimony_undated`; a dated account outside every volume is listed as `testimony_unplaced`.
- **The rule that keeps it consistent: a testimony may contradict another testimony; it may never contradict the note it lives in.** Two tellers disagreeing is playable. A teller contradicting the Details above them is a defect.
- **No figures** in an account unless the figure is the point, and then it must equal the note's. A figure may also name a person who is not an NPC — the point is texture, not a hook.
- **A thread reference belongs under `## Hooks`**, never in testimony: a teller may say what is public, never name a plot thread.

**Two checks guard the voices** (`docs/site.md` section 9): `tools/voice_lint.py` holds each teller to her **voice sheet** — a forbidden vocabulary (*never says*) and the **places she has been** (a place link outside it is a teller describing somewhere she never stood) — and `tools/voice_stale.py` reports every note whose canon changed after its account was written. The staleness check reads the account's year, because **an account may be old on purpose**: see `docs/testimony.md` section 3.5.

### 3.5 Voice sheets and staleness

- **The sheets live in `## Author Notes` of [[the-readers-book]]**: authoring material, never published. Six parts per teller — range, blind spots, wrong about, signature, never says, samples. Two are machine-readable, and those two are the checks.
- **`voice_stale.py` reads git history, not frontmatter.** `git blame --line-porcelain` gives every line a commit and an author time; the note is split into sections with the same parser the linter and the exporter use; the newest line in the voice section is compared with the newest line anywhere else. Body newer than voice = **stale**. Nothing is stamped into a note, and no derived value is authored — a recorded date would be a second source of truth that can lie.
- **Three verdicts, because most of the book is old on purpose.** An account taken within `RECENT_YEARS` (5) of the present must still agree with the canon around it — that is **`STALE`** when it does not. An account taken before that window is **old by design**: it describes its own moment, and is not nagged about. An account with **no year is `undated`** and is always reported, because it claims to be current. The present year is read from [[calendar]], which owns the count; the script does not restate it.
- **Its limits:** an uncommitted edit is invisible to blame, so a dirty note reads `unknown`, never `ok`; a squash-merge or whole-file rewrite makes everything simultaneous, which causes **misses, never false alarms**; author time is used, not committer time, because a rebase preserves it.
- **The reference case:** before any testimony existed it was run against the 18 `## Folklore` sections — **7 flagged**, of which two were true drift and two revealed defects the check was never meant to find (a Folklore that was really a register statement, and three pages believing the same thing in the same words). Four needed no change. That ratio is why it reports rather than gates.

## How to use the procedure

- **Read Parts 1 and 2 once, with your world's own note open** — the cast and the book are the world's.
  You will use Parts 3 to 5 every time, and Part 6 whenever a check fails.
- **Nothing here is published except the account itself.** Voice sheets, this document and the rules
  never ship.

## Part 1 — Write an account, in five steps


### 1. Choose the page

The account lives in the note it describes, so choose the **note whose open Details contain the fact you are voicing**. Not the faction; the thing. A pilgrim's dawn belongs on [[vigil]], not on the Church.

Check the note publishes: its Details must be `open`, or the page will not exist. `python3 tools/disclosure.py --check` must stay clean.

### 2. Choose the hand who could stand there

A hand can only speak about what is inside her **range** (Part 4). If the right hand has never been there, either a different hand, or the range is wrong, or the account is the wrong idea.

### 3. Write the entry heading — the order is fixed

Every entry opens the same way, because he always writes it that way: **the date, then the person, then the place, then how it reached him.**

```markdown
## Testimony
**Disclosure:** open
**CY 601, in the MELT.** **Edith Vane**, at Vigil — copied from her letters, after her death.
```

- The **date is first and is never omitted.** An account with no `CY <n>` silently claims to describe the present, and `voice_stale.py` will report it.
- **A date is approximate when he wrote the entry later than the event — never because the event is old.** This is the one to get right. An entry made in CY 578 is dated exactly, because he made it in CY 578 and knew the year; it does not matter that it is seventy years ago now. What costs him the date is **the delay between the happening and the page**: a conversation taken down the same evening is exact, and a letter copied after the writer's death is `CY 601, or near it — the MELT.` The hedge vocabulary is closed — **or near it**, **or thereabouts**, **as near as I can make it**, **I make it**, **my best reckoning**, **so far as I know**, **I cannot be sure** — and any of them makes the site print the byline as **`c. CY 601`**, so the reader is never given a precision he did not claim.
- The **teller is the first bold run that is not the date.**
- Seasons are MELT, BLAZE, LOW, CHILL ([[calendar]]).
- The section **must be marked `**Disclosure:** open`** on the line under the heading, and there may be only **one** `## Testimony` per note.

### 4. Add the pull-quote (optional but worth it)

The next line, as its own paragraph:

```markdown
**Quote:** One sentence that works standing alone.
```

Without one the exporter uses the account's opening sentence, which is often the weakest choice.

### 5. Write the account

- **His own passages are I and me.** The transmission line is his journal, so "told to **me**". The codex still describes him in the third person; only the book speaks as him.
- **300 to 600 words**, several paragraphs. A campfire anecdote, not a report. Hard cap 800.
- **Register is the teller's**, and the six-part sheet is what keeps it (Part 4).
- **End on something** — an opinion, a threat, a small human detail, a thing she is wrong about.

Then run Part 7's checks before you move on.

## Part 2 — The voice sheet


One sheet per hand, in `## Author Notes` of [[the-readers-book]]. Six parts; **two are machine-checked** and four are for the reader.

| Part | What it holds | Checked |
|---|---|---|
| **Range** | the places she has been, as wikilinks. A place link outside it fails the lint | ✅ `voice_lint` |
| **Blind spots** | what she cannot know. This is the guard against a teller who knows too much | reader |
| **Wrong about** | two or three things she misunderstands. **The most important part** | reader |
| **Signature** | units, oath, opening, pet metaphor — how she measures the world | reader |
| **Never says** | a short forbidden vocabulary: words from other trades, other classes, other places | ✅ `voice_lint` |
| **Sample** | three sentences that calibrate new prose | reader |

Two notes on writing them:

- **"Wrong about" is the anti-drift device.** A teller with a declared misunderstanding can be out of date without being in error, and the reader gets to feel clever. Edith believes the well under the Tithe-house is the Giver's own. It is not, and she never finds out.
- **"Never says" is about class and trade, not vocabulary size.** Sabel is a wrecker who cannot read: *resonant* and *provenance* are not hers. The Reader is a bookman: he **quotes** trade jargon, he does not use it.

A sheet is written **when the hand's first account is written**. Until then `voice_lint` warns and does not fail — that warning is the reminder, not a bug.

## Part 3 — The five rules


1. **A testimony may contradict another testimony. It may never contradict the note it lives in.** Two tellers disagreeing is playable. A teller contradicting the Details above them is a defect — the page and its account are the same page.
2. **Age is not error, and neither is doubt.** An account taken in CY 590 describes CY 590, and one he dated *or near it* only claims to be about then. It may be wrong about the present and still be true. What it may never do is describe the present *incorrectly without saying it is old* — which is what the date is for.
3. **No figures**, unless the figure is the point, and then it must equal the note's. Otherwise: "a cup", "a day's walk", "three houses". A figure may name a person who is not an NPC — the point is texture, not a hook.
4. **No threads and no secrets.** A thread reference belongs under `## Hooks`. `sealed` material may shape what a teller *avoids*, never what she says. The keystone scan reads every account (`keyword_hits` in the audit) and a hit is a line a human reads before deploying.
5. **One account per note.** A second `## Testimony` section is dropped by the exporter and logged, so it will not reach the reader.

## Part 4 — What the site does with it


The exporter lifts the section **out of the body** into page frontmatter, and the layout renders it in two places. Nothing about this is hand-written on the site.

| Frontmatter | Rendered as |
|---|---|
| `testimony.quote` | the **pull-quote at the head**, set in IBM Plex Serif, byline `CY 649 · Sabel Cray` |
| `testimony.heading` | the entry heading, quoted verbatim under *From the Reader's book* — which **links back to [[the-readers-book]]** |
| `testimony.paragraphs` | the account, after the body, in Plex Serif |
| `testimony.taken` | which **volume** of the book collects it, and `voice_stale`'s verdict |

**Volumes.** The book runs to four volumes, one page each, and each declares its years with `testimony_index: <first>-<last>`. An account is collected by the first volume whose range holds its year; `testimony_index: true` collects everything. The audit records the placement as `testimony`, and anything unplaced as `testimony_unplaced` (dated but in no volume) or `testimony_undated` (no year at all).

**To add a volume:** a new ITEM note, `testimony_index: <a>-<b>`, a row in [[the-readers-book]]'s `## The volumes` table. No code changes.

## Part 5 — The two checks


```
python3 tools/voice_lint.py      # fails: a teller using a word that is not hers, or standing in a place she has never been
python3 tools/voice_stale.py     # nags: canon that moved after a *recent* account was written
```

### `voice_lint.py` — errors and one warning

| Code | Meaning | Fix |
|---|---|---|
| **VL002** | the teller says a word from another trade or class | rewrite in her register, or the word does not belong |
| **VL003** | the account links a place outside her range | add it to her Range row **if she has genuinely been there**, otherwise cut it |
| **VL001** (warn) | no sheet for this teller | write the sheet |

`\|` is the table escape for a pipe inside a wikilink. Range rows are table rows, so **escape every pipe** — otherwise the link parses as a broken slug and a legitimate place looks out of range.

### `voice_stale.py` — three verdicts

| Verdict | Meaning | What to do |
|---|---|---|
| **`STALE`** | taken within 5 years of the present, and the canon around it changed since | read the account against the note and fix it |
| **`old (CY nnn)`** | taken before that window | nothing — it is old by design |
| **`undated`** | no `CY` in the entry heading | add the year; this one always matters |

The present year comes from [[calendar]]. An uncommitted edit reads `unknown`, never `ok` — commit before trusting a clean run.

## Part 6 — Common mistakes


| Symptom | Cause |
|---|---|
| The page vanished from the site | the note had no open section other than the Summary, so it never published |
| `####-like` rubbish in the frontmatter | two `## Testimony` sections; the second is dropped, not merged |
| `taken: 0` and an `undated` report | the `CY <n>` is missing from the entry heading |
| The account appears in no volume | its year falls between volumes; check `testimony_index` ranges |
| A teller reads like every other teller | no "Signature" or "Never says" on the sheet, or it was never used |
| `voice_lint` warns on an empty teller | the entry heading has no bold name at all: the date's bold run is not a name, and the teller must be the next one |
| The byline reads `CY 590` when he was guessing | no hedge phrase in the entry heading: `taken` will be right and `approx` will be false, so the site asserts a precision he never claimed |
| The account is stale six months later | it was written inside the 5-year window, so it *is* held to the present. Either keep it true, or date it back beyond the window and let it be old |

## Links

- `site.md` §3.3 — how a note's tags publish (accounts are scanned for keystones like any text)
- `conventions.md` §7 — the disclosure classes, which decide whether an account publishes at all
- a world's own testimony note — its book, its cast and its voice sheets
